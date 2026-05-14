from pydantic import BaseModel
import uuid


class PaymentIntentCreate(BaseModel):
    order_id: uuid.UUID


class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    amount: int
    currency: str
