"""Tests for the Marcus aggregated balance adapter."""

from decimal import Decimal

import pytest

from scripts.bank_sync.errors import NoDownloadError
from scripts.bank_sync.institutions import get_adapter
from scripts.bank_sync.institutions.guideline import parse_balance_text
from scripts.bank_sync.institutions.marcus import MarcusAdapter, sum_row_balances


class TestParseBalanceText:
    def test_parses_formatted_currency(self):
        assert parse_balance_text("$871.46") == Decimal("871.46")

    def test_parses_large_amount(self):
        assert parse_balance_text("$40,661.52") == Decimal("40661.52")


class TestSumRowBalances:
    def test_sums_multiple_rows(self):
        balances = [
            Decimal("871.46"),
            Decimal("17556.42"),
            Decimal("40661.52"),
        ]
        assert sum_row_balances(balances) == Decimal("59089.40")

    def test_raises_for_empty_list(self):
        with pytest.raises(NoDownloadError):
            sum_row_balances([])


class TestMarcusAdapterRegistry:
    def test_adapter_metadata(self):
        adapter = MarcusAdapter()
        assert adapter.slug == "marcus"
        assert adapter.login_url == "https://www.marcus.com/us/en/login"

    def test_registered_in_get_adapter(self):
        adapter = get_adapter("marcus")
        assert isinstance(adapter, MarcusAdapter)
