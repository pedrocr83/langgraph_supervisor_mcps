from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import auth, chat
from app.db.session import engine, Base

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
    """Initialize database on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

