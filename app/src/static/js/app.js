import { initConfigSettings } from "./ui/config-panel.js";
import { initDisplaySettings } from "./display/panel.js";
import { initDeleteConfirmModal } from "./ui/delete-modal.js";
import { initLogsPanel } from "./ui/logs-panel.js";
import { initToastsFromUrl } from "/static/js/ui/toast.js";

function init() {
  initToastsFromUrl();
  initDeleteConfirmModal();
  initDisplaySettings();
  initLogsPanel();
  initConfigSettings();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
