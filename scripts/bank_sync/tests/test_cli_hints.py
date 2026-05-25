"""Tests for bank-agent CLI hint helpers."""

import os

from scripts.bank_sync.cli_hints import signin_command_hint


def test_signin_command_hint_bank_agent(monkeypatch):
    monkeypatch.delenv("RICHTATO_CLI", raising=False)
    assert signin_command_hint(3) == "`bank-agent login signin 3`"
    assert signin_command_hint() == "`bank-agent login signin <id>`"


def test_signin_command_hint_richtato_cli(monkeypatch):
    monkeypatch.setenv("RICHTATO_CLI", "1")
    assert signin_command_hint(3) == "`richtato bank signin 3`"
    assert signin_command_hint() == "`richtato bank signin`"
