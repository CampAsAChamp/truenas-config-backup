# Restoring a backup

This app backs up configuration only — restore is done in the TrueNAS web UI. The dashboard includes a **How to restore** link with a quick reference; this page is the full guide.

## Get the backup file

Download a `.tar` file from the dashboard, or copy it from the `/backups` volume. Files are produced by TrueNAS `config.save` — the same format as **Manage Configuration → Download File** in the TrueNAS UI.

## Where to upload in TrueNAS SCALE

- **SCALE 24.10 – 25.04:** **System Settings → General** → **Manage Configuration** (top-right) → **Upload File**
- **SCALE 25.10+:** **System → Advanced Settings → Manage Configuration → Upload File**

## Step-by-step restore

1. Choose the downloaded `.tar` file and click **Upload**.
2. TrueNAS applies the configuration and **restarts** the system.
3. After reboot, log back into the web UI. Existing accounts and passwords are preserved when the backup included the secret seed.

## Fresh install / hardware migration

1. Install TrueNAS SCALE fresh on the new hardware and complete initial setup (set the `truenas_admin` password during install).
2. Log into the web UI and upload your backup via **Manage Configuration**.
3. After reboot, log out and back in — you may need your **pre-migration root password**.
4. Import pools separately if needed. Config restore does not recreate pools on blank disks.

## Backup option implications

| Option | Default | Restore impact |
|---|---|---|
| `INCLUDE_SECRET_SEED` | `true` | When enabled, encrypted passwords can be restored on new hardware. When disabled, passwords reset after restore. |
| `INCLUDE_POOL_KEYS` | `false` | When enabled, pool encryption keys are included — needed for encrypted pools on new hardware. |
| `INCLUDE_ROOT_AUTHORIZED_KEYS` | `false` | When enabled, root SSH authorized keys are preserved in the backup. |

Treat backups containing the secret seed or pool keys as highly sensitive. See [SECURITY.md](../SECURITY.md).

## Warnings / troubleshooting

- Uploading a config file **replaces** the entire current system configuration. Save the target system's current config first if it has settings worth keeping.
- **Network mismatch:** Restoring a config with static IPs or VLANs onto hardware with different NICs can make the web UI unreachable. Fix network settings via the system console (`/usr/bin/cli --menu`) before or after upload if needed.
- **Version compatibility:** Restoring onto a much older or newer SCALE version may fail or behave unexpectedly. Prefer matching major versions when possible.

## Related guides

- [Configuration](configuration.md) — backup options and environment variables
- [Installation](installation.md) — deploy on TrueNAS SCALE
- [Security](../SECURITY.md) — auth, secrets, and reporting
