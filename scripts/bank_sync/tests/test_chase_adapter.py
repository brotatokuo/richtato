"""Unit tests for Chase adapter URL helpers and flow routing."""

from __future__ import annotations

import pytest

from scripts.bank_sync.institutions.chase import (
    account_token_from_url,
    infer_flow_from_name,
    is_direct_download_url,
)

_DIRECT_DOWNLOAD_URL = (
    "https://secure.chase.com/web/auth/dashboard"
    "#/dashboard/accountDetails/downloadAccountTransactions/index;params=CARD,BAC,1150719850"
)
_LEGACY_ACTIVITY_URL = "https://secure.chase.com/activity?accountId=1134480538"


class TestChaseUrlHelpers:
    def test_is_direct_download_url(self):
        assert is_direct_download_url(_DIRECT_DOWNLOAD_URL) is True
        assert is_direct_download_url(_LEGACY_ACTIVITY_URL) is False
        assert is_direct_download_url("") is False

    def test_account_token_from_direct_download_url(self):
        assert account_token_from_url(_DIRECT_DOWNLOAD_URL) == "1150719850"

    def test_account_token_from_legacy_activity_url(self):
        assert account_token_from_url(_LEGACY_ACTIVITY_URL) == "1134480538"

    def test_account_token_from_empty_url(self):
        assert account_token_from_url("") == ""

    def test_infer_flow_credit_card(self):
        assert infer_flow_from_name("Prime Visa (...4397)") == "credit_card"
        assert infer_flow_from_name("Sapphire Reserve") == "credit_card"

    def test_infer_flow_deposit(self):
        assert infer_flow_from_name("TOTAL CHECKING (...3216)") == "deposit"
        assert infer_flow_from_name("CHASE SAVINGS (...9190)") == "deposit"


class TestChaseDownloadRouting:
    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            (_DIRECT_DOWNLOAD_URL, True),
            (_LEGACY_ACTIVITY_URL, False),
        ],
    )
    def test_uses_direct_download_when_url_matches(self, url: str, expected: bool):
        assert is_direct_download_url(url) is expected
