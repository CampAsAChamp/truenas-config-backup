# Configuration

All settings are environment variables. Set them in the TrueNAS Custom App wizard,
compose YAML, or your local shell when running the backend directly.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `TRUENAS_API_KEY` | *(required)* | API key for that TrueNAS system |
| `DASHBOARD_PASSWORD` | *(required)* | Password for the dashboard login page |
| `TRUENAS_URL` | `https://127.0.0.1` | Base URL of the TrueNAS system to back up |
| `TRUENAS_VERIFY_SSL` | `false` | Verify the TrueNAS TLS certificate |
| `BACKUP_DIR` | `/backups` | Where downloaded backup tars are stored |
| `CONFIG_DIR` | `/config` | Where the run-history log is stored |
| `CRON_SCHEDULE` | *(none)* | Optional cron expression for scheduled backups; omit for manual-only |
| `RETENTION_COUNT` | `8` | Number of backups to keep before pruning |
| `INCLUDE_SECRET_SEED` | `true` | Include the password secret seed in the backup |
| `INCLUDE_POOL_KEYS` | `false` | Include pool encryption keys in the backup |
| `INCLUDE_ROOT_AUTHORIZED_KEYS` | `false` | Include root SSH authorized keys in the backup |
| `DASHBOARD_PAGE_SIZE` | `20` | Number of backup runs shown per dashboard page |
| `WEB_PORT` | `8080` | Port the dashboard listens on |
| `DISPLAY_DATE_FORMAT` | `mm/dd/yy` | Default timestamp format on the dashboard (`dd/mm/yy`, `dd/mm/yyyy`, `mm/dd/yy`, `mm/dd/yyyy`, or `iso`) |
| `DISPLAY_CLOCK_FORMAT` | `12h` | Default clock style for non-ISO formats (`24h` or `12h`) |
| `DISPLAY_TIMEZONE_MODE` | `local` | Default timezone mode (`local`, `utc`, or `manual`) |
| `DISPLAY_TIMEZONE` | *(empty)* | IANA timezone when mode is `manual` (e.g. `Europe/London`) |
| `NOTIFY_WEBHOOK_URL` | *(none)* | Optional URL to POST backup event notifications |
| `NOTIFY_PROVIDER` | `generic` | Notification payload format: `generic` or `discord` |
| `NOTIFY_ON_SUCCESS` | `false` | Also notify the webhook when backups succeed |
| `HEALTH_CHECK_TRUENAS` | `false` | When true, `/readyz` probes TrueNAS connectivity (slower) |
| `LOG_LEVEL` | `INFO` | Application log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `LOG_FILE` | `{CONFIG_DIR}/app.log` | Path to the rotating application log file |
| `LOG_MAX_BYTES` | `1048576` | Maximum size of each log file before rotation |
| `LOG_BACKUP_COUNT` | `3` | Number of rotated log files to keep |
| `LOG_TAIL_LIMIT` | `200` | Maximum log lines returned to the dashboard log panel |

The dashboard **Display settings** section lets each browser override date format and timezone; overrides are stored in `localStorage` and fall back to these env defaults when unset.

The dashboard **Logs** panel at the bottom of the home page shows recent application log entries from `LOG_FILE`, with level filtering and automatic refresh every few seconds.

## Dashboard authentication

The dashboard requires a password. Set `DASHBOARD_PASSWORD` before starting the app; visiting `/` redirects to a login page where you enter that password. A signed session cookie keeps you signed in for seven days. Use **Log out** on the dashboard to clear the session.

See [SECURITY.md](../SECURITY.md) for more detail.

## Backup schedule

Set `CRON_SCHEDULE` with standard 5-field cron syntax (e.g. `0 3 * * 0` for weekly at 3am Sunday). Omit for manual-only backups. The TrueNAS Custom App wizard offers Daily / Weekly / Monthly presets that render to `CRON_SCHEDULE` automatically.

## Notifications

When `NOTIFY_WEBHOOK_URL` is set, the app POSTs on backup failures (and on success when `NOTIFY_ON_SUCCESS=true`). Set `NOTIFY_PROVIDER=discord` when using a Discord webhook URL (Server Settings → Integrations → Webhooks). Use `generic` (default) for Slack, ntfy, Home Assistant, and other JSON receivers.

## Health endpoints

- `GET /healthz` — liveness probe (always returns `OK`; unauthenticated)
- `GET /readyz` — readiness JSON (writable storage, last backup status; optional TrueNAS probe via `HEALTH_CHECK_TRUENAS`)

## Related guides

- [Installation](installation.md) — deploy on TrueNAS SCALE
- [Restore](restore.md) — upload backups back to TrueNAS
- [Security](../SECURITY.md) — auth, secrets, and reporting
