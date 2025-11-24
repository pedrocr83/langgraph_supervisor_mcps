from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from langchain.tools import tool as langchain_tool
from langchain_core.tools import BaseTool
from app.services.agents.mcp_tools import load_mcp_servers_from_config
from app.core.config import settings
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def categorize_tools(tools: List[BaseTool]) -> dict:
    """Categorize tools into agent types based on functionality."""
    categories = {
        "database": [],
        "sharepoint": [],
        "web": [],
    }
    
    for tool in tools:
        tool_lower = tool.name.lower()
        if any(kw in tool_lower for kw in ["postgres", "postgresql", "db_", "sql", "query", "table", "schema", "mcp-db", "mcp_db"]):
            categories["database"].append(tool)
        elif any(kw in tool_lower for kw in ["sharepoint", "onedrive", "filesystem", "file_", "directory", "list_directory", "search_files"]):
            categories["sharepoint"].append(tool)
        else:
            categories["web"].append(tool)
    
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


# SharePoint Agent
SHAREPOINT_AGENT_PROMPT = """You are the SharePoint File Information Agent for Misterios Lda.

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


SUPERVISOR_PROMPT = (
    "You are a helpful personal assistant called misteriosAI. "
    "You are the AI assistant for Misterios Lda, a premium gourmet food company specializing in high-end canned fish, olive oils, and jams under brands JOSE Gourmet, MariaOrganic, and ABC+ and ATIManel. The company focuses on artisanal Portuguese culinary heritage, premium quality, and traditional production methods."
    "You can plan and reason before answering and research using available tools. "
    "You will translate the request from the user from its language to English before calling the tools or answering AND also translate the answer from English to Portuguese from Portugal before answering. "
    "Break down user requests into appropriate tool calls and coordinate the results. "
    "You manage two specialist agents: one for database/ERP access and one for SharePoint/OneDrive files. "
    "You also have direct access to web search tools for research and current information.\n\n"
    "TOOL SELECTION GUIDELINES:\n\n"
    "1. **WEB SEARCH TOOLS** - Use web search tools (brave_search, web_search, etc.) for:\n"
    "   - Current date, time, or calendar questions (\"que dia é hoje?\", \"what day is today?\", \"what's the date?\")\n"
    "   - Current events, news, or recent information\n"
    "   - General knowledge questions that require up-to-date information\n"
    "   - Facts, definitions, or information not in your training data\n"
    "   - Weather, stock prices, or other real-time data\n"
    "   - Any question where you need to verify current information or research a topic\n"
    "   **CRITICAL**: Always use web search for date/time questions - NEVER guess or use your training cutoff date.\n\n"
    "2. **DATABASE AGENT** - Call the database agent tool for:\n"
    "   - Questions about sales, inventory, finance, or SQL data\n"
    "   - ERP system queries\n"
    "   - Company-specific data from the database\n\n"
    "3. **SHAREPOINT AGENT** - Call the SharePoint agent tool for:\n"
    "   - Requests about documents or files in the company drive\n"
    "   - Reading or searching company files\n"
    "   - Information from SharePoint/OneDrive directory\n\n"
    "DECISION PROCESS:\n"
    "Before answering ANY question, analyze it:\n"
    "1. Does it require current/real-time information? → Use web search tools\n"
    "2. Does it ask about company data/database? → Use database agent\n"
    "3. Does it ask about files/documents? → Use SharePoint agent\n"
    "4. Does it require general knowledge or research? → Use web search tools\n"
    "5. Is it a simple question you can answer directly? → Answer directly (but still use web search for dates/times)\n\n"
    "Handle language translation between English and Portuguese (Portugal) yourself within the supervisor; do not delegate translation. "
    "When a request involves multiple actions, use multiple tools in sequence.\n\n"
    "EMOTION CLASSIFICATION (CRITICAL - READ CAREFULLY):\n"
    "You MUST start EVERY response with an emotion tag: <emotion>TYPE</emotion>\n\n"
    "EMOTION TYPES AND WHEN TO USE THEM:\n\n"
    "1. <emotion>sad</emotion> - Use when:\n"
    "   - Apologizing for your limitations (\"I cannot predict the future...\")\n"
    "   - Giving bad news or disappointing information\n"
    "   - Dealing with sensitive topics (self-harm, loss, grief, serious health issues)\n"
    "   - Expressing sympathy or empathy\n"
    "   - Unable to help with something the user really needs\n"
    "   Example: <emotion>sad</emotion>Peço desculpa, mas não consigo prever o futuro...\n\n"
    "2. <emotion>confused</emotion> - Use when:\n"
    "   - You don't understand the request\n"
    "   - The request is unclear or ambiguous\n"
    "   - Asking for clarification\n"
    "   - The query is nonsensical or gibberish\n"
    "   Example: <emotion>confused</emotion>Desculpe, não compreendi. Pode reformular?\n\n"
    "3. <emotion>angry</emotion> - Use when:\n"
    "   - Refusing harmful, illegal, or unethical requests\n"
    "   - Enforcing safety policies\n"
    "   - Rejecting content that violates guidelines (violence, abuse, illegal content)\n"
    "   - The user is asking you to do something forbidden\n"
    "   Example: <emotion>angry</emotion>Não posso atender a esse pedido. Tal conteúdo é ilegal...\n\n"
    "4. <emotion>happy</emotion> - Use ONLY when:\n"
    "   - Successfully helping with a normal request\n"
    "   - Providing requested information\n"
    "   - General helpful conversation\n"
    "   - Positive, constructive responses\n"
    "   Example: <emotion>happy</emotion>Olá! Como posso ajudar?\n\n"
    "CRITICAL RULES:\n"
    "- Use ONLY <emotion>TYPE</emotion> format (NOT <happy>, <sad>, etc.)\n"
    "- The tag goes FIRST, then your response content\n"
    "- Choose the emotion that BEST MATCHES your response content\n"
    "- If refusing/apologizing = sad or angry, NOT happy\n"
    "- If providing help = happy\n"
    "- NEVER use happy when you're refusing or apologizing"
)


class SupervisorService:
    """Service for managing the LangGraph supervisor agent."""
    
    def __init__(self):
        self.llm = None
        self.database_agent = None
        self.sharepoint_agent = None
        self.supervisor_agent = None
        self.mcp_client = None
        self.web_tools: List[BaseTool] = []
        self.checkpointer = InMemorySaver()
        self._initialized = False
    
    async def initialize(self):
        """Initialize supervisor agent with MCP tools and specialized agents."""
        if self._initialized:
            return
        
        logger.info("-" * 80)
        logger.info("SUPERVISOR INITIALIZATION")
        logger.info("-" * 80)
        
        # Initialize LLM
        model_name = "gemini-2.5-pro"
        logger.info(f"🤖 Model: {model_name}")
        logger.info(f"   Temperature: 1.0")
        logger.info(f"   Max Retries: 2")
        
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=1.0,
            max_retries=2,
            google_api_key=settings.GOOGLE_API_KEY,
        )
        
        # Load MCP tools from config (gracefully handle errors)
        mcp_tools = []
        self.mcp_client = None
        logger.info("📦 Loading MCP tools...")
        logger.info(f"   Config path: {settings.MCP_CONFIG_PATH}")
        try:
            mcp_tools, self.mcp_client = await load_mcp_servers_from_config(settings.MCP_CONFIG_PATH)
            logger.info(f"✅ Successfully loaded {len(mcp_tools)} MCP tools")
        except Exception as e:
            logger.error(f"⚠️  Failed to load MCP servers: {e}")
            logger.error(f"   Error type: {type(e).__name__}")
            import traceback
            logger.debug(f"   Traceback: {traceback.format_exc()}")
            logger.info("   Continuing without MCP tools...")
            mcp_tools = []
        
        # Categorize tools
        categories = categorize_tools(mcp_tools)
        db_tools = categories.get("database", [])
        sharepoint_tools = categories.get("sharepoint", [])
        self.web_tools = categories.get("web", [])
        
        # Log categorized tools with details
        if mcp_tools:
            logger.info("   📋 MCP Tools by Category:")
            for category_name, category_tools in categories.items():
                if category_tools:
                    logger.info(f"      {category_name.upper().replace('_', ' ')} ({len(category_tools)} tools):")
                    for tool in sorted(category_tools, key=lambda t: t.name):
                        tool_desc = tool.description[:80] + "..." if len(tool.description) > 80 else tool.description
                        logger.info(f"         • {tool.name}")
                        logger.info(f"           Purpose: {tool_desc}")
        
        # Create specialized agents
        logger.info("🤖 Creating specialized agents...")
        agents_created = []
        agent_details = []
        
        if db_tools:
            self.database_agent = create_react_agent(
                self.llm,
                tools=db_tools,
                prompt=DATABASE_AGENT_PROMPT,
            )
            agents_created.append("Database Agent")
            tool_names = [t.name for t in db_tools]
            agent_details.append({
                "name": "Database Agent",
                "purpose": "Execute database queries and operations for Misterios Lda ERP system",
                "tools": tool_names,
                "count": len(db_tools),
            })
        
        if sharepoint_tools:
            self.sharepoint_agent = create_react_agent(
                self.llm,
                tools=sharepoint_tools,
                prompt=SHAREPOINT_AGENT_PROMPT,
            )
            agents_created.append("SharePoint Agent")
            tool_names = [t.name for t in sharepoint_tools]
            agent_details.append({
                "name": "SharePoint Agent",
                "purpose": "Read and provide information about files in SharePoint_100Misterios directory (read-only)",
                "tools": tool_names,
                "count": len(sharepoint_tools),
            })
        
        if self.web_tools:
            agent_details.append({
                "name": "Supervisor Web Tools",
                "purpose": "Direct tools available to the supervisor for research, browsing, and other external data",
                "tools": [t.name for t in self.web_tools],
                "count": len(self.web_tools),
            })
        
        logger.info(f"📊 Agents/Tools Configured ({len(agent_details)} entries):")
        for i, agent in enumerate(agent_details, 1):
            logger.info(f"   {i}. {agent['name']}")
            logger.info(f"      Purpose: {agent['purpose']}")
            if agent['count'] > 0:
                logger.info(f"      Tools ({agent['count']}): {', '.join(agent['tools'][:5])}")
                if len(agent['tools']) > 5:
                    logger.info(f"                ... and {len(agent['tools']) - 5} more")
            else:
                logger.info(f"      Tools: None")
        
        def _message_to_text(message) -> str:
            """Normalize LangChain/LangGraph message content to plain text."""
            content = getattr(message, "content", message)
            if isinstance(content, list):
                parts = []
                for block in content:
                    if isinstance(block, dict) and "text" in block:
                        parts.append(block["text"])
                    elif isinstance(block, str):
                        parts.append(block)
                return "".join(parts)
            return str(content)
        
        # Create tool wrappers that bind to self
        def _create_database_tool():
            @langchain_tool
            async def database_agent_tool(request: str) -> str:
                """Handle database queries and operations."""
                if self.database_agent is None:
                    return "Database agent not initialized."
                result = await self.database_agent.ainvoke({
                    "messages": [{"role": "user", "content": request}]
                })
                last_msg = result["messages"][-1]
                return _message_to_text(last_msg)
            return database_agent_tool
        
        def _create_sharepoint_tool():
            @langchain_tool
            async def sharepoint_agent_tool(request: str) -> str:
                """Handle SharePoint/OneDrive file questions (read-only)."""
                if self.sharepoint_agent is None:
                    return "SharePoint agent not initialized."
                result = await self.sharepoint_agent.ainvoke({
                    "messages": [{"role": "user", "content": request}]
                })
                last_msg = result["messages"][-1]
                return _message_to_text(last_msg)
            return sharepoint_agent_tool
        
        # Collect supervisor tools (specialized agents + direct web MCP tools)
        supervisor_tools: List[BaseTool] = []
        if self.database_agent:
            supervisor_tools.append(_create_database_tool())
        if self.sharepoint_agent:
            supervisor_tools.append(_create_sharepoint_tool())
        supervisor_tools.extend(self.web_tools)
        
        # Create supervisor agent with all supervisor tools
        logger.info("🎯 Creating supervisor agent...")
        self.supervisor_agent = create_react_agent(
            self.llm,
            tools=supervisor_tools,
            prompt=SUPERVISOR_PROMPT,
            checkpointer=self.checkpointer,
        )
        logger.info(f"   ✅ Supervisor Agent (with {len(supervisor_tools)} tools)")
        
        self._initialized = True
        logger.info("-" * 80)
        logger.info("✅ Supervisor initialization complete!")
        logger.info("-" * 80)


# Global singleton instance
_supervisor_service: Optional[SupervisorService] = None


async def get_supervisor_service() -> SupervisorService:
    """Get or create the supervisor service instance."""
    global _supervisor_service
    if _supervisor_service is None:
        _supervisor_service = SupervisorService()
        await _supervisor_service.initialize()
    return _supervisor_service
