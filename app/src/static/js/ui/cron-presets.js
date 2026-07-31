/** Common cron presets for the configuration panel. */
export const CRON_PRESETS = [
  { id: "manual", label: "Manual only (no schedule)", cron: "" },
  { id: "every_minute", label: "Every minute", cron: "* * * * *" },
  { id: "every_hour", label: "Every hour", cron: "0 * * * *" },
  { id: "daily", label: "Daily at 03:00", cron: "0 3 * * *" },
  { id: "weekly", label: "Weekly on Sunday at 03:00", cron: "0 3 * * 0" },
  { id: "custom", label: "Custom expression", cron: null },
];

export function presetIdForCron(cronSchedule) {
  const normalized = cronSchedule.trim();
  if (!normalized) {
    return "manual";
  }
  const match = CRON_PRESETS.find((preset) => preset.cron !== null && preset.cron === normalized);
  return match ? match.id : "custom";
}

export function cronForPresetId(presetId, customCron = "") {
  const preset = CRON_PRESETS.find((entry) => entry.id === presetId);
  if (!preset || preset.id === "custom") {
    return customCron.trim();
  }
  return preset.cron ?? "";
}
