"""Tests for core/parser.py"""
import pytest
from core.parser import extract_urls, extract_claims, ExtractedURL


class TestExtractURLs:
    def test_bare_url(self):
        text = "See https://example.com for details."
        urls = extract_urls(text)
        assert len(urls) == 1
        assert urls[0].url == "https://example.com"
        assert urls[0].source == "bare"

    def test_markdown_link(self):
        text = "See [this paper](https://arxiv.org/abs/1234.5678) for details."
        urls = extract_urls(text)
        assert len(urls) == 1
        assert urls[0].url == "https://arxiv.org/abs/1234.5678"
        assert urls[0].source == "markdown"

    def test_deduplication(self):
        text = "https://example.com and again https://example.com"
        urls = extract_urls(text)
        assert len(urls) == 1

    def test_trailing_punctuation_stripped(self):
        text = "See https://example.com."
        urls = extract_urls(text)
        assert urls[0].url == "https://example.com"

    def test_multiple_urls_ordered_by_position(self):
        text = "First https://a.com then https://b.com"
        urls = extract_urls(text)
        assert urls[0].url == "https://a.com"
        assert urls[1].url == "https://b.com"

    def test_no_urls(self):
        assert extract_urls("No links here.") == []

    def test_context_window_captured(self):
        text = "Some context before https://example.com and after"
        urls = extract_urls(text)
        assert "context before" in urls[0].context
        assert "and after" in urls[0].context


class TestExtractClaims:
    def test_numeric_claim(self):
        text = "The study found that 73% of participants showed improvement."
        claims = extract_claims(text)
        assert len(claims) == 1
        assert claims[0].has_number

    def test_date_claim(self):
        text = "The paper was published on 2023-04-15 by the research team."
        claims = extract_claims(text)
        assert any(c.has_date for c in claims)

    def test_entity_claim(self):
        text = "According to World Health Organization, the findings are significant."
        claims = extract_claims(text)
        assert any(c.has_entity for c in claims)

    def test_skips_short_sentences(self):
        claims = extract_claims("Yes. No. OK.")
        assert len(claims) == 0

    def test_skips_meta_sentences(self):
        claims = extract_claims("Here is a summary of the findings.")
        assert len(claims) == 0

    def test_associated_urls_nearby(self):
        text = "The value is 42%. See https://example.com for reference."
        urls = extract_urls(text)
        claims = extract_claims(text, urls)
        assert len(claims) >= 1
        assert "https://example.com" in claims[0].associated_urls
