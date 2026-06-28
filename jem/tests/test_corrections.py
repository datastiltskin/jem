"""Correction proposals and auth — marker: test_corrections."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def dev_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JEM_AUTH_MODE", "dev")
    monkeypatch.setenv("JEM_SESSION_SECRET", "test-secret")


def _login(client, name: str = "Alice", sub: str = "alice") -> None:
    resp = client.post("/api/v1/auth/dev/login", json={"display_name": name, "sub": sub})
    assert resp.status_code == 200


def test_corrections_public_read_empty(api_client) -> None:
    resp = api_client.get("/api/v1/corrections", params={"scope": "overview"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_new_user_proposal_pending_review(api_client) -> None:
    _login(api_client, "New User", "newuser")
    resp = api_client.post(
        "/api/v1/corrections",
        json={
            "scope": "entity:supreme_court_india",
            "body": "Appointment chain citation missing",
            "source_url": "https://www.indiacode.nic.in/",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "pending_review"
    assert body["pending_for_viewer"] is True

    public = api_client.get(
        "/api/v1/corrections",
        params={"scope": "entity:supreme_court_india"},
    )
    # Anonymous read must not show pending proposals
    api_client.cookies.clear()
    public = api_client.get(
        "/api/v1/corrections",
        params={"scope": "entity:supreme_court_india"},
    )
    assert public.json()["total"] == 0


def test_auto_trust_after_three_approvals(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JEM_MAINTAINER_OAUTH_SUBS", "maintainer1")

    _login(api_client, "Maintainer", "maintainer1")
    assert api_client.get("/api/v1/auth/me").json()["role"] == "maintainer"

    _login(api_client, "Author", "author1")
    for i in range(3):
        create = api_client.post(
            "/api/v1/corrections",
            json={
                "scope": "overview",
                "body": f"Correction {i}",
                "source_url": "https://example.com/source",
            },
        )
        assert create.status_code == 201
        pid = create.json()["id"]

        _login(api_client, "Maintainer", "maintainer1")
        approve = api_client.post(f"/admin/corrections/{pid}/approve", follow_redirects=False)
        assert approve.status_code == 303
        _login(api_client, "Author", "author1")

    assert api_client.get("/api/v1/auth/me").json()["role"] == "trusted"

    published = api_client.post(
        "/api/v1/corrections",
        json={
            "scope": "overview",
            "body": "Now auto-published",
            "source_url": "https://example.com/source2",
        },
    )
    assert published.status_code == 201
    assert published.json()["status"] == "published"


def test_trusted_user_can_vote(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JEM_MAINTAINER_OAUTH_SUBS", "maintainer1")

    _login(api_client, "Maintainer", "maintainer1")
    _login(api_client, "Voter", "voter1")
    _login(api_client, "Maintainer", "maintainer1")
    api_client.post(
        "/admin/users/2/role",
        data={"role": "trusted"},
        follow_redirects=False,
    )

    _login(api_client, "Voter", "voter1")
    create = api_client.post(
        "/api/v1/corrections",
        json={
            "scope": "overview",
            "body": "Published correction",
            "source_url": "https://example.com/src",
        },
    )
    assert create.json()["status"] == "published"
    pid = create.json()["id"]

    vote = api_client.post(f"/api/v1/corrections/{pid}/vote")
    assert vote.status_code == 200
    assert vote.json()["voted"] is True
    assert vote.json()["vote_count"] == 1
