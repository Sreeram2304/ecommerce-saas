import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def create_test_product(client, admin_token, name="Widget", price="20.00", stock=50):
    resp = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": name, "price": price, "stock_quantity": stock},
    )
    return resp.json()


async def test_create_order_success(client: AsyncClient, admin_token: str, customer_token: str):
    product = await create_test_product(client, admin_token)

    resp = await client.post(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "items": [{"product_id": product["id"], "quantity": 2}],
            "shipping_address": "123 Main St, Hyderabad, 500001",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["order_number"].startswith("ORD-")
    assert data["status"] == "pending"
    assert data["payment_status"] == "unpaid"
    assert len(data["items"]) == 1
    assert float(data["subtotal"]) == 40.00


async def test_order_calculates_tax_and_shipping(client: AsyncClient, admin_token: str, customer_token: str):
    product = await create_test_product(client, admin_token, price="20.00", stock=10)

    resp = await client.post(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "items": [{"product_id": product["id"], "quantity": 1}],
            "shipping_address": "456 Park Ave",
        },
    )
    data = resp.json()
    assert float(data["subtotal"]) == 20.00
    assert float(data["tax_amount"]) == 2.00   # 10% tax
    assert float(data["shipping_amount"]) == 5.00  # < $50 threshold
    assert float(data["total_amount"]) == 27.00


async def test_order_free_shipping_over_50(client: AsyncClient, admin_token: str, customer_token: str):
    product = await create_test_product(client, admin_token, price="60.00", stock=5)

    resp = await client.post(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "items": [{"product_id": product["id"], "quantity": 1}],
            "shipping_address": "789 Oak Rd",
        },
    )
    data = resp.json()
    assert float(data["shipping_amount"]) == 0.00


async def test_order_insufficient_stock(client: AsyncClient, admin_token: str, customer_token: str):
    product = await create_test_product(client, admin_token, stock=2)

    resp = await client.post(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "items": [{"product_id": product["id"], "quantity": 10}],
            "shipping_address": "Anywhere",
        },
    )
    assert resp.status_code == 400
    assert "Insufficient stock" in resp.json()["detail"]


async def test_update_order_status_as_admin(client: AsyncClient, admin_token: str, customer_token: str):
    product = await create_test_product(client, admin_token)
    order = await client.post(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "items": [{"product_id": product["id"], "quantity": 1}],
            "shipping_address": "Test Address",
        },
    )
    order_id = order.json()["id"]

    resp = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "confirmed"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmed"


async def test_customer_cannot_update_order_status(client: AsyncClient, admin_token: str, customer_token: str):
    product = await create_test_product(client, admin_token)
    order = await client.post(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "items": [{"product_id": product["id"], "quantity": 1}],
            "shipping_address": "Test Address",
        },
    )
    order_id = order.json()["id"]

    resp = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"status": "shipped"},
    )
    assert resp.status_code == 403
