import pytest
from httpx import AsyncClient
from app.models.tenant import Tenant
from app.models.user import User

pytestmark = pytest.mark.asyncio


async def test_create_product_as_admin(client: AsyncClient, admin_token: str):
    resp = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Test Product",
            "description": "A great product",
            "price": "29.99",
            "stock_quantity": 100,
            "sku": "SKU-001",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Product"
    assert data["slug"] == "test-product"
    assert float(data["price"]) == 29.99


async def test_create_product_as_customer_forbidden(client: AsyncClient, customer_token: str):
    resp = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"name": "Unauthorized", "price": "10.00", "stock_quantity": 5},
    )
    assert resp.status_code == 403


async def test_list_products_paginated(client: AsyncClient, admin_token: str):
    # Create 3 products
    for i in range(3):
        await client.post(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": f"Product {i}", "price": "10.00", "stock_quantity": 10},
        )

    resp = await client.get(
        "/api/v1/products?page=1&size=2",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["pages"] == 2


async def test_search_products(client: AsyncClient, admin_token: str):
    await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Blue Widget", "price": "15.00", "stock_quantity": 5},
    )
    await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Red Gadget", "price": "25.00", "stock_quantity": 5},
    )

    resp = await client.get(
        "/api/v1/products?search=widget",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["name"] == "Blue Widget"


async def test_update_product(client: AsyncClient, admin_token: str):
    create = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Old Name", "price": "10.00", "stock_quantity": 5},
    )
    product_id = create.json()["id"]

    resp = await client.patch(
        f"/api/v1/products/{product_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "New Name", "price": "19.99"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


async def test_delete_product(client: AsyncClient, admin_token: str):
    create = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "To Delete", "price": "5.00", "stock_quantity": 1},
    )
    product_id = create.json()["id"]

    resp = await client.delete(
        f"/api/v1/products/{product_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 204
