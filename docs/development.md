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

Then visit `http://127.0.0.1:8080`. Edits to Python, templates, CSS, or JS under `app/`
restart the server automatically and refresh the browser.

You can also use **Run and Debug → Run app** in VS Code/Cursor — it uses the same
reload settings and sets `DEV_MODE=true`.

`DEV_MODE` enables dev-only behavior: mtime-based cache busting for static assets and
a live-reload SSE endpoint. It is never set in the production container.

### Production-like run (no reload)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

BACKUP_DIR=/tmp/backups CONFIG_DIR=/tmp/config \
TRUENAS_URL=https://127.0.0.1 TRUENAS_API_KEY=your-api-key \
  uvicorn app.main:app --host 0.0.0.0 --port 8080
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

## Testing

Use the project venv so pytest picks up `pytest-cov` (system `pip3`/`pytest` often won't):

```bash
python3 -m venv .venv
source .venv/bin/activate   # prompt should show (.venv)
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest --cov
```

Confirm you're in the venv: `which python` should point at `.venv/bin/python`.

Optional local hooks:

```bash
pip install pre-commit && pre-commit install
```

Tests live under `tests/` and cover history logging, backup management, the TrueNAS
WebSocket client (mocked), and FastAPI routes. Pull requests run ruff and pytest via
[`.github/workflows/test-app.yml`](../.github/workflows/test-app.yml); pushes to `main` run the
same checks in [`.github/workflows/release.yml`](../.github/workflows/release.yml) before release.

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
pip install pyyaml psutil pytest pytest-cov bcrypt pydantic

python .github/scripts/ci.py --app truenas-config-backup --train community \
  --test-file basic-values.yaml --render-only=true
```

## Related guides

- [Contributing](../CONTRIBUTING.md) — releases and commit format
- [Configuration](configuration.md) — all environment variables
