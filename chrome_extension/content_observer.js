/**
 * Generic content script that forwards bank account-activity URLs to the
 * background worker.
 *
 * Per-bank URL pattern hints live here so the same script supports BoFA,
 * Chase, Marcus, Amex, and Fidelity. Anything that does not match a known
 * activity pattern is ignored — the goal is exactly the URLs the runner
 * needs to drive a download.
 */

(function () {
  const url = location.href;
  const title = document.title || "";
  const host = location.hostname;

  const PATTERNS = [
    {
      host: /(^|\.)bankofamerica\.com$/,
      url: /(\/deposit-details\/activity|\/cards|\/customer-account)\//i,
    },
    {
      host: /(^|\.)chase\.com$/,
      url: /(\/web\/auth\/dashboard\/details|\/activity|\/AccountActivity)/i,
    },
    {
      host: /(^|\.)marcus\.com$/,
      url: /(\/account|\/activity|\/transactions)\b/i,
    },
    {
      host: /(^|\.)americanexpress\.com$/,
      url: /(\/account-statement|\/statements|\/activity|\/transactions)\b/i,
    },
    {
      host: /(^|\.)fidelity\.com$/,
      url: /(\/portfolio\/activity|\/positions|\/history)\b/i,
    },
  ];

  const matched = PATTERNS.some(p => p.host.test(host) && p.url.test(url));
  if (!matched) return;

  chrome.runtime
    .sendMessage({ type: "ACTIVITY_URL_OBSERVED", payload: { url, title } })
    .catch(() => {});
})();
