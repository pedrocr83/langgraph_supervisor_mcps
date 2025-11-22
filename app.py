from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from tools import search_web
from langchain.tools import tool
from mcp_tools import load_mcp_servers_from_config
import asyncio

api_key = "AIzaSyAH3R43euWHXwtJ5tYQRo-_XULMV_7G4dM"
# Create LLM class
llm = ChatGoogleGenerativeAI(
    model= "gemini-2.5-pro",
    temperature=1.0,
    max_retries=2,
    google_api_key=api_key,
)


WEB_AGENT_PROMPT = (
    "You are a web research assistant. "
    "Parse the natural language request into web search requests. "
    "Use search_web to search the web. "
    "Always confirm that the request was understood and the search performed answers the request."
)

web_agent = create_agent(
    llm,
    tools=[search_web],
    system_prompt=WEB_AGENT_PROMPT,
)


@tool
def web_search(request: str) -> str:
    """
    Perform a web search based on a natural language request.
    """
    result = web_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text


SUPERVISOR_PROMPT = (
    "You are a helpful personal assistant. "
    "You can plan and reason before answering and research using available tools. "
    "Break down user requests into appropriate tool calls and coordinate the results. "
    "When a request involves multiple actions, use multiple tools in sequence."
)

checkpointer = InMemorySaver()


async def initialize_supervisor():
    """Initialize supervisor agent with MCP tools."""
    # Load MCP tools from config
    mcp_tools, mcp_client = await load_mcp_servers_from_config("mcp_config.json")
    
    # Combine all tools
    all_tools = [web_search] + mcp_tools
    
    # Create supervisor agent with all tools
    supervisor_agent = create_agent(
        llm,
        tools=all_tools,
        system_prompt=SUPERVISOR_PROMPT,
        checkpointer=checkpointer,
    )
    
    return supervisor_agent, mcp_client


# For synchronous usage, you can run:
# supervisor_agent, mcp_client = asyncio.run(initialize_supervisor())

# Or use this pattern in async context:
# async def main():
#     supervisor_agent, mcp_client = await initialize_supervisor()
#     # Use supervisor_agent here
#     result = supervisor_agent.invoke({"messages": [{"role": "user", "content": "your query"}]})
#     print(result)