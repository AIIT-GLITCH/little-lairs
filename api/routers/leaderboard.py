"""GET /api/leaderboard — ranked model scores."""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db

router = APIRouter(tags=["leaderboard"])


class LeaderboardEntry(BaseModel):
    rank: int
    model_id: str
    display_name: str
    provider: str
    score: int
    label: str
    fabricated_count: int
    dead_count: int
    total_anchors: int
    run_id: str
    run_count: int
    benchmark_version: str


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    benchmark_version: str = Query(default="latest"),
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db),
):
    # Get best run per model (highest score, most recent as tiebreak)
    q = text("""
        WITH best_runs AS (
            SELECT DISTINCT ON (r.model_id)
                r.run_id, r.model_id, r.benchmark_id,
                rs.score, rs.label::text as label,
                rs.fabricated_count, rs.dead_count, rs.total_anchors,
                b.version as benchmark_version
            FROM runs r
            JOIN run_scores rs ON rs.run_id = r.run_id
            JOIN benchmarks b ON b.benchmark_id = r.benchmark_id
            WHERE r.status = 'completed'
            ORDER BY r.model_id, rs.score DESC, r.finished_at DESC
        ),
        run_counts AS (
            SELECT model_id, COUNT(*) as run_count
            FROM runs WHERE status = 'completed'
            GROUP BY model_id
        )
        SELECT
            br.run_id, br.model_id, m.display_name, m.provider,
            br.score, br.label, br.fabricated_count, br.dead_count,
            br.total_anchors, br.benchmark_version,
            COALESCE(rc.run_count, 1) as run_count
        FROM best_runs br
        JOIN models m ON m.model_id = br.model_id
        LEFT JOIN run_counts rc ON rc.model_id = br.model_id
        ORDER BY br.score DESC, br.fabricated_count ASC, m.model_id
        LIMIT :lim
    """)
    rows = (await db.execute(q, {"lim": limit})).mappings().all()

    return [
        LeaderboardEntry(
            rank=i + 1,
            model_id=r["model_id"],
            display_name=r["display_name"],
            provider=r["provider"],
            score=r["score"],
            label=r["label"],
            fabricated_count=r["fabricated_count"],
            dead_count=r["dead_count"],
            total_anchors=r["total_anchors"],
            run_id=str(r["run_id"]),
            run_count=r["run_count"],
            benchmark_version=r["benchmark_version"],
        )
        for i, r in enumerate(rows)
    ]


@router.get("/leaderboard/summary")
async def get_leaderboard_summary(db: AsyncSession = Depends(get_db)):
    q = text("""
        SELECT
            COUNT(DISTINCT r.model_id) as total_models,
            COALESCE(SUM(rs.fabricated_count), 0) as total_fabrications,
            COALESCE(SUM(rs.dead_count), 0) as total_dead,
            MAX(r.finished_at) as last_run_at,
            COALESCE(MAX(b.version), 'v1.0.0') as benchmark_version
        FROM runs r
        JOIN run_scores rs ON rs.run_id = r.run_id
        JOIN benchmarks b ON b.benchmark_id = r.benchmark_id
        WHERE r.status = 'completed'
    """)
    row = (await db.execute(q)).mappings().first()
    return {
        "total_models": row["total_models"] if row else 0,
        "total_fabrications": row["total_fabrications"] if row else 0,
        "total_dead": row["total_dead"] if row else 0,
        "last_run_at": str(row["last_run_at"]) if row and row["last_run_at"] else None,
        "benchmark_version": row["benchmark_version"] if row else "v1.0.0",
    }
