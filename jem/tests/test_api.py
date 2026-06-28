"""FastAPI endpoint tests — marker: test_api."""

from __future__ import annotations


def test_health(api_client) -> None:
    resp = api_client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["entity_count"] == 9


def test_get_relationship_by_id(api_client) -> None:
    resp = api_client.get("/api/v1/relationships/rel_aft_to_sc_appellate")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "rel_aft_to_sc_appellate"
    assert body["source"] == "aft"


def test_get_entity(api_client) -> None:
    resp = api_client.get("/api/v1/entities/supreme_court_india")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "supreme_court_india"
    assert body["data_quality"] == "verified"
    assert body["unverified_fields"] == []
    assert "Apex Court" in body["aliases"]
    assert body["derived"]["structural_health_score"] == 0.54


def test_get_entity_not_found(api_client) -> None:
    resp = api_client.get("/api/v1/entities/does_not_exist")
    assert resp.status_code == 404


def test_entity_always_exposes_quality_flags(api_client) -> None:
    resp = api_client.get("/api/v1/entities/aar_income_tax")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data_quality"] == "partial"
    assert len(body["unverified_fields"]) >= 1


def test_search_entities(api_client) -> None:
    resp = api_client.get("/api/v1/entities", params={"q": "Supreme"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    for item in body["items"]:
        assert "data_quality" in item
        assert "unverified_fields" in item


def test_search_filter_cluster(api_client) -> None:
    resp = api_client.get(
        "/api/v1/entities",
        params={"cluster": "tribunals_adr", "limit": 10},
    )
    body = resp.json()
    assert body["total"] >= 1
    assert all(e["cluster"] == "tribunals_adr" for e in body["items"])


def test_search_filter_state(api_client) -> None:
    resp = api_client.get("/api/v1/entities", params={"state": "TN"})
    body = resp.json()
    assert body["total"] >= 1
    assert any(e["id"] == "aft_chennai" for e in body["items"])


def test_list_relationships(api_client) -> None:
    resp = api_client.get("/api/v1/relationships", params={"entity_id": "aft"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    ids = {r["id"] for r in body["items"]}
    assert "rel_aft_to_sc_appellate" in ids


def test_list_relationships_category_filter(api_client) -> None:
    resp = api_client.get(
        "/api/v1/relationships",
        params={"relationship_category": "appointment"},
    )
    body = resp.json()
    assert body["total"] >= 1
    assert all(r["relationship_category"] == "appointment" for r in body["items"])


def test_cluster_summary(api_client) -> None:
    resp = api_client.get("/api/v1/clusters/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert "clusters" in body
    clusters = {c["cluster"]: c for c in body["clusters"]}
    assert "constitutional_courts" in clusters
    assert clusters["constitutional_courts"]["entity_count"] >= 1
    assert "by_data_quality" in clusters["constitutional_courts"]
