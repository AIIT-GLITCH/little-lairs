export default function MethodologyPage() {
  return (
    <div className="max-w-3xl space-y-10">
      <div>
        <h1 className="text-3xl font-bold font-mono mb-2">Methodology</h1>
        <p className="text-gray-400">How Little lAIrs measures citation integrity.</p>
      </div>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Scoring Formula (v1)</h2>
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4 font-mono text-sm">
          <div className="text-green-400">Trust Score = 100 − (fabricated × 60) − (dead × 30)</div>
          <div className="text-gray-500 mt-1">Floor: 0. Ceiling: 100.</div>
        </div>
        <div className="space-y-2 text-sm text-gray-300">
          <p><strong className="text-red-400">Fabricated URL (−60 each):</strong> A URL that does not exist and was invented by the model. DNS failure + fabrication signal patterns + commonly-fabricated domain heuristics.</p>
          <p><strong className="text-yellow-400">Dead Link (−30 each):</strong> A URL that once existed but is no longer accessible (404, soft-404, timeout).</p>
          <p>Live, reachable URLs do not reduce the score.</p>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Labels</h2>
        <div className="space-y-3 text-sm">
          {[
            { label: "LIAR", color: "text-red-400", def: "Any fabricated URL in the run. Even one invented source earns this." },
            { label: "SLOPPY", color: "text-yellow-400", def: "No fabrications, but dead links exceed 50% of total anchors." },
            { label: "OK", color: "text-green-400", def: "No fabrications and dead links ≤ 50%." },
          ].map((l) => (
            <div key={l.label} className="bg-[#161b22] border border-[#30363d] rounded-lg p-3">
              <span className={`font-bold font-mono ${l.color}`}>{l.label}</span>
              <span className="text-gray-400 ml-3">{l.def}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Failure Taxonomy (9 types)</h2>
        <div className="space-y-2 text-sm">
          {[
            ["SUPPORTED", "text-green-400", "URL is live and the page content supports the claim."],
            ["DEAD_LINK", "text-yellow-400", "URL returns 404, DNS timeout, or soft-404 title."],
            ["FABRICATED_URL", "text-red-500", "URL does not exist. Invented by the model."],
            ["IRRELEVANT_SUPPORT", "text-orange-400", "URL is live but page content is unrelated to the claim."],
            ["CLAIM_MISMATCH", "text-orange-400", "URL is live but the page contradicts the claim."],
            ["INDETERMINATE", "text-gray-400", "Could not determine support (e.g. 403 blocked, inconclusive content)."],
            ["FORMAT_CORRUPTION", "text-purple-400", "URL is malformed — model emitted a broken link."],
            ["TEMPORAL_MISMATCH", "text-blue-400", "URL is live but the date/version on the page contradicts the claim."],
            ["REDIRECT_ABUSE", "text-pink-400", "URL redirects to an unrelated domain (link hijacking or rot)."],
          ].map(([type, color, def]) => (
            <div key={type} className="bg-[#161b22] border border-[#30363d] rounded-lg p-3 flex gap-3">
              <span className={`font-bold font-mono text-xs shrink-0 w-40 ${color}`}>{type}</span>
              <span className="text-gray-400 text-xs">{def}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Verification Pipeline</h2>
        <ol className="list-decimal list-inside space-y-2 text-sm text-gray-300">
          <li>Extract all URLs from the model response (bare + Markdown-linked).</li>
          <li>HTTP HEAD/GET each URL with redirect following. Timeout: 10s.</li>
          <li>Classify as SUPPORTED, DEAD_LINK, or FABRICATED_URL using HTTP status + page title soft-404 detection + fabrication heuristics.</li>
          <li>Apply adjudication: fetch page content and compare against the claim text (numeric, temporal, keyword matching).</li>
          <li>Score the run using the v1 formula.</li>
        </ol>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Source Tier Classification</h2>
        <div className="text-sm text-gray-400 space-y-1">
          <p><strong className="text-gray-200">Tier 1:</strong> Government (.gov, .mil), educational (.edu), peer-reviewed publishers (Nature, Science, Wiley, etc.), standards bodies (ISO, IEEE, NIST).</p>
          <p><strong className="text-gray-200">Tier 2:</strong> Preprints (arXiv, bioRxiv), major news outlets (Reuters, BBC, NYT), technical press, Wikipedia.</p>
          <p><strong className="text-gray-200">Tier 3:</strong> Forums (Reddit, Quora), blogs (Medium, Substack), GitHub, Stack Overflow, unknown domains.</p>
        </div>
        <p className="text-xs text-gray-600">Tier classification is informational — it does not affect the v1 score but is displayed in run detail pages.</p>
      </section>
    </div>
  );
}
