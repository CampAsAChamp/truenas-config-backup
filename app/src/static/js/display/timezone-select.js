import { formatTimezoneOffset } from "./format.js";

function readDisplayConfig() {
  const el = document.getElementById("display-config");
  if (!el) {
    return { timezoneOptions: ["UTC"], timezoneLabels: { UTC: "UTC" } };
  }
  return JSON.parse(el.textContent);
}

function formatRegionLabel(timeZone, timezoneLabels) {
  const name = timezoneLabels[timeZone] ?? timeZone;
  const offset = formatTimezoneOffset(timeZone);
  return offset ? `${name} (${offset})` : name;
}

function ensureTimezoneOption(select, value, timezoneLabels) {
  if (!select || !value) {
    return;
  }
  if ([...select.options].some((option) => option.value === value)) {
    return;
  }
  const option = document.createElement("option");
  option.value = value;
  option.textContent = formatRegionLabel(value, timezoneLabels);
  select.appendChild(option);
}

export function populateTimezoneSelect(select, selectedValue) {
  if (!select) {
    return;
  }
  const { timezoneOptions, timezoneLabels } = readDisplayConfig();
  const selected = selectedValue ?? select.value;
  select.replaceChildren();
  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = "Select region…";
  select.appendChild(placeholder);
  for (const timeZone of timezoneOptions) {
    const option = document.createElement("option");
    option.value = timeZone;
    option.textContent = formatRegionLabel(timeZone, timezoneLabels);
    select.appendChild(option);
  }
  if (selected) {
    ensureTimezoneOption(select, selected, timezoneLabels);
    select.value = selected;
  }
}

export { ensureTimezoneOption, formatRegionLabel, readDisplayConfig };
