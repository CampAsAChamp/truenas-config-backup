import { initDisplaySettings } from "./display/panel.js";
import { initDeleteConfirmModal } from "./ui/delete-modal.js";
import { initLogsPanel } from "./ui/logs-panel.js";
import { initToastsFromUrl } from "./ui/toast.js";

function init() {
  initToastsFromUrl();
  initDeleteConfirmModal();
  initDisplaySettings();
  initLogsPanel();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
