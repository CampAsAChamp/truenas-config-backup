# Configuration

Settings come from **environment variables** (container / compose) and, for backup and
notification tuning, a **`settings.json`** file in `CONFIG_DIR` that you can edit from the
dashboard. Connection secrets and paths always come from the environment.

## Minimum required (install)

| Variable | Description |
|---|---|
| `TRUENAS_URL` | Base URL of the TrueNAS system to back up (`https://…`) |
| `TRUENAS_API_KEY` | API key for that system |
| `DASHBOARD_PASSWORD` | Password for the dashboard login page |

Everything else has sensible defaults. The TrueNAS Custom App wizard groups settings into
Connection, Backups, Dashboard, Notifications, and Advanced sections.

## Connection (environment only)

| Variable | Default | Description |
|---|---|---|
| `TRUENAS_URL` | `https://127.0.0.1` | Base URL of the TrueNAS system to back up |
| `TRUENAS_API_KEY` | *(required)* | API key for that TrueNAS system |
| `TRUENAS_VERIFY_SSL` | `false` | Verify the TrueNAS TLS certificate |
| `DASHBOARD_PASSWORD` | *(required)* | Password for the dashboard login page |

## Backups

Persisted in `settings.json` (editable on the dashboard). Initial values come from the
environment on first boot.

| Variable | Default | Description |
|---|---|---|
| `CRON_SCHEDULE` | *(none)* | Optional cron expression for scheduled backups; omit for manual-only |
| `RETENTION_COUNT` | `8` | Number of backups to keep before pruning |
| `INCLUDE_SECRET_SEED` | `true` | Include the password secret seed in the backup |
| `INCLUDE_POOL_KEYS` | `false` | Include pool encryption keys in the backup |
| `INCLUDE_ROOT_AUTHORIZED_KEYS` | `false` | Include root SSH authorized keys in the backup |

## Notifications

Persisted in `settings.json`. Discord webhook URLs are detected automatically; set
`NOTIFY_PROVIDER=discord` via compose only when auto-detection is insufficient.

| Variable | Default | Description |
|---|---|---|
| `NOTIFY_WEBHOOK_URL` | *(none)* | Optional URL to POST backup event notifications |
| `NOTIFY_PROVIDER` | `generic` | Payload format: `generic` or `discord` (auto-detected from Discord URLs) |
| `NOTIFY_ON_SUCCESS` | `false` | Also notify the webhook when backups succeed |

## Display (app defaults / dashboard override)

These environment variables set server-side defaults for timestamp rendering. The dashboard
**Display settings** panel lets each browser override date format and timezone; overrides are
stored in `localStorage`. They are not exposed in the TrueNAS install wizard.

| Variable | Default | Description |
|---|---|---|
| `DISPLAY_DATE_FORMAT` | `mm/dd/yy` | Default timestamp format (`dd/mm/yy`, `iso`, etc.) |
| `DISPLAY_CLOCK_FORMAT` | `12h` | Default clock style (`24h` or `12h`) |
| `DISPLAY_TIMEZONE_MODE` | `local` | Default timezone mode (`local`, `utc`, or `manual`) |
| `DISPLAY_TIMEZONE` | *(empty)* | IANA timezone when mode is `manual` |

## Infrastructure (environment only)

| Variable | Default | Description |
|---|---|---|
| `BACKUP_DIR` | `/backups` | Where downloaded backup tars are stored |
| `CONFIG_DIR` | `/config` | Where run history and `settings.json` are stored |
| `WEB_PORT` | `8080` | Port the dashboard listens on |
| `DASHBOARD_PAGE_SIZE` | `20` | Number of backup runs shown per dashboard page |
| `HEALTH_CHECK_TRUENAS` | `false` | When true, `/readyz` probes TrueNAS connectivity (slower) |
| `DEV_MODE` | `false` | Development-only behavior (local reload, cache busting) |

## Logging (environment only, advanced)

| Variable | Default | Description |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Application log verbosity |
| `LOG_FILE` | `{CONFIG_DIR}/app.log` | Path to the rotating application log file |
| `LOG_MAX_BYTES` | `1048576` | Maximum size of each log file before rotation |
| `LOG_BACKUP_COUNT` | `3` | Number of rotated log files to keep |
| `LOG_TAIL_LIMIT` | `200` | Maximum log lines returned to the dashboard log panel |

The dashboard **Logs** panel shows recent application log entries from `LOG_FILE`.

## Dashboard authentication

The dashboard requires a password. Set `DASHBOARD_PASSWORD` before starting the app; visiting `/` redirects to a login page where you enter that password. A signed session cookie keeps you signed in for seven days. Use **Log out** on the dashboard to clear the session.

See [SECURITY.md](../SECURITY.md) for more detail.

## Backup schedule

Set `CRON_SCHEDULE` with standard 5-field cron syntax (e.g. `0 3 * * 0` for weekly at 3am Sunday), or use the dashboard Configuration form after install. Omit for manual-only backups. The TrueNAS Custom App wizard offers Daily / Weekly / Monthly presets that render to `CRON_SCHEDULE` automatically.

## Notifications

When `NOTIFY_WEBHOOK_URL` is set, the app POSTs on backup failures (and on success when `NOTIFY_ON_SUCCESS=true`). Discord webhooks are auto-detected. Use `NOTIFY_PROVIDER=generic` explicitly for Slack, ntfy, Home Assistant, and other JSON receivers if needed.

## Health endpoints

- `GET /healthz` — liveness probe (always returns `OK`; unauthenticated)
- `GET /readyz` — readiness JSON (writable storage, last backup status; optional TrueNAS probe via `HEALTH_CHECK_TRUENAS`)

## Related guides

- [Installation](installation.md) — deploy on TrueNAS SCALE
- [Restore](restore.md) — upload backups back to TrueNAS
- [Security](../SECURITY.md) — auth, secrets, and reporting
