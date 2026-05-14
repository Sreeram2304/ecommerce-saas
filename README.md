# 🛒 Multi-tenant SaaS E-commerce API

A production-ready backend built with **FastAPI**, **PostgreSQL**, and **Redis** — showcasing real-world patterns used in SaaS products.

[![CI](https://github.com/Sreeram2304/ecommerce-saas/actions/workflows/ci.yml/badge.svg)](https://github.com/Sreeram2304/ecommerce-saas/actions)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)

---

## ✨ Features

| Feature | Details |
|---|---|
| **Multi-tenancy** | Full tenant isolation — each store has its own users, products, and orders |
| **JWT Auth** | Access + refresh token rotation with revocation on logout |
| **RBAC** | Four roles: `super_admin`, `admin`, `manager`, `customer` |
| **Products** | Full CRUD, slug generation, pagination, full-text search |
| **Orders** | Stock validation, automatic tax (10%) + shipping logic, order lifecycle |
| **Payments** | Stripe PaymentIntents + webhook handler for async payment confirmation |
| **Async** | Fully async with SQLAlchemy 2.0 + asyncpg |
| **Background Jobs** | Celery + Redis for email notifications and async tasks |
| **Migrations** | Alembic with auto-generated migration scripts |
| **Tests** | pytest-asyncio with 20+ tests covering auth, products, and orders |
| **CI/CD** | GitHub Actions pipeline with PostgreSQL and Redis services |

---

## 🏗️ Project Structure

```
ecommerce-saas/
├── app/
│   ├── api/
│   │   ├── deps.py              # Auth dependencies & role guards
│   │   └── routes/
│   │       ├── auth.py          # Register, login, refresh, logout
│   │       ├── users.py         # User profile + admin management
│   │       ├── products.py      # Product CRUD + pagination
│   │       ├── orders.py        # Order lifecycle
│   │       └── payments.py      # Stripe integration + webhooks
│   ├── core/
│   │   ├── config.py            # Pydantic Settings (env-based config)
│   │   └── security.py          # JWT creation/decoding, bcrypt hashing
│   ├── db/
│   │   ├── session.py           # Async SQLAlchemy engine + session
│   │   └── base.py              # Alembic model registry
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── tenant.py            # Multi-tenant root model
│   │   ├── user.py              # User + UserRole enum
│   │   ├── product.py           # Product + Category
│   │   └── order.py             # Order + OrderItem + status enums
│   ├── schemas/                 # Pydantic v2 request/response schemas
│   └── services/                # Business logic layer (one per domain)
│       ├── auth.py
│       ├── product.py
│       ├── order.py
│       └── payment.py
├── alembic/                     # Database migrations
├── tests/
│   ├── conftest.py              # Fixtures: db, client, users, tokens
│   ├── api/
│   │   ├── test_auth.py
│   │   ├── test_products.py
│   │   └── test_orders.py
├── .github/workflows/ci.yml     # GitHub Actions CI
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## 🚀 Quick Start

### With Docker (recommended)

```bash
git clone https://github.com/Sreeram2304/ecommerce-saas
cd ecommerce-saas
cp .env.example .env         # edit your secrets
docker-compose up --build
```

API running at: http://localhost:8000  
Interactive docs: http://localhost:8000/docs

### Without Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # configure DATABASE_URL, REDIS_URL etc.

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

---

## 📡 API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register a new user |
| POST | `/api/v1/auth/login?tenant_slug=...` | Login and get tokens |
| POST | `/api/v1/auth/refresh` | Rotate refresh token |
| POST | `/api/v1/auth/logout` | Revoke refresh token |

### Users
| Method | Endpoint | Access |
|---|---|---|
| GET | `/api/v1/users/me` | All |
| PATCH | `/api/v1/users/me` | All |
| GET | `/api/v1/users` | Admin only |
| POST | `/api/v1/users` | Admin only |
| DELETE | `/api/v1/users/{id}` | Admin only |

### Products
| Method | Endpoint | Access |
|---|---|---|
| GET | `/api/v1/products?page=1&size=20&search=...` | All |
| POST | `/api/v1/products` | Manager+ |
| GET | `/api/v1/products/{id}` | All |
| PATCH | `/api/v1/products/{id}` | Manager+ |
| DELETE | `/api/v1/products/{id}` | Manager+ |

### Orders
| Method | Endpoint | Access |
|---|---|---|
| POST | `/api/v1/orders` | All |
| GET | `/api/v1/orders` | All (customers see own only) |
| GET | `/api/v1/orders/{id}` | All |
| PATCH | `/api/v1/orders/{id}/status` | Manager+ |

### Payments
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/payments/create-intent` | Create Stripe PaymentIntent |
| POST | `/api/v1/payments/webhook` | Stripe webhook handler |

---

## 🧪 Running Tests

```bash
# Ensure a test database exists: ecommerce_test
pytest tests/ -v
pytest tests/ -v --cov=app --cov-report=html   # with coverage
```

---

## 🗄️ Database Migrations

```bash
# Generate a new migration after model changes
alembic revision --autogenerate -m "add_column_xyz"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

---

## 🏛️ Architecture Decisions

- **Service layer** — Business logic lives in `services/`, not in route handlers. Routes only validate input and call services.
- **Tenant isolation** — Every query filters by `tenant_id`. Users can never access another tenant's data.
- **Stock snapshot** — `OrderItem.product_name` stores the product name at purchase time, so renaming a product doesn't corrupt order history.
- **Webhook security** — Stripe webhook signature is verified before processing any payment events.
- **Token rotation** — Refresh tokens are stored hashed per-user and rotated on every use.

---

## 🚢 Deployment

Recommended free-tier platforms: **Railway**, **Render**, or **Fly.io**

```bash
# Set production env vars
SECRET_KEY=<strong-random-key>
DATABASE_URL=<your-prod-postgres-url>
STRIPE_SECRET_KEY=sk_live_...
```
