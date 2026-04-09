"""Prompt routes: GET /api/prompts"""
from fastapi import APIRouter, Query

router = APIRouter(tags=["prompts"])


@router.get("/prompts")
async def list_prompts(
    benchmark_version: str = Query(default="latest"),
    category: str | None = Query(default=None),
):
    """Browse prompts by benchmark version and category."""
    return []
