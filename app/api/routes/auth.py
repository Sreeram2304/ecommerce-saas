from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest, RegisterRequest
from app.services.auth import AuthService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user under a tenant."""
    return await AuthService(db).register(data)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, tenant_slug: str, db: AsyncSession = Depends(get_db)):
    """Login with email and password for a specific tenant."""
    return await AuthService(db).login(data, tenant_slug)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Get a new access token using a refresh token."""
    return await AuthService(db).refresh(data.refresh_token)


@router.post("/logout", status_code=204)
async def logout(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Revoke the current user's refresh token."""
    await AuthService(db).logout(current_user)
