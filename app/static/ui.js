(function () {
  const TOAST_DURATION_MS = 4000;

  const TOAST_MESSAGES = {
    "backup-success": (msg) => `Backup saved as ${msg}`,
    "backup-failure": (msg) => `Backup failed: ${msg}`,
    "backup-deleted": (msg) => `Deleted ${msg}`,
    "backup-delete-failed": (msg) => `Could not delete ${msg || "backup"}`,
    "run-deleted": () => "Run removed",
    "run-delete-failed": () => "Could not remove run",
  };

  const TOAST_ICONS = {
    success: `
      <circle cx="12" cy="12" r="10"/>
      <path d="m9 12 2 2 4-4"/>
    `,
    error: `
      <circle cx="12" cy="12" r="10"/>
      <path d="m15 9-6 6"/>
      <path d="m9 9 6 6"/>
    `,
    info: `
      <circle cx="12" cy="12" r="10"/>
      <path d="M12 16v-4"/>
      <path d="M12 8h.01"/>
    `,
  };

  function createToastIcon(variant) {
    const icon = document.createElement("span");
    icon.className = "toast__icon";
    icon.setAttribute("aria-hidden", "true");
    icon.innerHTML = `
      <svg class="icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        ${TOAST_ICONS[variant] || TOAST_ICONS.info}
      </svg>
    `;
    return icon;
  }

  function showToast(message, variant) {
    const container = document.getElementById("toast-container");
    if (!container) {
      return;
    }

    const toastVariant = variant || "info";
    const toast = document.createElement("div");
    toast.className = `toast toast--${toastVariant}`;
    toast.setAttribute("role", "status");

    const messageEl = document.createElement("span");
    messageEl.className = "toast__message";
    messageEl.textContent = message;

    toast.append(createToastIcon(toastVariant), messageEl);
    container.appendChild(toast);

    requestAnimationFrame(() => {
      toast.classList.add("toast--visible");
    });

    window.setTimeout(() => {
      toast.classList.remove("toast--visible");
      toast.classList.add("toast--leaving");
      toast.addEventListener(
        "transitionend",
        () => {
          toast.remove();
        },
        { once: true },
      );
      window.setTimeout(() => toast.remove(), 500);
    }, TOAST_DURATION_MS);
  }

  function initToastsFromUrl() {
    const params = new URLSearchParams(window.location.search);
    const toastKey = params.get("toast");
    if (!toastKey) {
      return;
    }

    const msg = params.get("msg") || "";
    const builder = TOAST_MESSAGES[toastKey];
    if (builder) {
      const variant = toastKey.includes("failure") || toastKey.includes("failed") ? "error" : "success";
      showToast(builder(msg), variant);
    }

    params.delete("toast");
    params.delete("msg");
    const remaining = params.toString();
    const newUrl = remaining
      ? `${window.location.pathname}?${remaining}`
      : window.location.pathname;
    history.replaceState(null, "", newUrl);
  }

  function initDeleteConfirmModal() {
    const dialog = document.getElementById("delete-confirm-modal");
    if (!dialog) {
      return;
    }

    const titleEl = document.getElementById("delete-confirm-title");
    const backupMsgEl = document.getElementById("delete-confirm-backup-msg");
    const historyMsgEl = document.getElementById("delete-confirm-history-msg");
    const filenameEl = document.getElementById("delete-confirm-filename");
    const cancelBtn = document.getElementById("delete-confirm-cancel");
    const confirmBtn = document.getElementById("delete-confirm-submit");
    let pendingForm = null;
    let triggerButton = null;

    function openModal(form, button) {
      pendingForm = form;
      triggerButton = button;
      const hasBackup = form.dataset.deleteHasBackup === "true";
      const filename = form.dataset.deleteFilename || "";

      if (titleEl) {
        titleEl.textContent = hasBackup ? "Delete Backup?" : "Remove Run?";
      }
      if (backupMsgEl && historyMsgEl) {
        const showBackupMsg = hasBackup && filename;
        backupMsgEl.hidden = !showBackupMsg;
        historyMsgEl.hidden = showBackupMsg;
      }
      if (filenameEl) {
        filenameEl.textContent = filename;
      }
      dialog.showModal();
    }

    function closeModal() {
      if (dialog.open) {
        dialog.close();
      }
    }

    dialog.addEventListener("close", () => {
      pendingForm = null;
      if (triggerButton) {
        triggerButton.focus();
        triggerButton = null;
      }
    });

    document.querySelectorAll(".delete-run-form, .delete-backup-form").forEach((form) => {
      form.addEventListener("submit", (event) => {
        if (form.dataset.confirmed === "true") {
          return;
        }
        event.preventDefault();
        const button = form.querySelector('button[type="submit"]');
        openModal(form, button);
      });
    });

    cancelBtn?.addEventListener("click", closeModal);

    confirmBtn?.addEventListener("click", () => {
      if (!pendingForm) {
        return;
      }
      const form = pendingForm;
      closeModal();
      form.dataset.confirmed = "true";
      form.requestSubmit();
    });

    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) {
        closeModal();
      }
    });
  }

  function init() {
    initToastsFromUrl();
    initDeleteConfirmModal();
  }

  window.showToast = showToast;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
