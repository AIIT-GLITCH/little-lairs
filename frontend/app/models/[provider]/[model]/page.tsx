import { api } from "@/lib/api";
import { notFound } from "next/navigation";
import Link from "next/link";
import { labelColor, scoreColor, formatDate } from "@/lib/utils";

interface Props {
  params: Promise<{ provider: string; model: string }>;
}

export default async function ModelPage({ params }: Props) {
  const { provider, model } = await params;
  let m;
  try {
    m = await api.model(provider, model);
  } catch {
    notFound();
  }

  return (
    <div className="space-y-8">
      <div>
        <div className="text-sm text-gray-500 mb-1">
          <Link href="/" className="hover:text-gray-300">← Leaderboard</Link>
        </div>
        <h1 className="text-2xl font-bold font-mono">{m.display_name}</h1>
        <p className="text-gray-400 text-sm">{m.model_id} · {m.provider}</p>
      </div>

      {/* Aggregate stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Best Score", value: m.best_score, color: scoreColor(m.best_score) },
          { label: "Avg Score", value: m.avg_score, color: "text-gray-200" },
          { label: "Total Runs", value: m.run_count, color: "text-blue-400" },
          { label: "Fabrications", value: m.total_fabrications, color: "text-red-400" },
        ].map((s) => (
          <div key={s.label} className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
            <div className={`text-2xl font-bold font-mono ${s.color}`}>{s.value}</div>
            <div className="text-xs text-gray-500 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Run history */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Run History</h2>
        <div className="overflow-x-auto rounded-lg border border-[#30363d]">
          <table className="w-full text-sm">
            <thead className="bg-[#161b22]">
              <tr>
                {["Run", "Date", "Score", "Fabricated", "Dead", "Anchors", "Label", ""].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#21262d]">
              {m.runs.map((r) => (
                <tr key={r.run_id} className="hover:bg-[#161b22] transition-colors">
                  <td className="px-4 py-3 font-mono text-gray-400 text-xs">{r.run_id.slice(0, 8)}…</td>
                  <td className="px-4 py-3 text-gray-400">{formatDate(r.started_at)}</td>
                  <td className={`px-4 py-3 font-bold font-mono ${scoreColor(r.score)}`}>{r.score}</td>
                  <td className="px-4 py-3 font-mono text-red-400">{r.fabricated_count}</td>
                  <td className="px-4 py-3 font-mono text-yellow-400">{r.dead_count}</td>
                  <td className="px-4 py-3 font-mono text-gray-300">{r.total_anchors}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold text-white ${labelColor(r.label)}`}>
                      {r.label}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <Link href={`/runs/${r.run_id}`} className="text-xs text-blue-400 hover:text-blue-300">
                      Details →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
