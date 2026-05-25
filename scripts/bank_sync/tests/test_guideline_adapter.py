"""Tests for the Guideline balance adapter."""

from decimal import Decimal

import pytest

from scripts.bank_sync.errors import NoDownloadError
from scripts.bank_sync.institutions.guideline import GuidelineAdapter, parse_balance_text


class TestParseBalanceText:
    def test_parses_formatted_currency(self):
        assert parse_balance_text("$46,842.67") == Decimal("46842.67")

    def test_parses_plain_amount(self):
        assert parse_balance_text("1234.56") == Decimal("1234.56")

    def test_raises_for_empty_text(self):
        with pytest.raises(NoDownloadError):
            parse_balance_text("")

    def test_raises_for_unparseable_text(self):
        with pytest.raises(NoDownloadError):
            parse_balance_text("Balance unavailable")


class TestGuidelineAdapterRegistry:
    def test_adapter_metadata(self):
        adapter = GuidelineAdapter()
        assert adapter.slug == "guideline"
        assert adapter.login_url == "https://my.guideline.com/"
