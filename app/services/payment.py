import stripe
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from app.core.config import settings
from app.models.order import Order, PaymentStatus
from app.models.user import User

stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment_intent(self, order_id: uuid.UUID, current_user: User) -> dict:
        result = await self.db.execute(
            select(Order).where(Order.id == order_id, Order.tenant_id == current_user.tenant_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.payment_status == PaymentStatus.PAID:
            raise HTTPException(status_code=400, detail="Order already paid")

        # Convert to cents
        amount_cents = int(order.total_amount * 100)

        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="usd",
            metadata={
                "order_id": str(order.id),
                "order_number": order.order_number,
                "tenant_id": str(order.tenant_id),
            },
        )
        order.stripe_payment_intent_id = intent.id

        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
            "amount": amount_cents,
            "currency": "usd",
        }

    async def handle_webhook(self, payload: bytes, sig_header: str) -> dict:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

        if event["type"] == "payment_intent.succeeded":
            pi = event["data"]["object"]
            order_id = pi["metadata"].get("order_id")
            if order_id:
                result = await self.db.execute(select(Order).where(Order.id == uuid.UUID(order_id)))
                order = result.scalar_one_or_none()
                if order:
                    order.payment_status = PaymentStatus.PAID

        elif event["type"] == "payment_intent.payment_failed":
            pi = event["data"]["object"]
            order_id = pi["metadata"].get("order_id")
            if order_id:
                result = await self.db.execute(select(Order).where(Order.id == uuid.UUID(order_id)))
                order = result.scalar_one_or_none()
                if order:
                    order.payment_status = PaymentStatus.FAILED

        return {"status": "processed"}
