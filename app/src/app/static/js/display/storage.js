export const STORAGE_KEYS = {
  dateFormat: "display.dateFormat",
  clockFormat: "display.clockFormat",
  timezoneMode: "display.timezoneMode",
  timezone: "display.timezone",
};

export function readDefaults() {
  const el = document.getElementById("display-defaults");
  if (!el) {
    return { dateFormat: "mm/dd/yy", clockFormat: "12h", timezoneMode: "local", timezone: "" };
  }
  return JSON.parse(el.textContent);
}

function readOverride(key) {
  const value = localStorage.getItem(key);
  return value === null ? null : value;
}

export function effectiveSettings(defaults) {
  return {
    dateFormat: readOverride(STORAGE_KEYS.dateFormat) ?? defaults.dateFormat,
    clockFormat: readOverride(STORAGE_KEYS.clockFormat) ?? defaults.clockFormat ?? "12h",
    timezoneMode: readOverride(STORAGE_KEYS.timezoneMode) ?? defaults.timezoneMode,
    timezone: readOverride(STORAGE_KEYS.timezone) ?? defaults.timezone,
  };
}

export function saveOverride(key, value) {
  localStorage.setItem(key, value);
}

export function clearOverrides() {
  Object.values(STORAGE_KEYS).forEach((key) => localStorage.removeItem(key));
}
