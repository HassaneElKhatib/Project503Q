import os
import sys
import tempfile
from pathlib import Path

import pytest

# Use a per-session sqlite file. ":memory:" can't be shared across
# connections from a fresh async engine on Windows.
_TMP_DB = Path(tempfile.gettempdir()) / "shopcloud-gateway-tests.db"
if _TMP_DB.exists():
    _TMP_DB.unlink()
os.environ["GATEWAY_DB_URL"] = f"sqlite+aiosqlite:///{_TMP_DB.as_posix()}"
os.environ.setdefault("JWT_SECRET", "test-secret")

# Force reimport so settings pick up the env we just set.
for mod in list(sys.modules):
    if mod.startswith("gateway"):
        sys.modules.pop(mod, None)


@pytest.fixture
async def app():
    from gateway.db import init_db
    from gateway.main import app as fastapi_app
    from gateway.seed import seed_database

    await init_db()
    await seed_database()
    return fastapi_app


@pytest.fixture
async def client(app):
    import httpx

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
