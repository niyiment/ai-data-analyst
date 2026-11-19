"""Router tests for session endpoints and cookie flags (US-01, US-03)."""

from httpx import ASGITransport, AsyncClient
from tests.sessions.test_service import FakeSessionRepository

from app.main import create_app
from app.sessions.dependencies import SESSION_COOKIE_NAME, get_session_service
from app.sessions.service import SessionService


async def test_post_session_sets_httponly_secure_cookie_and_hides_token() -> None:
    repo = FakeSessionRepository()
    service = SessionService(repo, ttl_hours=24, cleanup_secret="secret-123")
    test_app = create_app()
    test_app.dependency_overrides[get_session_service] = lambda: service

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="https://test") as client:
        res = await client.post("/api/v1/sessions")
        assert res.status_code == 201
        set_cookie = res.headers.get("set-cookie", "")
        assert SESSION_COOKIE_NAME in set_cookie
        assert "HttpOnly" in set_cookie
        assert "Secure" in set_cookie
        assert "SameSite=lax" in set_cookie

        me = await client.get("/api/v1/sessions/me")
        assert me.status_code == 200
        assert me.json()["session_id"] == res.json()["session_id"]

        deleted = await client.delete("/api/v1/sessions/me")
        assert deleted.status_code == 200
        assert deleted.json()["deleted"] is True


async def test_internal_cleanup_endpoint_checks_secret_header() -> None:
    repo = FakeSessionRepository()
    service = SessionService(repo, ttl_hours=24, cleanup_secret="secret-123")
    test_app = create_app()
    test_app.dependency_overrides[get_session_service] = lambda: service

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="https://test") as client:
        denied = await client.post("/api/v1/internal/cleanup")
        assert denied.status_code == 403

        ok = await client.post(
            "/api/v1/internal/cleanup", headers={"X-Cleanup-Secret": "secret-123"}
        )
        assert ok.status_code == 200
        assert ok.json() == {"sessions_deleted": 0, "schemas_dropped": 0}
