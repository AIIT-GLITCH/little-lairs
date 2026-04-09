"""
core/artifact.py — Serialize a completed run into an immutable JSON artifact.
This is the downloadable evidence record for each run.
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any


def build_artifact(
    run_id: str,
    model_id: str,
    benchmark_version: str,
    executed_at: datetime,
    score_result: dict,
    prompts: list[dict],
) -> dict[str, Any]:
    """
    Build an immutable run artifact.

    prompts: list of {
        prompt_id, prompt_text, raw_response,
        urls: [{url, failure_type, http_status, confidence, page_title, tier}]
    }
    """
    return {
        "schema_version": "2.0.0",
        "run_id": run_id,
        "model_id": model_id,
        "benchmark_version": benchmark_version,
        "executed_at": executed_at.astimezone(timezone.utc).isoformat(),
        "score": score_result["score"],
        "label": score_result["label"],
        "fabricated_count": score_result["fabricated_count"],
        "dead_count": score_result["dead_count"],
        "total_anchors": score_result["total_anchors"],
        "prompts": [
            {
                "prompt_id": p["prompt_id"],
                "prompt_text": p["prompt_text"],
                "raw_response": p["raw_response"],
                "urls": [
                    {
                        "url": u["url"],
                        "failure_type": u["failure_type"],
                        "http_status": u.get("http_status"),
                        "final_url": u.get("final_url"),
                        "confidence": u.get("confidence", 1.0),
                        "page_title": u.get("page_title"),
                        "tier": u.get("tier", 3),
                    }
                    for u in p.get("urls", [])
                ],
            }
            for p in prompts
        ],
    }


def artifact_to_json(artifact: dict) -> str:
    return json.dumps(artifact, indent=2, ensure_ascii=False)


def artifact_filename(run_id: str, model_id: str) -> str:
    safe_model = model_id.replace("/", "_").replace(" ", "-")
    return f"run_{run_id[:8]}_{safe_model}.json"
