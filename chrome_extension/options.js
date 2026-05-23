function setStatus(text, kind) {
  const el = document.getElementById("status");
  el.textContent = text || "";
  el.classList.remove("success", "error");
  if (kind) el.classList.add(kind);
}

function load() {
  chrome.storage.local.get(
    ["apiBaseUrl", "apiToken", "username", "password"],
    (cfg) => {
      cfg = cfg || {};
      document.getElementById("api-base").value = cfg.apiBaseUrl || "";
      document.getElementById("api-token").value = cfg.apiToken || "";
      document.getElementById("username").value = cfg.username || "";
      document.getElementById("password").value = cfg.password || "";
    },
  );
}

function save() {
  const apiBaseUrl = document.getElementById("api-base").value.trim();
  const apiToken = document.getElementById("api-token").value.trim();
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;

  if (!apiBaseUrl) {
    setStatus("Set the Richtato API base URL.", "error");
    return;
  }
  if (!apiToken && !(username && password)) {
    setStatus("Provide either an API token or username + password.", "error");
    return;
  }

  chrome.storage.local.set(
    { apiBaseUrl, apiToken, username, password },
    () => setStatus("Saved.", "success"),
  );
}

document.addEventListener("DOMContentLoaded", () => {
  load();
  document.getElementById("save").addEventListener("click", save);
});
