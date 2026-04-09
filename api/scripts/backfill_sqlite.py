#!/usr/bin/env python3
"""
scripts/backfill_sqlite.py

Reads the existing AnchorForge SQLite database and writes all runs
into the new Little Lairs v2 PostgreSQL database.

Usage:
    python scripts/backfill_sqlite.py \
        --sqlite /home/buddy_ai/Desktop/APPS/ANCHORFORGE_APP/data/anchorforge.db \
        --postgres postgresql://user:pass@localhost:5432/little_lairs

DO NOT touch the source SQLite database — read-only.
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from uuid import uuid4

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

from core.scorer import score_from_verifications
from core.artifact import build_artifact, artifact_to_json


BENCHMARK_VERSION = "v1.0.0"
BENCHMARK_NOTES = "Initial backfill from AnchorForge SQLite — April 2026"


def connect_sqlite(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def connect_postgres(dsn: str):
    return psycopg2.connect(dsn)


def ensure_benchmark(pg_cur, benchmark_id_cache: dict) -> int:
    if "id" in benchmark_id_cache:
        return benchmark_id_cache["id"]
    pg_cur.execute("""
        INSERT INTO benchmarks (version, prompt_hash, scoring_rules, notes)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (version) DO UPDATE SET notes = EXCLUDED.notes
        RETURNING benchmark_id
    """, (
        BENCHMARK_VERSION,
        "backfill-no-hash",
        json.dumps({"formula": "score=100-fab*60-dead*30,floor=0"}),
        BENCHMARK_NOTES,
    ))
    bid = pg_cur.fetchone()[0]
    benchmark_id_cache["id"] = bid
    return bid


def ensure_model(pg_cur, model_id: str, provider: str, display_name: str):
    pg_cur.execute("""
        INSERT INTO models (model_id, provider, display_name)
        VALUES (%s, %s, %s)
        ON CONFLICT (model_id) DO NOTHING
    """, (model_id, provider, display_name))


def ensure_prompt(pg_cur, benchmark_id: int, prompt_text: str, category: str, prompt_cache: dict) -> int:
    key = (benchmark_id, prompt_text[:100])
    if key in prompt_cache:
        return prompt_cache[key]
    pg_cur.execute("""
        INSERT INTO prompts (benchmark_id, category, text, difficulty)
        VALUES (%s, %s, %s, 1)
        RETURNING prompt_id
    """, (benchmark_id, category or "A", prompt_text))
    pid = pg_cur.fetchone()[0]
    prompt_cache[key] = pid
    return pid


def backfill(sqlite_path: str, postgres_dsn: str):
    sl = connect_sqlite(sqlite_path)
    pg = connect_postgres(postgres_dsn)
    pg_cur = pg.cursor()

    benchmark_cache: dict = {}
    prompt_cache: dict = {}
    runs_migrated = 0
    errors = 0

    try:
        sl_runs = sl.execute("""
            SELECT r.run_id, r.model_id, r.started_at, r.finished_at,
                   r.total_prompts, r.status
            FROM runs r
            WHERE r.status = 'completed'
            ORDER BY r.run_id
        """).fetchall()

        print(f"Found {len(sl_runs)} completed runs in SQLite.")
        bid = ensure_benchmark(pg_cur, benchmark_cache)

        for sl_run in sl_runs:
            try:
                model_id = sl_run["model_id"]
                provider = model_id.split("/")[0] if "/" in model_id else "unknown"
                ensure_model(pg_cur, model_id, provider, model_id)

                new_run_id = str(uuid4())
                started = sl_run["started_at"] or datetime.now(timezone.utc).isoformat()
                finished = sl_run["finished_at"] or started

                pg_cur.execute("""
                    INSERT INTO runs (run_id, benchmark_id, model_id, status, started_at, finished_at, raw_responses)
                    VALUES (%s, %s, %s, 'completed', %s, %s, '[]'::jsonb)
                """, (new_run_id, bid, model_id, started, finished))

                # Pull responses + anchors for this run
                responses = sl.execute("""
                    SELECT resp.response_id, resp.raw_response, p.prompt_text, p.category
                    FROM responses resp
                    LEFT JOIN prompts p ON p.prompt_id = resp.prompt_id
                    WHERE resp.run_id = ?
                """, (sl_run["run_id"],)).fetchall()

                verifications: list[dict] = []
                prompt_details: list[dict] = []

                for resp in responses:
                    pid = ensure_prompt(pg_cur, bid, resp["prompt_text"] or "", resp["category"] or "A", prompt_cache)

                    anchors = sl.execute("""
                        SELECT a.url, a.url_status, a.http_code, a.is_fabricated,
                               a.final_url, a.page_title, a.source_tier
                        FROM anchors a
                        JOIN claims c ON c.claim_id = a.claim_id
                        WHERE c.response_id = ?
                    """, (resp["response_id"],)).fetchall()

                    url_records: list[dict] = []
                    for a in anchors:
                        failure_type = _map_failure_type(a)
                        verifications.append({"failure_type": failure_type})

                        pg_cur.execute("""
                            INSERT INTO extracted_urls (run_id, prompt_id, url)
                            VALUES (%s, %s, %s)
                            RETURNING url_id
                        """, (new_run_id, pid, a["url"]))
                        url_id = pg_cur.fetchone()[0]

                        pg_cur.execute("""
                            INSERT INTO url_verifications
                                (url_id, http_status, final_url, failure_type, page_title, confidence)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (url_id, a["http_code"], a["final_url"], failure_type,
                              a["page_title"], 0.9))

                        url_records.append({
                            "url": a["url"],
                            "failure_type": failure_type,
                            "http_status": a["http_code"],
                            "tier": a["source_tier"] or 3,
                        })

                    prompt_details.append({
                        "prompt_id": pid,
                        "prompt_text": resp["prompt_text"] or "",
                        "raw_response": resp["raw_response"] or "",
                        "urls": url_records,
                    })

                # Score
                sr = score_from_verifications(verifications)
                pg_cur.execute("""
                    INSERT INTO run_scores
                        (run_id, score, fabricated_count, dead_count, total_anchors, label, breakdown)
                    VALUES (%s, %s, %s, %s, %s, %s, '{}'::jsonb)
                """, (new_run_id, sr.score, sr.fabricated_count, sr.dead_count, sr.total_anchors, sr.label))

                pg.commit()
                runs_migrated += 1
                print(f"  [{runs_migrated}] {model_id} → run {new_run_id[:8]}... score={sr.score} {sr.label}")

            except Exception as e:
                pg.rollback()
                errors += 1
                print(f"  [ERROR] run {sl_run['run_id']}: {e}")

    finally:
        sl.close()
        pg_cur.close()
        pg.close()

    print(f"\nDone. {runs_migrated} runs migrated, {errors} errors.")


def _map_failure_type(anchor) -> str:
    """Map AnchorForge sqlite anchor status to new failure taxonomy."""
    if anchor["is_fabricated"]:
        return "FABRICATED_URL"
    status = (anchor["url_status"] or "").lower()
    if status == "dead":
        return "DEAD_LINK"
    if status == "alive":
        return "SUPPORTED"
    if status == "blocked":
        return "INDETERMINATE"
    return "INDETERMINATE"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill AnchorForge SQLite → Little Lairs v2 PostgreSQL")
    parser.add_argument("--sqlite", required=True, help="Path to anchorforge.db")
    parser.add_argument("--postgres", required=True, help="PostgreSQL DSN")
    args = parser.parse_args()
    backfill(args.sqlite, args.postgres)
