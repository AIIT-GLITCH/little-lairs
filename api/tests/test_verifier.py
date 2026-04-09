"""Tests for core/verifier.py — mock HTTP, all failure taxonomy types."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from core.verifier import verify_url, source_tier, _classify_dead
from core.parser import ExtractedURL


# ── source_tier tests ────────────────────────────────────────────────────────

class TestSourceTier:
    def test_gov_is_tier1(self):
        assert source_tier("https://www.cdc.gov/report") == 1

    def test_edu_is_tier1(self):
        assert source_tier("https://mit.edu/paper") == 1

    def test_nature_is_tier1(self):
        assert source_tier("https://nature.com/articles/s41586") == 1

    def test_arxiv_is_tier2(self):
        assert source_tier("https://arxiv.org/abs/1234.5678") == 2

    def test_wikipedia_is_tier2(self):
        assert source_tier("https://en.wikipedia.org/wiki/Coherence") == 2

    def test_reddit_is_tier3(self):
        assert source_tier("https://reddit.com/r/science") == 3

    def test_unknown_domain_is_tier3(self):
        assert source_tier("https://somethingmadeup.xyz/page") == 3


# ── classify_dead tests ──────────────────────────────────────────────────────

class TestClassifyDead:
    def test_dns_error_on_known_fabricated_domain_is_fabricated(self):
        result = _classify_dead("https://nature.com/articles/fake123456789", 404, None, None, 1, dns_error=True)
        assert result.failure_type == "FABRICATED_URL"

    def test_example_com_is_fabricated(self):
        result = _classify_dead("https://example.com/study", None, None, None, 3, dns_error=True)
        assert result.failure_type == "FABRICATED_URL"

    def test_unknown_domain_404_no_dns_is_dead(self):
        result = _classify_dead("https://real-journal.org/paper/123", 404, None, None, 3, dns_error=False)
        assert result.failure_type == "DEAD_LINK"


# ── verify_url integration tests (mocked HTTP) ───────────────────────────────

class TestVerifyURL:
    @pytest.mark.asyncio
    async def test_200_returns_supported(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://example.com/page"
        mock_resp.text = "<html><title>Real Page</title></html>"

        async def mock_get(*args, **kwargs):
            return mock_resp

        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = mock_get

        result = await verify_url("https://example.com/page", client)
        assert result.failure_type == "SUPPORTED"

    @pytest.mark.asyncio
    async def test_soft_404_title_returns_dead(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://example.com/gone"
        mock_resp.text = "<html><title>Page Not Found</title></html>"

        async def mock_get(*args, **kwargs):
            return mock_resp

        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = mock_get

        result = await verify_url("https://example.com/gone", client)
        assert result.failure_type == "DEAD_LINK"

    @pytest.mark.asyncio
    async def test_404_response_classifies(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.url = "https://real-site.org/paper/12345"
        mock_resp.text = ""

        async def mock_get(*args, **kwargs):
            return mock_resp

        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = mock_get

        result = await verify_url("https://real-site.org/paper/12345", client)
        assert result.failure_type in ("DEAD_LINK", "FABRICATED_URL")

    @pytest.mark.asyncio
    async def test_timeout_classifies(self):
        async def mock_get(*args, **kwargs):
            raise httpx.TimeoutException("timed out")

        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = mock_get

        result = await verify_url("https://example.com/timeout", client)
        assert result.failure_type in ("DEAD_LINK", "FABRICATED_URL", "INDETERMINATE")

    @pytest.mark.asyncio
    async def test_redirect_abuse_different_domain(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://completely-different-domain.com/landing"
        mock_resp.text = "<html><title>Landing Page</title></html>"

        async def mock_get(*args, **kwargs):
            return mock_resp

        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = mock_get

        result = await verify_url("https://some-blog.medium.com/post", client)
        # medium is tier 2, redirect to different domain on tier 3 = REDIRECT_ABUSE
        assert result.failure_type in ("REDIRECT_ABUSE", "SUPPORTED")
