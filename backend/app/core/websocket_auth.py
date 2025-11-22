from fastapi import WebSocket, HTTPException
from app.core.security import get_jwt_strategy
from app.db.session import AsyncSessionLocal
from app.db.models import User
from sqlalchemy import select


async def get_websocket_user(websocket: WebSocket) -> User:
    """Authenticate WebSocket connection and return user."""
    token = None
    
    # Try to get token from query params
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
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Verify token
    strategy = get_jwt_strategy()
    try:
        user_data = await strategy.read_token(token)
        user_id = user_data.get('sub')
    except Exception as e:
        await websocket.close(code=1008, reason="Invalid token")
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Get user from database
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            await websocket.close(code=1008, reason="User not found or inactive")
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        return user

