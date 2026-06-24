"""Cluster aggregate summary endpoint."""

from __future__ import annotations

import json
import sqlite3

from fastapi import APIRouter, Depends

from api.deps import get_db

router = APIRouter(prefix="/clusters", tags=["clusters"])


@router.get("/summary")
def cluster_summary(conn: sqlite3.Connection = Depends(get_db)) -> dict:
    rows = conn.execute(
        """
        SELECT cluster, data_quality, operational_status, entity_json
        FROM entities
        ORDER BY cluster
        """
    ).fetchall()

    clusters: dict[str, dict] = {}
    for row in rows:
        cluster = row["cluster"]
        if cluster not in clusters:
            clusters[cluster] = {
                "cluster": cluster,
                "entity_count": 0,
                "by_data_quality": {},
                "by_operational_status": {},
                "structural_health_scores": [],
            }
        entry = clusters[cluster]
        entry["entity_count"] += 1

        dq = row["data_quality"]
        entry["by_data_quality"][dq] = entry["by_data_quality"].get(dq, 0) + 1

        status = row["operational_status"]
        entry["by_operational_status"][status] = (
            entry["by_operational_status"].get(status, 0) + 1
        )

        blob = json.loads(row["entity_json"] or "{}")
        derived = blob.get("derived") or {}
        score = derived.get("structural_health_score")
        if isinstance(score, (int, float)):
            entry["structural_health_scores"].append(float(score))

    result = []
    for entry in clusters.values():
        scores = entry.pop("structural_health_scores")
        entry["avg_structural_health"] = (
            round(sum(scores) / len(scores), 4) if scores else None
        )
        result.append(entry)

    result.sort(key=lambda x: x["cluster"])
    return {"clusters": result}
