"""LinkedIn OAuth configuration — marker: test_auth."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def auth_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JEM_AUTH_MODE", "dev")
    monkeypatch.setenv("JEM_SESSION_SECRET", "test-secret")
    monkeypatch.setenv("JEM_BASE_URL", "https://friedso.com")
    monkeypatch.setenv("JEM_MAP_URL", "https://friedso.com/apps/jem")
    monkeypatch.setenv("JEM_PUBLIC_API_PREFIX", "/api/jem/v1")
    monkeypatch.setenv("JEM_OAUTH_REDIRECT_URI", "https://friedso.com/api/jem/v1/auth/linkedin/callback")
    monkeypatch.setenv("LINKEDIN_CLIENT_ID", "")
    monkeypatch.setenv("LINKEDIN_CLIENT_SECRET", "")


def test_auth_providers_without_linkedin(api_client) -> None:
    resp = api_client.get("/api/v1/auth/providers")
    assert resp.status_code == 200
    body = resp.json()
    assert body["linkedin"] is False
    assert body["dev_login"] is True
    assert body["linkedin_login_url"] is None


def test_auth_providers_with_linkedin(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LINKEDIN_CLIENT_ID", "test-id")
    monkeypatch.setenv("LINKEDIN_CLIENT_SECRET", "test-secret")

    from api.main import create_app
    from fastapi.testclient import TestClient

    client = TestClient(create_app())
    resp = client.get("/api/v1/auth/providers")
    assert resp.status_code == 200
    body = resp.json()
    assert body["linkedin"] is True
    assert body["linkedin_login_url"] == "/api/jem/v1/auth/linkedin/login"
    assert body["oauth_redirect_uri"] == "https://friedso.com/api/jem/v1/auth/linkedin/callback"


def test_linkedin_login_redirect(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LINKEDIN_CLIENT_ID", "test-id")
    monkeypatch.setenv("LINKEDIN_CLIENT_SECRET", "test-secret")

    from api.main import create_app
    from fastapi.testclient import TestClient

    client = TestClient(create_app(), follow_redirects=False)
    resp = client.get(
        "/api/v1/auth/linkedin/login",
        params={"next": "https://friedso.com/apps/jem/#/about"},
    )
    assert resp.status_code == 302
    location = resp.headers["location"]
    assert "linkedin.com/oauth/v2/authorization" in location
    assert "client_id=test-id" in location
    assert "redirect_uri=https%3A%2F%2Ffriedso.com%2Fapi%2Fjem%2Fv1%2Fauth%2Flinkedin%2Fcallback" in location


def test_linkedin_login_unconfigured(api_client) -> None:
    resp = api_client.get("/api/v1/auth/linkedin/login", follow_redirects=False)
    assert resp.status_code == 503
