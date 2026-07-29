#!/usr/bin/env bash
# Start the local dev server with hot reload for Python, templates, and static assets.
#
# Steps:
# 1. Resolve repo root and ensure a virtualenv Python is available.
# 2. Load .env.local when present and set local data directory defaults.
# 3. Seed sample backups/history when local-data is empty.
# 4. Run uvicorn with reload watching app/src/app source, templates, and static files.

set -euo pipefail

log_step() {
  echo "[*] $*" >&2
}

resolve_python() {
  # Inputs: none. Outputs: path to Python interpreter on stdout.
  if [[ -x "${REPO_ROOT}/.venv/bin/python" ]]; then
    echo "${REPO_ROOT}/.venv/bin/python"
    return
  fi
  command -v python3
}

load_env_file() {
  # Inputs: path to env file. Outputs: none. Side effects: exports variables.
  local env_file="$1"
  if [[ ! -f "${env_file}" ]]; then
    return
  fi
  log_step "Loading ${env_file}"
  set -a
  # shellcheck disable=SC1090
  source "${env_file}"
  set +a
}

seed_local_data() {
  # Inputs: none. Outputs: none. Side effects: writes sample data when empty.
  mkdir -p "${BACKUP_DIR}" "${CONFIG_DIR}"
  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/seed-local-data.py" --if-empty
}

run_dev_server() {
  # Inputs: none. Outputs: none. Side effects: starts uvicorn until interrupted.
  exec env PYTHONPATH="${REPO_ROOT}/app/src" "${PYTHON_BIN}" -m uvicorn app.main:app \
    --host 127.0.0.1 \
    --port "${WEB_PORT:-8080}" \
    --reload \
    --reload-dir app/src/app \
    --reload-include '*.py' \
    --reload-include '*.html' \
    --reload-include '*.css' \
    --reload-include '*.js'
}

main() {
  REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  PYTHON_BIN="$(resolve_python)"

  # Step 1: Load local env overrides when available.
  load_env_file "${REPO_ROOT}/.env.local"

  # Step 2: Apply dev-friendly defaults shared with VS Code launch config.
  export DEV_MODE="${DEV_MODE:-true}"
  export BACKUP_DIR="${BACKUP_DIR:-${REPO_ROOT}/local-data/backups}"
  export CONFIG_DIR="${CONFIG_DIR:-${REPO_ROOT}/local-data/config}"
  export TRUENAS_VERIFY_SSL="${TRUENAS_VERIFY_SSL:-false}"

  cd "${REPO_ROOT}"

  # Step 3: Seed sample data for dashboard testing without TrueNAS.
  log_step "Preparing local data"
  seed_local_data

  # Step 4: Start the dev server with hot reload.
  log_step "Starting dev server on http://127.0.0.1:${WEB_PORT:-8080}"
  run_dev_server
}

main "$@"
