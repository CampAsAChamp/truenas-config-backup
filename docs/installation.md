# Installation

This app isn't in the official iX catalog. On SCALE 24.10+ (Electric Eel and
later), third-party app catalogs are no longer supported — deploy it as a
**Custom App** instead.

## Custom App (wizard)

1. **Apps → Discover Apps → Custom App**.
2. Set the container image to `ghcr.io/campasachamp/truenas-config-backup:latest`
   (or pin to a specific release tag from [releases](https://github.com/CampAsAChamp/truenas-config-backup/releases)
   if you prefer fixed versions).
3. Add host-path volumes for backup storage and run history, mounted at `/backups`
   and `/config` respectively (e.g. datasets under your apps pool).
4. Set the environment variables from the [configuration reference](configuration.md)
   — at minimum `TRUENAS_URL`, `TRUENAS_API_KEY`, and `DASHBOARD_PASSWORD`.
5. Publish port **8080** (or match `WEB_PORT` if you change it) to reach the
   dashboard.

## Custom App (compose YAML)

Paste something like the following into **Install via YAML**, adjusting paths,
port, and secrets for your system:

```yaml
services:
  truenas-config-backup:
    image: ghcr.io/campasachamp/truenas-config-backup:latest
    user: "568:568"
    environment:
      TRUENAS_URL: "https://127.0.0.1"
      TRUENAS_API_KEY: "your-api-key"
      TRUENAS_VERIFY_SSL: "false"
      # CRON_SCHEDULE: "0 3 * * 0"   # optional; omit for manual-only backups
      DASHBOARD_PASSWORD: "your-dashboard-password"
      # NOTIFY_WEBHOOK_URL: "https://hooks.example.com/backup"
      RETENTION_COUNT: "8"
      INCLUDE_SECRET_SEED: "true"
      BACKUP_DIR: /backups
      CONFIG_DIR: /config
      WEB_PORT: "8080"
    volumes:
      - /mnt/tank/apps/truenas-config-backup/backups:/backups
      - /mnt/tank/apps/truenas-config-backup/config:/config
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/healthz"]
      interval: 30s
      timeout: 5s
      retries: 3
```

If `https://127.0.0.1` fails from inside the container, change `TRUENAS_URL` to
the host's LAN IP (see [HTTPS required for API keys](#https-required-for-api-keys)).

## Upgrading

Edit the deployed Custom App and bump the image tag to the new release. The
`/config` volume preserves run history across upgrades.

## Creating a least-privilege API key

1. On the TrueNAS system to back up, open **My API Keys** (user menu → **My API Keys**).
2. Click **Add** and give the key a descriptive name (e.g. `config-backup`).
3. If your TrueNAS version supports method scoping, restrict the key to configuration backup methods (`config.save` and related download access).
4. Copy the key into `TRUENAS_API_KEY` — it is shown only once.
5. Use **`https://`** in `TRUENAS_URL`. Keys used over plain HTTP are revoked by TrueNAS.

If a key was revoked, create a new one; revoked keys cannot be reused until renewed in the TrueNAS UI.

## HTTPS required for API keys

`TRUENAS_URL` must use **`https://`**, even on a local network. TrueNAS requires TLS for
API key authentication and **automatically revokes** any key used over plain HTTP (`http://`
or `ws://`). If that happens, create a new API key in **My API Keys** and update the app
configuration — the revoked key cannot be reused until it is renewed in the TrueNAS UI.

Home-lab setups usually run TrueNAS with a self-signed certificate. That is fine: leave
**Verify SSL Certificate** disabled (`TRUENAS_VERIFY_SSL=false`). The connection is still
encrypted; certificate verification is simply skipped.

When the app runs in a container on the same TrueNAS box, `https://127.0.0.1` may not reach
the host middleware depending on container networking. If backups fail to connect, try the
host's LAN IP instead (e.g. `https://192.168.1.50`).

## Related guides

- [Configuration](configuration.md) — all environment variables and options
- [Restore](restore.md) — upload backups back to TrueNAS
- [Security](../SECURITY.md) — auth, secrets, and reporting
