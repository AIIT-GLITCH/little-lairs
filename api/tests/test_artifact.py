"""Tests for core/artifact.py — round-trip serialize/deserialize."""
import json
from datetime import datetime, timezone
import pytest
from core.artifact import build_artifact, artifact_to_json, artifact_filename


SAMPLE_SCORE = {
    "score": 40,
    "label": "LIAR",
    "fabricated_count": 1,
    "dead_count": 2,
    "total_anchors": 5,
}

SAMPLE_PROMPTS = [
    {
        "prompt_id": 1,
        "prompt_text": "What is the capital of France?",
        "raw_response": "Paris. See https://example.com",
        "urls": [
            {
                "url": "https://example.com",
                "failure_type": "FABRICATED_URL",
                "http_status": None,
                "confidence": 0.9,
                "page_title": None,
                "tier": 3,
            }
        ],
    }
]


class TestBuildArtifact:
    def test_required_fields_present(self):
        art = build_artifact(
            run_id="abc123",
            model_id="openai/gpt-4o",
            benchmark_version="v1.0.0",
            executed_at=datetime(2026, 4, 9, tzinfo=timezone.utc),
            score_result=SAMPLE_SCORE,
            prompts=SAMPLE_PROMPTS,
        )
        assert art["run_id"] == "abc123"
        assert art["model_id"] == "openai/gpt-4o"
        assert art["benchmark_version"] == "v1.0.0"
        assert art["score"] == 40
        assert art["label"] == "LIAR"
        assert art["schema_version"] == "2.0.0"

    def test_prompts_serialized(self):
        art = build_artifact("x", "m", "v1", datetime.now(timezone.utc), SAMPLE_SCORE, SAMPLE_PROMPTS)
        assert len(art["prompts"]) == 1
        assert art["prompts"][0]["prompt_id"] == 1
        assert len(art["prompts"][0]["urls"]) == 1
        assert art["prompts"][0]["urls"][0]["failure_type"] == "FABRICATED_URL"

    def test_json_round_trip(self):
        art = build_artifact("x", "m", "v1", datetime.now(timezone.utc), SAMPLE_SCORE, SAMPLE_PROMPTS)
        json_str = artifact_to_json(art)
        reloaded = json.loads(json_str)
        assert reloaded["run_id"] == "x"
        assert reloaded["prompts"][0]["urls"][0]["tier"] == 3

    def test_utc_timestamp(self):
        art = build_artifact("x", "m", "v1", datetime(2026, 4, 9, 12, 0, tzinfo=timezone.utc), SAMPLE_SCORE, [])
        assert "2026-04-09" in art["executed_at"]
        assert "Z" in art["executed_at"] or "+00:00" in art["executed_at"]

    def test_filename_safe(self):
        name = artifact_filename("abc-123-def", "openai/gpt-4o")
        assert "/" not in name
        assert name.endswith(".json")
        assert "gpt-4o" in name or "gpt_4o" in name

    def test_empty_prompts(self):
        art = build_artifact("x", "m", "v1", datetime.now(timezone.utc), SAMPLE_SCORE, [])
        assert art["prompts"] == []
        assert art_to_json_valid(art)


def art_to_json_valid(art: dict) -> bool:
    try:
        json.dumps(art)
        return True
    except Exception:
        return False
