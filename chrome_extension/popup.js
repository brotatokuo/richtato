/**
 * Popup logic.
 *
 * State machine:
 *   not-configured -> open options to set API base + token/credentials
 *   not-supported  -> tab is not a recognized bank domain
 *   not-authed     -> bank tab loaded but no auth cookie present
 *   ready          -> show user's Richtato accounts as checkboxes
 *
 * In "ready" we fetch the user's Richtato FinancialAccounts from
 * /bank-automation/bindable-accounts/, prefer ones tagged with the
 * current institution, and let the user check the ones to sync. Submitting
 * sends one CAPTURE_SESSION message with N accounts so the user only has
 * to click once to set up a multi-account login.
 */

function tryQueryParam(url, names) {
  try {
    const params = new URL(url).searchParams;
    for (const name of names) {
      const value = params.get(name);
      if (value) return value;
    }
  } catch (_) {
    /* empty */
  }
  return "";
}

const SUPPORTED = {
  bofa: {
    label: "Bank of America",
    matchHost: /(^|\.)bankofamerica\.com$/,
    extractToken: (url) => tryQueryParam(url, ["adx"]),
  },
  chase: {
    label: "Chase",
    matchHost: /(^|\.)chase\.com$/,
    extractToken: (url) => tryQueryParam(url, ["aId", "accountId"]),
  },
  marcus: {
    label: "Marcus by Goldman Sachs",
    matchHost: /(^|\.)marcus\.com$/,
    extractToken: (url) => tryQueryParam(url, ["accountId", "accountUid"]),
  },
  amex: {
    label: "American Express",
    matchHost: /(^|\.)americanexpress\.com$/,
    extractToken: (url) =>
      tryQueryParam(url, ["accountKey", "account_id", "accountId"]),
  },
  fidelity: {
    label: "Fidelity",
    matchHost: /(^|\.)fidelity\.com$/,
    extractToken: (url) => tryQueryParam(url, ["accountId", "ACCT_NUM"]),
  },
};

const SECTIONS = ["not-configured", "not-supported", "not-authed", "ready"];

let cachedConfig = null;
let cachedAccounts = [];
let activeInstitution = null;
let activeTab = null;

function show(id) {
  for (const sec of SECTIONS) {
    const el = document.getElementById(sec);
    if (el) el.classList.toggle("hidden", sec !== id);
  }
}

function setStatus(text, kind) {
  const el = document.getElementById("status");
  el.textContent = text || "";
  el.classList.remove("success", "error");
  if (kind) el.classList.add(kind);
}

async function loadConfig() {
  return new Promise((resolve) => {
    chrome.storage.local.get(
      ["apiBaseUrl", "apiToken", "username", "password"],
      (cfg) => resolve(cfg || {}),
    );
  });
}

function detectInstitution(tab) {
  if (!tab || !tab.url) return null;
  let host;
  try {
    host = new URL(tab.url).hostname;
  } catch (_) {
    return null;
  }
  for (const [slug, def] of Object.entries(SUPPORTED)) {
    if (def.matchHost.test(host)) {
      return { slug, ...def };
    }
  }
  return null;
}

async function getActiveTab() {
  return new Promise((resolve) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      resolve(tabs && tabs[0]);
    });
  });
}

async function detectAuth(institution) {
  // Read all cookies and filter on hostname so we don't depend on
  // matchHost.source string parsing tricks. A bank session is presumed
  // when at least one cookie with a SESSION-flavored name has a value.
  const cookies = await new Promise((resolve) => {
    chrome.cookies.getAll({}, (c) => resolve(c || []));
  });
  const stripped = (d) => (d || "").replace(/^\./, "");
  const matching = cookies.filter((c) =>
    institution.matchHost.test(stripped(c.domain)),
  );
  return matching.some(
    (c) => /SESSION|AUTH|JSESSION|SSO/i.test(c.name) && !!c.value,
  );
}

function authHeaders(cfg) {
  if (cfg.apiToken) return { Authorization: `Token ${cfg.apiToken}` };
  if (cfg.username && cfg.password) {
    return { Authorization: `Basic ${btoa(`${cfg.username}:${cfg.password}`)}` };
  }
  return null;
}

async function fetchBindableAccounts(institutionSlug) {
  if (!cachedConfig || !cachedConfig.apiBaseUrl) {
    throw new Error("Configure the Richtato API URL in extension settings.");
  }
  const headers = authHeaders(cachedConfig);
  if (!headers) {
    throw new Error("Configure either an API token or username/password.");
  }
  const base = cachedConfig.apiBaseUrl.replace(/\/$/, "");
  const url = `${base}/api/v1/bank-automation/bindable-accounts/?institution_slug=${encodeURIComponent(
    institutionSlug,
  )}`;
  const response = await fetch(url, {
    method: "GET",
    headers: { ...headers, Accept: "application/json" },
    credentials: "omit",
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API ${response.status}: ${text.slice(0, 200)}`);
  }
  const body = await response.json();
  return body.accounts || [];
}

function renderAccountsList(accounts, institution) {
  const list = document.getElementById("accounts-list");
  list.innerHTML = "";

  for (const account of accounts) {
    const li = document.createElement("li");
    if (account.already_bound) li.classList.add("disabled");

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.id = `account-${account.id}`;
    checkbox.value = String(account.id);
    checkbox.dataset.flow = account.flow;
    checkbox.dataset.name = account.name;
    if (!account.already_bound && account.matches_institution) {
      checkbox.checked = true;
    }
    if (account.already_bound) {
      checkbox.disabled = true;
    }
    checkbox.addEventListener("change", updateCaptureButton);

    const meta = document.createElement("div");
    meta.className = "meta";

    const name = document.createElement("span");
    name.className = "name";
    name.textContent = account.name;
    meta.appendChild(name);

    const subParts = [];
    subParts.push(account.account_type_display || account.account_type);
    if (account.account_number_last4)
      subParts.push(`…${account.account_number_last4}`);
    if (account.institution_name && !account.matches_institution) {
      subParts.push(`(${account.institution_name})`);
    }
    if (account.already_bound) {
      subParts.push("already bound");
    } else if (!account.matches_institution && institution) {
      subParts.push(`not tagged ${institution.label}`);
    }
    const sub = document.createElement("span");
    sub.className = "sub";
    sub.textContent = subParts.join(" · ");
    meta.appendChild(sub);

    const label = document.createElement("label");
    label.htmlFor = checkbox.id;
    label.style.flex = "1";
    label.style.cursor = account.already_bound ? "not-allowed" : "pointer";
    label.appendChild(meta);

    li.appendChild(checkbox);
    li.appendChild(label);
    list.appendChild(li);
  }
}

function selectedAccounts() {
  const list = document.getElementById("accounts-list");
  const inputs = list.querySelectorAll("input[type=checkbox]:checked");
  return Array.from(inputs).map((el) => ({
    id: Number(el.value),
    flow: el.dataset.flow || "deposit",
    name: el.dataset.name || "",
  }));
}

function updateCaptureButton() {
  const button = document.getElementById("capture");
  const count = selectedAccounts().length;
  button.disabled = count === 0;
  button.textContent =
    count === 0
      ? "Pick at least one account"
      : `Sync ${count} account${count === 1 ? "" : "s"} to Richtato`;
}

async function showReadyState(institution) {
  document.getElementById("institution-label").textContent = institution.label;
  document.getElementById("accounts-loading").classList.remove("hidden");
  document.getElementById("accounts-empty").classList.add("hidden");
  document.getElementById("accounts-section").classList.add("hidden");
  show("ready");

  let accounts;
  try {
    accounts = await fetchBindableAccounts(institution.slug);
  } catch (err) {
    document.getElementById("accounts-loading").classList.add("hidden");
    setStatus(`Couldn't load accounts: ${err.message}`, "error");
    return;
  }
  cachedAccounts = accounts;

  document.getElementById("accounts-loading").classList.add("hidden");

  const matching = accounts.filter((a) => a.matches_institution);
  if (!matching.length) {
    document.getElementById("empty-institution-name").textContent =
      `accounts at ${institution.label}`;
    const link = document.getElementById("open-accounts-link");
    if (cachedConfig.apiBaseUrl) {
      const base = cachedConfig.apiBaseUrl
        .replace(/\/api\/?$/i, "")
        .replace(/\/$/, "");
      link.href = `${base}/accounts`;
    }
    document.getElementById("accounts-empty").classList.remove("hidden");
    return;
  }

  renderAccountsList(matching, institution);
  document.getElementById("accounts-section").classList.remove("hidden");
  updateCaptureButton();
}

async function init() {
  cachedConfig = await loadConfig();
  const apiBaseEl = document.getElementById("api-base");
  apiBaseEl.textContent = cachedConfig.apiBaseUrl
    ? `Sending to ${cachedConfig.apiBaseUrl}`
    : "Not configured";

  if (
    !cachedConfig.apiBaseUrl ||
    (!cachedConfig.apiToken &&
      !(cachedConfig.username && cachedConfig.password))
  ) {
    show("not-configured");
    return;
  }

  activeTab = await getActiveTab();
  activeInstitution = detectInstitution(activeTab);
  if (!activeInstitution) {
    show("not-supported");
    return;
  }

  const authed = await detectAuth(activeInstitution);
  if (!authed) {
    show("not-authed");
    return;
  }

  await showReadyState(activeInstitution);
}

document.addEventListener("DOMContentLoaded", () => {
  init().catch((err) => {
    setStatus(`Error: ${err.message}`, "error");
  });

  document.getElementById("open-options").addEventListener("click", () => {
    chrome.runtime.openOptionsPage();
  });
  document
    .getElementById("open-options-footer")
    .addEventListener("click", (e) => {
      e.preventDefault();
      chrome.runtime.openOptionsPage();
    });

  document.getElementById("retry").addEventListener("click", () => {
    init().catch((err) => setStatus(`Error: ${err.message}`, "error"));
  });

  document.getElementById("capture").addEventListener("click", async () => {
    const button = document.getElementById("capture");
    button.disabled = true;
    setStatus("Capturing session…", "");

    try {
      const tab = activeTab || (await getActiveTab());
      const institution = activeInstitution || detectInstitution(tab);
      if (!institution) {
        throw new Error("This tab isn't a supported bank.");
      }

      const picks = selectedAccounts();
      if (!picks.length) {
        throw new Error("Pick at least one account to sync.");
      }

      const activityUrl = tab.url;
      const externalToken = institution.extractToken(activityUrl) || "";

      // Send N captured accounts in a single payload. The first carries the
      // currently-active tab URL (most likely an account-specific page); the
      // rest get blank URLs and rely on the extension's auto-discovered
      // activity URLs (collected by the content_observer) to fill in. The
      // user can still bind/correct from the Richtato UI later.
      const accounts = picks.map((pick, idx) => ({
        flow: pick.flow,
        activity_url: idx === 0 ? activityUrl : "",
        external_account_token: idx === 0 ? externalToken : "",
        detected_account_name: pick.name,
        financial_account_id: pick.id,
      }));

      const response = await chrome.runtime.sendMessage({
        type: "CAPTURE_SESSION",
        payload: {
          institutionSlug: institution.slug,
          accounts,
        },
      });

      if (response && response.ok) {
        const n = response.capturedAccounts || picks.length;
        setStatus(
          `Synced ${n} account${n === 1 ? "" : "s"}! Richtato will start ` +
            "downloading on your schedule.",
          "success",
        );
      } else {
        const reason = (response && response.error) || "Unknown error";
        setStatus(`Failed: ${reason}`, "error");
      }
    } catch (err) {
      setStatus(`Error: ${err.message}`, "error");
    } finally {
      updateCaptureButton();
    }
  });
});
