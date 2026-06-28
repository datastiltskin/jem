"""MCP tool tests — marker: test_mcp."""

from __future__ import annotations

import json

from mcp.refusal import is_refused_query
from mcp.server import call_tool, list_tools


def test_list_tools() -> None:
    tools = list_tools()
    names = {t["name"] for t in tools}
    assert names == {
        "get_entity",
        "search_entities",
        "get_relationships",
        "get_structural_gaps",
    }


def test_get_entity(fixture_db) -> None:
    result = call_tool("get_entity", {"entity_id": "supreme_court_india"})
    assert result["id"] == "supreme_court_india"
    assert result["data_quality"] == "verified"
    assert "unverified_fields" in result


def test_get_entity_not_found(fixture_db) -> None:
    result = call_tool("get_entity", {"entity_id": "missing"})
    assert result["error"] == "not_found"


def test_search_entities(fixture_db) -> None:
    result = call_tool("search_entities", {"q": "Armed Forces", "limit": 5})
    assert result["total"] >= 1
    for item in result["items"]:
        assert "data_quality" in item
        assert "unverified_fields" in item


def test_get_relationships(fixture_db) -> None:
    result = call_tool("get_relationships", {"entity_id": "aft"})
    assert result["total"] >= 1
    assert any(r["id"] == "rel_aft_to_sc_appellate" for r in result["items"])


def test_get_structural_gaps(fixture_db) -> None:
    result = call_tool("get_structural_gaps", {"entity_id": "aft"})
    assert result["count"] >= 1
    assert result["gaps"][0]["entity_id"] == "aft"
    assert len(result["gaps"][0]["gaps"]) >= 1


def test_refusal_legal_advice(fixture_db) -> None:
    result = call_tool("search_entities", {"q": "legal advice on my case outcome"})
    assert result.get("refused") is True


def test_mcp_http_tools(api_client) -> None:
    resp = api_client.get("/mcp/tools")
    assert resp.status_code == 200
    assert len(resp.json()["tools"]) == 4

    resp = api_client.post(
        "/mcp/tools/get_entity",
        json={"arguments": {"entity_id": "aft"}},
    )
    assert resp.status_code == 200
    payload = json.loads(resp.json()["content"][0]["text"])
    assert payload["id"] == "aft"


def test_refusal_detector() -> None:
    assert is_refused_query("should I sue the government")
    assert not is_refused_query("Armed Forces Tribunal")
