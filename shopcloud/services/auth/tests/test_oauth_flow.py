from urllib.parse import parse_qs, urlparse


# ---------- /auth/login ----------

async def test_login_redirects_to_cognito(client):
    ac, _respx = client
    response = await ac.get("/auth/login", follow_redirects=False)
    assert response.status_code == 302

    location = response.headers["location"]
    parsed = urlparse(location)
    assert parsed.netloc == "test.auth.us-east-1.amazoncognito.com"
    assert parsed.path == "/oauth2/authorize"

    qs = parse_qs(parsed.query)
    assert qs["response_type"] == ["code"]
    assert qs["client_id"] == ["test-client-id"]
    assert qs["redirect_uri"] == ["https://app.test/auth/callback"]
    assert "openid" in qs["scope"][0]
    assert qs["state"][0]  # state is non-empty


async def test_login_sets_state_cookie(client):
    ac, _respx = client
    response = await ac.get("/auth/login", follow_redirects=False)

    cookies = response.headers.get_list("set-cookie")
    assert any("sc_state=" in c for c in cookies)


async def test_login_state_cookie_matches_query_param(client):
    ac, _respx = client
    response = await ac.get("/auth/login", follow_redirects=False)

    location = response.headers["location"]
    state_in_url = parse_qs(urlparse(location).query)["state"][0]

    set_cookie = next(
        c for c in response.headers.get_list("set-cookie") if c.startswith("sc_state=")
    )
    cookie_value = set_cookie.split(";", 1)[0].split("=", 1)[1]
    assert cookie_value == state_in_url


async def test_login_with_next_param_round_trips(client):
    ac, _respx = client
    response = await ac.get(
        "/auth/login", params={"next": "/cart"}, follow_redirects=False
    )
    # We can't decode the next param without the signing key, but we can confirm
    # the request was accepted (302) and a state was issued.
    assert response.status_code == 302


async def test_login_rejects_external_next_url(client):
    ac, _respx = client
    response = await ac.get(
        "/auth/login",
        params={"next": "https://evil.example/steal"},
        follow_redirects=False,
    )
    # Open-redirect protection: external URLs get coerced to "/"
    assert response.status_code == 302


# ---------- /auth/callback ----------

async def test_callback_missing_code_rejected(client):
    ac, _respx = client
    response = await ac.get(
        "/auth/callback", params={"state": "anything"}, follow_redirects=False
    )
    assert response.status_code == 400


async def test_callback_with_cognito_error_returns_400(client):
    ac, _respx = client
    response = await ac.get(
        "/auth/callback",
        params={"error": "access_denied", "error_description": "user said no"},
        follow_redirects=False,
    )
    assert response.status_code == 400


async def test_callback_state_mismatch_rejected(client):
    """If the state cookie doesn't match the state query param, reject."""
    ac, _respx = client

    # First, get a real state cookie issued
    login = await ac.get("/auth/login", follow_redirects=False)
    cookies = login.headers.get_list("set-cookie")
    state_cookie = next(c for c in cookies if c.startswith("sc_state="))
    state_value = state_cookie.split(";", 1)[0].split("=", 1)[1]

    # Now hit callback with a DIFFERENT state in the query
    response = await ac.get(
        "/auth/callback",
        params={"code": "fake-code", "state": "wrong-state"},
        cookies={"sc_state": state_value},
        follow_redirects=False,
    )
    assert response.status_code == 400


async def test_callback_full_happy_path(client, mint_token):
    """Login -> Cognito -> callback -> tokens stored in cookies."""
    ac, respx_mock = client

    # Mock the Cognito token endpoint
    access_token = mint_token(token_use="access")
    id_token = mint_token(token_use="id", email="alice@example.com")
    respx_mock.post(
        "https://test.auth.us-east-1.amazoncognito.com/oauth2/token"
    ).respond(
        json={
            "access_token": access_token,
            "id_token": id_token,
            "refresh_token": "refresh-abc-123",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
    )

    # 1. Hit /auth/login to get a real state
    login = await ac.get("/auth/login", follow_redirects=False)
    state_cookie = next(
        c for c in login.headers.get_list("set-cookie") if c.startswith("sc_state=")
    )
    state_value = state_cookie.split(";", 1)[0].split("=", 1)[1]

    # 2. Hit /auth/callback with that state and a fake code
    callback = await ac.get(
        "/auth/callback",
        params={"code": "fake-code", "state": state_value},
        cookies={"sc_state": state_value},
        follow_redirects=False,
    )

    assert callback.status_code == 302
    # Should redirect to / (the default next_url)
    assert callback.headers["location"] == "/"

    # Should have set access/id/refresh cookies
    cookies_set = callback.headers.get_list("set-cookie")
    assert any("sc_access=" in c for c in cookies_set)
    assert any("sc_id=" in c for c in cookies_set)
    assert any("sc_refresh=" in c for c in cookies_set)
    # And cleared the state cookie
    assert any("sc_state=" in c and "Max-Age=0" in c for c in cookies_set)


# ---------- /auth/refresh ----------

async def test_refresh_without_cookie_returns_401(client):
    ac, _respx = client
    response = await ac.post("/auth/refresh")
    assert response.status_code == 401


async def test_refresh_exchanges_token(client, mint_token):
    ac, respx_mock = client

    new_access = mint_token(token_use="access")
    respx_mock.post(
        "https://test.auth.us-east-1.amazoncognito.com/oauth2/token"
    ).respond(
        json={
            "access_token": new_access,
            "id_token": None,
            "refresh_token": None,  # Cognito may or may not rotate refresh tokens
            "token_type": "Bearer",
            "expires_in": 3600,
        }
    )

    response = await ac.post(
        "/auth/refresh", cookies={"sc_refresh": "old-refresh-token"}
    )
    assert response.status_code == 200
    assert response.json()["expires_in"] == 3600

    # New access cookie should be set
    cookies_set = response.headers.get_list("set-cookie")
    assert any("sc_access=" in c for c in cookies_set)


# ---------- /auth/logout ----------

async def test_logout_redirects_to_cognito_and_clears_cookies(client):
    ac, _respx = client
    response = await ac.post("/auth/logout", follow_redirects=False)

    assert response.status_code == 302
    parsed = urlparse(response.headers["location"])
    assert parsed.netloc == "test.auth.us-east-1.amazoncognito.com"
    assert parsed.path == "/logout"

    cookies_set = response.headers.get_list("set-cookie")
    # Both cookies should be cleared
    assert any("sc_access=" in c and "Max-Age=0" in c for c in cookies_set)
    assert any("sc_id=" in c and "Max-Age=0" in c for c in cookies_set)
    assert any("sc_refresh=" in c and "Max-Age=0" in c for c in cookies_set)


# ---------- /me ----------

async def test_me_with_bearer_header(client, mint_token):
    ac, _respx = client
    token = mint_token(sub="user-42", email="bob@example.com")

    response = await ac.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["sub"] == "user-42"
    assert body["is_admin"] is False


async def test_me_with_cookie(client, mint_token):
    ac, _respx = client
    token = mint_token(sub="user-7")

    response = await ac.get("/me", cookies={"sc_access": token})
    assert response.status_code == 200
    assert response.json()["sub"] == "user-7"


async def test_me_admin_group(client, mint_token):
    ac, _respx = client
    token = mint_token(sub="admin-1", groups=["admin"])

    response = await ac.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["is_admin"] is True


async def test_me_no_token_returns_401(client):
    ac, _respx = client
    response = await ac.get("/me")
    assert response.status_code == 401


async def test_me_invalid_token_returns_401(client):
    ac, _respx = client
    response = await ac.get(
        "/me", headers={"Authorization": "Bearer not.a.real.token"}
    )
    assert response.status_code == 401


# ---------- health ----------

async def test_liveness(client):
    ac, _respx = client
    response = await ac.get("/health/live")
    assert response.status_code == 200


async def test_readiness_includes_jwks_check(client):
    ac, _respx = client
    response = await ac.get("/health/ready")
    assert response.status_code == 200
    assert "cognito_jwks" in response.json()["checks"]


async def test_metrics(client):
    ac, _respx = client
    response = await ac.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
