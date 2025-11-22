from fastapi_users import BaseUserManager, UUIDIDMixin
from app.db.models import User
from app.core.config import settings
import uuid


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """Custom user manager for fastapi-users."""
    
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY
    
    async def on_after_register(self, user: User, request=None):
        """Called after user registration."""
        print(f"User {user.id} has registered.")
    
    async def on_after_forgot_password(self, user: User, token: str, request=None):
        """Called after forgot password."""
        print(f"User {user.id} has forgot their password. Reset token: {token}")
    
    async def on_after_request_verify(self, user: User, token: str, request=None):
        """Called after verification request."""
        print(f"Verification requested for user {user.id}. Verification token: {token}")

