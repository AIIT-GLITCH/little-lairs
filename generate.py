#!/usr/bin/env python3
"""Generate static Little lAIrs site from AnchorForge DB.

Outputs index.html to docs/ for GitHub Pages.
Run after every benchmark, then git push.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime

ANCHORFORGE_DB = Path.home() / "Desktop/APPS/ANCHORFORGE_APP/data/anchorforge.db"
V5_RESULTS_DIR = Path.home() / "AnchorForge/results"
OUTPUT_DIR = Path(__file__).parent / "docs"


def get_db():
    db = sqlite3.connect(str(ANCHORFORGE_DB))
    db.row_factory = sqlite3.Row
    return db


def load_leaderboard():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT r.model_id, r.run_id, r.total_prompts, r.total_latency_ms,
               r.status, r.started_at, r.run_mode,
               COUNT(DISTINCT resp.response_id) as responses,
               COUNT(DISTINCT c.claim_id) as claims,
               COUNT(DISTINCT a.anchor_id) as anchors,
               SUM(CASE WHEN a.is_fabricated = 1 THEN 1 ELSE 0 END) as fabricated,
               SUM(CASE WHEN a.url_status = 'dead' THEN 1 ELSE 0 END) as dead_links,
               SUM(CASE WHEN a.url_status = 'alive' THEN 1 ELSE 0 END) as live_links,
               SUM(CASE WHEN a.source_tier = 1 THEN 1 ELSE 0 END) as tier1,
               SUM(CASE WHEN a.source_tier = 2 THEN 1 ELSE 0 END) as tier2,
               SUM(CASE WHEN a.source_tier = 3 THEN 1 ELSE 0 END) as tier3,
               AVG(resp.latency_ms) as avg_latency,
               SUM(resp.token_count_in) as total_tokens_in,
               SUM(resp.token_count_out) as total_tokens_out
        FROM runs r
        LEFT JOIN responses resp ON resp.run_id = r.run_id
        LEFT JOIN claims c ON c.response_id = resp.response_id
        LEFT JOIN anchors a ON a.claim_id = c.claim_id
        GROUP BY r.run_id
        ORDER BY r.run_id DESC
    """)
    results = []
    for row in cur.fetchall():
        d = dict(row)
        anchors = d["anchors"] or 0
        fabricated = d["fabricated"] or 0
        dead = d["dead_links"] or 0
        live = d["live_links"] or 0
        d["fabrication_rate"] = round(fabricated / anchors * 100, 1) if anchors > 0 else 0
        d["dead_rate"] = round(dead / anchors * 100, 1) if anchors > 0 else 0
        d["live_rate"] = round(live / anchors * 100, 1) if anchors > 0 else 0
        d["anchor_integrity"] = round(live / anchors * 100, 1) if anchors > 0 else 0
        if anchors > 0:
            trust = 100 - (fabricated / anchors * 60) - (dead / anchors * 30)
            d["trust_score"] = round(max(0, min(100, trust)), 1)
        else:
            d["trust_score"] = 0
        parts = d["model_id"].split("/")
        d["model_short"] = parts[-1] if len(parts) > 1 else parts[0]
        d["provider"] = parts[0] if len(parts) > 1 else "unknown"
        results.append(d)
    db.close()
    results.sort(key=lambda x: x["trust_score"], reverse=True)
    return results


def load_fabrications():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT r.model_id, a.url, a.domain, a.url_status, a.http_code,
               c.claim_text, a.checked_at
        FROM anchors a
        JOIN claims c ON c.claim_id = a.claim_id
        JOIN responses resp ON resp.response_id = c.response_id
        JOIN runs r ON r.run_id = resp.run_id
        WHERE a.is_fabricated = 1
        ORDER BY a.checked_at DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    db.close()
    return rows


def load_dead_links():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT r.model_id, a.url, a.domain, a.http_code, a.source_tier,
               c.claim_text
        FROM anchors a
        JOIN claims c ON c.claim_id = a.claim_id
        JOIN responses resp ON resp.response_id = c.response_id
        JOIN runs r ON r.run_id = resp.run_id
        WHERE a.url_status = 'dead'
        ORDER BY r.model_id
    """)
    rows = [dict(r) for r in cur.fetchall()]
    db.close()
    return rows


def load_v5():
    results = []
    if not V5_RESULTS_DIR.exists():
        return results
    for f in V5_RESULTS_DIR.glob("anchorforge_v5_*.json"):
        try:
            data = json.loads(f.read_text())
            model = f.stem.replace("anchorforge_v5_", "").rsplit("_", 2)[0]
            results.append({
                "model": model,
                "aci_score": data.get("aci_percent", 0),
                "hallucinations": data.get("hallucinations", 0),
                "soft_hallucinations": data.get("soft_hallucinations", 0),
                "false_kills": data.get("false_kills", 0),
                "exact_match": round(data.get("exact_match_rate", 0) * 100, 1),
                "total_claims": data.get("total_claims", 0),
            })
        except Exception:
            pass
    return results


def escape(s):
    if not s:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def generate():
    lb = load_leaderboard()
    fab = load_fabrications()
    dead = load_dead_links()
    v5 = load_v5()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Build leaderboard rows
    lb_rows = ""
    for i, m in enumerate(lb, 1):
        trust = m["trust_score"]
        trust_class = "trust-high" if trust >= 80 else "trust-mid" if trust >= 50 else "trust-low"
        fab_count = m["fabricated"] or 0
        dead_count = m["dead_links"] or 0
        live_count = m["live_links"] or 0

        if fab_count > 0:
            fab_badge = f'<span class="badge badge-fab">{fab_count} FABRICATED</span>'
            status_badge = '<span class="badge badge-fab">LIAR</span>'
        else:
            fab_badge = '<span class="badge badge-clean">CLEAN</span>'
            if m["dead_rate"] > 50:
                status_badge = '<span class="badge badge-dead">SLOPPY</span>'
            else:
                status_badge = '<span class="badge badge-clean">OK</span>'

        rank_class = f"rank-{i}" if i <= 3 else ""
        latency = m["avg_latency"] or 0

        lb_rows += f"""<tr>
          <td><span class="badge badge-rank {rank_class}">{i}</span></td>
          <td><span class="model-name">{escape(m['model_short'])}</span><br><span class="provider">{escape(m['provider'])}</span></td>
          <td><div class="trust-bar"><div class="fill {trust_class}" style="width:{trust}%"></div></div> {trust}</td>
          <td>{m['anchors'] or 0}</td>
          <td style="color:var(--green)">{live_count}</td>
          <td style="color:var(--orange)">{dead_count}</td>
          <td>{fab_badge}</td>
          <td>{m['tier1'] or 0}</td>
          <td style="color:var(--text-dim)">{latency:.0f}ms</td>
          <td>{status_badge}</td>
        </tr>\n"""

    # Build shame cards
    shame_html = ""
    for f in fab:
        claim_preview = escape(str(f["claim_text"] or "")[:200])
        shame_html += f"""<div class="shame-card">
          <div class="model">{escape(f['model_id'])}</div>
          <div class="url">{escape(f['url'])}</div>
          <div class="claim">{claim_preview}</div>
          <div style="color:var(--text-dim);font-size:0.75em;margin-top:4px">
            HTTP {f['http_code'] or '???'} | {escape(f['domain'])} | Checked: {f['checked_at'] or 'n/a'}
          </div>
        </div>\n"""

    # Build dead link cards
    dead_html = ""
    for d in dead:
        model_short = d["model_id"].split("/")[-1] if "/" in d["model_id"] else d["model_id"]
        dead_html += f"""<div class="dead-card">
          <span class="model">{escape(model_short)}</span> —
          <span class="url">{escape(d['url'])}</span>
          <span style="color:var(--text-dim)">(HTTP {d['http_code'] or '?'})</span>
        </div>\n"""

    # V5 rows
    v5_rows = ""
    for v in v5:
        hall_badge = f'<span class="badge badge-fab">{v["hallucinations"]}</span>' if v["hallucinations"] > 0 else '<span class="badge badge-clean">0</span>'
        v5_rows += f"""<tr>
          <td class="model-name">{escape(v['model'])}</td>
          <td>{v['aci_score']}%</td>
          <td>{v['total_claims']}</td>
          <td>{v['exact_match']}%</td>
          <td>{hall_badge}</td>
          <td style="color:var(--orange)">{v['false_kills']}</td>
        </tr>\n"""

    # V5 section
    v5_section = ""
    if v5_rows:
        v5_section = f"""<div class="section">
    <h2>Legacy V5 Results</h2>
    <table><thead><tr>
      <th>Model</th><th>ACI Score</th><th>Claims</th><th>Exact Match</th><th>Hallucinations</th><th>False Kills</th>
    </tr></thead><tbody>{v5_rows}</tbody></table>
  </div>"""

    # Shame section
    shame_section = ""
    if shame_html:
        shame_section = f"""<div class="section">
    <h2>Wall of Shame: Fabricated Sources</h2>
    <p style="color:var(--text-dim);margin-bottom:16px">These models invented URLs that don't exist. Not dead links — completely made up.</p>
    {shame_html}
  </div>"""

    # Dead section
    dead_section = ""
    if dead_html:
        dead_section = f"""<div class="section">
    <h2>Dead Link Report ({len(dead)} total)</h2>
    <p style="color:var(--text-dim);margin-bottom:16px">Real domains, wrong URLs. The model tried but pointed to pages that don't exist.</p>
    {dead_html}
  </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Little lAIrs — Who's Lying?</title>
<meta name="description" content="AnchorForge epistemic benchmark dashboard. Which AI models fabricate sources? Which ones cite dead links? Trust scores for every major LLM.">
<meta property="og:title" content="Little lAIrs — Which AI is Lying?">
<meta property="og:description" content="Live trust leaderboard for AI models. Fabrication detection, dead link tracking, source verification. Built by AnchorForge.">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Little lAIrs — Which AI is Lying?">
<meta name="twitter:description" content="Trust scores for every major LLM. Who fabricates? Who cites ghosts? AnchorForge benchmark results.">
<style>
:root {{
  --bg:#0d1117;--surface:#161b22;--surface2:#1c2333;--border:#30363d;
  --text:#e6edf3;--text-dim:#8b949e;--green:#3fb950;--red:#f85149;
  --orange:#d29922;--blue:#58a6ff;--purple:#bc8cff;--pink:#f778ba;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'JetBrains Mono','Fira Code','Cascadia Code',monospace;background:var(--bg);color:var(--text);line-height:1.6}}
.container{{max-width:1400px;margin:0 auto;padding:20px}}
.header{{text-align:center;padding:40px 20px;border-bottom:1px solid var(--border);margin-bottom:30px}}
.header h1{{font-size:3em;letter-spacing:4px;margin-bottom:8px}}
.header h1 .ai{{color:var(--red)}}
.header .subtitle{{color:var(--text-dim);font-size:1em}}
.header .stats{{margin-top:15px;display:flex;justify-content:center;gap:30px;flex-wrap:wrap}}
.stat-box{{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px 24px;text-align:center}}
.stat-box .num{{font-size:2em;font-weight:bold}}
.stat-box .label{{color:var(--text-dim);font-size:0.8em}}
.stat-box.bad .num{{color:var(--red)}}
.stat-box.good .num{{color:var(--green)}}
.stat-box.warn .num{{color:var(--orange)}}
.section{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:24px;margin-bottom:24px}}
.section h2{{font-size:1.4em;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid var(--border)}}
table{{width:100%;border-collapse:collapse;font-size:0.9em}}
th{{text-align:left;padding:10px 12px;background:var(--surface2);color:var(--text-dim);font-weight:600;text-transform:uppercase;font-size:0.75em;letter-spacing:1px;border-bottom:2px solid var(--border)}}
td{{padding:10px 12px;border-bottom:1px solid var(--border)}}
tr:hover{{background:var(--surface2)}}
.model-name{{font-weight:bold;color:var(--blue)}}
.provider{{color:var(--text-dim);font-size:0.8em}}
.trust-bar{{display:inline-block;width:80px;height:8px;background:var(--surface2);border-radius:4px;overflow:hidden;vertical-align:middle;margin-right:8px}}
.trust-bar .fill{{height:100%;border-radius:4px}}
.trust-high{{background:var(--green)}}
.trust-mid{{background:var(--orange)}}
.trust-low{{background:var(--red)}}
.badge{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.75em;font-weight:bold}}
.badge-fab{{background:rgba(248,81,73,0.2);color:var(--red)}}
.badge-dead{{background:rgba(210,153,34,0.2);color:var(--orange)}}
.badge-clean{{background:rgba(63,185,80,0.2);color:var(--green)}}
.badge-rank{{background:rgba(188,140,255,0.2);color:var(--purple)}}
.shame-card{{background:var(--surface2);border:1px solid var(--red);border-left:4px solid var(--red);border-radius:8px;padding:16px;margin-bottom:12px}}
.shame-card .model{{color:var(--red);font-weight:bold;font-size:1.1em}}
.shame-card .url{{color:var(--orange);word-break:break-all;font-size:0.85em}}
.shame-card .claim{{color:var(--text-dim);font-size:0.85em;margin-top:6px}}
.dead-card{{background:var(--surface2);border-left:3px solid var(--orange);border-radius:6px;padding:10px 14px;margin-bottom:8px;font-size:0.85em}}
.dead-card .model{{color:var(--blue);font-weight:bold}}
.dead-card .url{{color:var(--orange);word-break:break-all}}
.rank-1{{color:#ffd700}}.rank-2{{color:#c0c0c0}}.rank-3{{color:#cd7f32}}
.footer{{text-align:center;padding:30px;color:var(--text-dim);font-size:0.8em;border-top:1px solid var(--border);margin-top:30px}}
.footer a{{color:var(--blue);text-decoration:none}}
.methodology{{background:var(--surface2);border-radius:8px;padding:16px;margin-top:12px;font-size:0.85em;color:var(--text-dim)}}
@media(max-width:768px){{.header h1{{font-size:2em}}table{{font-size:0.75em}}td,th{{padding:6px 8px}}.header .stats{{gap:10px}}}}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>Little l<span class="ai">AI</span>rs</h1>
  <div class="subtitle">AnchorForge Epistemic Benchmark Dashboard</div>
  <div class="subtitle" style="margin-top:4px">Who's lying? Who's fabricating? Who's citing ghosts?</div>
  <div class="stats">
    <div class="stat-box good"><div class="num">{len(lb)}</div><div class="label">Models Tested</div></div>
    <div class="stat-box bad"><div class="num">{len(fab)}</div><div class="label">Fabricated Sources</div></div>
    <div class="stat-box warn"><div class="num">{len(dead)}</div><div class="label">Dead Links</div></div>
    <div class="stat-box"><div class="num">{now[:10]}</div><div class="label">Last Updated</div></div>
  </div>
</div>

<div class="section">
  <h2>Trust Leaderboard</h2>
  <table><thead><tr>
    <th>#</th><th>Model</th><th>Trust</th><th>Anchors</th><th>Live</th><th>Dead</th><th>Fabricated</th><th>Tier 1</th><th>Latency</th><th>Status</th>
  </tr></thead><tbody>
  {lb_rows}
  </tbody></table>
  <div class="methodology">
    <strong>How Trust is Scored:</strong> Each model is given claims to evaluate and must cite sources.
    We verify every URL. Fabricated sources (invented URLs) cost 60 points. Dead links (real domain, wrong page) cost 30 points.
    Score = 100 - penalties. Models that fabricate sources are tagged <span class="badge badge-fab">LIAR</span>.
    Models with &gt;50% dead links are tagged <span class="badge badge-dead">SLOPPY</span>.
  </div>
</div>

{shame_section}
{dead_section}
{v5_section}

<div class="footer">
  <p><strong>Little lAIrs</strong> v1.0 | Powered by <a href="https://github.com/AIIT-GLITCH/anchorforge">AnchorForge</a> Epistemic Benchmark</p>
  <p>AIIT Corp | Rhet Wike | Council Hill, Oklahoma</p>
  <p>Generated: {now}</p>
  <p style="margin-top:8px">Every claim. Every source. Every URL. Verified.</p>
</div>

</div>
</body>
</html>"""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "index.html").write_text(html)
    print(f"Generated: {OUTPUT_DIR / 'index.html'}")
    print(f"  Models: {len(lb)}")
    print(f"  Fabrications: {len(fab)}")
    print(f"  Dead links: {len(dead)}")


if __name__ == "__main__":
    generate()
