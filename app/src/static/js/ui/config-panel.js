import { formatIso } from "../display/format.js";
import { effectiveSettings, readDefaults } from "../display/storage.js";
import { cronForPresetId, presetIdForCron } from "./cron-presets.js";
import { showToast } from "/static/js/ui/toast.js";

let savedPayload = null;
let baselineReady = false;

function debounce(fn, delayMs) {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delayMs);
  };
}

function setScheduleFieldsVisible(isManual) {
  for (const id of ["config-cron-schedule-field", "config-next-run-field"]) {
    const field = document.getElementById(id);
    if (!field) {
      continue;
    }
    field.hidden = isManual;
    field.classList.toggle("is-schedule-hidden", isManual);
  }
}

function currentCronSchedule() {
  const presetSelect = document.getElementById("config-cron-preset");
  const cronInput = document.getElementById("config-cron-schedule");
  if (!presetSelect || !cronInput) {
    return "";
  }
  return cronForPresetId(presetSelect.value, cronInput.value);
}

function formDataToPayload(form) {
  return {
    cron_schedule: currentCronSchedule(),
    retention_count: Number.parseInt(form.retention_count.value, 10),
    include_secret_seed: form.include_secret_seed.checked,
    include_pool_keys: form.include_pool_keys.checked,
    include_root_authorized_keys: form.include_root_authorized_keys.checked,
    notify_webhook_url: form.notify_webhook_url.value.trim(),
    notify_on_success: form.notify_on_success.checked,
  };
}

function normalizePayload(payload) {
  return JSON.stringify({
    cron_schedule: payload.cron_schedule ?? "",
    retention_count: Number.isFinite(payload.retention_count) ? payload.retention_count : 0,
    include_secret_seed: Boolean(payload.include_secret_seed),
    include_pool_keys: Boolean(payload.include_pool_keys),
    include_root_authorized_keys: Boolean(payload.include_root_authorized_keys),
    notify_webhook_url: (payload.notify_webhook_url ?? "").trim(),
    notify_on_success: Boolean(payload.notify_on_success),
  });
}

function setSavedBaseline(form) {
  savedPayload = normalizePayload(formDataToPayload(form));
  baselineReady = true;
}

function updateDirtyState(form) {
  const unsavedHint = document.getElementById("config-unsaved-hint");
  const saveButton = document.getElementById("config-save-settings");
  const dirty = baselineReady && normalizePayload(formDataToPayload(form)) !== savedPayload;

  saveButton?.classList.toggle("button--primary", dirty);
  if (unsavedHint) {
    unsavedHint.classList.toggle("is-visible", dirty);
    unsavedHint.setAttribute("aria-hidden", dirty ? "false" : "true");
  }
}

function updateNextRun(nextRunIso, invalidMessage = "") {
  const valueEl = document.getElementById("config-next-run-value");
  if (!valueEl) {
    return;
  }

  valueEl.classList.remove("config-field__preview--invalid", "config-field__preview--muted");

  if (invalidMessage) {
    valueEl.textContent = invalidMessage;
    valueEl.classList.add("config-field__preview--invalid");
    return;
  }

  if (nextRunIso) {
    const settings = effectiveSettings(readDefaults());
    const timestamp = document.createElement("span");
    timestamp.className = "timestamp";
    timestamp.dataset.iso = nextRunIso;
    timestamp.textContent = formatIso(nextRunIso, settings);
    valueEl.replaceChildren(timestamp);
    return;
  }

  valueEl.textContent = "not scheduled";
  valueEl.classList.add("config-field__preview--muted");
}

async function refreshNextRunPreview() {
  const presetSelect = document.getElementById("config-cron-preset");
  if (!presetSelect || presetSelect.value === "manual") {
    return;
  }

  const cronSchedule = currentCronSchedule();
  if (!cronSchedule) {
    updateNextRun("");
    return;
  }

  try {
    const params = new URLSearchParams({ cron_schedule: cronSchedule });
    const response = await fetch(`/api/settings/next-run?${params.toString()}`);
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      updateNextRun("", body.detail || "invalid schedule");
      return;
    }
    updateNextRun(body.next_run_iso);
  } catch {
    // Ignore preview failures; saved settings remain unchanged.
  }
}

function syncCronPresetUi() {
  const presetSelect = document.getElementById("config-cron-preset");
  const cronInput = document.getElementById("config-cron-schedule");
  const cronDisplay = document.getElementById("config-cron-schedule-display");
  if (!presetSelect || !cronInput || !cronDisplay) {
    return;
  }

  const presetId = presetSelect.value;
  const isManual = presetId === "manual";
  const isCustom = presetId === "custom";
  const cronValue = cronForPresetId(presetId, cronInput.value);

  setScheduleFieldsVisible(isManual);

  if (isManual) {
    cronInput.value = "";
    return;
  }

  cronInput.hidden = !isCustom;
  cronDisplay.hidden = isCustom;

  if (isCustom) {
    cronInput.placeholder = "e.g. 0 3 * * 0";
    void refreshNextRunPreview();
    return;
  }

  cronInput.value = cronValue;
  cronDisplay.textContent = cronValue;
  void refreshNextRunPreview();
}

export function initConfigSettings() {
  const form = document.getElementById("config-settings-form");
  if (!form || form.dataset.configSettingsInit === "true") {
    return;
  }
  form.dataset.configSettingsInit = "true";

  const presetSelect = document.getElementById("config-cron-preset");
  const cronInput = document.getElementById("config-cron-schedule");
  if (presetSelect && cronInput) {
    presetSelect.value = presetIdForCron(cronInput.value);
    syncCronPresetUi();
    presetSelect.addEventListener("change", () => {
      syncCronPresetUi();
      updateDirtyState(form);
    });
    cronInput.addEventListener("input", debounce(() => {
      if (presetSelect.value === "custom") {
        void refreshNextRunPreview();
      }
      updateDirtyState(form);
    }, 300));
  }

  setSavedBaseline(form);
  updateDirtyState(form);
  form.addEventListener("input", () => updateDirtyState(form));
  form.addEventListener("change", () => updateDirtyState(form));

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const response = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formDataToPayload(form)),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(body.detail || "Failed to save settings");
      }
      if ("next_run_iso" in body) {
        updateNextRun(body.next_run_iso);
      }
      syncCronPresetUi();
      setSavedBaseline(form);
      updateDirtyState(form);
      showToast("Settings saved", "success");
    } catch (error) {
      showToast(error.message || "Failed to save settings", "error");
    }
  });
}
