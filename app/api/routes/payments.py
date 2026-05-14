from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.payment import PaymentIntentCreate, PaymentIntentResponse
from app.services.payment import PaymentService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/create-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    data: PaymentIntentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe PaymentIntent for an order. Returns client_secret for frontend."""
    return await PaymentService(db).create_payment_intent(data.order_id, current_user)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(alias="stripe-signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Stripe webhook endpoint. Handles payment_intent.succeeded and payment_intent.payment_failed.
    Register this URL in your Stripe dashboard.
    """
    payload = await request.body()
    return await PaymentService(db).handle_webhook(payload, stripe_signature)
