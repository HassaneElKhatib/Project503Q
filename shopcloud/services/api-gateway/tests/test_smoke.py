"""Smoke tests covering the customer journey end-to-end through the gateway."""
import uuid

import pytest


def _email() -> str:
    return f"user-{uuid.uuid4().hex[:8]}@example.com"


async def _login_and_get_token(client, email: str, password: str) -> str:
    login = await client.post(
        "/api/users/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, f"login failed: {login.status_code} {login.text}"

    login_body = login.json()
    assert login_body["mfaRequired"] is True
    assert login_body["mfaToken"]

    otp = login_body.get("debugOtp")
    assert otp, "test login expected debugOtp when email delivery is disabled"

    verify = await client.post(
        "/api/users/verify-otp",
        json={"mfaToken": login_body["mfaToken"], "code": otp},
    )
    assert verify.status_code == 200, f"OTP failed: {verify.status_code} {verify.text}"

    token = verify.json()["token"]
    assert token
    return token


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


@pytest.mark.asyncio
async def test_register_login_and_me(client):
    email = _email()
    register = await client.post(
        "/api/users", json={"email": email, "password": "hunter2!", "name": "Alice"}
    )
    assert register.status_code == 201

    token = await _login_and_get_token(client, email, "hunter2!")

    me = await client.get("/api/users/me/", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == email


@pytest.mark.asyncio
async def test_products_listing_seeded(client):
    resp = await client.get("/api/products")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert body["products"]


@pytest.mark.asyncio
async def test_admin_can_create_product(client):
    token = await _login_and_get_token(client, "admin@shopcloud.io", "AdminPass1!")

    create = await client.post(
        "/api/products",
        json={
            "name": "Test Cream",
            "altNames": ["Cream"],
            "description": "A face cream",
            "images": ["https://picsum.photos/seed/test-cream/600/600"],
            "price": 19.99,
            "lastPrice": 24.99,
            "stock": 10,
            "category": "skincare",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create.status_code == 201, create.text
    pid = create.json()["_id"]

    fetched = await client.get(f"/api/products/{pid}")
    assert fetched.status_code == 200


@pytest.mark.asyncio
async def test_full_customer_flow(client):
    """Register, browse, add to cart, place order, leave a review."""
    email = _email()
    await client.post(
        "/api/users", json={"email": email, "password": "hunter2!", "name": "Bob"}
    )

    token = await _login_and_get_token(client, email, "hunter2!")
    auth = {"Authorization": f"Bearer {token}"}

    products = (await client.get("/api/products")).json()["products"]
    assert products
    product = products[0]

    add = await client.post(
        "/api/cart/add", json={"productId": product["_id"], "quantity": 2}, headers=auth
    )
    assert add.status_code == 200
    items = add.json()["cart"]["items"]
    assert items and items[0]["quantity"] == 2

    place = await client.post(
        "/api/orders",
        json={
            "items": [
                {
                    "productId": product["_id"],
                    "name": product["name"],
                    "price": product["price"],
                    "quantity": 2,
                    "image": "",
                }
            ],
            "address": {
                "name": "Bob",
                "line1": "1 Test St",
                "city": "Beirut",
                "country": "LB",
            },
        },
        headers=auth,
    )
    assert place.status_code == 201, place.text
    order_id = place.json()["_id"]

    history = await client.get("/api/orders/history/1/10", headers=auth)
    assert history.status_code == 200
    orders = history.json()["orders"]
    assert any(o["_id"] == order_id for o in orders)

    review = await client.post(
        "/api/reviews",
        json={"productId": product["_id"], "rating": 5, "comment": "Amazing!"},
        headers=auth,
    )
    assert review.status_code == 201

    listing = await client.get(f"/api/reviews/product/{product['_id']}")
    assert listing.status_code == 200
    assert any(r["comment"] == "Amazing!" for r in listing.json()["reviews"])


@pytest.mark.asyncio
async def test_admin_dashboard_aggregates(client):
    token = await _login_and_get_token(client, "admin@shopcloud.io", "AdminPass1!")
    auth = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/dashboard", headers=auth)
    assert resp.status_code == 200
    body = resp.json()
    assert "totals" in body
    assert "products" in body["totals"]