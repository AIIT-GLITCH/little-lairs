"""
core/verifier.py — URL verification and failure type classification.
Ported from AnchorForge dead_link_detector.py + url_checker.py + domain_classifier.py.
"""

from __future__ import annotations
import asyncio
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
import tldextract

from core.parser import ExtractedURL


# ── Domain → Tier mapping ─────────────────────────────────────────────────────

_DOMAIN_TIERS: dict[str, int] = {
    # Tier 1 — primary sources
    "gov": 1, "mil": 1, "edu": 1,
    "who.int": 1, "un.org": 1, "worldbank.org": 1,
    "iso.org": 1, "ieee.org": 1, "nist.gov": 1,
    "nature.com": 1, "science.org": 1, "sciencedirect.com": 1,
    "springer.com": 1, "wiley.com": 1, "cell.com": 1,
    "pnas.org": 1, "doi.org": 1, "pubmed.ncbi.nlm.nih.gov": 1,
    # Tier 2 — secondary
    "arxiv.org": 2, "biorxiv.org": 2, "medrxiv.org": 2,
    "reuters.com": 2, "apnews.com": 2, "bbc.com": 2,
    "nytimes.com": 2, "washingtonpost.com": 2, "economist.com": 2,
    "techcrunch.com": 2, "arstechnica.com": 2, "wired.com": 2,
    "theverge.com": 2, "wikipedia.org": 2,
    # Tier 3 — low credibility
    "reddit.com": 3, "quora.com": 3, "medium.com": 3,
    "substack.com": 3, "blogspot.com": 3, "wordpress.com": 3,
    "github.com": 3, "stackoverflow.com": 3,
}

_FABRICATION_SIGNALS = [
    re.compile(r'doi\.org/10\.\d+/fake', re.IGNORECASE),
    re.compile(r'/article/\d{10,}$'),
    re.compile(r'/reports?/\d{4}/[a-z-]+\d{6,}'),
    re.compile(r'example\.(com|org|net)'),
]

_COMMONLY_FABRICATED = {
    "nature.com", "sciencedirect.com", "springer.com", "wiley.com",
    "pubmed.ncbi.nlm.nih.gov", "arxiv.org", "doi.org",
}

_SOFT_404_PATTERNS = re.compile(
    r'(page not found|404|not found|does not exist|no longer available)',
    re.IGNORECASE,
)


def source_tier(url: str) -> int:
    """Return 1, 2, or 3 for a URL."""
    ext = tldextract.extract(url)
    domain = f"{ext.domain}.{ext.suffix}".lower()
    full = f"{ext.subdomain}.{domain}".lstrip(".").lower()

    # TLD-level overrides
    if ext.suffix in ("gov", "mil", "edu"):
        return 1
    if ext.suffix in ("ac.uk", "gc.ca", "gov.uk"):
        return 1

    return _DOMAIN_TIERS.get(full) or _DOMAIN_TIERS.get(domain) or 3


# ── Verification result ───────────────────────────────────────────────────────

@dataclass
class VerificationResult:
    url: str
    http_status: int | None
    final_url: str | None
    failure_type: str           # failure_type enum value
    page_title: str | None
    confidence: float
    tier: int


async def verify_url(url: str, client: httpx.AsyncClient) -> VerificationResult:
    """Verify a single URL and classify its failure type."""
    http_status = None
    final_url = None
    page_title = None
    tier = source_tier(url)

    try:
        r = await client.get(url, follow_redirects=True, timeout=10.0)
        http_status = r.status_code
        final_url = str(r.url)

        # Soft-404 check via page title
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', r.text, re.IGNORECASE)
        page_title = title_match.group(1).strip() if title_match else None

        if r.status_code == 200:
            if page_title and _SOFT_404_PATTERNS.search(page_title):
                return VerificationResult(url, http_status, final_url, "DEAD_LINK", page_title, 0.7, tier)

            # Redirect abuse — final URL domain ≠ original domain
            orig_host = urlparse(url).netloc
            final_host = urlparse(final_url).netloc
            if orig_host and final_host and orig_host != final_host:
                if tier >= 3:
                    return VerificationResult(url, http_status, final_url, "REDIRECT_ABUSE", page_title, 0.8, tier)

            return VerificationResult(url, http_status, final_url, "SUPPORTED", page_title, 0.95, tier)

        if r.status_code in (301, 302, 307, 308):
            return VerificationResult(url, http_status, final_url, "REDIRECT_ABUSE", page_title, 0.75, tier)

        # 4xx / 5xx — dead or fabricated
        return _classify_dead(url, http_status, final_url, page_title, tier, dns_error=False)

    except (httpx.ConnectError, httpx.TimeoutException):
        return _classify_dead(url, None, None, None, tier, dns_error=True)
    except Exception:
        return VerificationResult(url, None, None, "INDETERMINATE", None, 0.5, tier)


def _classify_dead(
    url: str,
    http_status: int | None,
    final_url: str | None,
    page_title: str | None,
    tier: int,
    dns_error: bool,
) -> VerificationResult:
    fab_score = 0.0

    for pattern in _FABRICATION_SIGNALS:
        if pattern.search(url):
            fab_score += 0.4

    ext = tldextract.extract(url)
    domain = f"{ext.domain}.{ext.suffix}".lower()

    if domain in _COMMONLY_FABRICATED:
        fab_score += 0.2
    if tier == 3:
        fab_score += 0.3
    if dns_error:
        fab_score += 0.5

    failure = "FABRICATED_URL" if fab_score >= 0.5 else "DEAD_LINK"
    confidence = min(0.95, 0.5 + fab_score * 0.45) if failure == "FABRICATED_URL" else 0.85

    return VerificationResult(url, http_status, final_url, failure, page_title, confidence, tier)


async def verify_all(
    urls: list[ExtractedURL],
    concurrency: int = 10,
) -> list[VerificationResult]:
    """Verify a list of extracted URLs concurrently."""
    sem = asyncio.Semaphore(concurrency)
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)
    headers = {"User-Agent": "LittleLairs/2.0 citation-forensics-benchmark"}

    async with httpx.AsyncClient(limits=limits, headers=headers) as client:
        async def _checked(u: ExtractedURL) -> VerificationResult:
            async with sem:
                return await verify_url(u.url, client)

        return list(await asyncio.gather(*[_checked(u) for u in urls]))
