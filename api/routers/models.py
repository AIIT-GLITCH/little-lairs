"""Model routes: GET /api/models/{provider}/{model}"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db

router = APIRouter(tags=["models"])


@router.get("/models/{provider}/{model}")
async def get_model(provider: str, model: str, db: AsyncSession = Depends(get_db)):
    model_id = f"{provider}/{model}"
    q = text("""
        SELECT m.model_id, m.display_name, m.provider,
               COUNT(r.run_id) as run_count,
               MAX(rs.score) as best_score,
               AVG(rs.score)::int as avg_score,
               SUM(rs.fabricated_count) as total_fabricated,
               SUM(rs.dead_count) as total_dead,
               SUM(rs.total_anchors) as total_anchors
        FROM models m
        JOIN runs r ON r.model_id = m.model_id
        JOIN run_scores rs ON rs.run_id = r.run_id
        WHERE m.model_id = :mid AND r.status = 'completed'
        GROUP BY m.model_id, m.display_name, m.provider
    """)
    row = (await db.execute(q, {"mid": model_id})).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    # Get all runs for this model
    runs_q = text("""
        SELECT r.run_id, rs.score, rs.label::text as label,
               rs.fabricated_count, rs.dead_count, rs.total_anchors,
               r.finished_at, b.version as benchmark_version
        FROM runs r
        JOIN run_scores rs ON rs.run_id = r.run_id
        JOIN benchmarks b ON b.benchmark_id = r.benchmark_id
        WHERE r.model_id = :mid AND r.status = 'completed'
        ORDER BY r.finished_at DESC
    """)
    runs = [dict(r) | {"run_id": str(r["run_id"]), "finished_at": str(r["finished_at"]) if r["finished_at"] else None}
            for r in (await db.execute(runs_q, {"mid": model_id})).mappings().all()]

    return {
        "model_id": row["model_id"],
        "display_name": row["display_name"],
        "provider": row["provider"],
        "run_count": row["run_count"],
        "best_score": row["best_score"],
        "avg_score": row["avg_score"],
        "total_fabricated": row["total_fabricated"],
        "total_dead": row["total_dead"],
        "total_anchors": row["total_anchors"],
        "runs": runs,
    }


@router.get("/models")
async def list_models(db: AsyncSession = Depends(get_db)):
    q = text("""
        SELECT m.model_id, m.display_name, m.provider,
               COUNT(r.run_id) as run_count,
               MAX(rs.score) as best_score
        FROM models m
        LEFT JOIN runs r ON r.model_id = m.model_id AND r.status = 'completed'
        LEFT JOIN run_scores rs ON rs.run_id = r.run_id
        GROUP BY m.model_id, m.display_name, m.provider
        ORDER BY best_score DESC NULLS LAST
    """)
    rows = (await db.execute(q)).mappings().all()
    return [dict(r) for r in rows]
