"""FastAPI BFF that exposes the customer-web (faybeauty) REST contract on
top of ShopCloud services.

The gateway owns its own store (SQLite in local auth mode, PostgreSQL in
production) so the React UI can exercise
every feature locally without the AWS-native services. When the upstream
catalog/cart/checkout/admin URLs are configured (see settings.py), the
gateway proxies relevant reads to those services. Everything else
(orders, reviews, dashboards, users) is handled in the gateway itself.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .security import init_gateway_verifiers
from .routes import (
    auth_recovery,
    categories,
    cart,
    dashboard,
    images,
    orders,
    products,
    reviews,
    site_reviews,
    users,
)
from .seed import seed_database
from .settings import settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_gateway_verifiers()
    await init_db()
    await seed_database()
    yield


app = FastAPI(
    title="ShopCloud API Gateway",
    version="1.0.0",
    description=(
        "Backend-for-frontend that maps the customer-web REST contract onto the "
        "ShopCloud microservices."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "service": settings.service_name}


@app.get("/api/healthz")
async def api_healthz() -> dict:
    return {"status": "ok", "service": settings.service_name}


# Mount routers under the /api prefix expected by the React UI.
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(auth_recovery.router, prefix="/api/auth", tags=["auth"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(cart.router, prefix="/api/cart", tags=["cart"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])
app.include_router(site_reviews.router, prefix="/api/site-reviews", tags=["site-reviews"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(images.router, prefix="/api/images", tags=["images"])
