# TrueNAS Config Backup — TODO

Living checklist for this repo. Update as items ship.

## Done

### Real-world validation
- [x] End-to-end install via Custom App on a live TrueNAS SCALE box
- [x] Verify scheduled backup, manual run-now, dashboard download/delete
- [x] Test app upgrade (version bump) — confirm `/config` history and settings survive
- [x] Confirm behavior on target SCALE version(s) (25.04+)

### Backend (`app/`)
- [x] Scheduled backups via APScheduler (cron + run-now)
- [x] TrueNAS `config.save` over WebSocket + `core.download` (SCALE 25.04+ compatible)
- [x] API key authentication (`TRUENAS_URL`, `TRUENAS_API_KEY`, `TRUENAS_VERIFY_SSL`)
- [x] Retention pruning, run-history jsonl log, web dashboard
- [x] Configurable paths via env (`BACKUP_DIR`, `CONFIG_DIR`)
- [x] `GET /healthz` for container health checks
- [x] Unit/integration tests for `app/` (`tests/`, pytest, CI workflow)
- [x] Optional dashboard HTTP Basic Auth (`DASHBOARD_PASSWORD`)
- [x] Backup run lock (no overlapping scheduled + manual runs)
- [x] Startup config validation (cron, retention)
- [x] Post-download tar sanity check
- [x] Webhook notifications (`NOTIFY_WEBHOOK_URL`)
- [x] `GET /readyz` readiness endpoint

### Container
- [x] Dockerfile + `requirements.txt`
- [x] Zscaler root CA support for builds behind corporate TLS inspection

### Catalog app (`ix-dev/community/truenas-config-backup/`)
- [x] `app.yaml`, `ix_values.yaml`, `questions.yaml`, `item.yaml`
- [x] Jinja2 compose template with storage/port helpers
- [x] Catalog README (`ix-dev/community/truenas-config-backup/README.md`)
- [x] Pinned image tag in `ix_values.yaml` (`ghcr.io/campasachamp/truenas-config-backup:0.1.0`)
- [x] Vendored `truenas/apps` library + local render/validate via `.github/scripts/ci.py`
- [x] Root README with local run, build, validate, and Custom App install steps
- [x] App icon in-repo (`icon.svg`) with GitHub raw URL in `app.yaml` / `item.yaml`
- [x] Cron schedule presets (Daily / Weekly / Monthly + custom)

### Release & CI
- [x] GitHub Actions workflow: build and push image to GHCR on release (same workflow as semantic-release; tag hook alone does not fire because GITHUB_TOKEN suppresses downstream workflows)
- [x] Manual re-publish via workflow_dispatch in publish-image.yml
- [x] Ruff lint in CI
- [x] MIT LICENSE, SECURITY.md, pre-commit hooks
- [ ] Backfill GHCR image for `0.1.1` (run Publish image workflow manually after merge)

### Architecture decisions
- [x] Connection via API key + URL (not middleware socket mount)
- [x] Custom App (compose YAML) as the primary distribution path for SCALE 24.10+


## Maybe later

- [ ] Upstream PR to [truenas/apps](https://github.com/truenas/apps) (after real-world mileage)
- [ ] Local socket-mount mode (`/var/run/middlewared.sock`) for zero-config same-box backup — skipped for now due to app-framework restrictions
