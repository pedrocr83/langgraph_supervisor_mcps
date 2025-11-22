from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://langraph:langraph_dev_password@localhost:5432/langraph_supervisor"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    # API Keys
    GOOGLE_API_KEY: str = ""
    BRAVE_API_KEY: str = ""
    
    # MCP Config
    MCP_CONFIG_PATH: str = "mcp_config.json"
    MCP_FILESYSTEM_ENABLED: bool = False  # Disable filesystem MCP in Docker by default
    MCP_FILESYSTEM_PATHS: List[str] = []  # Paths to mount for filesystem MCP
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

