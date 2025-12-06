from pydantic_settings import BaseSettings
from typing import List, Optional
from pathlib import Path


# Get the project root directory (3 levels up from this file: backend/app/core/config.py)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://172.18.0.4:3000",  # Docker network
        "*",  # Allow all origins in development
    ]
    
    # API Keys
    GOOGLE_API_KEY: str
    BRAVE_API_KEY: str
    
    # MCP Config
    MCP_CONFIG_PATH: Optional[str] = None
    MCP_FILESYSTEM_ENABLED: Optional[bool] = None
    MCP_FILESYSTEM_PATHS: Optional[List[str]] = None
    
    # Local Agents (vLLM) Config
    USE_LOCAL_AGENTS: Optional[bool] = None
    VLLM_API_BASE: Optional[str] = None
    VLLM_MODEL: Optional[str] = None
    VLLM_TEMPERATURE: Optional[float] = None
    VLLM_MAX_TOKENS: Optional[int] = None
    
    class Config:
        env_file = str(ENV_FILE) if ENV_FILE.exists() else ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

