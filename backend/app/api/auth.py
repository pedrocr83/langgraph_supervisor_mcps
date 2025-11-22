from fastapi import APIRouter
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend
from app.core.security import fastapi_users, auth_backend
from app.db.models import User
from fastapi_users.schemas import CreateUpdateDictModel
from pydantic import BaseModel, EmailStr
import uuid

router = APIRouter()

# User schemas
class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    is_active: bool
    is_superuser: bool
    is_verified: bool

    class Config:
        from_attributes = True


class UserCreate(CreateUpdateDictModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = None


# Include FastAPI Users routes
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/jwt",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/reset-password",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/verify",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

