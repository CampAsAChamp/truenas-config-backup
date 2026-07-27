# TrueNAS Config Backup

[TrueNAS Config Backup](https://github.com/CampAsAChamp/truenas-config-backup) schedules
and manages downloads of your TrueNAS system configuration backup (via the `config.save`
API), with retention pruning, a run-history log, and a simple web dashboard.

## First-time setup

1. **Create an API key** on the TrueNAS system you want to back up
   (**My API Keys** in the TrueNAS UI). Paste it into the **API Key** field during install.
   Scope the key to `config.save` only if your TrueNAS version supports method scoping.
2. **Set TrueNAS URL** to the target system's base URL. Use `https://127.0.0.1` when the
   app runs on the same box, or the host's LAN IP (e.g. `https://192.168.1.50`) if the
   container cannot reach loopback.
3. **Leave Verify SSL Certificate disabled** for self-signed certificates (typical home-lab
   setups). The connection is still encrypted; only certificate verification is skipped.
4. **Optional:** set a cron schedule (e.g. `0 3 * * 0` for weekly at 3am Sunday). Leave
   empty for manual-only backups — use **Run backup now** on the dashboard.
5. Open the **WebUI** portal after install to view, download, or delete backups and see
   run history.

## Important notes

- **HTTPS is required.** TrueNAS revokes API keys used over plain `http://`. If a key was
  revoked, create a new one in **My API Keys** and update the app configuration.
- **Include Secret Seed** should stay enabled if you may restore encrypted passwords from
  this backup onto a new system.
- **Retention Count** controls how many past backup files are kept; older files are pruned
  automatically after each successful run.

For full documentation, see the [upstream repository](https://github.com/CampAsAChamp/truenas-config-backup).
