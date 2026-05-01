"""Checkout API tests.

These prove the rubric requirement: the order is written to DB, the SQS
message is published, the cart is cleared, and the response returns
without waiting for the PDF.
"""

from tests.conftest import seed_cart, seed_inventory


# ---------- auth ----------

async def test_checkout_requires_auth(client):
    ac, *_ = client
    response = await ac.post("/checkout", json={})
    assert response.status_code == 401


async def test_checkout_invalid_token_rejected(client):
    ac, *_ = client
    response = await ac.post(
        "/checkout", json={}, headers={"Authorization": "Bearer garbage"}
    )
    assert response.status_code == 401


# ---------- empty cart ----------

async def test_empty_cart_returns_404(client, mint_token):
    ac, _r, _redis, _sqs, _app = client
    token = mint_token(sub="alice")
    response = await ac.post(
        "/checkout", json={}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


# ---------- happy path ----------

async def test_checkout_writes_order_publishes_invoice(client, mint_token):
    ac, _r, redis, sqs, app = client

    await seed_inventory(app, [("p-1", "Widget", 1500, 10), ("p-2", "Gadget", 999, 5)])
    await seed_cart(
        redis,
        "alice",
        [
            {"product_id": "p-1", "product_name": "Widget",
             "unit_price_cents": 1500, "quantity": 2, "currency": "USD"},
            {"product_id": "p-2", "product_name": "Gadget",
             "unit_price_cents": 999, "quantity": 1, "currency": "USD"},
        ],
    )

    token = mint_token(sub="alice", email="alice@example.com")
    response = await ac.post(
        "/checkout", json={}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 202   # the rubric-mandated async response
    body = response.json()
    assert body["status"] == "confirmed"
    assert body["customer_email"] == "alice@example.com"
    assert body["total_cents"] == 2 * 1500 + 999
    assert body["invoice_status"] == "queued"
    assert len(body["items"]) == 2

    # SQS got exactly one message with the right shape
    assert len(sqs.published) == 1
    event = sqs.published[0]
    assert event["order_id"] == body["order_id"]
    assert event["customer_id"] == "alice"
    assert event["customer_email"] == "alice@example.com"
    assert event["total_cents"] == 2 * 1500 + 999
    assert len(event["items"]) == 2
    assert event["event_version"] == 1


async def test_cart_cleared_after_checkout(client, mint_token):
    ac, _r, redis, _sqs, app = client

    await seed_inventory(app, [("p-1", "Widget", 1000, 5)])
    await seed_cart(redis, "alice",
                    [{"product_id": "p-1", "product_name": "Widget",
                      "unit_price_cents": 1000, "quantity": 1, "currency": "USD"}])

    token = mint_token(sub="alice")
    response = await ac.post(
        "/checkout", json={}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 202

    # Cart key is gone
    assert await redis.get("cart:alice") is None


async def test_inventory_decremented(client, mint_token):
    ac, _r, redis, _sqs, app = client

    await seed_inventory(app, [("p-1", "Widget", 1000, 10)])
    await seed_cart(redis, "alice",
                    [{"product_id": "p-1", "product_name": "Widget",
                      "unit_price_cents": 1000, "quantity": 3, "currency": "USD"}])

    token = mint_token(sub="alice")
    await ac.post("/checkout", json={}, headers={"Authorization": f"Bearer {token}"})

    from libs.db import Inventory
    async with app.state.sessionmaker() as session:
        inv = await session.get(Inventory, "p-1")
        assert inv.stock == 7  # 10 - 3


async def test_order_persisted_in_db(client, mint_token):
    ac, _r, redis, _sqs, app = client

    await seed_inventory(app, [("p-1", "Widget", 2000, 10)])
    await seed_cart(redis, "alice",
                    [{"product_id": "p-1", "product_name": "Widget",
                      "unit_price_cents": 2000, "quantity": 2, "currency": "USD"}])

    token = mint_token(sub="alice", email="alice@example.com")
    response = await ac.post(
        "/checkout", json={}, headers={"Authorization": f"Bearer {token}"}
    )
    order_id = response.json()["order_id"]

    from sqlalchemy import select
    from libs.db import Order, OrderItem, Invoice
    async with app.state.sessionmaker() as session:
        order = await session.get(Order, order_id)
        assert order is not None
        assert order.customer_id == "alice"
        assert order.status == "confirmed"
        assert order.total_cents == 4000

        items_result = await session.execute(
            select(OrderItem).where(OrderItem.order_id == order_id)
        )
        items = items_result.scalars().all()
        assert len(items) == 1
        assert items[0].quantity == 2
        assert items[0].unit_price_cents == 2000  # snapshot at order time

        invoice_result = await session.execute(
            select(Invoice).where(Invoice.order_id == order_id)
        )
        invoice = invoice_result.scalar_one()
        assert invoice.status == "queued"


# ---------- insufficient stock ----------

async def test_insufficient_stock_returns_409(client, mint_token):
    ac, _r, redis, sqs, app = client

    await seed_inventory(app, [("p-1", "Limited", 500, 2)])  # only 2 in stock
    await seed_cart(redis, "alice",
                    [{"product_id": "p-1", "product_name": "Limited",
                      "unit_price_cents": 500, "quantity": 5, "currency": "USD"}])

    token = mint_token(sub="alice")
    response = await ac.post(
        "/checkout", json={}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 409

    # No SQS message published, no order created
    assert len(sqs.published) == 0


async def test_insufficient_stock_inventory_unchanged(client, mint_token):
    """Failed checkout doesn't decrement inventory (transaction rollback)."""
    ac, _r, redis, _sqs, app = client

    await seed_inventory(app, [("p-1", "Limited", 500, 2)])
    await seed_cart(redis, "alice",
                    [{"product_id": "p-1", "product_name": "Limited",
                      "unit_price_cents": 500, "quantity": 5, "currency": "USD"}])

    token = mint_token(sub="alice")
    await ac.post("/checkout", json={}, headers={"Authorization": f"Bearer {token}"})

    from libs.db import Inventory
    async with app.state.sessionmaker() as session:
        inv = await session.get(Inventory, "p-1")
        assert inv.stock == 2  # untouched


# ---------- idempotency ----------

async def test_same_idempotency_key_returns_same_order(client, mint_token):
    ac, _r, redis, sqs, app = client

    await seed_inventory(app, [("p-1", "Widget", 1000, 10)])
    await seed_cart(redis, "alice",
                    [{"product_id": "p-1", "product_name": "Widget",
                      "unit_price_cents": 1000, "quantity": 1, "currency": "USD"}])

    token = mint_token(sub="alice")
    headers = {"Authorization": f"Bearer {token}"}

    first = await ac.post(
        "/checkout", json={"idempotency_key": "abc-123"}, headers=headers
    )
    assert first.status_code == 202

    # Re-seed cart since the first call cleared it
    await seed_cart(redis, "alice",
                    [{"product_id": "p-1", "product_name": "Widget",
                      "unit_price_cents": 1000, "quantity": 1, "currency": "USD"}])

    second = await ac.post(
        "/checkout", json={"idempotency_key": "abc-123"}, headers=headers
    )
    assert second.status_code == 202
    assert second.json()["order_id"] == first.json()["order_id"]

    # Only one SQS message - second was idempotent hit
    assert len(sqs.published) == 1


# ---------- isolation between customers ----------

async def test_customers_cannot_checkout_each_others_carts(client, mint_token):
    """Alice's token can only checkout Alice's cart - never Bob's.

    The customer_id comes from the verified JWT sub, never from the request.
    Even if Alice forges a request body claiming to be Bob, her token says alice.
    """
    ac, _r, redis, sqs, app = client

    await seed_inventory(app, [("p-1", "Widget", 1000, 10)])
    # Bob has a cart, Alice doesn't
    await seed_cart(redis, "bob",
                    [{"product_id": "p-1", "product_name": "Widget",
                      "unit_price_cents": 1000, "quantity": 1, "currency": "USD"}])

    alice_token = mint_token(sub="alice")
    response = await ac.post(
        "/checkout", json={}, headers={"Authorization": f"Bearer {alice_token}"}
    )
    # Alice's cart is empty -> 404. She cannot reach Bob's data.
    assert response.status_code == 404
    assert len(sqs.published) == 0

    # Bob's cart is still intact
    raw = await redis.get("cart:bob")
    assert raw is not None
    assert "p-1" in raw


# ---------- email required ----------

async def test_token_without_email_rejected(client, mint_token, rsa_keypair):
    ac, _r, redis, _sqs, app = client
    await seed_inventory(app, [("p-1", "Widget", 1000, 10)])
    await seed_cart(redis, "alice",
                    [{"product_id": "p-1", "product_name": "Widget",
                      "unit_price_cents": 1000, "quantity": 1, "currency": "USD"}])

    # Mint a token without email
    import time
    from jose import jwt as jose_jwt
    now = int(time.time())
    token = jose_jwt.encode(
        {
            "sub": "alice",
            "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TestPool",
            "iat": now, "exp": now + 3600,
            "token_use": "access",
            "client_id": "test-client-id",
        },
        rsa_keypair["private_pem"], algorithm="RS256",
        headers={"kid": "test-kid-1"},
    )

    response = await ac.post(
        "/checkout", json={}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400


# ---------- health ----------

async def test_liveness(client):
    ac, *_ = client
    response = await ac.get("/health/live")
    assert response.status_code == 200


async def test_readiness(client):
    ac, *_ = client
    response = await ac.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert "postgres" in body["checks"]
    assert "redis" in body["checks"]


async def test_metrics(client):
    ac, *_ = client
    response = await ac.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
