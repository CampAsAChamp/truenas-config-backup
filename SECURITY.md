# Security Policy

## Supported versions

Security fixes are applied to the latest release on the `main` branch.

## Reporting a vulnerability

Please report security issues privately via [GitHub Security Advisories](https://github.com/CampAsAChamp/truenas-config-backup/security/advisories/new) or email the maintainer listed in the repository profile.

Do not open public issues for undisclosed vulnerabilities.

## Security considerations

### Dashboard access

The web dashboard can trigger backups, download full TrueNAS configuration archives, and delete stored backups. **Authentication is required** via a login page protected by `DASHBOARD_PASSWORD`.

- Set a strong `DASHBOARD_PASSWORD` during install or in your environment before starting the container.
- Successful login sets an HttpOnly session cookie (7-day lifetime).
- Restrict port exposure where possible (localhost-only binding, VLAN firewall, TrueNAS ingress rules).

### Backup file sensitivity

Config backup `.tar` files may include the **password secret seed** when `INCLUDE_SECRET_SEED=true` (the default). When `INCLUDE_POOL_KEYS=true` or `INCLUDE_ROOT_AUTHORIZED_KEYS=true`, backups also contain pool encryption keys and root SSH keys respectively. Treat downloaded backups and the backup storage volume as highly sensitive.

### TrueNAS API keys

- `TRUENAS_URL` must use **`https://`**. TrueNAS revokes API keys used over plain HTTP.
- Use a least-privilege API key scoped to configuration backup methods where TrueNAS allows it.
- Rotate keys if exposure is suspected.

### Notification webhooks

`NOTIFY_WEBHOOK_URL` receives backup event metadata (status, message, TrueNAS URL). Use HTTPS endpoints and treat webhook URLs as secrets.

### Container health checks

`/healthz` is intentionally unauthenticated for Docker/TrueNAS liveness probes. It does not expose backup data. `/readyz` reports operational status but also does not serve backup contents.
