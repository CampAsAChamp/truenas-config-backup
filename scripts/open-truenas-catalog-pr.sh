#!/usr/bin/env bash
# Open a PR to truenas/apps adding the community catalog definition.
#
# Run from a machine with GitHub push access to github.com (not blocked by corp hooks).
#
# Steps:
#   1. Fork truenas/apps (if needed)
#   2. Clone fork, copy ix-dev/community/truenas-config-backup (no templates/rendered/)
#   3. Commit, push branch, open PR linked to issue #5473

set -euo pipefail

log_step() { echo "[*] $*" >&2; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_SRC="${REPO_ROOT}/ix-dev/community/truenas-config-backup"
BRANCH="add-truenas-config-backup"
WORK_DIR="${TMPDIR:-/tmp}/truenas-apps-pr-$$"

do_clone_fork() {
  log_step "Forking truenas/apps (no-op if fork already exists)..."
  GH_HOST=github.com gh repo fork truenas/apps --clone=false 2>/dev/null || true

  log_step "Cloning CampAsAChamp/apps..."
  git clone --depth 1 "https://github.com/CampAsAChamp/apps.git" "${WORK_DIR}"
}

do_copy_app() {
  log_step "Copying catalog app (excluding templates/rendered/)..."
  rsync -a --exclude 'templates/rendered' "${APP_SRC}/" "${WORK_DIR}/ix-dev/community/truenas-config-backup/"
}

do_commit_push() {
  cd "${WORK_DIR}"
  git checkout -b "${BRANCH}"
  git add ix-dev/community/truenas-config-backup
  git commit -m "$(cat <<'EOF'
feat(community): add TrueNAS Config Backup app

Adds truenas-config-backup to the community train. Schedules and manages
TrueNAS configuration backups via the config.save WebSocket API with
retention, run history, and a web dashboard.

Closes #5473
EOF
)"
  git push -u origin "${BRANCH}"
}

do_open_pr() {
  GH_HOST=github.com gh pr create \
    --repo truenas/apps \
    --head "CampAsAChamp:${BRANCH}" \
    --base master \
    --title "feat(community): add TrueNAS Config Backup app" \
    --body-file "${REPO_ROOT}/scripts/truenas-catalog-pr-body.md"
}

main() {
  log_step "Step 1/4: Clone fork"
  do_clone_fork
  log_step "Step 2/4: Copy app definition"
  do_copy_app
  log_step "Step 3/4: Commit and push"
  do_commit_push
  log_step "Step 4/4: Open pull request"
  do_open_pr
  log_step "Done. PR URL printed above."
}

main "$@"
