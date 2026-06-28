"""Auth dependencies for FastAPI routes."""

from __future__ import annotations

import sqlite3
from typing import Optional

from fastapi import Cookie, Depends, HTTPException

from api.auth.session import SESSION_COOKIE, User, get_user_for_session_cookie
from api.deps import get_db


def optional_user(
    conn: sqlite3.Connection = Depends(get_db),
    jem_session: Optional[str] = Cookie(None, alias=SESSION_COOKIE),
) -> Optional[User]:
    return get_user_for_session_cookie(conn, jem_session)


def require_user(user: Optional[User] = Depends(optional_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in required")
    return user


def require_maintainer(user: User = Depends(require_user)) -> User:
    if not user.is_maintainer:
        raise HTTPException(status_code=403, detail="Maintainer access required")
    return user
