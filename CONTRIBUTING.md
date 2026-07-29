# Contributing

## Releasing

Releases are fully automated with [semantic-release](https://github.com/semantic-release/semantic-release).
Push to `main` — no manual version bumps, git tags, or release PRs.

### How it works

1. Each push to `main` runs [`.github/workflows/release.yml`](.github/workflows/release.yml).
2. semantic-release analyzes commits since the last tag using the
   [Conventional Commits](https://www.conventionalcommits.org/) format.
3. If there are releasable changes, it automatically:
   - picks the next semver (`fix:` → patch, `feat:` → minor, breaking change → major)
   - updates [`VERSION`](VERSION), [`package.json`](package.json), catalog files, and
     [`CHANGELOG.md`](CHANGELOG.md)
   - commits, tags (bare semver, e.g. `0.2.0`, no `v` prefix), and creates a GitHub Release
4. When a release is created, the same workflow builds the container and pushes it to
   GHCR as `:0.2.0` and `:latest`.

Tag pushes from semantic-release use `GITHUB_TOKEN`, which does **not** trigger other
workflows on GitHub — so image publish runs in `release.yml`, not via a separate tag hook.
Use **Actions → Publish Docker image → Run workflow** to re-publish an existing tag manually.

Commits that do not use conventional prefixes (`chore:`, `docs:`, etc. without `fix`/`feat`) do
**not** trigger a release.

### Commit format

```text
fix: correct backup retention when count is zero
feat: add dark theme to dashboard
feat!: drop deprecated REST config-save path

BREAKING CHANGE: removed legacy env var FOO
```

### After a release

- **Verify CI** published `ghcr.io/campasachamp/truenas-config-backup:<version>` and updated `:latest`
- **Custom App users on `:latest`:** restart or redeploy the app to pull the new image (TrueNAS may cache — use **Pull latest image** if available)
- **Custom App users pinned to a version tag:** edit the deployed app and bump the image tag to the new release

The GHCR package must stay **public** so TrueNAS can pull the image without authentication.
CI fails if the git tag does not match `VERSION`, `app_version`, and the image tag in `ix_values.yaml`.

## Development

See [docs/development.md](docs/development.md) for local setup, testing, building the container, and validating the catalog app definition.
