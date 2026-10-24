# Contributing

Thanks for helping improve the store. Bug reports, fixes, documentation and features are all welcome.

## Before you start

- **Bugs:** [open a bug report](https://github.com/everettlopez/online-shopping-store/issues/new/choose). The form asks for the release, what you did, what you expected, and what happened. [docs/troubleshooting.md](docs/troubleshooting.md#collect-this-before-asking-for-help) lists the details that help.
- **Questions** about setting up or running a store: ask in [Discussions](https://github.com/everettlopez/online-shopping-store/discussions).
- **Security problems:** don't open an issue; follow [SECURITY.md](SECURITY.md).
- **Features:** open a feature request first to talk it through, so your work fits the project's direction before you spend time on it.

Everyone taking part is expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Set up

Follow [Development Setup](README.md#development-setup) in the README: MySQL, a `.env` from `.env.example`, the Python virtualenv, `npm install`, and the API and storefront dev servers. [CLAUDE.md](CLAUDE.md) describes the architecture and conventions in detail and is worth reading before larger changes.

## Make your change

1. Fork the repository and create a branch from `main` (`feature/...` or `fix/...`).
2. Keep the change focused; one pull request per fix or feature.
3. Follow the existing patterns:
   - **The store must stay configurable.** Never hard-code a store's name, domain, email address, prices or images. Add a setting instead (`app/settings.py` for the API, a `VITE_*` variable read in `frontend/src/config/store.ts` for the storefront), with a sensible default, and document it in the matching `.env.example`.
   - **Money:** `Decimal` in Python and cents with Stripe, never `float` arithmetic (see `app/money.py`).
   - **Database changes** go through an Alembic migration (`alembic revision --autogenerate -m "..."`); review the generated file.
   - **Orders** are only created from paid Stripe Checkout sessions; don't add a route that charges an amount the client sends.
4. Add or update tests for backend changes (`tests/`, using the fixtures in `tests/conftest.py`).
5. Update the docs in the same pull request: the README, `.env.example`, `docs/hosting.md`, `docs/launch-checklist.md`, `docs/troubleshooting.md` or `CLAUDE.md`, whichever your change affects.
6. Add a line under **Unreleased** in [CHANGELOG.md](CHANGELOG.md) for anything a store owner would notice.

## Check it

```bash
venv/bin/python -m pytest                # Windows: venv\Scripts\python -m pytest
npm --prefix frontend run build          # includes the TypeScript check
npm --prefix frontend run lint
```
All tests must pass, the lint must report no problems, and the build must succeed (CI checks all three). If you changed the deploy kit, run `docker compose -f deploy/docker-compose.yml config` with example settings (CI does this too).

## Open a pull request

The pull request template asks for what changed and why, how you tested it, and anything a store owner needs to do after updating (a new setting, a migration). CI runs the tests, the frontend build and the Docker builds on every pull request.

## Releasing (maintainers)

Stores run releases, not `main`, so `main` can hold work that isn't released yet. Versions follow [Semantic Versioning](https://semver.org/): a patch (`1.0.1`) for fixes and docs, a minor (`1.1.0`) for new features or settings, a major (`2.0.0`) when owners must change something by hand to keep their store working.

1. On a `release/vX.Y.Z` branch, set the version in `package.json` and `frontend/package.json` and their lockfiles (`npm version X.Y.Z --no-git-tag-version` in the root and in `frontend/`).
2. In [CHANGELOG.md](CHANGELOG.md), move the **Unreleased** entries under a new `## [X.Y.Z] - YYYY-MM-DD` heading, and update the comparison links at the bottom.
3. Merge the pull request once CI passes.
4. Tag the merge commit on `main` and publish the release:
   ```bash
   git switch main && git pull
   git tag -a vX.Y.Z -m "vX.Y.Z"
   git push origin vX.Y.Z
   gh release create vX.Y.Z --title "vX.Y.Z" --generate-notes --notes-file notes.md
   ```
   `notes.md` starts with a short summary and a **Before you update** section: new migrations (`git diff --name-only --diff-filter=A <previous tag> vX.Y.Z -- alembic/versions`), new or changed settings (`git diff <previous tag> vX.Y.Z -- .env.example deploy/.env.example`), anything an owner must do by hand, and whether it fixes a security problem. Write "Nothing" when there's nothing. GitHub adds the list of merged pull requests after it, grouped by label (`.github/release.yml`).

By contributing, you agree that your contributions are licensed under the project's [MIT License](LICENSE).
