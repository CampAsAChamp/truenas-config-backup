# Plan: TrueNAS Config Backup — Catalog App

## Goal
Ship "TrueNAS Config Backup" as a real, installable catalog app (native
install form in the Apps UI, not a raw compose paste) so other TrueNAS SCALE
users can add it from a catalog and configure it without touching YAML.

## Current status
A working single-container prototype already exists (FastAPI + APScheduler +
Jinja2 dashboard). It:
- Calls `POST /api/v2.0/config/save` directly (confirmed this returns the
  tar synchronously over plain HTTP — no job/pipe polling needed).
- Lets you set a cron schedule, retention count, and whether to include the
  secret seed.
- Lists/downloads/deletes existing backups from a dashboard.
- Logs run history (success/failure) to a small jsonl file.

This code is attached as `truenas-config-backup-starter-code/` — treat it as
the reference backend implementation to adapt into the catalog format below,
not as a finished catalog app.

## Two things to build, in order

### 1. The app itself (mostly done, needs one open architecture question resolved)
### 2. The catalog wrapper (app.yaml / ix_values.yaml / questions.yaml / Jinja2 compose template) that makes it installable via the Apps UI

---

## Open architecture question to resolve FIRST (spike before building the rest)

**How does the app reach the TrueNAS API it's backing up?**

Two options, and this materially changes the questions.yaml design:

- **Option A — mount the middleware socket** (`/var/run/middlewared.sock`)
  into the container and talk to it directly. No API key needed (root-level
  local trust), zero-config for the common case of "app runs on the same box
  it's backing up." *Risk to validate*: TrueNAS's app framework may restrict
  host path/device mounts to ix-managed dataset paths for catalog apps
  unless the app explicitly declares elevated capabilities in `app.yaml`.
  Confirm this is actually permitted (and what `app.yaml` needs to declare)
  before designing around it — check current `truenas/apps` example apps for
  any that mount host sockets/devices, and check the `app.yaml` metadata
  docs for a capabilities/security section.
- **Option B — API key + URL over the network** (what the prototype does
  today). Works regardless of app-framework restrictions, and also supports
  the case of backing up a *different* TrueNAS box from this app. Requires
  the user to paste an API key into a form field (needs to render as a
  masked/"private" field type in questions.yaml, not plain text).

**Recommendation:** spend an hour confirming whether Option A is actually
permitted under the current app security model. If yes, make it the default
with Option B exposed as an "advanced" toggle for remote/cross-box backup.
If host socket mounts are restricted, go with Option B only and don't spend
more time on A.

---

## Part 1 — App-level changes needed before wrapping in a catalog

- Make the TrueNAS connection method conditional on the above decision
  (env vars either way: `TRUENAS_MODE=socket|api`, plus
  `TRUENAS_URL`/`TRUENAS_API_KEY` when in `api` mode).
- Make `BACKUP_DIR` and `CONFIG_DIR` paths configurable via env var only
  (already true) — the catalog's storage questions will map user-chosen
  datasets onto these paths.
- Add a `/healthz` endpoint (simple 200 OK) — TrueNAS app health checks /
  readiness probes expect something to poll.
- Pin the container to a specific non-`latest` tag once versioning starts
  (see CI section) so catalog `ix_values.yaml` can reference reproducible
  image digests.

## Part 2 — Catalog app definition

Reference: the current (Docker-Compose-era) catalog format lives in the
`truenas/apps` GitHub repo — this replaced the old Helm-chart-based
`truenas/charts` format. Read `truenas/apps/CONTRIBUTIONS.md` first; it has
a "Getting Started: Local Development Environment" section with tooling to
render/test an app definition without a live TrueNAS box, which should be
step one of implementation (don't hand-edit YAML against a live NAS as the
only feedback loop).

Directory/file layout to create (one train/app pair):

```
<train>/truenas-config-backup/
├── app.yaml              # metadata: name, version, categories, capabilities/security, min_scale_version
├── ix_values.yaml        # static defaults + image repo/tag/digest
├── questions.yaml        # user-facing install form (see fields below)
├── app-readme.md         # shown in the UI on the app's detail screen
├── item.yaml             # icon_url + categories (older-format equivalent; confirm current field name)
└── templates/
    └── docker-compose.yaml.j2   # Jinja2 template rendered against ix_values + user answers
```

### questions.yaml — fields to expose
- **Connection mode** (radio/select): "Local (same TrueNAS box)" vs "Remote (API key)" — only show URL/API-key fields when Remote is selected (questions.yaml supports conditional/`show_if` fields).
- **TrueNAS URL** (text, shown only in Remote mode)
- **API Key** (masked/private field type, shown only in Remote mode)
- **Verify SSL** (checkbox, default off — home-lab self-signed certs are common)
- **Cron schedule** (text, default `0 3 * * 0`) — or consider a friendlier
  set of preset dropdown options (Daily/Weekly/Monthly) plus an "Advanced/
  custom cron" escape hatch, since not every user wants to hand-write cron.
- **Retention count** (int, default 8)
- **Include secret seed** (checkbox, default true)
- **Backup storage path** — use TrueNAS's native storage/dataset picker
  question type (`hostPath` or ix storage field, whatever the current
  library helper is called) rather than a raw text path, so the install
  form gives users the normal "browse and pick a dataset" UX. Maps to the
  container's `/backups` mount.
- **Config/state storage path** — same pattern, maps to `/config` mount.
- **Web UI port** — int, default e.g. 8080, using the library's port-question
  helper so TrueNAS handles conflict detection against other apps.

### app.yaml — key metadata to set
- `name`, `train`, `app_version` / `version` (per the current versioning
  scheme: internal chart version bumps independently of the app's own
  version — confirm exact fields against a recent example app in the repo).
- `categories`: something like `backup`, `system` — check existing category
  taxonomy in the repo for the closest match.
- `capabilities`/security section — resolve in tandem with the socket-mount
  spike above.
- `min_scale_version` — set to whatever version supports the storage/port
  question helpers you use.

### templates/docker-compose.yaml.j2
Adapt the existing manual `docker-compose.yml` into the Jinja2 template
format, pulling values from the rendered question answers via the
library's helper functions (storage mount helper, port helper, etc.) rather
than hand-writing volume/port blocks — this is what the render engine
expects and validates against.

## Part 3 — Testing before publishing
- Use the repo's local dev tooling (from Getting Started docs) to render
  the app definition against test values and confirm the compose output is
  valid, without needing a live TrueNAS box for every iteration.
- Then do one real end-to-end install on your own TrueNAS as a custom
  catalog (see Part 4) to confirm the actual install wizard, storage
  pickers, and running container all behave as expected.
- Test both "just installed, first scheduled run hasn't fired yet",
  "manual run-now", and "upgrade the app to a new version" paths — catalog
  apps support in-place upgrades and there's a `migrations` mechanism for
  changing question schemas across versions; at minimum confirm a version
  bump doesn't silently wipe the settings/history files in `/config`.

## Part 4 — Publishing so other people can use it

Two tracks, not mutually exclusive:

1. **Self-hosted custom catalog (fast, no gatekeeping)** — put the
   `<train>/truenas-config-backup/` directory in your own public GitHub
   repo, formatted the same way the official catalog expects. Other users
   add it via *Apps → Manage Catalogs → Add Catalog* pointing at your repo
   URL, then it shows up in Discover Apps like any official app. This is
   the realistic "ship it this week" path — do this first.
2. **Upstream contribution to `truenas/apps`** — once the app is stable and
   you've used it yourself for a while, open a PR against the official repo
   per their `CONTRIBUTIONS.md`. This gets it in front of every TrueNAS user
   by default (no catalog-adding step required on their end) but goes
   through review/CI and iX's own bar for what they accept into the
   official catalog. Treat as a stretch goal after the self-hosted catalog
   has some real mileage on it.

## Part 5 — Container image / CI
- Public GitHub repo for the app code (the FastAPI backend), separate from
  or alongside the catalog-definition repo.
- GitHub Actions: build + push image to GHCR on tag push, so `ix_values.yaml`
  can reference a stable, versioned image rather than `latest`.
- Basic README covering: what it does, how to add the catalog, required
  permissions/API key scope (if using Remote mode, note that TrueNAS API
  keys can reportedly be scoped to specific methods — worth confirming and
  recommending users scope the key to `config.save` only, least-privilege).

## Suggested build order for Claude Code
1. Spike: confirm socket-mount vs API-key architecture question (Part 1).
2. Adjust the existing prototype app to support the chosen connection
   mode(s) + add `/healthz`.
3. Read `truenas/apps/CONTRIBUTIONS.md` + one or two comparable existing
   apps in that repo as structural references.
4. Build `app.yaml`, `ix_values.yaml`, `questions.yaml`,
   `templates/docker-compose.yaml.j2`, `app-readme.md`.
5. Render/validate locally using the repo's dev tooling.
6. Stand up your own catalog repo, add it to your TrueNAS, do a real install
   end-to-end.
7. Fix whatever the real install reveals that local rendering didn't catch.
8. Publish the catalog repo publicly + write the README.
9. (Later) consider upstreaming via PR.
