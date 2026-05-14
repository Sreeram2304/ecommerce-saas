import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.main import app
from app.db.session import Base, get_db
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.core.security import hash_password

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/ecommerce_test"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def tenant(db: AsyncSession) -> Tenant:
    t = Tenant(name="Test Store", slug="test-store", is_active=True, plan="free")
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return t


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession, tenant: Tenant) -> User:
    user = User(
        tenant_id=tenant.id,
        email="admin@test.com",
        hashed_password=hash_password("password123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def customer_user(db: AsyncSession, tenant: Tenant) -> User:
    user = User(
        tenant_id=tenant.id,
        email="customer@test.com",
        hashed_password=hash_password("password123"),
        full_name="Test Customer",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, tenant: Tenant, admin_user: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        params={"tenant_slug": tenant.slug},
        json={"email": "admin@test.com", "password": "password123"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def customer_token(client: AsyncClient, tenant: Tenant, customer_user: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        params={"tenant_slug": tenant.slug},
        json={"email": "customer@test.com", "password": "password123"},
    )
    return resp.json()["access_token"]