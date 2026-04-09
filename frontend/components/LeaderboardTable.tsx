"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import type { LeaderboardEntry } from "@/types";
import { labelColor, scoreColor, shortModelId } from "@/lib/utils";

interface Props {
  data: LeaderboardEntry[];
}

type SortKey = "rank" | "score" | "fabricated_count" | "dead_count" | "total_anchors";

export function LeaderboardTable({ data }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("rank");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [filter, setFilter] = useState("");

  const sorted = useMemo(() => {
    const filtered = data.filter((r) =>
      r.model_id.toLowerCase().includes(filter.toLowerCase()) ||
      r.display_name.toLowerCase().includes(filter.toLowerCase())
    );
    return filtered.sort((a, b) => {
      const av = a[sortKey] as number;
      const bv = b[sortKey] as number;
      return sortDir === "asc" ? av - bv : bv - av;
    });
  }, [data, sortKey, sortDir, filter]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(key === "score" ? "desc" : "asc");
    }
  };

  const Col = ({ k, label }: { k: SortKey; label: string }) => (
    <th
      className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider cursor-pointer hover:text-gray-200 select-none"
      onClick={() => toggleSort(k)}
    >
      {label} {sortKey === k ? (sortDir === "asc" ? "↑" : "↓") : ""}
    </th>
  );

  return (
    <div className="space-y-4">
      <input
        type="text"
        placeholder="Filter models..."
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        className="w-full max-w-sm px-3 py-2 bg-[#161b22] border border-[#30363d] rounded-md text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500"
      />

      <div className="overflow-x-auto rounded-lg border border-[#30363d]">
        <table className="w-full text-sm">
          <thead className="bg-[#161b22]">
            <tr>
              <Col k="rank" label="#" />
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Model</th>
              <Col k="score" label="Trust Score" />
              <Col k="total_anchors" label="Anchors" />
              <Col k="dead_count" label="Dead" />
              <Col k="fabricated_count" label="Fabricated" />
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Label</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Run</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#21262d]">
            {sorted.map((row) => {
              const [provider, ...rest] = row.model_id.split("/");
              const modelSlug = rest.join("/");
              return (
                <tr key={row.run_id} className="hover:bg-[#161b22] transition-colors">
                  <td className="px-4 py-3 font-mono text-gray-400">
                    {row.rank <= 3 ? (
                      <span className={row.rank === 1 ? "text-yellow-400" : row.rank === 2 ? "text-gray-300" : "text-amber-600"}>
                        {row.rank}
                      </span>
                    ) : row.rank}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/models/${row.model_id}`}
                      className="text-blue-400 hover:text-blue-300 font-mono"
                    >
                      {shortModelId(row.model_id)}
                    </Link>
                    <div className="text-xs text-gray-500">{row.provider}</div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="trust-bar-track w-16">
                        <div
                          className={`trust-bar-fill ${row.score >= 80 ? "bg-green-500" : row.score >= 50 ? "bg-yellow-500" : "bg-red-500"}`}
                          style={{ width: `${row.score}%` }}
                        />
                      </div>
                      <span className={`font-mono font-bold ${scoreColor(row.score)}`}>{row.score}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 font-mono text-gray-300">{row.total_anchors}</td>
                  <td className="px-4 py-3 font-mono text-yellow-400">{row.dead_count}</td>
                  <td className="px-4 py-3 font-mono text-red-400">{row.fabricated_count}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold text-white ${labelColor(row.label)}`}>
                      {row.label}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/runs/${row.run_id}`}
                      className="text-xs text-gray-500 hover:text-gray-300 font-mono"
                    >
                      {row.run_id.slice(0, 8)}…
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-gray-600">{sorted.length} models shown</p>
    </div>
  );
}
