import { applyTimestamps, formatIso, formatTimezoneOffset, localTimeZoneName } from "./format.js";
import { clearOverrides, effectiveSettings, readDefaults, saveOverride, STORAGE_KEYS } from "./storage.js";
import { ensureTimezoneOption, populateTimezoneSelect, readDisplayConfig } from "./timezone-select.js";
import { showToast } from "../ui/toast.js";

function updatePreview(settings) {
  const preview = document.getElementById("display-preview");
  if (preview) {
    preview.textContent = formatIso(new Date().toISOString(), settings);
  }
}

function syncControls(defaults, settings) {
  const dateFormat = document.getElementById("display-date-format");
  const clockFormat = document.getElementById("display-clock-format");
  const clockFormatRow = document.getElementById("display-clock-format-row");
  const timezoneMode = document.getElementById("display-timezone-mode");
  const timezone = document.getElementById("display-timezone");
  const manualRow = document.querySelector(".manual-timezone");
  const localTzHint = document.getElementById("display-local-timezone");
  const { timezoneLabels } = readDisplayConfig();

  if (dateFormat) {
    dateFormat.value = settings.dateFormat;
  }
  if (clockFormat) {
    clockFormat.value = settings.clockFormat;
  }
  if (clockFormatRow) {
    clockFormatRow.hidden = settings.dateFormat === "iso";
  }
  if (timezoneMode) {
    timezoneMode.value = settings.timezoneMode;
  }
  if (timezone) {
    ensureTimezoneOption(timezone, settings.timezone, timezoneLabels);
    timezone.value = settings.timezone;
  }
  if (manualRow) {
    manualRow.classList.toggle("is-visible", settings.timezoneMode === "manual");
  }
  if (localTzHint) {
    if (settings.timezoneMode === "local") {
      const name = localTimeZoneName();
      const offset = formatTimezoneOffset();
      localTzHint.textContent = offset
        ? `Local Timezone: ${name} (${offset})`
        : `Local Timezone: ${name}`;
      localTzHint.hidden = false;
    } else {
      localTzHint.hidden = true;
    }
  }
}

function refreshUI(defaults, settings) {
  syncControls(defaults, settings);
  applyTimestamps(settings);
  updatePreview(settings);
}

function bindSelect(select, key, defaults, onChange) {
  if (!select) {
    return;
  }
  select.addEventListener("change", () => {
    saveOverride(key, select.value);
    onChange(effectiveSettings(defaults));
    showToast("Display Settings Updated", "success");
  });
}

export function initDisplaySettings() {
  const defaults = readDefaults();
  let settings = effectiveSettings(defaults);
  populateTimezoneSelect(document.getElementById("display-timezone"), settings.timezone);
  refreshUI(defaults, settings);

  const onSettingsChange = (nextSettings) => {
    settings = nextSettings;
    refreshUI(defaults, settings);
  };

  bindSelect(document.getElementById("display-date-format"), STORAGE_KEYS.dateFormat, defaults, onSettingsChange);
  bindSelect(document.getElementById("display-clock-format"), STORAGE_KEYS.clockFormat, defaults, onSettingsChange);
  bindSelect(document.getElementById("display-timezone-mode"), STORAGE_KEYS.timezoneMode, defaults, onSettingsChange);
  bindSelect(document.getElementById("display-timezone"), STORAGE_KEYS.timezone, defaults, onSettingsChange);

  const resetBtn = document.getElementById("display-reset");
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      clearOverrides();
      settings = effectiveSettings(defaults);
      refreshUI(defaults, settings);
      showToast("Display Settings Reset To Defaults", "success");
    });
  }

  setInterval(() => updatePreview(settings), 1000);
}
