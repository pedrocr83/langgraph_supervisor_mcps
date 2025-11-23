# mcp_tools.py
import json
from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio
from langchain_core.tools import StructuredTool
from typing import Any, Callable
import inspect
import logging
import warnings

# Suppress schema validation warnings from MCP servers
logging.getLogger("langchain_mcp_adapters").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message="Key.*is not supported in schema")


def make_sync_tool(async_tool):
    """Convert an async MCP tool to a sync tool."""
    
    # Get the coroutine function from the tool
    if hasattr(async_tool, 'coroutine'):
        async_func = async_tool.coroutine
    elif hasattr(async_tool, 'coroutine_func'):
        async_func = async_tool.coroutine_func
    elif hasattr(async_tool, 'func'):
        async_func = async_tool.func
    elif hasattr(async_tool, '_run'):
        async_func = async_tool._run
    elif hasattr(async_tool, 'ainvoke'):
        # Use ainvoke method if available
        async def async_func(**kwargs):
            return await async_tool.ainvoke(kwargs)
    else:
        raise ValueError(f"Could not find async function in tool: {async_tool.name}")
    
    # Create a sync wrapper
    def sync_wrapper(**kwargs):
        """Synchronous wrapper for async tool."""
        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, async_func(**kwargs))
                return future.result()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run
            return asyncio.run(async_func(**kwargs))
    
    # Create a new StructuredTool with the sync wrapper
    return StructuredTool(
        name=async_tool.name,
        description=async_tool.description,
        func=sync_wrapper,
        args_schema=async_tool.args_schema if hasattr(async_tool, 'args_schema') else None,
    )


async def load_mcp_servers_from_config(config_path: str):
    """Load MCP servers from config file using MultiServerMCPClient."""
    import os
    from pathlib import Path
    
    logger = logging.getLogger(__name__)
    
    # Resolve config path (handle both absolute and relative paths)
    possible_paths = []
    
    # If absolute path, use as-is
    if Path(config_path).is_absolute():
        possible_paths.append(Path(config_path))
    else:
        # Try relative to current working directory
        possible_paths.append(Path.cwd() / config_path)
        # Try relative to /app (Docker container working directory)
        possible_paths.append(Path("/app") / config_path)
        # Try as-is (in case it's already relative to cwd)
        possible_paths.append(Path(config_path))
    
    config_file = None
    for path in possible_paths:
        logger.debug(f"   Checking: {path}")
        if path.exists():
            config_file = path
            break
    
    if config_file is None:
        error_msg = f"MCP config file not found. Tried paths: {', '.join(str(p) for p in possible_paths)}"
        logger.error(error_msg)
        logger.error(f"   Current working directory: {Path.cwd()}")
        raise FileNotFoundError(error_msg)
    
    logger.info(f"   ✅ Found MCP config file: {config_file}")
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Convert config to MultiServerMCPClient format
    mcp_servers = config.get("mcpServers", {})
    server_configs = {}
    
    for name, server_config in mcp_servers.items():
        # Skip filesystem server if absolute host paths don't exist (common in Docker)
        if name == "filesystem" and "args" in server_config:
            args = [arg for arg in server_config.get("args", []) if isinstance(arg, str)]
            abs_paths = [arg for arg in args if os.path.isabs(arg)]
            if abs_paths:
                paths_exist = any(os.path.exists(path) for path in abs_paths)
                if not paths_exist:
                    logging.warning("Skipping filesystem MCP server: configured paths are missing in this runtime")
                    continue
        
        # Determine transport type based on config
        # Default to stdio if not specified
        if "url" in server_config:
            # SSE/HTTP transport
            url = server_config["url"]
            # If URL uses localhost and we're in Docker, try to use service name
            # For brave-search, use the service name if available
            if "localhost" in url and name == "brave-search":
                # Try service name first, fallback to host.docker.internal, then original
                import socket
                try:
                    # Test if we can resolve the service name
                    socket.gethostbyname("brave-search-mcp-server")
                    url = url.replace("localhost", "brave-search-mcp-server")
                    logger.info(f"   Using service name for {name}: {url}")
                except socket.gaierror:
                    # Try host.docker.internal as fallback
                    try:
                        socket.gethostbyname("host.docker.internal")
                        url = url.replace("localhost", "host.docker.internal")
                        logger.info(f"   Using host.docker.internal for {name}: {url}")
                    except socket.gaierror:
                        logger.warning(f"   Using original URL for {name}: {url} (may not work in Docker)")
            
            server_configs[name] = {
                "url": url,
                "transport": "streamable_http",
            }
        else:
            # stdio transport
            server_configs[name] = {
                "command": server_config.get("command"),
                "args": server_config.get("args", []),
                "transport": "stdio",
            }
            # Add env if present
            if "env" in server_config:
                server_configs[name]["env"] = server_config["env"]
    
    # If no valid servers, return empty
    if not server_configs:
        return [], None
    
    # Create MultiServerMCPClient with better error handling
    import sys
    
    logger.info(f"   Connecting to {len(server_configs)} MCP server(s): {', '.join(server_configs.keys())}")
    
    # Temporarily redirect stderr to suppress MCP server warnings
    old_stderr = sys.stderr
    try:
        # Redirect stderr to devnull during client initialization
        sys.stderr = open(os.devnull, 'w')
        client = MultiServerMCPClient(server_configs)
        # Get all tools from all servers (these are async tools)
        logger.info("   Attempting to load tools from MCP servers...")
        async_tools = await client.get_tools()
    except FileNotFoundError as e:
        # Restore stderr first
        sys.stderr.close()
        sys.stderr = old_stderr
        error_msg = str(e)
        logger.error(f"   ❌ MCP server command not found: {error_msg}")
        logger.error(f"   This usually means:")
        logger.error(f"      - For 'npx' commands: Node.js/npm might not be properly installed")
        logger.error(f"      - For 'docker exec' commands: Docker containers might not be running")
        logger.error(f"      - For HTTP endpoints: The service might not be accessible")
        raise
    except Exception as e:
        # Restore stderr first
        sys.stderr.close()
        sys.stderr = old_stderr
        error_msg = str(e)
        logger.error(f"   ❌ Failed to connect to MCP servers: {error_msg}")
        logger.error(f"   Error type: {type(e).__name__}")
        # Log which servers we tried to connect to
        for server_name, server_config in server_configs.items():
            transport = server_config.get("transport", "unknown")
            if transport == "stdio":
                cmd = server_config.get("command", "unknown")
                args = server_config.get("args", [])
                logger.error(f"      - {server_name}: {cmd} {' '.join(str(a) for a in args[:3])}...")
            elif transport == "streamable_http":
                url = server_config.get("url", "unknown")
                logger.error(f"      - {server_name}: HTTP endpoint {url}")
        raise
    finally:
        # Restore stderr if not already restored
        if sys.stderr != old_stderr:
            sys.stderr.close()
            sys.stderr = old_stderr
    
    # Convert async tools to sync tools
    sync_tools = [make_sync_tool(tool) for tool in async_tools]
    
    # Log summary of loaded tools
    if sync_tools:
        tool_names = [tool.name for tool in sync_tools]
        logger.info(f"   ✅ Loaded {len(sync_tools)} MCP tools: {', '.join(sorted(tool_names))}")
    
    return sync_tools, client


def load_mcp_servers_sync(config_path: str):
    """Synchronous wrapper for loading MCP servers."""
    return asyncio.run(load_mcp_servers_from_config(config_path))
