from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json
import uuid
from app.core.security import current_active_user
from app.db.models import User
from app.services.agents.supervisor import get_supervisor_service
from app.db.session import get_db, AsyncSessionLocal
from app.db.models import Conversation, Message
from sqlalchemy import select
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import re

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[uuid.UUID] = None


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    message: str


@router.websocket("/ws/{conversation_id}")
async def websocket_chat(
    websocket: WebSocket,
    conversation_id: str,
):
    """WebSocket endpoint for streaming chat responses."""
    await websocket.accept()
    
    try:
        # Authenticate WebSocket connection
        token = None
        query_params = dict(websocket.query_params)
        if 'token' in query_params:
            token = query_params['token']
        else:
            # Try to get from headers
            headers = dict(websocket.headers)
            auth_header = headers.get('authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
        
        if not token:
            await websocket.close(code=1008, reason="Authentication required")
            return
        
        # Verify token and get user
        from app.core.security import get_jwt_strategy
        strategy = get_jwt_strategy()
        try:
            user_data = await strategy.read_token(token)
            user_id = user_data.get('sub')
        except Exception:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # Get user from database
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user or not user.is_active:
                await websocket.close(code=1008, reason="User not found or inactive")
                return
        
        supervisor_service = await get_supervisor_service()
        
        # Get or create conversation
        async with AsyncSessionLocal() as session:
            conv_id = uuid.UUID(conversation_id) if conversation_id != "new" else None
            
            if conv_id:
                result = await session.execute(
                    select(Conversation).where(
                        Conversation.id == conv_id,
                        Conversation.user_id == user.id
                    )
                )
                conversation = result.scalar_one_or_none()
                if not conversation:
                    raise HTTPException(status_code=404, detail="Conversation not found")
            else:
                conversation = Conversation(
                    user_id=user.id,
                    title="New Conversation"
                )
                session.add(conversation)
                await session.commit()
                await session.refresh(conversation)
                conv_id = conversation.id
            
            # Send conversation ID to client
            await websocket.send_json({
                "type": "conversation_id",
                "conversation_id": str(conv_id)
            })
            
            # Wait for messages
            while True:
                data = await websocket.receive_json()
                
                if data.get("type") == "message":
                    user_message = data.get("message", "")
                    
                    # Save user message
                    user_msg = Message(
                        conversation_id=conv_id,
                        role="user",
                        content=user_message
                    )
                    session.add(user_msg)
                    await session.commit()
                    
                    # Log user message
                    logger.info(f"User ({conv_id}): {user_message}")
                    
                    # Stream response from supervisor
                    config = {"configurable": {"thread_id": str(conv_id)}}
                    inputs = {"messages": [{"role": "user", "content": user_message}]}
                    
                    full_response = ""
                    for step in supervisor_service.supervisor_agent.stream(inputs, config):
                        for key, update in step.items():
                            if "messages" in update:
                                for msg in update["messages"]:
                                    if hasattr(msg, 'content') and msg.content:
                                        # Handle tool messages
                                        if msg.type == 'tool':
                                            await websocket.send_json({
                                                "type": "tool",
                                                "name": msg.name or "Unknown",
                                                "content": str(msg.content)
                                            })
                                        
                                        # Handle AI messages
                                        elif msg.type == 'ai':
                                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                                for tool_call in msg.tool_calls:
                                                    await websocket.send_json({
                                                        "type": "tool_call",
                                                        "name": tool_call.get('name', 'Unknown'),
                                                        "args": tool_call.get('args', {})
                                                    })
                                            
                                            if msg.content:
                                                content_str = ""
                                                if isinstance(msg.content, list):
                                                    for block in msg.content:
                                                        if isinstance(block, dict) and "text" in block:
                                                            content_str += block["text"]
                                                        elif isinstance(block, str):
                                                            content_str += block
                                                else:
                                                    content_str = str(msg.content)
                                                
                                                full_response += content_str
                                                await websocket.send_json({
                                                    "type": "content",
                                                    "content": content_str
                                                })
                    
                    # Save assistant message
                    if full_response:
                        # Extract emotion for logging
                        # Try standard format first: <emotion>type</emotion>
                        emotion_match = re.search(r'<emotion>(.*?)</emotion>', full_response)
                        if emotion_match:
                            emotion = emotion_match.group(1)
                            clean_content = re.sub(r'<emotion>.*?</emotion>', '', full_response)
                        else:
                            # Try fallback format: <type>...</type> or <type>...
                            fallback_match = re.search(r'<(happy|confused|sad|angry)>', full_response)
                            if fallback_match:
                                emotion = fallback_match.group(1)
                                # Remove the opening tag
                                clean_content = re.sub(r'<(happy|confused|sad|angry)>', '', full_response)
                                # Remove potential closing tag
                                clean_content = re.sub(r'</(happy|confused|sad|angry)>', '', clean_content)
                            else:
                                emotion = "unknown"
                                clean_content = full_response
                        
                        logger.info(f"AI ({conv_id}) [Emotion: {emotion}]: {clean_content}")
                        
                        assistant_msg = Message(
                            conversation_id=conv_id,
                            role="assistant",
                            content=full_response
                        )
                        session.add(assistant_msg)
                        await session.commit()
                    else:
                        # Handle empty response (likely blocked)
                        # Default to confused, but if we suspect a block (which usually results in empty response here), use angry as requested
                        # Since we can't easily access the block reason from the stream iterator without more complex error handling,
                        # and the user requested "angry" for prohibited content which causes empty responses, we will use a generic safety message.
                        
                        fallback_message = "<emotion>angry</emotion>I apologize, but I cannot fulfill this request as it violates my safety policies or contains prohibited content."
                        
                        logger.warning(f"AI ({conv_id}) [Blocked/Empty]: Sending fallback message")
                        
                        await websocket.send_json({
                            "type": "content",
                            "content": fallback_message
                        })
                        
                        assistant_msg = Message(
                            conversation_id=conv_id,
                            role="assistant",
                            content=fallback_message
                        )
                        session.add(assistant_msg)
                        await session.commit()
                    
                    await websocket.send_json({
                        "type": "done"
                    })
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """REST endpoint for chat (non-streaming)."""
    supervisor_service = await get_supervisor_service()
    
    # Get or create conversation
    if request.conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == request.conversation_id,
                Conversation.user_id == user.id
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        conv_id = request.conversation_id
    else:
        conversation = Conversation(
            user_id=user.id,
            title="New Conversation"
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        conv_id = conversation.id
    
    # Save user message
    user_msg = Message(
        conversation_id=conv_id,
        role="user",
        content=request.message
    )
    db.add(user_msg)
    await db.commit()
    
    # Log user message
    logger.info(f"User ({conv_id}): {request.message}")
    
    # Get response from supervisor
    config = {"configurable": {"thread_id": str(conv_id)}}
    inputs = {"messages": [{"role": "user", "content": request.message}]}
    
    result = supervisor_service.supervisor_agent.invoke(inputs, config)
    
    # Extract final message
    final_message = ""
    for msg in result.get("messages", []):
        if hasattr(msg, 'type') and msg.type == 'ai' and hasattr(msg, 'content'):
            if isinstance(msg.content, list):
                for block in msg.content:
                    if isinstance(block, dict) and "text" in block:
                        final_message += block["text"]
                    elif isinstance(block, str):
                        final_message += block
            else:
                final_message = str(msg.content)
    
    # Save assistant message
    if not final_message:
        final_message = "<emotion>angry</emotion>I apologize, but I cannot fulfill this request as it violates my safety policies or contains prohibited content."
        logger.warning(f"AI ({conv_id}) [Blocked/Empty]: Sending fallback message")
    
    # Extract emotion for logging
    # Try standard format first: <emotion>type</emotion>
    emotion_match = re.search(r'<emotion>(.*?)</emotion>', final_message)
    if emotion_match:
        emotion = emotion_match.group(1)
        clean_content = re.sub(r'<emotion>.*?</emotion>', '', final_message)
    else:
        # Try fallback format: <type>...</type> or <type>...
        fallback_match = re.search(r'<(happy|confused|sad|angry)>', final_message)
        if fallback_match:
            emotion = fallback_match.group(1)
            # Remove the opening tag
            clean_content = re.sub(r'<(happy|confused|sad|angry)>', '', final_message)
            # Remove potential closing tag
            clean_content = re.sub(r'</(happy|confused|sad|angry)>', '', clean_content)
        else:
            emotion = "unknown"
            clean_content = final_message
    
    logger.info(f"AI ({conv_id}) [Emotion: {emotion}]: {clean_content}")

    assistant_msg = Message(
        conversation_id=conv_id,
        role="assistant",
        content=final_message
    )
    db.add(assistant_msg)
    await db.commit()
    
    return ChatResponse(
        conversation_id=conv_id,
        message=final_message
    )


@router.get("/conversations")
async def list_conversations(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all conversations for the current user."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
    )
    conversations = result.scalars().all()
    
    return [
        {
            "id": str(conv.id),
            "title": conv.title,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat(),
        }
        for conv in conversations
    ]


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all messages for a conversation."""
    # Verify conversation belongs to user
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()
    
    return [
        {
            "id": str(msg.id),
            "role": msg.role,
            "content": msg.content,
            "tool_name": msg.tool_name,
            "created_at": msg.created_at.isoformat(),
        }
        for msg in messages
    ]


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation and all its messages."""
    # Verify conversation belongs to user
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Delete the conversation (messages will be cascade deleted)
    await db.delete(conversation)
    await db.commit()
    
    return {"success": True, "message": "Conversation deleted successfully"}
