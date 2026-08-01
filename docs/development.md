# Development

## Running the backend locally

### Hot reload (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.local.example .env.local   # edit TRUENAS_API_KEY and DASHBOARD_PASSWORD
./scripts/dev.sh
```

Then visit `http://127.0.0.1:8080`. Edits to Python or templates restart the server
automatically; CSS/JS changes reload the browser without a server restart.

You can also use **Run and Debug → Run app** in VS Code/Cursor — it uses the same
reload settings and sets `DEV_MODE=true`.

`DEV_MODE` enables dev-only behavior: mtime-based cache busting for static assets and
a live-reload client (`dev-reload.js`) that listens for server restarts over SSE and
polls a combined reload-state endpoint for static asset changes. High-frequency dev
polling routes are hidden from uvicorn access logs. It is never set in the production
container.

### Production-like run (no reload)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

BACKUP_DIR=/tmp/backups CONFIG_DIR=/tmp/config \
TRUENAS_URL=https://127.0.0.1 TRUENAS_API_KEY=your-api-key \
PYTHONPATH=app \
  uvicorn src.main:app --host 0.0.0.0 --port 8080
```

Then visit `http://localhost:8080`.

### Sample data for local testing

When you run the app via **Run and Debug → Run app** or `./scripts/dev.sh`, sample backups and
run history are seeded automatically into `local-data/` if that folder has no `.tar` files yet.
No TrueNAS connection is required to browse, download, or delete those backups.

To seed manually (CLI or container runs):

```bash
mkdir -p local-data/backups local-data/config
python scripts/seed-local-data.py          # skip if backups already exist
python scripts/seed-local-data.py --force  # replace existing seed data
```

The seed data is fake — placeholder tar archives and a hand-written `history.jsonl` for
exercising the dashboard.

## Dashboard screenshot

The README shows [`docs/dashboard.png`](dashboard.png). Regenerate it after UI changes.

### Local capture

One-time setup, then run capture:

```bash
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
npm install -g github:CampAsAChamp/readme-screenshot#v1.1.4
npx playwright install chromium
readme-screenshot capture
```

Or use **Terminal → Run Task → Capture dashboard screenshot** in VS Code/Cursor (installs Chromium if needed, then overwrites `docs/dashboard.png`).

Capture is driven by [`.readme-screenshot.yml`](../.readme-screenshot.yml): seeds demo data into gitignored `local-data/`, starts uvicorn without reload, logs in with Playwright, and overwrites `docs/dashboard.png`. Clock and timezone are pinned (`America/Los_Angeles`, fixed instant) so repeated runs produce identical PNGs except when the UI or `app/src/VERSION` changes.

### CI auto-update

Pushes to `main` that touch dashboard UI files (templates, static assets, `app/src/VERSION`,
the seed script, or `.readme-screenshot.yml`) run
[`.github/workflows/dashboard-screenshot.yml`](../.github/workflows/dashboard-screenshot.yml).
When the PNG changes, CI commits `docs: update dashboard screenshot` back to `main`.

That auto-commit uses `GITHUB_TOKEN`, so it does not start another workflow on its own.
[`.github/workflows/release.yml`](../.github/workflows/release.yml) runs afterward via
`workflow_run`, once the screenshot job finishes, so semantic-release always sees the final
`main` tip (including any bot screenshot commit) before publishing.

Pushes that only change UI files skip the push-triggered release job; other pushes to `main`
still run release directly.

You can also refresh manually from **Actions → Dashboard screenshot → Run workflow** (which
also triggers release when the job completes).

## Testing

Use the project venv so pytest picks up `pytest-cov` (system `pip3`/`pytest` often won't):

```bash
python3 -m venv .venv
source .venv/bin/activate   # prompt should show (.venv)
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest --cov
```

Confirm you're in the venv: `which python` should point at `.venv/bin/python`.

Optional local hooks (ruff + pytest before every push, matching CI):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
git config core.hooksPath .githooks
```

The repo includes [`.githooks/pre-push`](../.githooks/pre-push), which runs the same checks as
CI. To run them manually:

```bash
.githooks/pre-push
```

Tests live under `app/tests/` and cover history logging, backup management, the TrueNAS
WebSocket client (mocked), and FastAPI routes. Pushes to `main` run ruff and pytest via
[`.github/workflows/release.yml`](../.github/workflows/release.yml) before semantic-release.

## Building the container

Build with Podman from the repo root:

```bash
podman build -t ghcr.io/campasachamp/truenas-config-backup:local .
```

### Behind Zscaler

On a corporate network, `pip install` during the build can fail with:

```text
SSLCertVerificationError: certificate verify failed: unable to get local issuer certificate
```

The Dockerfile installs `docker/certs/zscaler-root-ca.pem` into the image trust store before
running pip when that file is present. The cert is gitignored (not needed for CI or public
builds). Copy your Zscaler root CA to that path for local builds on a corporate network:

```bash
cp ~/.ssl/zscaler-ca.pem docker/certs/zscaler-root-ca.pem
```

Podman's VM (libkrun on Apple Silicon) already pulls the base image from Docker Hub; the cert
file is only needed for HTTPS inside the build (pypi.org).

## Validating the catalog app definition

The catalog app under `ix-dev/community/truenas-config-backup/` follows the
[truenas/apps](https://github.com/truenas/apps) format. To render/validate it
locally (requires a running container runtime — Docker or Podman):

```bash
source .venv/bin/activate
pip install pyyaml psutil pytest pytest-cov bcrypt pydantic pydantic-settings

python .github/scripts/ci.py --app truenas-config-backup --train community \
  --test-file basic-values.yaml --render-only=true

# Additional test scenario (host_path storage, daily schedule):
python .github/scripts/ci.py --app truenas-config-backup --train community \
  --test-file host-path-values.yaml --render-only=true

# Full container validation (requires /opt/tests on Linux, or sudo mkdir on macOS):
python .github/scripts/ci.py --app truenas-config-backup --train community \
  --test-file basic-values.yaml
```

## Related guides

- [Contributing](../CONTRIBUTING.md) — releases and commit format
- [Configuration](configuration.md) — all environment variables
