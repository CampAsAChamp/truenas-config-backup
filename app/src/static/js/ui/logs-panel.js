import { applyTimestamps, formatIso } from "../display/format.js";
import { effectiveSettings, readDefaults } from "../display/storage.js";

const POLL_INTERVAL_MS = 5000;
const LEVEL_RANK = {
  DEBUG: 0,
  INFO: 1,
  WARNING: 2,
  ERROR: 3,
  CRITICAL: 4,
};

function levelClass(level) {
  return (level || "INFO").toLowerCase();
}

function passesFilter(level, filter) {
  const rank = LEVEL_RANK[level] ?? LEVEL_RANK.INFO;
  if (filter === "all") {
    return true;
  }
  if (filter === "info") {
    return rank >= LEVEL_RANK.INFO;
  }
  if (filter === "warning") {
    return rank >= LEVEL_RANK.WARNING;
  }
  if (filter === "error") {
    return rank >= LEVEL_RANK.ERROR;
  }
  return true;
}

function formatEntryTimestamp(iso, settings) {
  if (!iso) {
    return "";
  }
  return formatIso(iso, settings);
}

function renderEntries(entries, filter) {
  const list = document.getElementById("logs-list");
  const empty = document.getElementById("logs-empty");
  if (!list || !empty) {
    return;
  }

  const settings = effectiveSettings(readDefaults());
  const filtered = entries.filter((entry) => passesFilter(entry.level, filter));

  list.replaceChildren();
  if (filtered.length === 0) {
    empty.hidden = false;
    return;
  }

  empty.hidden = true;
  for (const entry of filtered) {
    const item = document.createElement("li");
    item.className = `log-entry log-entry--${levelClass(entry.level)}`;

    const timestamp = document.createElement("span");
    timestamp.className = "log-entry__timestamp timestamp";
    if (entry.timestamp) {
      timestamp.dataset.iso = entry.timestamp;
      timestamp.textContent = formatEntryTimestamp(entry.timestamp, settings);
    }

    const level = document.createElement("span");
    level.className = "log-entry__level";
    level.textContent = entry.level || "INFO";

    const message = document.createElement("span");
    message.className = "log-entry__message";
    message.textContent = entry.message;

    item.append(timestamp, level, message);
    list.append(item);
  }

  applyTimestamps(settings);
}

async function fetchLogs() {
  const response = await fetch("/api/logs");
  if (!response.ok) {
    return null;
  }
  const data = await response.json();
  return data.entries || [];
}

function shouldPoll() {
  return document.visibilityState === "visible";
}

export function initLogsPanel() {
  const panel = document.getElementById("logs-panel");
  const refreshButton = document.getElementById("logs-refresh");
  const filterSelect = document.getElementById("logs-level-filter");
  const autoScrollCheckbox = document.getElementById("logs-auto-scroll");
  const viewport = document.getElementById("logs-viewport");
  if (!panel) {
    return;
  }

  let pollTimer = null;

  async function refresh() {
    const filter = filterSelect?.value || "all";
    const entries = await fetchLogs();
    if (entries === null) {
      return;
    }
    renderEntries(entries, filter);
    if (autoScrollCheckbox?.checked && viewport) {
      viewport.scrollTop = viewport.scrollHeight;
    }
  }

  function schedulePoll() {
    if (pollTimer !== null) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
    if (shouldPoll()) {
      pollTimer = setInterval(refresh, POLL_INTERVAL_MS);
    }
  }

  refreshButton?.addEventListener("click", refresh);
  filterSelect?.addEventListener("change", refresh);

  document.addEventListener("visibilitychange", () => {
    if (shouldPoll()) {
      refresh();
      schedulePoll();
    } else if (pollTimer !== null) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  });

  refresh();
  schedulePoll();
}
