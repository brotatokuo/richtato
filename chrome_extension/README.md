# Richtato Bank Sync — Chrome Extension

Captures the user's authenticated bank session cookies and posts them to a
Richtato deployment so the server-side runner can download statements
unattended.

## Supported banks

Bank of America, Chase, Marcus by Goldman Sachs, American Express, Fidelity.

## Setup flow

The extension is intentionally simple: **add accounts in Richtato first,
then bind them from the extension.**

1. In Richtato, open **Accounts → New** and create the bank accounts you
   want synced (just the name and type — leave the balance blank, the
   automation will fill it in).
2. Open `chrome://extensions`, enable "Developer mode", click
   "Load unpacked", and select the `chrome_extension/` folder.
3. Click the extension icon, then "Open settings". Enter your Richtato
   API URL (e.g. `http://localhost:8000`) and either an API token or your
   Richtato username + password.
4. Sign in to your bank in Chrome.
5. Click the extension. It will list the Richtato accounts that match the
   bank you're on. Tick the accounts you want synced from this login and
   click **Sync N accounts to Richtato**.
6. The first sync uses whatever account-activity page you happen to be on,
   plus any other account pages the extension passively observed during
   this browsing session. Open Richtato → **Bank Sync** to confirm the
   bindings, change the cadence, or trigger a manual run.

## Files

- `manifest.json` — MV3 manifest, permissions limited to bank domains.
- `popup.html`/`popup.js`/`styles.css` — popup UI and orchestration.
- `background.js` — service worker that reads cookies and POSTs to Richtato.
- `content_observer.js` — lightweight observer that picks up account
  activity URLs as the user navigates between accounts.
- `options.html`/`options.js` — settings page where the user configures the
  API base URL and credentials.
- `icons/` — placeholder icons (replace before publishing to the Web Store).

## Security model

- Cookies are read in-memory via `chrome.cookies.getAll` and POSTed
  immediately. They are not written to extension-local storage.
- Credentials (API token or username/password) are stored in
  `chrome.storage.local`, scoped to the user's Chrome profile.
- The runner-side storage of the captured `storage_state` is encrypted
  per-user with Fernet (`apps.bank_automation.encryption`).
- Activity URLs and account bindings are stored on the Richtato side; the
  extension keeps the picked accounts in `chrome.storage.local` only as a
  short-lived cache for re-auth flows.

## Roadmap

- Chrome Web Store publication.
- Per-account silent re-capture when the user is signed in to the bank.
- Adapters for additional banks; submit a PR with a Playwright adapter and
  a host pattern in `manifest.json`.
