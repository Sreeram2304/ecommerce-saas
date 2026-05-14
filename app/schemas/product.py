import uuid
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, field_validator


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: Decimal
    compare_price: Decimal | None = None
    stock_quantity: int = 0
    sku: str | None = None
    category_id: uuid.UUID | None = None
    is_active: bool = True

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Price must be positive")
        return v


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: Decimal | None = None
    stock_quantity: int | None = None
    is_active: bool | None = None


class ProductResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    price: Decimal
    compare_price: Decimal | None
    stock_quantity: int
    sku: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    size: int
    pages: int
