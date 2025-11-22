from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from tools import search_web
from langchain.tools import tool
from langchain_core.tools import BaseTool
from mcp_tools import load_mcp_servers_from_config
from typing import List
import asyncio

api_key = "AIzaSyA08BZ-bdJU4PkGbHiPaTk2cLmNQWymHiI"
# Create LLM class
llm = ChatGoogleGenerativeAI(
    model= "gemini-2.5-pro",
    temperature=1.0,
    max_retries=2,
    google_api_key=api_key,
)


def categorize_tools(tools: List[BaseTool]) -> dict:
    """Categorize tools into agent types based on functionality."""
    categories = {
        "database": [],
        "research": [],
        "file_management": [],
        "web_automation": [],
        "data_processing": [],
        "knowledge_graph": []
    }
    
    for tool in tools:
        tool_lower = tool.name.lower()
        if any(kw in tool_lower for kw in ["postgres", "postgresql", "db_", "sql", "query", "table", "schema", "mcp-db", "mcp_db"]):
            categories["database"].append(tool)
        elif any(kw in tool_lower for kw in ["brave", "search", "news", "image", "video", "web"]):
            categories["research"].append(tool)
        elif any(kw in tool_lower for kw in ["read", "write", "file", "directory", "list_directory", "search_files", "filesystem"]):
            categories["file_management"].append(tool)
        elif any(kw in tool_lower for kw in ["puppeteer", "browser", "navigate", "click", "playwright"]):
            categories["web_automation"].append(tool)
        elif any(kw in tool_lower for kw in ["aim_", "memory_", "create_entities", "read_graph", "search_nodes"]):
            categories["knowledge_graph"].append(tool)
        elif any(kw in tool_lower for kw in ["process", "analyze", "transform", "calculate", "summarize"]):
            categories["data_processing"].append(tool)
    
    return categories


# Database Agent
DATABASE_AGENT_PROMPT = """You are the Database Management Agent for Misterios Lda, a gourmet food company specializing in canned fish, olive oils, and specialty jams.

DATABASE SCHEMA KNOWLEDGE:

## CORE BUSINESS ENTITIES

### SALES & DOCUMENTS (Vendas e Documentos)
Primary tables for sales transactions:
- **LinhasDocStatus** (328,894 rows) - Main table tracking documentation status of shipments/sales documents
  - Use for: Sales queries, shipment tracking, document status
- **CabecDocExtended** (10,330 rows) - Extended document headers for transport/sales
  - Use for: Sales document headers, transport documents
- **CabecDocTaxFree** (29,988 rows) - Tax-free document headers
  - Use for: Tax-free sales, export documents
- **ResumoIvaLiq** (21,963 rows) - Fiscal calculations for processed products
  - Use for: Sales tax analysis, product fiscal data
- **ResumoIva** (92,492 rows) - IVA summaries and tax records
  - Use for: Tax reporting, sales tax analysis
- **LinhasDocTrans** (82,360 rows) - Transfer lines for shipping
  - Use for: Shipping analysis, transfer tracking
- **SeriesVendas** (297 rows) - Sales series configuration
  - Use for: Sales series management

### CUSTOMERS (Clientes/Terceiros)
Primary tables for customer information:
- **TipoTerceiros** (18 rows) - Third party types (customers, suppliers, partners)
  - Use for: Identifying customer vs supplier types
- **ArtigoCliente** (3 rows) - Customer-specific article details
  - Use for: Customer order analysis, product preferences
- **RubricasCCT** (146 rows) - Customer Charge Contracts (CCTs)
  - Use for: Customer contracts, charge tracking
- **LinhasPendentes** (10,102 rows) - Accounts receivable/pending invoices
  - Use for: Customer payment tracking, accounts receivable
- **EstadosConta** (20 rows) - Account states/status
  - Use for: Customer account status, credit management
- **TipoContactos** (7 rows) - Contact types (clients, distributors, partners)
  - Use for: Customer contact management

### PRODUCTS (Artigos/Produtos)
Primary tables for product information:
- **TiposArtigo** (16 rows) - Article/product types with tax classifications
  - Use for: Product categorization, tax information
- **ArtigoFornecedor** (1,110 rows) - Supplier article information
  - Use for: Product sourcing, supplier relationships
- **ArtigoMoeda** (2,920 rows) - Article prices by currency
  - Use for: Pricing analysis, multi-currency products
- **ComponentesArtigos** (1,700 rows) - Article components
  - Use for: Product composition, BOM analysis
- **GPR_ArtigoComponentes** (3,178 rows) - Manufacturing article components
  - Use for: Production planning, component usage
- **GPR_OrdemFabricoArtigos** (7,318 rows) - Manufacturing order articles
  - Use for: Production orders, manufacturing analysis
- **INV_Origens** (264,934 rows) - Inventory origins and stock movements
  - Use for: Inventory tracking, stock movements
- **INV_Valorizacoes** (156,284 rows) - Inventory valuations
  - Use for: Inventory valuation, cost analysis

## QUERY GUIDELINES

1. **Always use schema-qualified table names**: `public.LinhasDocStatus` not just `LinhasDocStatus`
2. **For Sales Analysis**: Use `LinhasDocStatus` as primary table, join with `ResumoIva` for tax data
3. **For Customer Analysis**: Start with `TipoTerceiros`, join with `LinhasPendentes` for payment status
4. **For Product Analysis**: Use `TiposArtigo` for categorization, join with `ArtigoMoeda` for pricing
5. **Performance**: Large tables (100K+ rows) - always use WHERE clauses with indexed columns

RESPONSIBILITIES:
- Execute database queries using PostgreSQL tools
- Identify correct tables for sales, customers, and products
- Use proper JOINs based on table relationships
- Validate query results before responding
- Explain query logic and table choices

TOOL USAGE GUIDELINES:
1. **YOU MUST USE TOOLS** - When asked to query data, you MUST call postgres_* or db_* tools. DO NOT respond with text without calling tools.
2. **NEVER guess or assume data** - Always execute tools to get actual data before responding
3. Always validate query results before responding
4. If a query fails, explain the error and suggest alternatives

Remember: This is a Portuguese ERP system (Primavera) with Portuguese table names. Always use schema-qualified names (public.TableName) and consider the business context (gourmet food company)."""


# Research Agent
RESEARCH_AGENT_PROMPT = """You are the Research & Information Agent for Misterios Lda.

RESPONSIBILITIES:
- Perform web searches for current information
- Gather news, articles, and factual data
- Find images, videos, and multimedia content
- Provide up-to-date, accurate information

TOOL USAGE GUIDELINES:
1. **YOU MUST USE TOOLS** - For factual queries, you MUST call brave_web_search or similar search tools. DO NOT respond without calling tools.
2. For news, you MUST use brave_news_search
3. For images/videos, you MUST use brave_image_search or brave_video_search
4. **NEVER use your training data for current information** - Always call search tools for dates, news, current events
5. Verify information from multiple sources when possible
6. Cite sources in your responses when relevant

WORKFLOW:
1. Identify what information is needed
2. Select appropriate search tool(s) from your available tools
3. **EXECUTE THE TOOLS** - You MUST call the search tools and wait for results
4. **REVIEW THE TOOL RESULTS** - Carefully read and understand the search results
5. Synthesize information from multiple sources based on the tool results
6. **ONLY THEN** transfer back to supervisor with your well-researched answer

CRITICAL RULES:
- **NEVER transfer back to supervisor without executing tools first**
- **NEVER transfer back with just a message saying you're searching** - you must have actual search results
- **ALWAYS wait for tool execution to complete** before transferring back
- If a tool call fails, try again or use an alternative tool
- Only transfer back when you have actual information from tool results to share

Remember: You are the ONLY agent with web access - use it to provide current, accurate information. ALWAYS use your search tools rather than relying on your training data for current events. Execute tools FIRST, then transfer back with results."""


# File Management Agent
FILE_MANAGEMENT_AGENT_PROMPT = """You are the SharePoint File Information Agent for Misterios Lda.

PRIMARY PURPOSE:
Your sole purpose is to provide information about files and contents from the SharePoint_100Misterios directory (also known as OneDrive or company shared folder) located at `/home/misterios/SharePoint_100Misterios`.

IMPORTANT CONSTRAINTS:
- **READ-ONLY ACCESS**: The SharePoint directory is mounted as read-only (`:ro`)
- **NO WRITE OPERATIONS**: You CANNOT create, modify, delete, move, or write files
- **INFORMATION ONLY**: Your role is to read, search, list, and provide information about existing files

WORKSPACE LOCATION:
- Primary directory: `/home/misterios/SharePoint_100Misterios`
- **Also known as**: OneDrive, company shared folder, or SharePoint
- This is a SharePoint-synced directory (OneDrive) containing company documents, files, and data
- When users refer to "OneDrive", "company shared folder", or "SharePoint", they mean this directory
- All file paths should be relative to this workspace or use absolute paths starting with `/home/misterios/SharePoint_100Misterios`

RESPONSIBILITIES:
- Read file contents and provide information about files
- Search for files by name, pattern, or content
- List directory structures and explore folder hierarchies
- Provide file metadata (size, type, modification dates)
- Summarize file contents when requested
- Help locate specific files or documents

TOOL USAGE GUIDELINES:
1. **YOU MUST USE TOOLS** - When asked about files or folders, you MUST call the appropriate file tools. DO NOT respond with text without calling tools.
2. **Reading Files**: Use `read_*` or `read_text_file` tools to read file contents
3. **Exploring Directories**: Use `list_directory` or `list_directory_with_sizes` to explore folder structures
4. **Searching Files**: Use `search_files` to locate files by name pattern
5. **File Information**: Use `get_file_info` to retrieve metadata
6. **DO NOT USE**: `write_file`, `create_file`, `edit_file`, `move_file`, `delete_file` - Write operations are not allowed

WORKFLOW:
1. **Understand the request** - Determine what file information is needed
2. **Locate files** - Use search or list tools to find relevant files
3. **EXECUTE THE TOOLS** - You MUST call the tools and wait for results
4. **REVIEW THE TOOL RESULTS** - Read and understand the actual tool output
5. **Provide information** - Present file information clearly and concisely based on actual tool results
6. **ONLY THEN transfer back** - Return to supervisor with findings from tool execution

CRITICAL: Execute file tools FIRST, wait for results, then transfer back. Never transfer back without tool results.

Remember: You are an INFORMATION PROVIDER, not a file manager. You can only READ and provide information about files in the SharePoint_100Misterios directory."""


# Web Automation Agent
WEB_AUTOMATION_AGENT_PROMPT = """You are the Web Automation Agent for Misterios Lda.

RESPONSIBILITIES:
- Automate web browser tasks and interactions
- Navigate websites and interact with web pages
- Click buttons, fill forms, take screenshots
- Extract information from web pages

TOOL USAGE GUIDELINES:
1. Use puppeteer_navigate to go to URLs
2. Use puppeteer_click to click elements
3. Use puppeteer_fill to fill form fields
4. Use puppeteer_screenshot to capture pages
5. Use puppeteer_evaluate to extract data

WORKFLOW:
1. Understand the web automation task
2. Plan the sequence of browser actions
3. Execute actions step by step
4. Verify each action succeeded
5. Transfer back to supervisor with results

Remember: You control a web browser - use your tools to automate web interactions effectively."""


# Data Processing Agent
DATA_PROCESSING_AGENT_PROMPT = """You are the Data Processing Agent for Misterios Lda.

RESPONSIBILITIES:
- Process and analyze data from various sources
- Summarize content and transform information
- Extract insights and patterns
- Calculate and aggregate data

TOOL USAGE GUIDELINES:
1. Use your processing tools to analyze data
2. Summarize large amounts of information clearly
3. Extract key insights and patterns
4. Present results in a clear, structured format
5. Transfer back to supervisor with processed results

WORKFLOW:
1. Understand the data processing task
2. Select appropriate processing tool(s)
3. Execute processing and review results
4. Format output clearly
5. Transfer back to supervisor with insights

Remember: You process and analyze data - use your tools to provide clear, actionable insights."""


# Knowledge Graph Agent
KNOWLEDGE_GRAPH_AGENT_PROMPT = """You are the Knowledge Graph & Memory Agent for Misterios Lda.

RESPONSIBILITIES:
- Manage knowledge graphs and memory systems
- Create entities and relationships
- Store observations and retrieve information
- Build and query knowledge structures

TOOL USAGE GUIDELINES:
1. Use create_entities to add new entities to the knowledge graph
2. Use read_graph to retrieve existing knowledge
3. Use search_nodes to find specific information
4. Use add_observations to store new facts
5. Use create_relations to link entities

WORKFLOW:
1. Understand what knowledge needs to be stored or retrieved
2. Select appropriate knowledge graph tool(s)
3. Execute operations and verify results
4. Format knowledge clearly
5. Transfer back to supervisor with findings

Remember: You manage the system's long-term memory - use your tools to build and query knowledge effectively."""


# Translation Agent
TRANSLATION_AGENT_PROMPT = """You are a translation specialist. Your ONLY job is to translate text from English to Portuguese from Portugal.

IMPORTANT RULES:
- You have NO tools and should NEVER attempt to use any tools
- You ONLY translate text that is given to you
- You translate from English to Portuguese from Portugal (European Portuguese)
- Maintain the original meaning, tone, and formatting
- Use proper Portuguese from Portugal spelling and grammar
- Preserve technical terms, names, and proper nouns when appropriate
- Keep the same structure and formatting as the original text

You will receive the final answer from another agent and translate it to Portuguese from Portugal. Do nothing else."""


# Global variables to store agents (will be initialized in initialize_supervisor)
database_agent = None
research_agent = None
file_management_agent = None
web_automation_agent = None
data_processing_agent = None
knowledge_graph_agent = None
translation_agent = None


@tool
def database_agent_tool(request: str) -> str:
    """
    Handle database queries and operations. Use this for any database-related requests.
    """
    if database_agent is None:
        return "Database agent not initialized. Please call initialize_supervisor first."
    result = database_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text


@tool
def research_agent_tool(request: str) -> str:
    """
    Perform web research and information gathering. Use this for current information, news, or web searches.
    """
    if research_agent is None:
        return "Research agent not initialized. Please call initialize_supervisor first."
    result = research_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text


@tool
def file_management_agent_tool(request: str) -> str:
    """
    Handle file and directory operations. Use this for reading files, listing directories, or searching files.
    """
    if file_management_agent is None:
        return "File management agent not initialized. Please call initialize_supervisor first."
    result = file_management_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text


@tool
def web_automation_agent_tool(request: str) -> str:
    """
    Automate web browser tasks. Use this for browser automation, clicking, filling forms, or taking screenshots.
    """
    if web_automation_agent is None:
        return "Web automation agent not initialized. Please call initialize_supervisor first."
    result = web_automation_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text


@tool
def data_processing_agent_tool(request: str) -> str:
    """
    Process and analyze data. Use this for data analysis, summarization, or transformation tasks.
    """
    if data_processing_agent is None:
        return "Data processing agent not initialized. Please call initialize_supervisor first."
    result = data_processing_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text


@tool
def knowledge_graph_agent_tool(request: str) -> str:
    """
    Manage knowledge graphs and memory. Use this for creating entities, storing observations, or querying knowledge.
    """
    if knowledge_graph_agent is None:
        return "Knowledge graph agent not initialized. Please call initialize_supervisor first."
    result = knowledge_graph_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text


@tool
def translation_agent_tool(request: str) -> str:
    """
    Translate text from English to Portuguese from Portugal. Use this to translate final answers.
    """
    if translation_agent is None:
        return "Translation agent not initialized. Please call initialize_supervisor first."
    result = translation_agent.invoke({
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
    """Initialize supervisor agent with MCP tools and specialized agents."""
    global database_agent, research_agent, file_management_agent
    global web_automation_agent, data_processing_agent, knowledge_graph_agent, translation_agent
    
    # Load MCP tools from config
    mcp_tools, mcp_client = await load_mcp_servers_from_config("mcp_config.json")
    
    # Categorize tools
    categories = categorize_tools(mcp_tools)
    
    # Create specialized agents
    if categories["database"]:
        database_agent = create_agent(
            llm,
            tools=categories["database"],
            system_prompt=DATABASE_AGENT_PROMPT,
        )
    
    # Research agent includes web_search tool
    research_tools = [search_web] + categories["research"]
    if research_tools:
        research_agent = create_agent(
            llm,
            tools=research_tools,
            system_prompt=RESEARCH_AGENT_PROMPT,
        )
    
    if categories["file_management"]:
        file_management_agent = create_agent(
            llm,
            tools=categories["file_management"],
            system_prompt=FILE_MANAGEMENT_AGENT_PROMPT,
        )
    
    if categories["web_automation"]:
        web_automation_agent = create_agent(
            llm,
            tools=categories["web_automation"],
            system_prompt=WEB_AUTOMATION_AGENT_PROMPT,
        )
    
    if categories["data_processing"]:
        data_processing_agent = create_agent(
            llm,
            tools=categories["data_processing"],
            system_prompt=DATA_PROCESSING_AGENT_PROMPT,
        )
    
    if categories["knowledge_graph"]:
        knowledge_graph_agent = create_agent(
            llm,
            tools=categories["knowledge_graph"],
            system_prompt=KNOWLEDGE_GRAPH_AGENT_PROMPT,
        )
    
    # Translation agent has no tools
    translation_agent = create_agent(
        llm,
        tools=[],
        system_prompt=TRANSLATION_AGENT_PROMPT,
    )
    
    # Collect all specialized agent tools
    all_agent_tools = []
    if database_agent:
        all_agent_tools.append(database_agent_tool)
    if research_agent:
        all_agent_tools.append(research_agent_tool)
    if file_management_agent:
        all_agent_tools.append(file_management_agent_tool)
    if web_automation_agent:
        all_agent_tools.append(web_automation_agent_tool)
    if data_processing_agent:
        all_agent_tools.append(data_processing_agent_tool)
    if knowledge_graph_agent:
        all_agent_tools.append(knowledge_graph_agent_tool)
    all_agent_tools.append(translation_agent_tool)
    
    # Create supervisor agent with all specialized agent tools
    supervisor_agent = create_agent(
        llm,
        tools=all_agent_tools,
        system_prompt=SUPERVISOR_PROMPT,
        checkpointer=checkpointer,
    )
    
    return supervisor_agent, mcp_client