"""Authentication routes — LinkedIn OIDC + dev mock."""

from __future__ import annotations

import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from api.auth import oauth
from api.auth.deps import optional_user, require_user
from api.auth.session import SESSION_COOKIE, SESSION_DAYS, User, create_session, delete_session, upsert_oauth_user
from api.deps import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class DevLoginRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)
    sub: Optional[str] = Field(default=None, max_length=120)


class UserResponse(BaseModel):
    id: int
    display_name: str
    avatar_url: str | None
    role: str
    can_vote: bool
    oauth_provider: str


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        role=user.role,
        can_vote=user.can_vote,
        oauth_provider=user.oauth_provider,
    )


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_DAYS * 86400,
        path="/",
    )


@router.get("/me")
def auth_me(user: Optional[User] = Depends(optional_user)) -> Optional[UserResponse]:
    return _user_response(user) if user else None


@router.post("/logout")
def logout(
    response: Response,
    conn: sqlite3.Connection = Depends(get_db),
    user: User = Depends(require_user),
    jem_session: Optional[str] = None,
) -> dict:
    from api.auth.session import _decode_session

    session_id = _decode_session(jem_session or "")
    if session_id:
        delete_session(conn, session_id)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"status": "ok", "user_id": user.id}


@router.get("/linkedin/login")
def linkedin_login() -> RedirectResponse:
    if not oauth.linkedin_configured():
        raise HTTPException(
            status_code=503,
            detail="LinkedIn OAuth not configured (set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET)",
        )
    url, _ = oauth.linkedin_login_url()
    return RedirectResponse(url=url, status_code=302)


@router.get("/linkedin/callback")
def linkedin_callback(
    response: Response,
    conn: sqlite3.Connection = Depends(get_db),
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
) -> RedirectResponse:
    if error:
        raise HTTPException(status_code=400, detail=f"LinkedIn OAuth error: {error}")
    if not code or not state or not oauth.pop_oauth_state(state):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    if not oauth.linkedin_configured():
        raise HTTPException(status_code=503, detail="LinkedIn OAuth not configured")

    info = oauth.exchange_linkedin_code(code)
    profile = oauth.profile_from_linkedin(info)
    user = upsert_oauth_user(conn, provider="linkedin", **profile)
    token = create_session(conn, user.id)

    redirect = RedirectResponse(url=f"{oauth.base_url()}/admin/", status_code=302)
    _set_session_cookie(redirect, token)
    return redirect


@router.post("/dev/login", response_model=UserResponse)
def dev_login(
    body: DevLoginRequest,
    response: Response,
    conn: sqlite3.Connection = Depends(get_db),
) -> UserResponse:
    if not oauth.dev_login_available():
        raise HTTPException(status_code=403, detail="Dev auth disabled (set JEM_AUTH_MODE=dev)")

    sub = body.sub or body.display_name.lower().replace(" ", "_")
    user = upsert_oauth_user(
        conn,
        provider="dev",
        sub=sub,
        display_name=body.display_name,
    )
    token = create_session(conn, user.id)
    _set_session_cookie(response, token)
    return _user_response(user)


@router.get("/providers")
def auth_providers() -> dict:
    return {
        "mode": oauth.auth_mode(),
        "linkedin": oauth.linkedin_configured(),
        "dev_login": oauth.dev_login_available(),
        "linkedin_login_url": "/api/v1/auth/linkedin/login" if oauth.linkedin_configured() else None,
    }
