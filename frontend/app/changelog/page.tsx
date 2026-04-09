const entries = [
  {
    version: "v2.0.0",
    date: "2026-04-09",
    label: "Current",
    changes: [
      "Full production rebuild: Next.js 15 + FastAPI + PostgreSQL + Celery",
      "Immutable run records with UUID primary keys",
      "Per-run downloadable JSON artifacts",
      "Drill-down model detail pages and run detail pages with per-URL evidence",
      "9-type failure taxonomy (SUPPORTED, DEAD_LINK, FABRICATED_URL, IRRELEVANT_SUPPORT, CLAIM_MISMATCH, INDETERMINATE, FORMAT_CORRUPTION, TEMPORAL_MISMATCH, REDIRECT_ABUSE)",
      "Source tier classification (Tier 1/2/3) displayed in run detail",
      "Scoring engine v1 unchanged — backward compatible with all published results",
      "Backfill script to migrate AnchorForge SQLite → PostgreSQL",
    ],
  },
  {
    version: "v1.x (Little Lairs legacy)",
    date: "2026-04-05",
    label: "Legacy",
    changes: [
      "Flask + SQLite + static GitHub Pages generator",
      "37 models tested, 9 fabrications, 229 dead links",
      "Scoring formula: Trust Score = 100 − (fabricated × 60) − (dead × 30)",
      "LIAR / SLOPPY / OK labels introduced",
      "Source live at https://aiit-glitch.github.io/little-lairs",
    ],
  },
];

export default function ChangelogPage() {
  return (
    <div className="max-w-3xl space-y-10">
      <div>
        <h1 className="text-3xl font-bold font-mono mb-2">Changelog</h1>
        <p className="text-gray-400">Version history and scoring changes.</p>
      </div>

      <div className="space-y-8">
        {entries.map((e) => (
          <div key={e.version} className="border-l-2 border-[#30363d] pl-6 space-y-3">
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-bold font-mono">{e.version}</h2>
              <span className="text-xs text-gray-500">{e.date}</span>
              {e.label === "Current" && (
                <span className="px-2 py-0.5 bg-green-500 text-white text-xs rounded font-bold">Current</span>
              )}
              {e.label === "Legacy" && (
                <span className="px-2 py-0.5 bg-gray-600 text-white text-xs rounded font-bold">Legacy</span>
              )}
            </div>
            <ul className="space-y-1">
              {e.changes.map((c) => (
                <li key={c} className="text-sm text-gray-400 flex gap-2">
                  <span className="text-gray-600 shrink-0">·</span>
                  {c}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4 text-sm text-gray-400">
        <strong className="text-gray-200">Scoring stability policy:</strong> Once a scoring formula version is published,
        it will not be changed retroactively. New formula versions (v2, v3, etc.) will be applied to new benchmark
        snapshots only. All published run scores are permanent.
      </div>
    </div>
  );
}
