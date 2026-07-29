/** Intl-based date/time formatting. Mirrors app/datetime_display.py logic. */

export const PRESETS = {
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

export function resolveTimeZone(settings) {
  if (settings.timezoneMode === "utc") {
    return "UTC";
  }
  if (settings.timezoneMode === "manual") {
    return settings.timezone || "UTC";
  }
  return undefined;
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

export function formatIso(iso, settings, { includeSeconds = false } = {}) {
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
  const basePreset = PRESETS[settings.dateFormat] || PRESETS["mm/dd/yy"];
  const preset =
    includeSeconds && !basePreset.seconds
      ? { ...basePreset, second: "2-digit", seconds: true }
      : basePreset;
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

export function applyTimestamps(settings) {
  document.querySelectorAll(".timestamp[data-iso]").forEach((el) => {
    const includeSeconds = el.dataset.seconds === "true";
    el.textContent = formatIso(el.dataset.iso, settings, { includeSeconds });
  });
}

export function localTimeZoneName() {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}

export function formatTimezoneOffset(timeZone) {
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
