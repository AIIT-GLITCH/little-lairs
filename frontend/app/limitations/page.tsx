export default function LimitationsPage() {
  return (
    <div className="max-w-3xl space-y-10">
      <div>
        <h1 className="text-3xl font-bold font-mono mb-2">Limitations</h1>
        <p className="text-gray-400">Known gaps and edge cases in the benchmark.</p>
      </div>

      <div className="space-y-6">
        {[
          {
            title: "Dead ≠ Fabricated",
            body: "A URL can be dead because it genuinely existed and then went offline — not because the model invented it. The fabrication heuristics (DNS failure + domain patterns + URL structure) have false positive and false negative rates. We err on the side of labeling ambiguous cases as DEAD_LINK (lower penalty) rather than FABRICATED_URL.",
          },
          {
            title: "Paywall and Bot-Blocked Pages",
            body: "Many academic publishers (Nature, ScienceDirect, Wiley) return 200 OK to bots while showing a paywall. We classify these as INDETERMINATE rather than SUPPORTED. This understates citation quality for models that cite primary literature.",
          },
          {
            title: "Temporal Validity",
            body: "A URL that was live at run time may be dead a month later — or vice versa. Run artifacts are timestamped but URL verification results are point-in-time. Historical scores should not be retroactively revised based on later link status.",
          },
          {
            title: "Benchmark Contamination",
            body: "Prompts are public. Models trained after benchmark publication may have seen these prompts in training data, which could artificially inflate scores on specific questions.",
          },
          {
            title: "English Only",
            body: "All prompts are in English. Citation behavior in other languages is not tested.",
          },
          {
            title: "Scoring Formula Simplicity",
            body: "The v1 formula (fabricated×60, dead×30) is intentionally simple and legible. It does not account for: claim count, source tier, confidence calibration, or domain expertise of the question. v2 scoring will add these dimensions.",
          },
          {
            title: "No Human Adjudication (v1)",
            body: "All adjudications in v1 are automated. Human review is tracked in the system but no human-reviewed results are published yet. Automated claim matching is approximate, especially for nuanced empirical claims.",
          },
        ].map((l) => (
          <div key={l.title} className="bg-[#161b22] border border-[#30363d] rounded-lg p-4 space-y-2">
            <h3 className="font-semibold text-gray-200">{l.title}</h3>
            <p className="text-sm text-gray-400">{l.body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
