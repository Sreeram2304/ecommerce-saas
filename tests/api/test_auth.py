import pytest
from httpx import AsyncClient
from app.models.tenant import Tenant
from app.models.user import User

pytestmark = pytest.mark.asyncio


async def test_register_success(client: AsyncClient, tenant: Tenant):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "newuser@test.com",
        "password": "securepass123",
        "full_name": "New User",
        "tenant_slug": tenant.slug,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_register_duplicate_email(client: AsyncClient, tenant: Tenant, customer_user: User):
    resp = await client.post("/api/v1/auth/register", json={
        "email": customer_user.email,
        "password": "securepass123",
        "full_name": "Another User",
        "tenant_slug": tenant.slug,
    })
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


async def test_login_success(client: AsyncClient, tenant: Tenant, admin_user: User):
    resp = await client.post(
        "/api/v1/auth/login",
        params={"tenant_slug": tenant.slug},
        json={"email": admin_user.email, "password": "password123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_wrong_password(client: AsyncClient, tenant: Tenant, admin_user: User):
    resp = await client.post(
        "/api/v1/auth/login",
        params={"tenant_slug": tenant.slug},
        json={"email": admin_user.email, "password": "wrongpassword"},
    )
    assert resp.status_code == 401


async def test_get_me(client: AsyncClient, admin_token: str, admin_user: User):
    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == admin_user.email


async def test_get_me_unauthorized(client: AsyncClient):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 403


async def test_refresh_token(client: AsyncClient, tenant: Tenant, admin_user: User):
    login = await client.post(
        "/api/v1/auth/login",
        params={"tenant_slug": tenant.slug},
        json={"email": admin_user.email, "password": "password123"},
    )
    refresh_token = login.json()["refresh_token"]

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
