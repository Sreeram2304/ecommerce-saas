import math
import re
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductListResponse, ProductResponse
import uuid


def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9-]+', '-', text.lower()).strip('-')


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_product(self, data: ProductCreate, current_user: User) -> Product:
        slug = slugify(data.name)
        # Ensure slug uniqueness
        result = await self.db.execute(
            select(Product).where(Product.slug == slug, Product.tenant_id == current_user.tenant_id)
        )
        if result.scalar_one_or_none():
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"

        product = Product(
            tenant_id=current_user.tenant_id,
            name=data.name,
            slug=slug,
            description=data.description,
            price=data.price,
            compare_price=data.compare_price,
            stock_quantity=data.stock_quantity,
            sku=data.sku,
            category_id=data.category_id,
            is_active=data.is_active,
        )
        self.db.add(product)
        await self.db.flush()
        return product

    async def get_products(
        self,
        tenant_id: uuid.UUID,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> ProductListResponse:
        filters = [Product.tenant_id == tenant_id]
        if search:
            filters.append(Product.name.ilike(f"%{search}%"))
        if is_active is not None:
            filters.append(Product.is_active == is_active)

        count_result = await self.db.execute(select(func.count()).where(*filters))
        total = count_result.scalar()

        result = await self.db.execute(
            select(Product).where(*filters).offset((page - 1) * size).limit(size).order_by(Product.created_at.desc())
        )
        products = result.scalars().all()

        return ProductListResponse(
            items=[ProductResponse.model_validate(p) for p in products],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total > 0 else 1,
        )

    async def get_product_by_id(self, product_id: uuid.UUID, tenant_id: uuid.UUID) -> Product:
        result = await self.db.execute(
            select(Product).where(Product.id == product_id, Product.tenant_id == tenant_id)
        )
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product

    async def update_product(self, product_id: uuid.UUID, data: ProductUpdate, current_user: User) -> Product:
        product = await self.get_product_by_id(product_id, current_user.tenant_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        return product

    async def delete_product(self, product_id: uuid.UUID, current_user: User) -> None:
        product = await self.get_product_by_id(product_id, current_user.tenant_id)
        await self.db.delete(product)
