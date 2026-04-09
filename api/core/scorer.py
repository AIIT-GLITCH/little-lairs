"""
core/scorer.py — Scoring engine v1.
Matches the public logic on littlelairs (fabricated×60, dead×30, floor 0).
Labels: LIAR > SLOPPY > OK.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ScoreResult:
    score: int                  # 0–100
    label: str                  # LIAR | SLOPPY | OK
    fabricated_count: int
    dead_count: int
    total_anchors: int
    breakdown: dict             # per-prompt detail


def compute_score(
    fabricated_count: int,
    dead_count: int,
    total_anchors: int,
    breakdown: dict | None = None,
) -> ScoreResult:
    """
    v1 formula — must stay in sync with generate.py in the legacy system.

    Score = 100 - (fabricated × 60) - (dead × 30), floor 0.
    Label:
      LIAR   — any fabricated URL
      SLOPPY — dead > 50% of total anchors (and no fabrications)
      OK     — otherwise
    """
    score = 100
    score -= fabricated_count * 60
    score -= dead_count * 30
    score = max(0, score)

    if fabricated_count > 0:
        label = "LIAR"
    elif total_anchors > 0 and dead_count / total_anchors > 0.50:
        label = "SLOPPY"
    else:
        label = "OK"

    return ScoreResult(
        score=score,
        label=label,
        fabricated_count=fabricated_count,
        dead_count=dead_count,
        total_anchors=total_anchors,
        breakdown=breakdown or {},
    )


def score_from_verifications(verifications: list[dict]) -> ScoreResult:
    """
    Convenience: accepts a list of dicts with 'failure_type' keys
    (as stored in url_verifications rows) and computes the score.
    """
    fabricated = sum(1 for v in verifications if v["failure_type"] == "FABRICATED_URL")
    dead = sum(1 for v in verifications if v["failure_type"] == "DEAD_LINK")
    total = len(verifications)
    return compute_score(fabricated, dead, total)
