from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.core.security import verify_password, hash_password, create_access_token, create_refresh_token, decode_token
import uuid
import re


def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9-]', '-', text.lower()).strip('-')


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: RegisterRequest) -> TokenResponse:
        # Check if tenant exists
        result = await self.db.execute(select(Tenant).where(Tenant.slug == data.tenant_slug))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        # Check if email already exists in tenant
        result = await self.db.execute(
            select(User).where(User.email == data.email, User.tenant_id == tenant.id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")

        user = User(
            tenant_id=tenant.id,
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=UserRole.CUSTOMER,
        )
        self.db.add(user)
        await self.db.flush()

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        user.refresh_token = refresh_token

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def login(self, data: LoginRequest, tenant_slug: str) -> TokenResponse:
        result = await self.db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        result = await self.db.execute(
            select(User).where(User.email == data.email, User.tenant_id == tenant.id)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not user.is_active:
            raise HTTPException(status_code=400, detail="Account disabled")

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        user.refresh_token = refresh_token

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        result = await self.db.execute(
            select(User).where(User.id == uuid.UUID(payload["sub"]), User.refresh_token == refresh_token)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="Refresh token revoked")

        access_token = create_access_token(str(user.id))
        new_refresh = create_refresh_token(str(user.id))
        user.refresh_token = new_refresh

        return TokenResponse(access_token=access_token, refresh_token=new_refresh)

    async def logout(self, user: User) -> None:
        user.refresh_token = None
