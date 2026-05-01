"""Admin API tests.

Critical test: a token from the customer pool MUST NOT work here. Even if it
contains "admin" in its groups claim, the issuer/client_id won't match this
service's admin pool config and the verifier rejects it.
"""
from tests.conftest import seed_data


# ---------- auth: missing/invalid ----------

async def test_no_token_returns_401(client):
    ac, _r, _app = client
    response = await ac.get("/admin/orders")
    assert response.status_code == 401


async def test_invalid_token_returns_401(client):
    ac, _r, _app = client
    response = await ac.get(
        "/admin/orders", headers={"Authorization": "Bearer garbage"}
    )
    assert response.status_code == 401


# ---------- auth: customer pool token rejected ----------

async def test_customer_pool_token_rejected(client, rsa_keypair):
    """A token from the customer pool must NOT grant admin access.

    This is the security boundary. Customer pool != admin pool. Even with
    'admin' in groups, the issuer claim won't match and the verifier fails.
    """
    import time
    from jose import jwt as jose_jwt

    now = int(time.time())
    customer_token = jose_jwt.encode(
        {
            "sub": "evil-customer",
            # Wrong pool!
            "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_CustomerPool",
            "iat": now, "exp": now + 3600,
            "token_use": "access",
            "client_id": "customer-client-id",
            "cognito:groups": ["admin"],   # even with admin group claim
        },
        rsa_keypair["private_pem"], algorithm="RS256",
        headers={"kid": "test-kid-1"},
    )

    ac, _r, _app = client
    response = await ac.get(
        "/admin/orders", headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert response.status_code == 401  # issuer mismatch


# ---------- auth: admin token without admin group ----------

async def test_admin_token_without_admin_group_returns_403(client, mint_admin_token):
    """User from admin pool but not in 'admin' group -> 403, not 401."""
    ac, _r, _app = client
    token = mint_admin_token(groups=[])  # token valid but no admin group
    response = await ac.get(
        "/admin/orders", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


# ---------- stats ----------

async def test_stats(client, mint_admin_token):
    ac, _r, app = client
    await seed_data(app)
    token = mint_admin_token()
    response = await ac.get(
        "/admin/stats", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_orders"] == 3
    assert body["total_revenue_cents"] == 2000 + 1500 + 3000
    assert "confirmed" in body["by_status"]


# ---------- list orders ----------

async def test_list_orders(client, mint_admin_token):
    ac, _r, app = client
    await seed_data(app)
    token = mint_admin_token()
    response = await ac.get(
        "/admin/orders", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3
    # Ordered newest-first
    assert all(item["status"] == "confirmed" for item in body["items"])


async def test_list_orders_filter_by_status(client, mint_admin_token):
    ac, _r, app = client
    await seed_data(app)
    token = mint_admin_token()
    response = await ac.get(
        "/admin/orders", params={"status": "fulfilled"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0


async def test_list_orders_pagination(client, mint_admin_token):
    ac, _r, app = client
    await seed_data(app)
    token = mint_admin_token()
    response = await ac.get(
        "/admin/orders", params={"page": 1, "page_size": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["page_size"] == 2
    assert len(body["items"]) == 2
    assert body["total_pages"] == 2


# ---------- get one order ----------

async def test_get_order(client, mint_admin_token):
    ac, _r, app = client
    await seed_data(app)
    token = mint_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_resp = await ac.get("/admin/orders", headers=headers)
    order_id = list_resp.json()["items"][0]["id"]

    response = await ac.get(f"/admin/orders/{order_id}", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == order_id
    assert len(body["items"]) >= 1


async def test_get_order_not_found(client, mint_admin_token):
    ac, _r, app = client
    token = mint_admin_token()
    response = await ac.get(
        "/admin/orders/doesnotexist",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


# ---------- update status ----------

async def test_update_order_status(client, mint_admin_token):
    ac, _r, app = client
    await seed_data(app)
    token = mint_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_resp = await ac.get("/admin/orders", headers=headers)
    order_id = list_resp.json()["items"][0]["id"]

    response = await ac.patch(
        f"/admin/orders/{order_id}/status",
        json={"status": "fulfilled"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "fulfilled"

    # Verify persisted
    response = await ac.get(f"/admin/orders/{order_id}", headers=headers)
    assert response.json()["status"] == "fulfilled"


async def test_update_status_invalid_value_rejected(client, mint_admin_token):
    ac, _r, _app = client
    token = mint_admin_token()
    response = await ac.patch(
        "/admin/orders/whatever/status",
        json={"status": "DELETED_BY_HACKER"},
        headers={"Authorization": f"Bearer {token}"},
    )
    # Pydantic regex blocks at request validation
    assert response.status_code == 422


# ---------- list customers ----------

async def test_list_customers(client, mint_admin_token):
    ac, _r, app = client
    await seed_data(app)
    token = mint_admin_token()
    response = await ac.get(
        "/admin/customers", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    customers = {c["id"]: c for c in body["items"]}
    assert customers["alice"]["order_count"] == 2
    assert customers["alice"]["total_spent_cents"] == 2000 + 1500
    assert customers["bob"]["order_count"] == 1


# ---------- health ----------

async def test_liveness(client):
    ac, *_ = client
    response = await ac.get("/health/live")
    assert response.status_code == 200


async def test_readiness(client):
    ac, *_ = client
    response = await ac.get("/health/ready")
    assert response.status_code == 200
    assert "postgres" in response.json()["checks"]


async def test_metrics(client):
    ac, *_ = client
    response = await ac.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
