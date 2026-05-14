import uuid
import random
import string
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate, OrderResponse


def generate_order_number() -> str:
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"ORD-{suffix}"


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order(self, data: OrderCreate, current_user: User) -> Order:
        if not data.items:
            raise HTTPException(status_code=400, detail="Order must have at least one item")

        # Fetch and validate all products
        order_items = []
        subtotal = Decimal("0")

        for item_data in data.items:
            result = await self.db.execute(
                select(Product).where(
                    Product.id == item_data.product_id,
                    Product.tenant_id == current_user.tenant_id,
                    Product.is_active == True,
                )
            )
            product = result.scalar_one_or_none()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product {item_data.product_id} not found")
            if product.stock_quantity < item_data.quantity:
                raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.name}")

            item_total = product.price * item_data.quantity
            subtotal += item_total

            order_items.append((product, item_data.quantity, item_total))

        tax_rate = Decimal("0.10")  # 10% tax
        tax_amount = subtotal * tax_rate
        shipping_amount = Decimal("5.00") if subtotal < 50 else Decimal("0")
        total_amount = subtotal + tax_amount + shipping_amount

        order = Order(
            tenant_id=current_user.tenant_id,
            customer_id=current_user.id,
            order_number=generate_order_number(),
            subtotal=subtotal,
            tax_amount=tax_amount,
            shipping_amount=shipping_amount,
            total_amount=total_amount,
            shipping_address=data.shipping_address,
            notes=data.notes,
        )
        self.db.add(order)
        await self.db.flush()

        for product, quantity, item_total in order_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,  # snapshot
                quantity=quantity,
                unit_price=product.price,
                total_price=item_total,
            )
            self.db.add(order_item)
            product.stock_quantity -= quantity  # deduct stock

        return order

    async def get_orders(self, current_user: User) -> list[Order]:
        result = await self.db.execute(
            select(Order)
            .where(Order.tenant_id == current_user.tenant_id)
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()

    async def get_order_by_id(self, order_id: uuid.UUID, current_user: User) -> Order:
        result = await self.db.execute(
            select(Order).where(Order.id == order_id, Order.tenant_id == current_user.tenant_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        # Customers can only see their own orders
        from app.models.user import UserRole
        if current_user.role == UserRole.CUSTOMER and order.customer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        return order

    async def update_order_status(self, order_id: uuid.UUID, new_status: OrderStatus, current_user: User) -> Order:
        order = await self.get_order_by_id(order_id, current_user)
        order.status = new_status
        return order
