/**
 * Background service worker.
 *
 * Responsibilities:
 *  - Read all cookies for the bank's domain into a Playwright-shaped
 *    `storage_state` blob.
 *  - POST that blob plus the captured activity URL to Richtato's session
 *    ingest endpoint.
 *  - Stable login_id derivation: hash of (institution + the bank's session
 *    cookie value) so re-captures from the same login update the existing
 *    BankConnection instead of creating a duplicate.
 *  - Phase 3: silent re-auth — when Richtato has flagged a connection as
 *    `reauth_required` and the user happens to be signed in to the bank
 *    in Chrome, refresh the cookies in the background without a click.
 *  - Phase 3: activity URL auto-discovery — listen for navigations to
 *    bank account pages and remember the URLs so the user does not have
 *    to click into each account.
 */

const HOST_PATTERNS = {
  bofa: /(^|\.)bankofamerica\.com$/,
  chase: /(^|\.)chase\.com$/,
  marcus: /(^|\.)marcus\.com$/,
  amex: /(^|\.)americanexpress\.com$/,
  fidelity: /(^|\.)fidelity\.com$/,
};

const SESSION_INGEST_PATH = "/api/v1/bank-automation/sessions/";
const CONNECTIONS_LIST_PATH = "/api/v1/bank-automation/connections/";
const SILENT_REAUTH_ALARM = "richtato-silent-reauth";
const SILENT_REAUTH_PERIOD_MINUTES = 60;

const ACTIVITY_URL_PATTERNS = {
  bofa: /\/(deposit-details\/activity|customer-account|cards)\//i,
  chase: /(\/web\/auth\/dashboard\/details|\/activity|\/AccountActivity)/i,
  marcus: /(\/account|\/activity|\/transactions)\b/i,
  amex: /(\/account-statement|\/statements|\/activity|\/transactions)\b/i,
  fidelity: /(\/portfolio\/activity|\/positions|\/history)\b/i,
};

async function getConfig() {
  return new Promise((resolve) => {
    chrome.storage.local.get(
      ["apiBaseUrl", "apiToken", "username", "password"],
      (cfg) => resolve(cfg || {}),
    );
  });
}

async function getCookiesForInstitution(slug) {
  const pattern = HOST_PATTERNS[slug];
  if (!pattern) return [];
  // Walk every cookie store the user has. Filter by hostname pattern so
  // we don't accidentally read cookies for unrelated sites that happen to
  // share a TLD.
  const all = await new Promise((resolve) => {
    chrome.cookies.getAll({}, (c) => resolve(c || []));
  });
  return all.filter((c) => pattern.test((c.domain || "").replace(/^\./, "")));
}

function toPlaywrightStorageState(cookies) {
  return {
    cookies: cookies.map((c) => ({
      name: c.name,
      value: c.value,
      domain: c.domain,
      path: c.path || "/",
      expires: c.expirationDate ? Math.floor(c.expirationDate) : -1,
      httpOnly: !!c.httpOnly,
      secure: !!c.secure,
      sameSite: mapSameSite(c.sameSite),
    })),
    origins: [],
  };
}

function mapSameSite(value) {
  switch ((value || "").toLowerCase()) {
    case "strict":
      return "Strict";
    case "lax":
      return "Lax";
    case "no_restriction":
    case "none":
      return "None";
    default:
      return "Lax";
  }
}

async function deriveLoginId(slug, cookies) {
  // Hash a stable cookie so re-captures from the same login coalesce.
  const stable = cookies.find((c) => /SESSION/i.test(c.name));
  const seed = `${slug}:${stable ? stable.value : "anon"}`;
  const buf = new TextEncoder().encode(seed);
  const digest = await crypto.subtle.digest("SHA-256", buf);
  return `${slug}_${[...new Uint8Array(digest)]
    .slice(0, 8)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("")}`;
}

async function postSessionCapture(payload) {
  const cfg = await getConfig();
  if (!cfg.apiBaseUrl) {
    throw new Error("Configure the Richtato API URL in extension settings first.");
  }

  const url = `${cfg.apiBaseUrl.replace(/\/$/, "")}${SESSION_INGEST_PATH}`;
  const headers = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };
  if (cfg.apiToken) {
    headers["Authorization"] = `Token ${cfg.apiToken}`;
  } else if (cfg.username && cfg.password) {
    const basic = btoa(`${cfg.username}:${cfg.password}`);
    headers["Authorization"] = `Basic ${basic}`;
  } else {
    throw new Error("Configure either an API token or username/password.");
  }

  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
    credentials: "omit",
  });
  const text = await response.text();
  if (!response.ok) {
    throw new Error(`Richtato API ${response.status}: ${text.slice(0, 200)}`);
  }
  try {
    return JSON.parse(text);
  } catch (_) {
    return { raw: text };
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (!message) return false;
  if (message.type === "CAPTURE_SESSION") {
    (async () => {
      try {
        const { institutionSlug } = message.payload;
        // Two payload shapes are accepted:
        //   1. Multi: { accounts: [{...}, ...] } — current popup
        //   2. Single (legacy): top-level activityUrl/flow/etc.
        let inputAccounts;
        if (Array.isArray(message.payload.accounts)) {
          inputAccounts = message.payload.accounts.map((a) => ({
            flow: a.flow || "deposit",
            activity_url: a.activity_url || a.activityUrl || "",
            external_account_token:
              a.external_account_token || a.externalAccountToken || "",
            detected_account_name:
              a.detected_account_name || a.detectedAccountName || "",
            financial_account_id:
              a.financial_account_id ?? a.financialAccountId ?? null,
          }));
        } else {
          inputAccounts = [
            {
              flow: message.payload.flow || "deposit",
              activity_url: message.payload.activityUrl || "",
              external_account_token:
                message.payload.externalAccountToken || "",
              detected_account_name: message.payload.detectedAccountName || "",
              financial_account_id: message.payload.financialAccountId ?? null,
            },
          ];
        }

        const cookies = await getCookiesForInstitution(institutionSlug);
        if (!cookies.length) {
          throw new Error("No cookies found for this bank. Are you signed in?");
        }
        const storageState = toPlaywrightStorageState(cookies);
        const loginId = await deriveLoginId(institutionSlug, cookies);

        // Mix in any auto-discovered URLs that aren't already covered by the
        // explicit picks. We try to reuse a discovered URL for picks that
        // came in without one (multi-select case); leftover discoveries are
        // appended as bare account entries the user can later bind from
        // the Richtato UI.
        const discovered = await loadDiscoveredActivityUrls(institutionSlug);
        const usedDiscovered = new Set();
        for (const account of inputAccounts) {
          if (!account.activity_url) {
            const candidate = discovered.find(
              (d) =>
                !usedDiscovered.has(d.url) &&
                d.flow === account.flow &&
                d.adx,
            );
            if (candidate) {
              account.activity_url = candidate.url;
              account.external_account_token =
                account.external_account_token || candidate.adx;
              usedDiscovered.add(candidate.url);
            }
          }
          if (!account.external_account_token && account.activity_url) {
            account.external_account_token =
              extractAdx(account.activity_url, institutionSlug) || "";
          }
        }

        const seenUrls = new Set(
          inputAccounts.map((a) => a.activity_url).filter(Boolean),
        );
        const accounts = [...inputAccounts];
        for (const entry of discovered) {
          if (usedDiscovered.has(entry.url)) continue;
          if (seenUrls.has(entry.url)) continue;
          accounts.push({
            flow: entry.flow || "deposit",
            activity_url: entry.url,
            external_account_token: entry.adx || "",
            detected_account_name: entry.title || "",
            financial_account_id: null,
          });
          seenUrls.add(entry.url);
        }

        const payload = {
          institution_slug: institutionSlug,
          login_id: loginId,
          storage_state: storageState,
          accounts,
        };

        const result = await postSessionCapture(payload);
        await clearDiscoveredActivityUrls(institutionSlug);
        sendResponse({ ok: true, result, capturedAccounts: accounts.length });
      } catch (err) {
        sendResponse({ ok: false, error: err.message || String(err) });
      }
    })();
    return true;
  }

  if (message.type === "ACTIVITY_URL_OBSERVED") {
    (async () => {
      try {
        await rememberActivityUrl(message.payload);
        sendResponse({ ok: true });
      } catch (err) {
        sendResponse({ ok: false, error: err.message || String(err) });
      }
    })();
    return true;
  }

  return false;
});

const TOKEN_PARAM_BY_SLUG = {
  bofa: ["adx"],
  chase: ["aId", "accountId"],
  marcus: ["accountId", "accountUid"],
  amex: ["accountKey", "account_id", "accountId"],
  fidelity: ["accountId", "ACCT_NUM"],
};

function extractAdx(url, slug) {
  // Backwards-compatible name; reads whatever per-bank token the URL
  // carries. Falls back to "adx" so legacy BoFA capture still works.
  const params = (slug && TOKEN_PARAM_BY_SLUG[slug]) || ["adx"];
  try {
    const search = new URL(url).searchParams;
    for (const name of params) {
      const value = search.get(name);
      if (value) return value;
    }
  } catch (_) {
    /* empty */
  }
  return "";
}

function detectInstitutionByUrl(url) {
  let host;
  try {
    host = new URL(url).hostname;
  } catch (_) {
    return null;
  }
  for (const [slug, pattern] of Object.entries(HOST_PATTERNS)) {
    if (pattern.test(host)) return slug;
  }
  return null;
}

async function loadDiscoveredActivityUrls(slug) {
  return new Promise(resolve => {
    chrome.storage.local.get([`discovered:${slug}`], data => {
      resolve((data && data[`discovered:${slug}`]) || []);
    });
  });
}

async function clearDiscoveredActivityUrls(slug) {
  return new Promise(resolve => {
    chrome.storage.local.remove(`discovered:${slug}`, () => resolve());
  });
}

async function rememberActivityUrl({ url, title }) {
  if (!url) return;
  const slug = detectInstitutionByUrl(url);
  if (!slug) return;
  const pattern = ACTIVITY_URL_PATTERNS[slug];
  if (!pattern || !pattern.test(url)) return;
  const adx = extractAdx(url, slug);
  const flow = /\/(cards|credit)\//i.test(url) ? "credit_card" : "deposit";

  const existing = await loadDiscoveredActivityUrls(slug);
  if (existing.some(e => e.adx && adx && e.adx === adx)) return;
  if (existing.some(e => e.url === url)) return;
  existing.push({ url, title: title || "", adx, flow, observedAt: Date.now() });
  // Cap the list so a long-lived session does not balloon storage.
  while (existing.length > 50) existing.shift();
  await new Promise(resolve => {
    chrome.storage.local.set({ [`discovered:${slug}`]: existing }, () =>
      resolve()
    );
  });
}

// Phase 3: Silent re-auth — periodically check the user's connections and,
// if any are flagged reauth_required AND we have fresh bank cookies,
// re-post the session without requiring an extension click.

async function fetchConnections() {
  const cfg = await getConfig();
  if (!cfg.apiBaseUrl) return [];

  const headers = { Accept: "application/json" };
  if (cfg.apiToken) {
    headers["Authorization"] = `Token ${cfg.apiToken}`;
  } else if (cfg.username && cfg.password) {
    headers["Authorization"] = `Basic ${btoa(`${cfg.username}:${cfg.password}`)}`;
  } else {
    return [];
  }

  try {
    const response = await fetch(
      `${cfg.apiBaseUrl.replace(/\/$/, "")}${CONNECTIONS_LIST_PATH}`,
      { method: "GET", headers, credentials: "omit" }
    );
    if (!response.ok) return [];
    const data = await response.json();
    return data.connections || [];
  } catch (_) {
    return [];
  }
}

async function trySilentReauth() {
  const connections = await fetchConnections();
  const reauth = connections.filter(c => c.status === "reauth_required");
  if (!reauth.length) return;

  for (const connection of reauth) {
    try {
      const slug = connection.institution_slug;
      const cookies = await getCookiesForInstitution(slug);
      if (!cookies.length) continue;
      const stable = cookies.find(c => /SESSION/i.test(c.name) && c.value);
      if (!stable) continue;

      const storageState = toPlaywrightStorageState(cookies);
      const loginId = await deriveLoginId(slug, cookies);
      if (loginId !== connection.login_id) {
        // Different bank login signed in than the one Richtato has on
        // file. Don't risk blowing away a different connection's cookies.
        continue;
      }

      // Re-send only the storage state; preserve account links by sending
      // the existing tokens as accounts.
      const accounts = (connection.account_links || [])
        .filter(link => link.enabled)
        .map(link => ({
          flow: link.flow,
          activity_url: "",
          external_account_token: link.external_account_token,
          detected_account_name: link.detected_account_name,
          financial_account_id: link.financial_account,
        }))
        .filter(a => a.external_account_token);

      if (!accounts.length) continue;

      await postSessionCapture({
        institution_slug: slug,
        login_id: loginId,
        storage_state: storageState,
        accounts,
      });
    } catch (err) {
      console.warn("Silent reauth failed for connection", connection.id, err);
    }
  }
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create(SILENT_REAUTH_ALARM, {
    periodInMinutes: SILENT_REAUTH_PERIOD_MINUTES,
    delayInMinutes: 1,
  });
});

chrome.runtime.onStartup.addListener(() => {
  chrome.alarms.create(SILENT_REAUTH_ALARM, {
    periodInMinutes: SILENT_REAUTH_PERIOD_MINUTES,
    delayInMinutes: 1,
  });
});

chrome.alarms.onAlarm.addListener(alarm => {
  if (alarm.name === SILENT_REAUTH_ALARM) {
    trySilentReauth().catch(err =>
      console.warn("trySilentReauth threw", err)
    );
  }
});
