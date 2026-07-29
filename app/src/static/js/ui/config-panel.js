import { formatIso } from "../display/format.js";
import { effectiveSettings, readDefaults } from "../display/storage.js";
import { showToast } from "/static/js/ui/toast.js";

function formDataToPayload(form) {
  return {
    cron_schedule: form.cron_schedule.value.trim(),
    retention_count: Number.parseInt(form.retention_count.value, 10),
    include_secret_seed: form.include_secret_seed.checked,
    include_pool_keys: form.include_pool_keys.checked,
    include_root_authorized_keys: form.include_root_authorized_keys.checked,
    notify_webhook_url: form.notify_webhook_url.value.trim(),
    notify_on_success: form.notify_on_success.checked,
  };
}

function updateNextRun(nextRunIso) {
  const valueEl = document.getElementById("config-next-run-value");
  if (!valueEl) {
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
}

export function initConfigSettings() {
  const form = document.getElementById("config-settings-form");
  if (!form) {
    return;
  }

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
      showToast("Settings saved", "success");
    } catch (error) {
      showToast(error.message || "Failed to save settings", "error");
    }
  });
}
