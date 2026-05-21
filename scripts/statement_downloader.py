#!/usr/bin/env python3
"""Local-only Playwright helper for downloading statement files.

This script deliberately keeps bank credentials and browser sessions outside the
Django app. It opens a headed browser, lets the user complete login/MFA, and
captures the first CSV/XLS/XLSX download triggered by the user.
"""

from __future__ import annotations

import argparse
from pathlib import Path

INSTITUTION_URLS = {
    "bofa": "https://www.bankofamerica.com/",
    "marcus": "https://www.marcus.com/",
    "amex": "https://www.americanexpress.com/",
    "robinhood_bank": "https://robinhood.com/",
    "fidelity": "https://www.fidelity.com/",
    "robinhood_investments": "https://robinhood.com/",
    "guideline": "https://www.guideline.com/",
    "chase": "https://www.chase.com/",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download a bank statement with a local headed browser.")
    parser.add_argument("institution", choices=sorted(INSTITUTION_URLS))
    parser.add_argument(
        "--download-dir",
        default="local_data/statements",
        help="Local directory where downloaded statements are saved.",
    )
    parser.add_argument(
        "--storage-state",
        default=None,
        help="Optional Playwright storage state JSON path for this institution.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit("Install Playwright locally first: python -m pip install playwright && playwright install") from exc

    institution_dir = Path(args.download_dir) / args.institution
    institution_dir.mkdir(parents=True, exist_ok=True)
    storage_state = Path(args.storage_state) if args.storage_state else None

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context_kwargs = {"accept_downloads": True}
        if storage_state and storage_state.exists():
            context_kwargs["storage_state"] = str(storage_state)
        context = browser.new_context(**context_kwargs)
        page = context.new_page()
        page.goto(INSTITUTION_URLS[args.institution])

        print("Complete login/MFA in the browser, navigate to statements, then click the CSV/Excel download.")
        with page.expect_download(timeout=10 * 60 * 1000) as download_info:
            page.bring_to_front()

        download = download_info.value
        suggested = download.suggested_filename
        target = institution_dir / suggested
        download.save_as(target)

        if storage_state:
            storage_state.parent.mkdir(parents=True, exist_ok=True)
            context.storage_state(path=str(storage_state))

        print(f"Downloaded statement: {target}")
        context.close()
        browser.close()


if __name__ == "__main__":
    main()
