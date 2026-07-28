import { initDisplaySettings } from "./display/panel.js";
import { initDeleteConfirmModal } from "./ui/delete-modal.js";
import { initToastsFromUrl } from "./ui/toast.js";

function init() {
  initToastsFromUrl();
  initDeleteConfirmModal();
  initDisplaySettings();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
