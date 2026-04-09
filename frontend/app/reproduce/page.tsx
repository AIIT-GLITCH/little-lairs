export default function ReproducePage() {
  return (
    <div className="max-w-3xl space-y-10">
      <div>
        <h1 className="text-3xl font-bold font-mono mb-2">Reproduce</h1>
        <p className="text-gray-400">Run the benchmark yourself. All prompts and scoring are open.</p>
      </div>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Requirements</h2>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-300">
          <li>Python 3.11+</li>
          <li>PostgreSQL 15+ (or Docker)</li>
          <li>Redis (for job queue)</li>
          <li>API keys: OpenAI / Anthropic / Google / xAI (whichever models you want to test)</li>
        </ul>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Quick Start (Docker)</h2>
        <pre className="bg-[#161b22] border border-[#30363d] rounded-lg p-4 text-xs font-mono text-gray-300 overflow-x-auto">
{`git clone https://github.com/AIIT-GLITCH/little-lairs
cd little-lairs/api

# Start Postgres + Redis + API + Worker
docker-compose -f ../infra/docker-compose.yml up -d

# Install dependencies
pip install -e ".[dev]"

# Submit a benchmark run via API
curl -X POST http://localhost:8000/api/runs \\
  -H "Content-Type: application/json" \\
  -d '{
    "model_id": "openai/gpt-4o",
    "benchmark_version": "v1.0.0",
    "temperature": 0.0
  }'

# Poll job status
curl http://localhost:8000/api/jobs/{job_id}`}
        </pre>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Backfill Existing AnchorForge Data</h2>
        <pre className="bg-[#161b22] border border-[#30363d] rounded-lg p-4 text-xs font-mono text-gray-300 overflow-x-auto">
{`python api/scripts/backfill_sqlite.py \\
  --sqlite /path/to/anchorforge.db \\
  --postgres postgresql://llair:llair_dev@localhost:5432/little_lairs`}
        </pre>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Scoring Formula</h2>
        <p className="text-sm text-gray-400">
          The v1 formula is public and simple. See{" "}
          <a href="/methodology" className="text-blue-400 hover:text-blue-300">Methodology</a> for the full derivation.
          The formula in <code className="font-mono bg-[#161b22] px-1 rounded">api/core/scorer.py</code> is the canonical implementation.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Download Benchmark Prompts</h2>
        <p className="text-sm text-gray-400">
          All prompts for a benchmark version are available via the API:
        </p>
        <pre className="bg-[#161b22] border border-[#30363d] rounded-lg p-4 text-xs font-mono text-gray-300">
{`GET /api/prompts?benchmark_version=v1.0.0`}
        </pre>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Run Artifacts</h2>
        <p className="text-sm text-gray-400">
          Every completed run has a downloadable JSON artifact — the immutable evidence record including every prompt,
          raw model response, extracted URL, and verification result.
        </p>
        <pre className="bg-[#161b22] border border-[#30363d] rounded-lg p-4 text-xs font-mono text-gray-300">
{`GET /api/runs/{run_id}/artifact`}
        </pre>
      </section>
    </div>
  );
}
