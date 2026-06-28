"""OAuth providers — LinkedIn OIDC + dev mock for local testing."""

from __future__ import annotations

import os
import secrets
import urllib.parse
from typing import Any, Optional

import httpx

LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
LINKEDIN_SCOPES = "openid profile email"

_oauth_states: dict[str, str] = {}


def auth_mode() -> str:
    return os.environ.get("JEM_AUTH_MODE", "dev")


def base_url() -> str:
    return os.environ.get("JEM_BASE_URL", "http://localhost:8000").rstrip("/")


def linkedin_configured() -> bool:
    return bool(os.environ.get("LINKEDIN_CLIENT_ID") and os.environ.get("LINKEDIN_CLIENT_SECRET"))


def linkedin_login_url() -> tuple[str, str]:
    state = secrets.token_urlsafe(16)
    _oauth_states[state] = "linkedin"
    params = {
        "response_type": "code",
        "client_id": os.environ["LINKEDIN_CLIENT_ID"],
        "redirect_uri": f"{base_url()}/api/v1/auth/linkedin/callback",
        "scope": LINKEDIN_SCOPES,
        "state": state,
    }
    return f"{LINKEDIN_AUTH_URL}?{urllib.parse.urlencode(params)}", state


def pop_oauth_state(state: str) -> bool:
    return _oauth_states.pop(state, None) == "linkedin"


def exchange_linkedin_code(code: str) -> dict[str, Any]:
    redirect_uri = f"{base_url()}/api/v1/auth/linkedin/callback"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": os.environ["LINKEDIN_CLIENT_ID"],
        "client_secret": os.environ["LINKEDIN_CLIENT_SECRET"],
    }
    with httpx.Client(timeout=30.0) as client:
        token_resp = client.post(LINKEDIN_TOKEN_URL, data=data)
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]
        user_resp = client.get(
            LINKEDIN_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_resp.raise_for_status()
        return user_resp.json()


def profile_from_linkedin(info: dict[str, Any]) -> dict[str, Optional[str]]:
    return {
        "sub": info.get("sub", ""),
        "display_name": info.get("name") or info.get("given_name") or "LinkedIn User",
        "avatar_url": info.get("picture"),
        "profile_url": None,
        "email": info.get("email"),
    }


def dev_login_available() -> bool:
    return auth_mode() == "dev"
