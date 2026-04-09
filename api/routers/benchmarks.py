"""Benchmark routes: GET /api/benchmarks/{version}"""
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["benchmarks"])


@router.get("/benchmarks/{version}")
async def get_benchmark(version: str):
    """Benchmark snapshot: prompts, scoring rules, leaderboard for that version."""
    # TODO: DB query benchmarks + prompts + run_scores for this version
    raise HTTPException(status_code=404, detail=f"Benchmark version {version} not found")


@router.get("/benchmarks")
async def list_benchmarks():
    """All benchmark versions."""
    return []
