## What and why

<!-- What this changes, and the problem it solves. Link the issue: "Fixes #123". -->

## How it was tested

<!-- Tests added or run, and what you checked by hand (pages, checkout, emails, the deploy kit). -->

## Store owners

<!-- Anything an owner must do after updating: a new or changed setting, a database migration, a manual step. Write "Nothing" if there's nothing. This goes into the release notes. -->

## Checklist

- [ ] `venv\Scripts\python -m pytest` passes, with tests added or updated for backend changes.
- [ ] `venv\Scripts\ruff check .`, `npm --prefix frontend run lint` and `npm --prefix frontend run build` report no problems.
- [ ] Nothing store-specific is hard-coded (names, domains, emails, prices, images); new settings have defaults and are in the matching `.env.example`.
- [ ] A database change has an Alembic migration with a working `downgrade()`.
- [ ] Docs are updated where the change affects them (README, `docs/`, `.env.example`, `CLAUDE.md`), and `CHANGELOG.md` has a line under **Unreleased** for anything owners would notice.
- [ ] No secrets, keys or customers' details in the code, tests or screenshots.
