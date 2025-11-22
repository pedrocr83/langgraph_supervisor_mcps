import asyncio
import contextlib
from app.db.session import AsyncSessionLocal
from app.db.models import User
from app.core.security import UserManager
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from fastapi_users import schemas

class UserCreate(schemas.BaseUserCreate):
    pass

async def create_user():
    async with AsyncSessionLocal() as session:
        user_db = SQLAlchemyUserDatabase(session, User)
        user_manager = UserManager(user_db)
        
        email = "admin@example.com"
        password = "password123"
        
        try:
            user = await user_manager.get_by_email(email)
            print(f"User {email} already exists.")
        except Exception:
            user = await user_manager.create(
                UserCreate(
                    email=email,
                    password=password,
                    is_active=True,
                    is_superuser=True,
                    is_verified=True
                )
            )
            print(f"Created user: {email} / {password}")

if __name__ == "__main__":
    asyncio.run(create_user())
