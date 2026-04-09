export type FailureType =
  | "SUPPORTED"
  | "DEAD_LINK"
  | "FABRICATED_URL"
  | "IRRELEVANT_SUPPORT"
  | "CLAIM_MISMATCH"
  | "INDETERMINATE"
  | "FORMAT_CORRUPTION"
  | "TEMPORAL_MISMATCH"
  | "REDIRECT_ABUSE";

export type RunLabel = "LIAR" | "SLOPPY" | "OK";

export interface LeaderboardEntry {
  rank: number;
  model_id: string;
  display_name: string;
  provider: string;
  score: number;
  label: RunLabel;
  fabricated_count: number;
  dead_count: number;
  total_anchors: number;
  run_id: string;
  run_count: number;
  benchmark_version: string;
}

export interface URLVerification {
  url: string;
  failure_type: FailureType;
  http_status: number | null;
  final_url: string | null;
  page_title: string | null;
  confidence: number;
  tier: 1 | 2 | 3;
}

export interface PromptResult {
  prompt_id: number;
  prompt_text: string;
  raw_response: string;
  urls: URLVerification[];
}

export interface RunDetail {
  run_id: string;
  model_id: string;
  display_name: string;
  benchmark_version: string;
  started_at: string;
  finished_at: string;
  score: number;
  label: RunLabel;
  fabricated_count: number;
  dead_count: number;
  total_anchors: number;
  prompts: PromptResult[];
}

export interface ModelDetail {
  model_id: string;
  display_name: string;
  provider: string;
  family: string | null;
  is_reasoning: boolean;
  avg_score: number;
  best_score: number;
  run_count: number;
  total_fabrications: number;
  total_dead: number;
  runs: RunSummary[];
}

export interface RunSummary {
  run_id: string;
  score: number;
  label: RunLabel;
  fabricated_count: number;
  dead_count: number;
  total_anchors: number;
  started_at: string;
  benchmark_version: string;
}
