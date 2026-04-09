"""Tests for core/scorer.py — v1 formula, all label boundaries."""
import pytest
from core.scorer import compute_score, score_from_verifications


class TestComputeScore:
    def test_perfect_score(self):
        r = compute_score(0, 0, 10)
        assert r.score == 100
        assert r.label == "OK"

    def test_one_fabricated_is_liar(self):
        r = compute_score(1, 0, 5)
        assert r.label == "LIAR"
        assert r.score == 40   # 100 - 60

    def test_fabricated_penalty_stacks(self):
        r = compute_score(2, 0, 10)
        assert r.score == 0    # 100 - 120, floor 0
        assert r.label == "LIAR"

    def test_dead_link_penalty(self):
        r = compute_score(0, 1, 10)
        assert r.score == 70   # 100 - 30
        assert r.label == "OK"

    def test_sloppy_threshold(self):
        # dead > 50% of total → SLOPPY (no fabrications)
        r = compute_score(0, 6, 10)
        assert r.label == "SLOPPY"

    def test_dead_exactly_50pct_is_ok(self):
        # dead == 50% is NOT > 50%, so still OK
        r = compute_score(0, 5, 10)
        assert r.label == "OK"

    def test_floor_zero(self):
        r = compute_score(10, 10, 20)
        assert r.score == 0

    def test_liar_beats_sloppy(self):
        # fabricated > 0 → LIAR even if dead > 50%
        r = compute_score(1, 8, 10)
        assert r.label == "LIAR"

    def test_no_anchors_ok(self):
        r = compute_score(0, 0, 0)
        assert r.label == "OK"
        assert r.score == 100


class TestScoreFromVerifications:
    def test_all_supported(self):
        verifs = [{"failure_type": "SUPPORTED"}] * 5
        r = score_from_verifications(verifs)
        assert r.score == 100
        assert r.label == "OK"

    def test_mixed(self):
        verifs = [
            {"failure_type": "FABRICATED_URL"},
            {"failure_type": "DEAD_LINK"},
            {"failure_type": "SUPPORTED"},
        ]
        r = score_from_verifications(verifs)
        assert r.fabricated_count == 1
        assert r.dead_count == 1
        assert r.label == "LIAR"

    def test_all_failure_types_counted(self):
        """All 9 failure types — only FABRICATED_URL and DEAD_LINK affect score."""
        verifs = [
            {"failure_type": "SUPPORTED"},
            {"failure_type": "DEAD_LINK"},
            {"failure_type": "FABRICATED_URL"},
            {"failure_type": "IRRELEVANT_SUPPORT"},
            {"failure_type": "CLAIM_MISMATCH"},
            {"failure_type": "INDETERMINATE"},
            {"failure_type": "FORMAT_CORRUPTION"},
            {"failure_type": "TEMPORAL_MISMATCH"},
            {"failure_type": "REDIRECT_ABUSE"},
        ]
        r = score_from_verifications(verifs)
        assert r.fabricated_count == 1
        assert r.dead_count == 1
        assert r.total_anchors == 9
