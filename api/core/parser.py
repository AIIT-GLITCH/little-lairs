"""
core/parser.py — URL + claim extraction from raw model responses.
Ported from AnchorForge anchor_extractor.py + claim_parser.py.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field


# ── URL patterns ─────────────────────────────────────────────────────────────

_URL_RE = re.compile(r'https?://[^\s\)\]\>\"\'\,\;\<]+')
_MD_LINK_RE = re.compile(r'\[([^\]]+)\]\((https?://[^\)]+)\)')
_TRAILING = re.compile(r'[\.\,\;\:\!\?\)\]\>\"\']+$')
_CONTEXT_WINDOW = 200  # chars around each URL


@dataclass
class ExtractedURL:
    url: str
    context: str        # surrounding text window
    position: int       # char offset in response
    source: str         # "bare" | "markdown"


def extract_urls(text: str) -> list[ExtractedURL]:
    """Extract and deduplicate URLs from a model response."""
    seen: set[str] = set()
    results: list[ExtractedURL] = []

    def _add(url: str, pos: int, source: str) -> None:
        url = _TRAILING.sub('', url)
        if not url or url in seen:
            return
        seen.add(url)
        start = max(0, pos - _CONTEXT_WINDOW)
        end = min(len(text), pos + len(url) + _CONTEXT_WINDOW)
        results.append(ExtractedURL(url=url, context=text[start:end], position=pos, source=source))

    # Markdown links first (higher signal)
    for m in _MD_LINK_RE.finditer(text):
        _add(m.group(2), m.start(2), "markdown")

    # Bare URLs
    for m in _URL_RE.finditer(text):
        _add(m.group(0), m.start(), "bare")

    results.sort(key=lambda u: u.position)
    return results


# ── Claim patterns ────────────────────────────────────────────────────────────

_NUM_RE = re.compile(
    r'\b\d[\d,\.]*(?:[eE][+-]?\d+)?(?:\s*(?:million|billion|trillion|%|percent))?\b'
)
_DATE_RE = re.compile(
    r'\b(?:\d{4}-\d{2}-\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}|\d{4})\b',
    re.IGNORECASE,
)
_ENTITY_RE = re.compile(r'\b(?:[A-Z][a-z]+\s+){1,4}[A-Z][a-z]+\b')

_SKIP_STARTS = re.compile(
    r"^(?:here is|here's|i'll|i will|let me|as requested|the following|"
    r"below is|sure|certainly|of course|absolutely|great|note that)",
    re.IGNORECASE,
)

_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')


@dataclass
class ParsedClaim:
    text: str
    position: int
    has_number: bool = False
    has_date: bool = False
    has_entity: bool = False
    extracted_numbers: list[str] = field(default_factory=list)
    extracted_dates: list[str] = field(default_factory=list)
    extracted_entities: list[str] = field(default_factory=list)
    associated_urls: list[str] = field(default_factory=list)


def extract_claims(text: str, urls: list[ExtractedURL] | None = None) -> list[ParsedClaim]:
    """Parse atomic verifiable claims from response text."""
    urls = urls or []
    claims: list[ParsedClaim] = []
    offset = 0

    for sentence in _SENTENCE_SPLIT.split(text):
        sentence = sentence.strip()
        pos = text.find(sentence, offset)
        offset = pos + len(sentence) if pos >= 0 else offset

        if len(sentence) < 15:
            continue
        if _SKIP_STARTS.match(sentence):
            continue

        numbers = _NUM_RE.findall(sentence)
        dates = _DATE_RE.findall(sentence)
        entities = _ENTITY_RE.findall(sentence)

        if not (numbers or dates or entities):
            continue

        # Associate nearby URLs (within 500 chars)
        nearby = [u.url for u in urls if abs(u.position - pos) < 500]

        claims.append(ParsedClaim(
            text=sentence,
            position=pos,
            has_number=bool(numbers),
            has_date=bool(dates),
            has_entity=bool(entities),
            extracted_numbers=numbers,
            extracted_dates=dates,
            extracted_entities=entities,
            associated_urls=nearby,
        ))

    return claims
