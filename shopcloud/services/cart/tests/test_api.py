"""Cart API tests."""


def _mock_catalog_product(respx_mock, product_id: str, *, price: int = 1000,
                          name: str = "Test Product", active: bool = True,
                          status: int = 200):
    """Helper - register a catalog product response."""
    if status == 200:
        respx_mock.get(f"http://catalog.test/products/{product_id}").respond(
            status_code=200,
            json={
                "id": product_id,
                "sku": "T-001",
                "name": name,
                "description": "test",
                "category": "books",
                "price_cents": price,
                "currency": "USD",
                "stock": 10,
                "image_url": "",
                "tags": [],
                "is_active": active,
            },
        )
    else:
        respx_mock.get(f"http://catalog.test/products/{product_id}").respond(
            status_code=status, json={"error": {"code": "x", "message": "x"}}
        )


# ---------- auth ----------

async def test_get_cart_requires_auth(client):
    ac, _r, _redis = client
    response = await ac.get("/cart")
    assert response.status_code == 401


async def test_get_cart_invalid_token_rejected(client):
    ac, _r, _redis = client
    response = await ac.get("/cart", headers={"Authorization": "Bearer garbage"})
    assert response.status_code == 401


# ---------- get ----------

async def test_get_empty_cart(client, mint_token):
    ac, _r, _redis = client
    token = mint_token(sub="alice")
    response = await ac.get("/cart", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["customer_id"] == "alice"
    assert body["items"] == []


# ---------- add ----------

async def test_add_item_success(client, mint_token):
    ac, respx_mock, _redis = client
    _mock_catalog_product(respx_mock, "p-1", price=1500, name="Widget")
    token = mint_token(sub="alice")

    response = await ac.post(
        "/cart/items",
        json={"product_id": "p-1", "quantity": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["product_id"] == "p-1"
    assert body["items"][0]["quantity"] == 2
    assert body["items"][0]["unit_price_cents"] == 1500


async def test_add_item_persisted(client, mint_token):
    """After add, GET returns the same items."""
    ac, respx_mock, _redis = client
    _mock_catalog_product(respx_mock, "p-1")
    token = mint_token(sub="alice")
    headers = {"Authorization": f"Bearer {token}"}

    await ac.post("/cart/items", json={"product_id": "p-1", "quantity": 1}, headers=headers)

    response = await ac.get("/cart", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


async def test_add_same_product_twice_increments(client, mint_token):
    ac, respx_mock, _redis = client
    _mock_catalog_product(respx_mock, "p-1")
    token = mint_token(sub="alice")
    headers = {"Authorization": f"Bearer {token}"}

    await ac.post("/cart/items", json={"product_id": "p-1", "quantity": 2}, headers=headers)
    response = await ac.post(
        "/cart/items", json={"product_id": "p-1", "quantity": 3}, headers=headers
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1  # not duplicated
    assert body["items"][0]["quantity"] == 5


async def test_add_product_not_in_catalog_returns_404(client, mint_token):
    ac, respx_mock, _redis = client
    _mock_catalog_product(respx_mock, "p-missing", status=404)
    token = mint_token(sub="alice")

    response = await ac.post(
        "/cart/items",
        json={"product_id": "p-missing", "quantity": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


async def test_add_inactive_product_rejected(client, mint_token):
    ac, respx_mock, _redis = client
    _mock_catalog_product(respx_mock, "p-1", active=False)
    token = mint_token(sub="alice")

    response = await ac.post(
        "/cart/items",
        json={"product_id": "p-1", "quantity": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


async def test_add_excess_quantity_rejected(client, mint_token):
    ac, respx_mock, _redis = client
    _mock_catalog_product(respx_mock, "p-1")
    token = mint_token(sub="alice")
    headers = {"Authorization": f"Bearer {token}"}

    # Pydantic rejects q > 99 at the request layer
    response = await ac.post(
        "/cart/items", json={"product_id": "p-1", "quantity": 200}, headers=headers
    )
    assert response.status_code == 422


# ---------- update ----------

async def test_update_quantity(client, mint_token):
    ac, respx_mock, _redis = client
    _mock_catalog_product(respx_mock, "p-1")
    token = mint_token(sub="alice")
    headers = {"Authorization": f"Bearer {token}"}

    await ac.post("/cart/items", json={"product_id": "p-1", "quantity": 1}, headers=headers)
    response = await ac.patch(
        "/cart/items/p-1", json={"quantity": 5}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["items"][0]["quantity"] == 5


async def test_update_quantity_to_zero_removes(client, mint_token):
    ac, respx_mock, _redis = client
    _mock_catalog_product(respx_mock, "p-1")
    token = mint_token(sub="alice")
    headers = {"Authorization": f"Bearer {token}"}

    await ac.post("/cart/items", json={"product_id": "p-1", "quantity": 1}, headers=headers)
    response = await ac.patch(
        "/cart/items/p-1", json={"quantity": 0}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["items"] == []


async def test_update_missing_item_returns_404(client, mint_token):
    ac, _r, _redis = client
    token = mint_token(sub="alice")
    response = await ac.patch(
        "/cart/items/p-nope",
        json={"quantity": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


# ---------- delete ----------

async def test_remove_item(client, mint_token):
    ac, respx_mock, _redis = client
    _mock_catalog_product(respx_mock, "p-1")
    token = mint_token(sub="alice")
    headers = {"Authorization": f"Bearer {token}"}

    await ac.post("/cart/items", json={"product_id": "p-1", "quantity": 1}, headers=headers)
    response = await ac.delete("/cart/items/p-1", headers=headers)
    assert response.status_code == 200
    assert response.json()["items"] == []


async def test_clear_cart(client, mint_token):
    ac, respx_mock, _redis = client
    _mock_catalog_product(respx_mock, "p-1")
    token = mint_token(sub="alice")
    headers = {"Authorization": f"Bearer {token}"}

    await ac.post("/cart/items", json={"product_id": "p-1", "quantity": 1}, headers=headers)
    response = await ac.delete("/cart", headers=headers)
    assert response.status_code == 204

    # Cart should be empty afterwards
    response = await ac.get("/cart", headers=headers)
    assert response.json()["items"] == []


# ---------- isolation ----------

async def test_carts_isolated_between_customers(client, mint_token):
    """Alice's cart cannot be seen or modified by Bob, and vice versa."""
    ac, respx_mock, _redis = client
    _mock_catalog_product(respx_mock, "p-1")

    alice_token = mint_token(sub="alice")
    bob_token = mint_token(sub="bob")

    await ac.post(
        "/cart/items",
        json={"product_id": "p-1", "quantity": 3},
        headers={"Authorization": f"Bearer {alice_token}"},
    )

    # Bob's cart is empty
    response = await ac.get(
        "/cart", headers={"Authorization": f"Bearer {bob_token}"}
    )
    assert response.json()["items"] == []

    # Alice's cart still has the item
    response = await ac.get(
        "/cart", headers={"Authorization": f"Bearer {alice_token}"}
    )
    assert len(response.json()["items"]) == 1


# ---------- health ----------

async def test_liveness(client):
    ac, _r, _redis = client
    response = await ac.get("/health/live")
    assert response.status_code == 200


async def test_readiness(client):
    ac, _r, _redis = client
    response = await ac.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert "redis" in body["checks"]
    assert "catalog" in body["checks"]
