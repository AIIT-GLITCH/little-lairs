import { api } from "@/lib/api";
import { notFound } from "next/navigation";
import Link from "next/link";
import { labelColor, scoreColor, failureColor, formatDate } from "@/lib/utils";
import type { URLVerification } from "@/types";

interface Props {
  params: Promise<{ run_id: string }>;
}

export default async function RunPage({ params }: Props) {
  const { run_id } = await params;
  let run;
  try {
    run = await api.run(run_id);
  } catch {
    notFound();
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="text-sm text-gray-500 mb-1">
            <Link href="/" className="hover:text-gray-300">← Leaderboard</Link>
            {" / "}
            <Link href={`/models/${run.model_id}`} className="hover:text-gray-300 text-blue-400">
              {run.display_name}
            </Link>
          </div>
          <h1 className="text-2xl font-bold font-mono">{run.display_name}</h1>
          <p className="text-gray-400 text-sm mt-1">
            Run {run.run_id.slice(0, 8)}… · {formatDate(run.started_at)} · {run.benchmark_version}
          </p>
        </div>
        <div className="text-right">
          <div className={`text-4xl font-bold font-mono ${scoreColor(run.score)}`}>{run.score}</div>
          <span className={`inline-block mt-1 px-3 py-1 rounded text-sm font-bold text-white ${labelColor(run.label)}`}>
            {run.label}
          </span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4 text-center">
          <div className="text-2xl font-bold font-mono text-gray-100">{run.total_anchors}</div>
          <div className="text-xs text-gray-500 mt-1">Total Anchors</div>
        </div>
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4 text-center">
          <div className="text-2xl font-bold font-mono text-yellow-400">{run.dead_count}</div>
          <div className="text-xs text-gray-500 mt-1">Dead Links</div>
        </div>
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4 text-center">
          <div className="text-2xl font-bold font-mono text-red-400">{run.fabricated_count}</div>
          <div className="text-xs text-gray-500 mt-1">Fabricated</div>
        </div>
      </div>

      {/* Download artifact */}
      <div>
        <a
          href={api.artifactUrl(run.run_id)}
          download
          className="inline-flex items-center gap-2 px-4 py-2 bg-[#161b22] border border-[#30363d] rounded-lg text-sm hover:border-blue-500 transition-colors"
        >
          ↓ Download Evidence Artifact (.json)
        </a>
        <p className="text-xs text-gray-600 mt-1">Immutable record of all prompts, responses, and URL verifications.</p>
      </div>

      {/* Per-prompt breakdown */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Prompt Results</h2>
        <div className="space-y-4">
          {run.prompts.map((p) => (
            <div key={p.prompt_id} className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
              <div className="text-xs text-gray-500 mb-2 font-mono">Prompt #{p.prompt_id}</div>
              <p className="text-sm text-gray-300 mb-3">{p.prompt_text}</p>

              {p.urls.length > 0 && (
                <div className="space-y-2">
                  <div className="text-xs text-gray-500 uppercase tracking-wider">URLs Cited</div>
                  {p.urls.map((u, i) => (
                    <URLRow key={i} u={u} />
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function URLRow({ u }: { u: URLVerification }) {
  return (
    <div className="flex items-start gap-3 text-xs font-mono bg-[#0d1117] rounded p-2">
      <span className={`font-bold shrink-0 ${failureColor(u.failure_type)}`}>
        {u.failure_type}
      </span>
      <span className="text-gray-400 truncate flex-1">{u.url}</span>
      {u.http_status && <span className="text-gray-600 shrink-0">HTTP {u.http_status}</span>}
      <span className="text-gray-600 shrink-0">T{u.tier}</span>
    </div>
  );
}
