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
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Convert config to MultiServerMCPClient format
    mcp_servers = config.get("mcpServers", {})
    server_configs = {}
    
    for name, server_config in mcp_servers.items():
        # Skip filesystem server if paths don't exist (common in Docker)
        if name == "filesystem" and "args" in server_config:
            # Check if any of the filesystem paths exist
            paths_exist = any(os.path.exists(path) for path in server_config.get("args", []) if isinstance(path, str) and not path.startswith("-"))
            if not paths_exist:
                logging.warning(f"Skipping filesystem MCP server: paths don't exist in container")
                continue
        
        # Determine transport type based on config
        # Default to stdio if not specified
        if "url" in server_config:
            # SSE/HTTP transport
            server_configs[name] = {
                "url": server_config["url"],
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
    
    # Create MultiServerMCPClient with stderr suppression
    import sys
    
    # Temporarily redirect stderr to suppress MCP server warnings
    old_stderr = sys.stderr
    try:
        # Redirect stderr to devnull during client initialization
        sys.stderr = open(os.devnull, 'w')
        client = MultiServerMCPClient(server_configs)
        # Get all tools from all servers (these are async tools)
        async_tools = await client.get_tools()
    finally:
        # Restore stderr
        sys.stderr.close()
        sys.stderr = old_stderr
    
    # Convert async tools to sync tools
    sync_tools = [make_sync_tool(tool) for tool in async_tools]
    
    return sync_tools, client


def load_mcp_servers_sync(config_path: str):
    """Synchronous wrapper for loading MCP servers."""
    return asyncio.run(load_mcp_servers_from_config(config_path))
