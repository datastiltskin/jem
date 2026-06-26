"""Signed session cookies and DB-backed sessions."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from base64 import urlsafe_b64decode, urlsafe_b64encode
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

SESSION_COOKIE = "jem_session"
SESSION_DAYS = 14


@dataclass
class User:
    id: int
    oauth_provider: str
    oauth_sub: str
    display_name: str
    avatar_url: Optional[str]
    profile_url: Optional[str]
    email: Optional[str]
    role: str
    approved_correction_count: int

    @property
    def can_vote(self) -> bool:
        return self.role in ("trusted", "expert", "maintainer")

    @property
    def is_maintainer(self) -> bool:
        return self.role == "maintainer"


def _session_secret() -> bytes:
    secret = os.environ.get("JEM_SESSION_SECRET", "dev-insecure-change-me")
    return secret.encode("utf-8")


def _sign(payload: str) -> str:
    sig = hmac.new(_session_secret(), payload.encode("utf-8"), hashlib.sha256).digest()
    return urlsafe_b64encode(sig).decode("ascii").rstrip("=")


def _encode_session(session_id: str) -> str:
    payload = urlsafe_b64encode(session_id.encode("utf-8")).decode("ascii").rstrip("=")
    return f"{payload}.{_sign(payload)}"


def _decode_session(value: str) -> Optional[str]:
    if not value or "." not in value:
        return None
    payload, sig = value.rsplit(".", 1)
    if not hmac.compare_digest(_sign(payload), sig):
        return None
    pad = "=" * (-len(payload) % 4)
    try:
        return urlsafe_b64decode(payload + pad).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def row_to_user(row: sqlite3.Row) -> User:
    return User(
        id=row["id"],
        oauth_provider=row["oauth_provider"],
        oauth_sub=row["oauth_sub"],
        display_name=row["display_name"],
        avatar_url=row["avatar_url"],
        profile_url=row["profile_url"],
        email=row["email"],
        role=row["role"],
        approved_correction_count=row["approved_correction_count"],
    )


def get_user_by_id(conn: sqlite3.Connection, user_id: int) -> Optional[User]:
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return row_to_user(row) if row else None


def upsert_oauth_user(
    conn: sqlite3.Connection,
    *,
    provider: str,
    sub: str,
    display_name: str,
    avatar_url: Optional[str] = None,
    profile_url: Optional[str] = None,
    email: Optional[str] = None,
) -> User:
    row = conn.execute(
        "SELECT * FROM users WHERE oauth_provider = ? AND oauth_sub = ?",
        (provider, sub),
    ).fetchone()
    now = _iso(_utcnow())
    if row:
        conn.execute(
            """
            UPDATE users
            SET display_name = ?, avatar_url = ?, profile_url = ?, email = ?, last_login_at = ?
            WHERE id = ?
            """,
            (display_name, avatar_url, profile_url, email, now, row["id"]),
        )
        user_id = row["id"]
    else:
        maintainer_subs = {
            s.strip()
            for s in os.environ.get("JEM_MAINTAINER_OAUTH_SUBS", "").split(",")
            if s.strip()
        }
        role = "maintainer" if sub in maintainer_subs else "new"
        cur = conn.execute(
            """
            INSERT INTO users (
                oauth_provider, oauth_sub, display_name, avatar_url, profile_url, email, role, last_login_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (provider, sub, display_name, avatar_url, profile_url, email, role, now),
        )
        user_id = cur.lastrowid
    conn.commit()
    user = get_user_by_id(conn, user_id)
    assert user is not None
    return user


def create_session(conn: sqlite3.Connection, user_id: int) -> str:
    session_id = secrets.token_urlsafe(32)
    expires = _utcnow() + timedelta(days=SESSION_DAYS)
    conn.execute(
        "INSERT INTO sessions (id, user_id, expires_at) VALUES (?, ?, ?)",
        (session_id, user_id, _iso(expires)),
    )
    conn.commit()
    return _encode_session(session_id)


def delete_session(conn: sqlite3.Connection, session_id: str) -> None:
    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()


def get_user_for_session_cookie(conn: sqlite3.Connection, cookie_value: Optional[str]) -> Optional[User]:
    session_id = _decode_session(cookie_value or "")
    if not session_id:
        return None
    row = conn.execute(
        """
        SELECT u.* FROM users u
        JOIN sessions s ON s.user_id = u.id
        WHERE s.id = ? AND s.expires_at > datetime('now')
        """,
        (session_id,),
    ).fetchone()
    return row_to_user(row) if row else None


def promote_if_trusted(conn: sqlite3.Connection, user_id: int) -> None:
    """Auto-promote new → trusted after 3 approved corrections."""
    row = conn.execute("SELECT role, approved_correction_count FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row or row["role"] != "new":
        return
    if row["approved_correction_count"] >= 3:
        conn.execute("UPDATE users SET role = 'trusted' WHERE id = ?", (user_id,))


def audit(
    conn: sqlite3.Connection,
    action: str,
    table_name: str,
    record_id: str,
    actor: str,
    details: dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO audit_log (action, table_name, record_id, actor, details_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (action, table_name, record_id, actor, json.dumps(details)),
    )
