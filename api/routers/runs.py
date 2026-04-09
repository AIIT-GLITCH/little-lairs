"""Run routes: GET /api/runs/{run_id}, artifact download, job submission."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db

router = APIRouter(tags=["runs"])


@router.get("/runs/{run_id}")
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    q = text("""
        SELECT r.run_id, r.model_id, r.status::text, r.started_at, r.finished_at,
               rs.score, rs.label::text as label, rs.fabricated_count, rs.dead_count, rs.total_anchors,
               m.display_name, m.provider, b.version as benchmark_version
        FROM runs r
        JOIN run_scores rs ON rs.run_id = r.run_id
        JOIN models m ON m.model_id = r.model_id
        JOIN benchmarks b ON b.benchmark_id = r.benchmark_id
        WHERE r.run_id = :rid
    """)
    row = (await db.execute(q, {"rid": run_id})).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    # Get URLs for this run
    urls_q = text("""
        SELECT eu.url, eu.prompt_id, p.category, p.text as prompt_text,
               uv.http_status, uv.failure_type::text as failure_type, uv.page_title
        FROM extracted_urls eu
        JOIN url_verifications uv ON uv.url_id = eu.url_id
        JOIN prompts p ON p.prompt_id = eu.prompt_id
        WHERE eu.run_id = :rid
        ORDER BY eu.prompt_id, eu.url_id
    """)
    urls = [dict(r) for r in (await db.execute(urls_q, {"rid": run_id})).mappings().all()]

    return {
        "run_id": str(row["run_id"]),
        "model_id": row["model_id"],
        "display_name": row["display_name"],
        "provider": row["provider"],
        "status": row["status"],
        "score": row["score"],
        "label": row["label"],
        "fabricated_count": row["fabricated_count"],
        "dead_count": row["dead_count"],
        "total_anchors": row["total_anchors"],
        "benchmark_version": row["benchmark_version"],
        "started_at": str(row["started_at"]) if row["started_at"] else None,
        "finished_at": str(row["finished_at"]) if row["finished_at"] else None,
        "urls": urls,
    }


@router.get("/runs/{run_id}/artifact")
async def download_artifact(run_id: str):
    raise HTTPException(status_code=404, detail=f"Artifact not yet implemented")


@router.post("/runs")
async def submit_run(body: dict):
    return {"job_id": "not-implemented-yet", "status": "queued"}


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    return {"job_id": job_id, "status": "unknown"}
