(function () {
  const STORAGE_KEYS = {
    dateFormat: "display.dateFormat",
    clockFormat: "display.clockFormat",
    timezoneMode: "display.timezoneMode",
    timezone: "display.timezone",
  };

  const TIMEZONE_OPTIONS = [
    "UTC",
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "Europe/London",
    "Europe/Paris",
    "Asia/Tokyo",
    "Australia/Sydney",
  ];

  const TIMEZONE_LABELS = {
    UTC: "UTC",
    "America/New_York": "Eastern",
    "America/Chicago": "Central",
    "America/Denver": "Mountain",
    "America/Los_Angeles": "Pacific",
    "Europe/London": "UK",
    "Europe/Paris": "Central European",
    "Asia/Tokyo": "Japan",
    "Australia/Sydney": "Sydney",
  };

  const PRESETS = {
    "dd/mm/yy": {
      day: "2-digit",
      month: "2-digit",
      year: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      order: "dmy",
      seconds: false,
    },
    "dd/mm/yyyy": {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      order: "dmy",
      seconds: true,
    },
    "mm/dd/yy": {
      day: "2-digit",
      month: "2-digit",
      year: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      order: "mdy",
      seconds: false,
    },
    "mm/dd/yyyy": {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      order: "mdy",
      seconds: true,
    },
    iso: null,
  };

  function readDefaults() {
    const el = document.getElementById("display-defaults");
    if (!el) {
      return { dateFormat: "dd/mm/yy", clockFormat: "24h", timezoneMode: "local", timezone: "" };
    }
    return JSON.parse(el.textContent);
  }

  function readOverride(key) {
    const value = localStorage.getItem(key);
    return value === null ? null : value;
  }

  function effectiveSettings(defaults) {
    return {
      dateFormat: readOverride(STORAGE_KEYS.dateFormat) ?? defaults.dateFormat,
      clockFormat: readOverride(STORAGE_KEYS.clockFormat) ?? defaults.clockFormat ?? "24h",
      timezoneMode: readOverride(STORAGE_KEYS.timezoneMode) ?? defaults.timezoneMode,
      timezone: readOverride(STORAGE_KEYS.timezone) ?? defaults.timezone,
    };
  }

  function saveOverride(key, value) {
    localStorage.setItem(key, value);
  }

  function clearOverrides() {
    Object.values(STORAGE_KEYS).forEach((key) => localStorage.removeItem(key));
  }

  function resolveTimeZone(settings) {
    if (settings.timezoneMode === "utc") {
      return "UTC";
    }
    if (settings.timezoneMode === "manual") {
      return settings.timezone || "UTC";
    }
    return undefined;
  }

  function localTimeZoneName() {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  }

  function ensureTimezoneOption(select, value) {
    if (!select || !value) {
      return;
    }
    if ([...select.options].some((option) => option.value === value)) {
      return;
    }
    const option = document.createElement("option");
    option.value = value;
    option.textContent = formatRegionLabel(value);
    select.appendChild(option);
  }

  function formatTimezoneOffset(timeZone) {
    try {
      const options = { timeZoneName: "shortOffset" };
      if (timeZone) {
        options.timeZone = timeZone;
      }
      const part = new Intl.DateTimeFormat("en-GB", options)
        .formatToParts(new Date())
        .find((p) => p.type === "timeZoneName");
      if (!part) {
        return "";
      }
      return part.value.replace(/^GMT/i, "UTC");
    } catch {
      return "";
    }
  }

  function formatRegionLabel(timeZone) {
    const name = TIMEZONE_LABELS[timeZone] ?? timeZone;
    const offset = formatTimezoneOffset(timeZone);
    return offset ? `${name} (${offset})` : name;
  }

  function populateTimezoneSelect(select, selectedValue) {
    if (!select) {
      return;
    }
    const selected = selectedValue ?? select.value;
    select.replaceChildren();
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Select region…";
    select.appendChild(placeholder);
    for (const timeZone of TIMEZONE_OPTIONS) {
      const option = document.createElement("option");
      option.value = timeZone;
      option.textContent = formatRegionLabel(timeZone);
      select.appendChild(option);
    }
    if (selected) {
      ensureTimezoneOption(select, selected);
      select.value = selected;
    }
  }

  function uses12HourClock(settings) {
    return settings.clockFormat === "12h";
  }

  function formatDateTimeParts(parts, preset, hour12) {
    const date =
      preset.order === "mdy"
        ? `${parts.month}/${parts.day}/${parts.year}`
        : `${parts.day}/${parts.month}/${parts.year}`;
    let time;
    if (preset.seconds) {
      time = hour12
        ? `${parts.hour}:${parts.minute}:${parts.second} ${parts.dayPeriod.toUpperCase()}`
        : `${parts.hour}:${parts.minute}:${parts.second}`;
    } else {
      time = hour12
        ? `${parts.hour}:${parts.minute} ${parts.dayPeriod.toUpperCase()}`
        : `${parts.hour}:${parts.minute}`;
    }
    return `${date} ${time}`;
  }

  function formatIso(iso, settings) {
    if (!iso) {
      return "";
    }
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) {
      return iso;
    }
    if (settings.dateFormat === "iso") {
      return date.toISOString().replace(".000Z", "+00:00").replace("Z", "+00:00");
    }
    const preset = PRESETS[settings.dateFormat] || PRESETS["dd/mm/yy"];
    const tz = resolveTimeZone(settings);
    const hour12 = uses12HourClock(settings);
    const fmt = new Intl.DateTimeFormat("en-GB", {
      day: preset.day,
      month: preset.month,
      year: preset.year,
      hour: preset.hour,
      minute: preset.minute,
      second: preset.second,
      hour12,
      timeZone: tz,
    });
    const parts = Object.fromEntries(fmt.formatToParts(date).map((p) => [p.type, p.value]));
    return formatDateTimeParts(parts, preset, hour12);
  }

  function applyTimestamps(settings) {
    document.querySelectorAll(".timestamp[data-iso]").forEach((el) => {
      el.textContent = formatIso(el.dataset.iso, settings);
    });
  }

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
      ensureTimezoneOption(timezone, settings.timezone);
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

  function notifyDisplaySettingsChanged(message) {
    if (typeof window.showToast === "function") {
      window.showToast(message, "success");
    }
  }

  function init() {
    const defaults = readDefaults();
    let settings = effectiveSettings(defaults);
    populateTimezoneSelect(document.getElementById("display-timezone"), settings.timezone);
    refreshUI(defaults, settings);

    const dateFormat = document.getElementById("display-date-format");
    const clockFormat = document.getElementById("display-clock-format");
    const timezoneMode = document.getElementById("display-timezone-mode");
    const timezone = document.getElementById("display-timezone");
    const resetBtn = document.getElementById("display-reset");

    if (dateFormat) {
      dateFormat.addEventListener("change", () => {
        saveOverride(STORAGE_KEYS.dateFormat, dateFormat.value);
        settings = effectiveSettings(defaults);
        refreshUI(defaults, settings);
        notifyDisplaySettingsChanged("Display Settings Updated");
      });
    }

    if (clockFormat) {
      clockFormat.addEventListener("change", () => {
        saveOverride(STORAGE_KEYS.clockFormat, clockFormat.value);
        settings = effectiveSettings(defaults);
        refreshUI(defaults, settings);
        notifyDisplaySettingsChanged("Display Settings Updated");
      });
    }

    if (timezoneMode) {
      timezoneMode.addEventListener("change", () => {
        saveOverride(STORAGE_KEYS.timezoneMode, timezoneMode.value);
        settings = effectiveSettings(defaults);
        refreshUI(defaults, settings);
        notifyDisplaySettingsChanged("Display Settings Updated");
      });
    }

    if (timezone) {
      timezone.addEventListener("change", () => {
        saveOverride(STORAGE_KEYS.timezone, timezone.value);
        settings = effectiveSettings(defaults);
        refreshUI(defaults, settings);
        notifyDisplaySettingsChanged("Display Settings Updated");
      });
    }

    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        clearOverrides();
        settings = effectiveSettings(defaults);
        refreshUI(defaults, settings);
        notifyDisplaySettingsChanged("Display Settings Reset To Defaults");
      });
    }

    setInterval(() => updatePreview(settings), 1000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
