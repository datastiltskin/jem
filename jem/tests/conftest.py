"""Shared pytest fixtures — never use production data/jem.db."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

JEM_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = JEM_ROOT / "tests" / "fixtures"
MINI_GRAPH = FIXTURES / "mini_graph.json"
SCHEMA_SQL = JEM_ROOT / "config" / "schema.sql"
DEFAULT_GRAPH = JEM_ROOT.parent / "graph.json"

sys.path.insert(0, str(JEM_ROOT))
sys.path.insert(0, str(JEM_ROOT / "scripts"))


@pytest.fixture
def mini_graph() -> dict:
    return json.loads(MINI_GRAPH.read_text())


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    """Isolated SQLite path for tests."""
    return tmp_path / "jem_test.db"


@pytest.fixture
def schema_sql_path() -> Path:
    return SCHEMA_SQL


@pytest.fixture
def fixture_db(tmp_db: Path, mini_graph: dict, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Build mini_graph into an isolated DB and point JEM_DB_PATH at it."""
    from build_db import build_db

    graph_path = tmp_db.parent / "mini.json"
    graph_path.write_text(json.dumps(mini_graph))
    build_db(graph_path, tmp_db, force=True)
    monkeypatch.setenv("JEM_DB_PATH", str(tmp_db))
    return tmp_db


@pytest.fixture
def staging_db(tmp_db: Path) -> Path:
    """Empty schema DB for staging pipeline tests."""
    from build_db import apply_schema, connect

    conn = connect(tmp_db)
    apply_schema(conn)
    conn.close()
    return tmp_db


@pytest.fixture
def api_client(fixture_db: Path) -> TestClient:
    from api.main import create_app

    return TestClient(create_app())
