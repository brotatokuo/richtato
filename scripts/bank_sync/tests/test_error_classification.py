"""Tests for bank-sync failure classification helpers."""

from scripts.bank_sync.errors import (
    FailureKind,
    format_failure_reason,
    parse_failure_kind,
    strip_failure_prefix,
    worst_failure_kind,
)
from scripts.bank_sync.playwright_helpers import html_body_suggests_reauth, is_login_url


class TestFailureKindHelpers:
    def test_format_failure_reason(self):
        assert format_failure_reason(
            FailureKind.DOM_BROKEN, "missing button"
        ) == "[dom_broken] missing button"

    def test_parse_failure_kind_round_trip(self):
        text = format_failure_reason(FailureKind.NEEDS_REAUTH, "Session expired")
        assert parse_failure_kind(text) == FailureKind.NEEDS_REAUTH

    def test_parse_failure_kind_returns_none_for_plain_text(self):
        assert parse_failure_kind("something went wrong") is None

    def test_strip_failure_prefix(self):
        text = format_failure_reason(FailureKind.DOM_BROKEN, "missing button")
        assert strip_failure_prefix(text) == "missing button"

    def test_worst_failure_kind_prefers_reauth(self):
        kinds = [FailureKind.NO_DOWNLOAD, FailureKind.DOM_BROKEN, FailureKind.NEEDS_REAUTH]
        assert worst_failure_kind(kinds) == FailureKind.NEEDS_REAUTH


class TestLoginUrlDetection:
    def test_is_login_url_matches_markers(self):
        assert is_login_url(
            "https://secure.bankofamerica.com/signin/overview.go",
            ("signin", "login"),
        )
        assert not is_login_url(
            "https://secure.chase.com/web/auth/dashboard",
            ("signin", "login"),
        )


class TestHtmlReauthDetection:
    def test_html_body_suggests_reauth_for_sign_in_page(self):
        body = b"<html><body><h1>Sign in to your account</h1></body></html>"
        assert html_body_suggests_reauth(body)

    def test_html_body_suggests_reauth_for_password_field(self):
        body = b'<html><body><input type="password" name="password"></body></html>'
        assert html_body_suggests_reauth(body)

    def test_html_body_does_not_flag_generic_error_page(self):
        body = b"<html><body><h1>Service unavailable</h1></body></html>"
        assert not html_body_suggests_reauth(body)

    def test_html_body_ignores_non_html(self):
        assert not html_body_suggests_reauth(b"date,amount,description\n2026-01-01,1.00,test")
