/**
 * Content script for Bank of America pages.
 *
 * Phase 3: every time the user lands on a BoFA account-activity page (which
 * carries the per-account `adx` token in the URL), forward the URL +
 * page title to the background worker so it can build up the full set of
 * accounts under one login. The background script keeps these in
 * `chrome.storage.local` and bundles them into the next "Sync this account"
 * capture so the user only clicks once per login.
 *
 * No bank content is captured beyond the title and the URL the browser is
 * already showing in the address bar.
 */

(function () {
  const url = location.href;
  const title = document.title || "";

  if (!/(\/deposit-details\/activity|\/cards|\/customer-account)\//i.test(url)) {
    return;
  }

  chrome.runtime
    .sendMessage({ type: "ACTIVITY_URL_OBSERVED", payload: { url, title } })
    .catch(() => {
      // Background may be inactive while the popup is closed; that's fine.
    });
})();
