import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import type { RunLabel, FailureType } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function labelColor(label: RunLabel): string {
  return { LIAR: "bg-red-500", SLOPPY: "bg-yellow-500", OK: "bg-green-500" }[label];
}

export function scoreColor(score: number): string {
  if (score >= 80) return "text-green-400";
  if (score >= 50) return "text-yellow-400";
  return "text-red-400";
}

export function failureColor(type: FailureType): string {
  const map: Record<FailureType, string> = {
    SUPPORTED:          "text-green-400",
    DEAD_LINK:          "text-yellow-400",
    FABRICATED_URL:     "text-red-500",
    IRRELEVANT_SUPPORT: "text-orange-400",
    CLAIM_MISMATCH:     "text-orange-400",
    INDETERMINATE:      "text-gray-400",
    FORMAT_CORRUPTION:  "text-purple-400",
    TEMPORAL_MISMATCH:  "text-blue-400",
    REDIRECT_ABUSE:     "text-pink-400",
  };
  return map[type] ?? "text-gray-400";
}

export function shortModelId(modelId: string): string {
  return modelId.split("/").pop() ?? modelId;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric", month: "short", day: "numeric",
  });
}
