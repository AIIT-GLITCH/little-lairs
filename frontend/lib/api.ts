import type { LeaderboardEntry, RunDetail, ModelDetail } from "@/types";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return res.json();
}

export const api = {
  leaderboard: (version = "latest") =>
    apiFetch<LeaderboardEntry[]>(`/api/leaderboard?benchmark_version=${version}`),

  leaderboardSummary: () =>
    apiFetch<{ total_models: number; total_fabrications: number; total_dead: number; last_run_at: string | null; benchmark_version: string }>(
      "/api/leaderboard/summary"
    ),

  run: (runId: string) => apiFetch<RunDetail>(`/api/runs/${runId}`),

  model: (provider: string, model: string) =>
    apiFetch<ModelDetail>(`/api/models/${provider}/${model}`),

  prompts: (version = "latest", category?: string) => {
    const params = new URLSearchParams({ benchmark_version: version });
    if (category) params.set("category", category);
    return apiFetch<unknown[]>(`/api/prompts?${params}`);
  },

  benchmark: (version: string) =>
    apiFetch<unknown>(`/api/benchmarks/${version}`),

  artifactUrl: (runId: string) => `${API}/api/runs/${runId}/artifact`,
};
