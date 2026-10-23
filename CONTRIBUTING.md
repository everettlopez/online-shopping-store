# Contributing

Thanks for helping improve the store. Bug reports, fixes, documentation and features are all welcome.

## Before you start

- **Bugs:** open an issue with what you did, what you expected, and what happened (screenshots and API error messages help).
- **Security problems:** don't open an issue; follow [SECURITY.md](SECURITY.md).
- **Features:** open an issue first to talk it through, so your work fits the project's direction before you spend time on it.

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
5. Update the docs in the same pull request: the README, `.env.example`, `docs/hosting.md`, `docs/launch-checklist.md` or `CLAUDE.md`, whichever your change affects.

## Check it

```bash
venv/bin/python -m pytest                # Windows: venv\Scripts\python -m pytest
npm --prefix frontend run build          # includes the TypeScript check
npm --prefix frontend run lint
```
All tests must pass and the build must succeed. The lint has some existing problems on `main`; don't add new ones. If you changed the deploy kit, run `docker compose -f deploy/docker-compose.yml config` with example settings (CI does this too).

## Open a pull request

Describe what changed and why, how you tested it, and anything a store owner needs to do after updating (a new setting, a migration). CI runs the tests, the frontend build and the Docker builds on every pull request.

By contributing, you agree that your contributions are licensed under the project's [MIT License](LICENSE).
