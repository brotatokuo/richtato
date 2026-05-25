"""Tests for the Robinhood balance adapter."""

from decimal import Decimal

import pytest

from scripts.bank_sync.errors import NoDownloadError
from scripts.bank_sync.institutions.robinhood import (
    RobinhoodAdapter,
    account_name_from_activity_url,
    parse_balance_text,
    portfolio_url_for_account,
)


class TestParseBalanceText:
    def test_parses_formatted_currency(self):
        assert parse_balance_text("$165,706.11") == Decimal("165706.11")

    def test_parses_aria_label_amount(self):
        assert parse_balance_text("$46,842.67") == Decimal("46842.67")

    def test_parses_plain_amount(self):
        assert parse_balance_text("1234.56") == Decimal("1234.56")

    def test_raises_for_empty_text(self):
        with pytest.raises(NoDownloadError):
            parse_balance_text("")

    def test_raises_for_unparseable_text(self):
        with pytest.raises(NoDownloadError):
            parse_balance_text("Balance unavailable")


class TestPortfolioUrlHelpers:
    def test_portfolio_url_for_account_encodes_label(self):
        url = portfolio_url_for_account("Individual")
        assert "classic=1" in url
        assert "rh_account=Individual" in url

    def test_account_name_from_activity_url_round_trip(self):
        url = portfolio_url_for_account("Roth IRA")
        assert account_name_from_activity_url(url) == "Roth IRA"

    def test_account_name_from_activity_url_defaults_empty(self):
        assert account_name_from_activity_url("https://robinhood.com/?classic=1") == ""


class TestRobinhoodAdapterRegistry:
    def test_adapter_metadata(self):
        adapter = RobinhoodAdapter()
        assert adapter.slug == "robinhood"
        assert adapter.login_url == "https://robinhood.com/login"
