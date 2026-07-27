# TrueNAS Config Backup

Scheduled backups of a TrueNAS system's configuration, downloaded via the TrueNAS
API, with retention pruning, run-history logging, and a small web dashboard.
Ships as an installable TrueNAS SCALE catalog app.

## What it does

- Calls `config.save` over the TrueNAS JSON-RPC WebSocket API (via `core.download`)
  to produce a config backup tar, authenticating with an API key.
- Runs on a cron schedule (APScheduler) and supports an on-demand "run now".
- Prunes old backups down to a configurable retention count.
- Logs every run (success/failure) to a jsonl history file.
- Serves a dashboard to view/download/delete backups and see run history.
- Exposes `GET /healthz` for container health checks.

Note: TrueNAS SCALE 25.04 deprecated the old synchronous REST config-save endpoint
(removed in 26). This app uses the current WebSocket + `core.download` flow instead.

## Repository layout

```
app/                              FastAPI backend (the container's application code)
Dockerfile, requirements.txt      Container build
ix-dev/community/truenas-config-backup/
                                  TrueNAS catalog app definition (app.yaml, questions.yaml,
                                  ix_values.yaml, Jinja2 compose template) — installable via
                                  Apps → Manage Catalogs in TrueNAS SCALE
.github/scripts/, library/        Vendored truenas/apps tooling used to render/validate the
                                  catalog app definition locally (see below)
```

## Running the backend locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

BACKUP_DIR=/tmp/backups CONFIG_DIR=/tmp/config \
TRUENAS_URL=https://127.0.0.1 TRUENAS_API_KEY=your-api-key \
  uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Then visit `http://localhost:8080`.

### Configuration (env vars)

| Variable | Default | Description |
|---|---|---|
| `TRUENAS_URL` | `https://127.0.0.1` | Base URL of the TrueNAS system to back up |
| `TRUENAS_API_KEY` | *(required)* | API key for that TrueNAS system |
| `TRUENAS_VERIFY_SSL` | `false` | Verify the TrueNAS TLS certificate |
| `BACKUP_DIR` | `/backups` | Where downloaded backup tars are stored |
| `CONFIG_DIR` | `/config` | Where the run-history log is stored |
| `CRON_SCHEDULE` | `0 3 * * 0` | Cron expression for the scheduled backup |
| `RETENTION_COUNT` | `8` | Number of backups to keep before pruning |
| `INCLUDE_SECRET_SEED` | `true` | Include the password secret seed in the backup |
| `WEB_PORT` | `8080` | Port the dashboard listens on |

## Building the container

```bash
docker build -t truenas-config-backup .
```

## Validating the catalog app definition

The catalog app under `ix-dev/community/truenas-config-backup/` follows the
[truenas/apps](https://github.com/truenas/apps) format. To render/validate it
locally (requires a running container runtime — Docker or Podman):

```bash
source .venv/bin/activate
pip install pyyaml psutil pytest pytest-cov bcrypt pydantic

python .github/scripts/ci.py --app truenas-config-backup --train community \
  --test-file basic-values.yaml --render-only=true
```

## Installing on TrueNAS SCALE

This app isn't in the official catalog. To use it, add this repository as a
custom catalog: **Apps → Discover Apps → Manage Catalogs → Add Catalog**, then
point it at this repo's URL. The app will then appear under Discover Apps.
