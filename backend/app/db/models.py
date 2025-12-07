from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Boolean, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from pgvector.sqlalchemy import Vector
from app.db.session import Base
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID


class User(SQLAlchemyBaseUserTableUUID, Base):
    """User model for authentication."""
    __tablename__ = "users"
    
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    """Conversation model for storing chat sessions."""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Message model for storing individual chat messages."""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)  # 'user', 'assistant', 'tool'
    content = Column(Text, nullable=False)
    tool_name = Column(String, nullable=True)  # For tool messages
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class SemanticMemoryEntry(Base):
    """Semantic memory items stored for supervisor retrieval."""
    __tablename__ = "semantic_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    agent_id = Column(String, index=True, nullable=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True)
    text = Column(Text, nullable=False)
    meta = Column(JSON, nullable=True)
    embedding = Column(Vector(1024), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index(
            "ix_semantic_items_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index("ix_semantic_items_agent_created", "agent_id", "created_at"),
        Index("ix_semantic_items_user_created", "user_id", "created_at"),
    )


class ProceduralTrace(Base):
    """Procedural memory for sub-agents (steps and tool usage)."""
    __tablename__ = "procedural_traces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    agent_id = Column(String, index=True, nullable=True)
    task_id = Column(String, index=True, nullable=True)
    step = Column(Integer, nullable=True)
    input = Column(Text, nullable=True)
    output = Column(Text, nullable=True)
    tools_used = Column(JSON, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_procedural_traces_agent_created", "agent_id", "created_at"),
        Index("ix_procedural_traces_task", "task_id"),
        Index("ix_procedural_traces_user_created", "user_id", "created_at"),
    )

