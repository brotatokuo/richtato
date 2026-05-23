# Richtato Bank Sync — Privacy Policy

**Last updated:** 2026-05-22

The Richtato Bank Sync extension exists to forward an authenticated bank
session from the user's own Chrome browser to a Richtato deployment that the
user has installed and credentialed. This document explains exactly what
data the extension touches and where it goes.

## What the extension reads

1. **Cookies for the bank domain you choose to sync.** When you press
   "Sync this account to Richtato" while signed in to a supported bank in
   the active tab, the extension calls `chrome.cookies.getAll` for that
   bank's domain. The result is the same authenticated session your bank
   already trusts in your browser.
2. **The active tab's URL.** Used to capture the per-account activity URL
   (which encodes the bank's opaque account token) so the server-side
   runner can navigate directly to the download page.
3. **A friendly account name you optionally type into the popup.**

The extension does **not**:

- Read your bank password, biometric, or MFA secrets.
- Read content from other tabs or other websites.
- Persist cookies in `chrome.storage.local`.
- Share any data with the extension author or any third party other than
  the Richtato deployment URL you configured.

## Where the data goes

Captured cookies and the account URL are sent over HTTPS to the Richtato
deployment URL you configured in the extension's settings page (e.g.
`https://richtato.example.com`). They are never sent anywhere else.

The Richtato server stores cookies and URLs encrypted at rest using
Fernet (AES-128-CBC + HMAC-SHA256) with a per-user envelope key.

## What is stored locally

The extension stores **only** the configuration you provide on its settings
page in `chrome.storage.local`:

- Richtato deployment URL.
- Optional API token, **or** Richtato username + password.

These values stay scoped to your Chrome profile.

## Permissions and why we need them

| Permission | Why |
| --- | --- |
| `cookies` | Read the bank session cookies you ask us to forward. |
| `storage` | Persist your Richtato URL and credentials between popup launches. |
| `tabs` / `activeTab` | Read the active tab's URL to grab the activity URL. |
| `host_permissions` for bank domains | Limit cookie reads to the supported banks; never accesses other sites. |

## User control

- Delete a saved connection inside Richtato to immediately erase the
  encrypted cookies on the server.
- Uninstall the extension to wipe the Richtato URL and credentials from
  Chrome's local storage.
- All actions are logged in your Richtato deployment's audit log under
  events like `session_captured`, `connection_deleted`, `run_failed`.

## Contact

For privacy questions, open an issue at the Richtato repository or contact
the maintainer of your Richtato deployment.
