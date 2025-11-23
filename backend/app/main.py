from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api import auth, chat
from app.db.session import engine, Base
import logging

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LangGraph Supervisor API",
    description="Production-ready API for LangGraph Supervisor Agent",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])


@app.on_event("startup")
async def startup_event():
    """Initialize database and supervisor on startup."""
    logger.info("=" * 80)
    logger.info("Starting MisteriosAI Application")
    logger.info("=" * 80)
    
    # Initialize database
    logger.info("Initializing database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully")
    
    # Initialize supervisor (this will log model, MCP tools, and agents)
    logger.info("Initializing supervisor agent...")
    from app.services.agents.supervisor import get_supervisor_service
    await get_supervisor_service()
    logger.info("Supervisor agent initialized successfully")
    logger.info("=" * 80)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

