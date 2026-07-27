# TrueNAS Config Backup — TODO

Living checklist for this repo. Update as items ship.

## Remaining

### Release & CI
- [ ] GitHub Actions workflow: build and push image to GHCR on version tag
- [ ] Publish `0.1.0` (or next tag) to GHCR so installs pull a real image
- [ ] Tag/release process documented (bump `app_version` in `app.yaml`, image tag in `ix_values.yaml`, git tag)

### Real-world validation
- [ ] End-to-end install from custom catalog on a live TrueNAS SCALE box
- [ ] Verify scheduled backup, manual run-now, dashboard download/delete
- [ ] Test app upgrade (version bump) — confirm `/config` history and settings survive
- [ ] Confirm behavior on target SCALE version(s) (25.04+)

## Done

### Backend (`app/`)
- [x] Scheduled backups via APScheduler (cron + run-now)
- [x] TrueNAS `config.save` over WebSocket + `core.download` (SCALE 25.04+ compatible)
- [x] API key authentication (`TRUENAS_URL`, `TRUENAS_API_KEY`, `TRUENAS_VERIFY_SSL`)
- [x] Retention pruning, run-history jsonl log, web dashboard
- [x] Configurable paths via env (`BACKUP_DIR`, `CONFIG_DIR`)
- [x] `GET /healthz` for container health checks
- [x] Unit/integration tests for `app/` (`tests/`, pytest, CI workflow)

### Container
- [x] Dockerfile + `requirements.txt`
- [x] Zscaler root CA support for builds behind corporate TLS inspection

### Catalog app (`ix-dev/community/truenas-config-backup/`)
- [x] `app.yaml`, `ix_values.yaml`, `questions.yaml`, `item.yaml`
- [x] Jinja2 compose template with storage/port helpers
- [x] Catalog README (`ix-dev/community/truenas-config-backup/README.md`)
- [x] Pinned image tag in `ix_values.yaml` (`ghcr.io/campasachamp/truenas-config-backup:0.1.0`)
- [x] Vendored `truenas/apps` library + local render/validate via `.github/scripts/ci.py`
- [x] Root README with local run, build, validate, and custom-catalog install steps
- [x] App icon in-repo (`icon.svg`) with GitHub raw URL in `app.yaml` / `item.yaml`

### Architecture decisions
- [x] Connection via API key + URL (not middleware socket mount)
- [x] Self-hosted custom catalog as the primary distribution path


## Maybe later

- [ ] Upstream PR to [truenas/apps](https://github.com/truenas/apps) (after real-world mileage)
- [ ] Friendlier cron UX (Daily/Weekly/Monthly presets + custom escape hatch)
- [ ] Local socket-mount mode (`/var/run/middlewared.sock`) for zero-config same-box backup — skipped for now due to app-framework restrictions
- [ ] Scope/minimum-privilege API key docs (recommend `config.save`-only key if TrueNAS supports method scoping)
