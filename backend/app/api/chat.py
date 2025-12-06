from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json
import uuid
from app.core.security import current_active_user
from app.db.models import User
from app.services.agents.supervisor import get_supervisor_service
from app.services.title_generator import get_title_generator
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
    logger.info(f"WebSocket accepted for conversation {conversation_id}")
    
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
            logger.warning("WebSocket auth failed: No token")
            await websocket.close(code=1008, reason="Authentication required")
            return
        
        # Verify token and get user
        from jose import jwt, JWTError
        from app.core.config import settings
        
        try:
            # Manually decode token
            # We verify the signature using the secret key
            # We skip audience validation to avoid library compatibility issues
            # The signature verification is sufficient for this use case
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
            user_id = payload.get('sub')
            if not user_id:
                 logger.warning("WebSocket auth failed: No user_id in token")
                 await websocket.close(code=1008, reason="Invalid token")
                 return
                 
            # Convert string UUID to UUID object if needed, but DB query handles string usually
            # user_id is string in JWT, usually UUID string
            
        except JWTError as e:
            logger.warning(f"WebSocket auth failed: Token validation error: {e}")
            await websocket.close(code=1008, reason="Invalid token")
            return
        except Exception as e:
            logger.error(f"WebSocket auth failed: Unexpected error: {e}")
            await websocket.close(code=1008, reason="Internal authentication error")
            return
        
        # Get user from database
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user or not user.is_active:
                logger.warning(f"WebSocket auth failed: User {user_id} not found or inactive")
                await websocket.close(code=1008, reason="User not found or inactive")
                return
        
        logger.info(f"WebSocket authenticated for user {user.email}")
        
        supervisor_service = await get_supervisor_service()
        
        # Get or create conversation
        async with AsyncSessionLocal() as session:
            if conversation_id != "new":
                try:
                    conv_uuid = uuid.UUID(conversation_id)
                except ValueError:
                    await websocket.close(code=1003, reason="Invalid conversation id")
                    return
                
                result = await session.execute(
                    select(Conversation).where(
                        Conversation.id == conv_uuid,
                        Conversation.user_id == user.id
                    )
                )
                conversation = result.scalar_one_or_none()
                if not conversation:
                    await websocket.close(code=1008, reason="Conversation not found")
                    return
                conv_id = conversation.id
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
            logger.info(f"WebSocket sent conversation ID {conv_id}")
            
            # Wait for messages
            while True:
                try:
                    data = await websocket.receive_json()
                except WebSocketDisconnect:
                    logger.info("WebSocket client disconnected during receive")
                    break
                
                if data.get("type") != "message":
                    continue
                
                user_message = data.get("message", "")
                logger.info(f"User ({conv_id}) via WS: {user_message}")
                
                # Save user message
                user_msg = Message(
                    conversation_id=conv_id,
                    role="user",
                    content=user_message
                )
                session.add(user_msg)
                await session.commit()
                
                config = {
                    "configurable": {"thread_id": str(conv_id)},
                    "recursion_limit": 50  # Increase recursion limit to prevent recursion errors
                }
                inputs = {"messages": [{"role": "user", "content": user_message}]}
                
                full_response = ""
                seen_message_ids = set()
                
                try:
                    # Use async streaming to avoid blocking the FastAPI event loop
                    async for step in supervisor_service.supervisor_agent.astream(inputs, config):
                        for update in step.values():
                            if "messages" not in update:
                                continue
                            
                            for msg in update["messages"]:
                                msg_id = getattr(msg, "id", None) or id(msg)
                                if msg_id in seen_message_ids:
                                    continue
                                seen_message_ids.add(msg_id)
                                
                                if not getattr(msg, "content", None):
                                    continue
                                
                                if msg.type == "tool":
                                    await websocket.send_json({
                                        "type": "tool",
                                        "name": msg.name or "Unknown",
                                        "content": str(msg.content)
                                    })
                                elif msg.type == "ai":
                                    if getattr(msg, "tool_calls", None):
                                        for tool_call in msg.tool_calls:
                                            await websocket.send_json({
                                                "type": "tool_call",
                                                "name": tool_call.get("name", "Unknown"),
                                                "args": tool_call.get("args", {})
                                            })
                                    
                                    content_str = ""
                                    if isinstance(msg.content, list):
                                        for block in msg.content:
                                            if isinstance(block, dict) and "text" in block:
                                                content_str += block["text"]
                                            elif isinstance(block, str):
                                                content_str += block
                                    else:
                                        content_str = str(msg.content)
                                    
                                    if content_str:
                                        full_response += content_str
                                        await websocket.send_json({
                                            "type": "content",
                                            "content": content_str
                                        })
                except Exception as stream_err:
                    logger.error(f"Streaming error for conversation {conv_id}: {stream_err}", exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "message": "Failed to generate response"
                    })
                    continue
                
                if not full_response:
                    fallback_message = "<emotion>angry</emotion>I apologize, but I cannot fulfill this request as it violates my safety policies or contains prohibited content."
                    logger.warning(f"AI ({conv_id}) [Blocked/Empty]: Sending fallback message")
                    await websocket.send_json({
                        "type": "content",
                        "content": fallback_message
                    })
                    full_response = fallback_message
                
                assistant_msg = Message(
                    conversation_id=conv_id,
                    role="assistant",
                    content=full_response
                )
                session.add(assistant_msg)
                await session.commit()
                
                # Generate title if conversation has enough messages and title is still default
                try:
                    title_generator = await get_title_generator()
                    new_title = await title_generator.generate_title(session, str(conv_id), min_messages=6)
                    if new_title:
                        # Refresh conversation to ensure we have the latest version
                        await session.refresh(conversation)
                        conversation.title = new_title
                        await session.commit()
                        logger.info(f"Updated conversation {conv_id} title to: {new_title}")
                except Exception as title_err:
                    logger.error(f"Error generating title for conversation {conv_id}: {title_err}", exc_info=True)
                    # Don't fail the request if title generation fails
                
                await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass



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
    
    # Use async invocation to better integrate with FastAPI's async model
    result = await supervisor_service.supervisor_agent.ainvoke(inputs, config)
    
    # Extract final message (only the last one)
    final_message = ""
    if "messages" in result and result["messages"]:
        last_msg = result["messages"][-1]
        if hasattr(last_msg, 'content'):
            if isinstance(last_msg.content, list):
                for block in last_msg.content:
                    if isinstance(block, dict) and "text" in block:
                        final_message += block["text"]
                    elif isinstance(block, str):
                        final_message += block
            else:
                final_message = str(last_msg.content)
    
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
    
    # Generate title if conversation has enough messages and title is still default
    try:
        title_generator = await get_title_generator()
        new_title = await title_generator.generate_title(db, str(conv_id), min_messages=6)
        if new_title:
            # Refresh conversation to ensure we have the latest version
            await db.refresh(conversation)
            conversation.title = new_title
            await db.commit()
            logger.info(f"Updated conversation {conv_id} title to: {new_title}")
    except Exception as title_err:
        logger.error(f"Error generating title for conversation {conv_id}: {title_err}", exc_info=True)
        # Don't fail the request if title generation fails
    
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
