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

_oauth_states: dict[str, dict[str, str]] = {}


def auth_mode() -> str:
    return os.environ.get("JEM_AUTH_MODE", "dev")


def base_url() -> str:
    return os.environ.get("JEM_BASE_URL", "http://localhost:8000").rstrip("/")


def map_url() -> str:
    return os.environ.get("JEM_MAP_URL", f"{base_url()}/apps/jem").rstrip("/")


def public_api_prefix() -> str:
    return os.environ.get("JEM_PUBLIC_API_PREFIX", "/api/v1").rstrip("/")


def oauth_redirect_uri() -> str:
    explicit = os.environ.get("JEM_OAUTH_REDIRECT_URI", "").strip()
    if explicit:
        return explicit.rstrip("/")
    return f"{base_url()}{public_api_prefix()}/auth/linkedin/callback"


def safe_return_url(next_param: Optional[str]) -> str:
    default = f"{map_url()}/"
    if not next_param:
        return default
    candidate = next_param.strip()
    if not candidate:
        return default
    try:
        parsed = urllib.parse.urlparse(candidate)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return default
        for base in (map_url(), base_url()):
            if candidate.startswith(base.rstrip("/")):
                return candidate
        return default
    except ValueError:
        return default


def linkedin_configured() -> bool:
    return bool(os.environ.get("LINKEDIN_CLIENT_ID") and os.environ.get("LINKEDIN_CLIENT_SECRET"))


def linkedin_login_url(next_url: Optional[str] = None) -> tuple[str, str]:
    state = secrets.token_urlsafe(16)
    _oauth_states[state] = {"provider": "linkedin", "next": next_url or ""}
    params = {
        "response_type": "code",
        "client_id": os.environ["LINKEDIN_CLIENT_ID"],
        "redirect_uri": oauth_redirect_uri(),
        "scope": LINKEDIN_SCOPES,
        "state": state,
    }
    return f"{LINKEDIN_AUTH_URL}?{urllib.parse.urlencode(params)}", state


def pop_oauth_state(state: str) -> Optional[dict[str, str]]:
    entry = _oauth_states.pop(state, None)
    if entry and entry.get("provider") == "linkedin":
        return entry
    return None


def exchange_linkedin_code(code: str) -> dict[str, Any]:
    redirect_uri = oauth_redirect_uri()
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
    # LinkedIn OIDC userinfo provides name, picture, email — not vanity profile URL.
    profile_url = info.get("profile") or info.get("profile_url")
    if isinstance(profile_url, str) and profile_url.startswith("http"):
        profile_url = profile_url.rstrip("/")
    else:
        profile_url = None
    return {
        "sub": info.get("sub", ""),
        "display_name": info.get("name") or info.get("given_name") or "LinkedIn User",
        "avatar_url": info.get("picture"),
        "profile_url": profile_url,
        "email": info.get("email"),
    }


def dev_login_available() -> bool:
    return auth_mode() == "dev"
