# Import all models here so Alembic can detect them
from app.db.session import Base  # noqa
from app.models.tenant import Tenant  # noqa
from app.models.user import User  # noqa
from app.models.product import Product, Category  # noqa
from app.models.order import Order, OrderItem  # noqa
