"""
Little Lairs v2 — FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import leaderboard, runs, models, prompts, benchmarks

app = FastAPI(
    title="Little Lairs v2",
    description="Citation Forensics Benchmark API",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten for prod: set to Vercel domain
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leaderboard.router, prefix="/api")
app.include_router(runs.router, prefix="/api")
app.include_router(models.router, prefix="/api")
app.include_router(prompts.router, prefix="/api")
app.include_router(benchmarks.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
