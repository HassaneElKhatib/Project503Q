"""HTTP-level tests for the catalog API.

Uses ASGITransport so we don't need a real socket - the requests go straight
to the FastAPI app in-process.
"""
import pytest


async def test_root_returns_service_info(client):
    response = await client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "catalog"
    assert body["environment"] == "test"


async def test_liveness_always_ok(client):
    response = await client.get("/health/live")
    assert response.status_code == 200


async def test_readiness_returns_check_results(client):
    response = await client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert "checks" in body
    assert "data" in body["checks"]


async def test_metrics_endpoint(client):
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text


async def test_list_products_default(client):
    response = await client.get("/products")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 20
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert len(body["items"]) == 20


async def test_list_products_pagination(client):
    response = await client.get("/products", params={"page": 2, "page_size": 5})
    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 2
    assert body["page_size"] == 5
    assert len(body["items"]) == 5
    assert body["total_pages"] == 4


async def test_list_products_invalid_page_size_clamped_by_validation(client):
    response = await client.get("/products", params={"page_size": 9999})
    assert response.status_code == 422  # Pydantic rejects > 100


async def test_list_products_filter_by_category(client):
    response = await client.get("/products", params={"category": "skincare"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 6
    assert all(p["category"] == "skincare" for p in body["items"])


async def test_list_products_in_stock_only(client):
    response = await client.get("/products", params={"in_stock": "true"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 20
    assert all(p["stock"] > 0 for p in body["items"])


async def test_get_product_by_id(client):
    response = await client.get("/products/p-001")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "p-001"
    assert body["sku"] == "SKN-001"
    assert body["name"] == "Hydra Calm Gel Cleanser"


async def test_get_product_not_found(client):
    response = await client.get("/products/p-999")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert "request_id" in body["error"]


async def test_get_product_response_has_request_id_header(client):
    response = await client.get(
        "/products/p-001", headers={"X-Request-ID": "test-trace-abc"}
    )
    assert response.headers["X-Request-ID"] == "test-trace-abc"


async def test_search_endpoint(client):
    response = await client.get("/products/search", params={"q": "serum"})
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 2
    assert all(
        "serum" in p["name"].lower()
        or "serum" in p["description"].lower()
        or any("serum" in tag.lower() for tag in p["tags"])
        for p in body
    )


async def test_search_requires_query(client):
    response = await client.get("/products/search")
    assert response.status_code == 422


async def test_categories_endpoint(client):
    response = await client.get("/categories")
    assert response.status_code == 200
    body = response.json()
    names = [c["name"] for c in body["categories"]]
    assert names == ["bodycare", "fragrance", "haircare", "makeup", "skincare"]


@pytest.mark.parametrize("path", ["/products", "/products/p-001", "/categories"])
async def test_responses_are_json(client, path):
    response = await client.get(path)
    assert "application/json" in response.headers["content-type"]
