export function initDeleteConfirmModal() {
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
