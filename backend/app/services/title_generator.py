from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from app.db.models import Conversation, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import re

logger = logging.getLogger(__name__)


class TitleGenerator:
    """Service for generating conversation titles based on message content."""
    
    def __init__(self):
        self.llm = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the LLM for title generation."""
        if self._initialized:
            return
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",  # Use faster model for title generation
            temperature=0.7,
            max_retries=2,
            google_api_key=settings.GOOGLE_API_KEY,
        )
        self._initialized = True
        logger.info("Title generator initialized")
    
    def _clean_message_content(self, content: str) -> str:
        """Remove emotion tags and clean message content for title generation."""
        if not content:
            return ""
        
        # Remove emotion tags: <emotion>type</emotion>
        content = re.sub(r'<emotion>.*?</emotion>', '', content)
        
        # Remove other potential tags
        content = re.sub(r'<(happy|confused|sad|angry)>', '', content)
        content = re.sub(r'</(happy|confused|sad|angry)>', '', content)
        
        return content.strip()
    
    async def generate_title(
        self,
        session: AsyncSession,
        conversation_id: str,
        min_messages: int = 6  # 3 user + 3 assistant = 6 messages minimum
    ) -> str | None:
        """
        Generate a title for a conversation based on its messages.
        
        Args:
            session: Database session
            conversation_id: UUID of the conversation
            min_messages: Minimum number of messages before generating title
            
        Returns:
            Generated title string or None if generation fails
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get conversation to check current title
            result = await session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found")
                return None
            
            # Only generate title if it's still "New Conversation" or None
            if conversation.title and conversation.title != "New Conversation":
                logger.debug(f"Conversation {conversation_id} already has title: {conversation.title}")
                return None
            
            # Get recent messages (user and assistant only, exclude tool messages)
            result = await session.execute(
                select(Message)
                .where(
                    Message.conversation_id == conversation_id,
                    Message.role.in_(["user", "assistant"])
                )
                .order_by(Message.created_at.asc())
            )
            messages = result.scalars().all()
            
            # Check if we have enough messages
            if len(messages) < min_messages:
                logger.debug(
                    f"Conversation {conversation_id} has only {len(messages)} messages, "
                    f"need at least {min_messages} for title generation"
                )
                return None
            
            # Extract meaningful conversation content (first few exchanges)
            # Take first 4-6 messages to get initial context
            relevant_messages = messages[:min(len(messages), 8)]
            
            conversation_text = ""
            for msg in relevant_messages:
                cleaned_content = self._clean_message_content(msg.content)
                if cleaned_content:
                    role_label = "User" if msg.role == "user" else "Assistant"
                    conversation_text += f"{role_label}: {cleaned_content}\n\n"
            
            if not conversation_text.strip():
                logger.warning(f"No meaningful content found in conversation {conversation_id}")
                return None
            
            # Generate title using LLM
            prompt = f"""Based on the following conversation, generate a concise, descriptive title (maximum 60 characters) that captures the main topic or purpose of the conversation.

The title should be:
- Short and descriptive (max 60 characters)
- In Portuguese (Portugal) if the conversation is in Portuguese, otherwise in English
- Reflect the main topic or question being discussed
- Not include quotes or special formatting

Conversation:
{conversation_text}

Title:"""

            response = await self.llm.ainvoke(prompt)
            
            # Extract title from response
            title = ""
            if hasattr(response, 'content'):
                if isinstance(response.content, list):
                    for block in response.content:
                        if isinstance(block, dict) and "text" in block:
                            title += block["text"]
                        elif isinstance(block, str):
                            title += block
                else:
                    title = str(response.content)
            else:
                title = str(response)
            
            # Clean and validate title
            title = title.strip()
            
            # Remove quotes if present
            title = re.sub(r'^["\']|["\']$', '', title)
            
            # Limit length
            if len(title) > 60:
                title = title[:57] + "..."
            
            # Ensure title is not empty
            if not title or title.lower() == "new conversation":
                logger.warning(f"Generated empty or invalid title for conversation {conversation_id}")
                return None
            
            logger.info(f"Generated title for conversation {conversation_id}: {title}")
            return title
            
        except Exception as e:
            logger.error(f"Error generating title for conversation {conversation_id}: {e}", exc_info=True)
            return None


# Global singleton instance
_title_generator: TitleGenerator | None = None


async def get_title_generator() -> TitleGenerator:
    """Get or create the title generator instance."""
    global _title_generator
    if _title_generator is None:
        _title_generator = TitleGenerator()
        await _title_generator.initialize()
    return _title_generator

