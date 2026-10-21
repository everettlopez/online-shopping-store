# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Online store: a FastAPI + SQLModel backend (`app/`) on MySQL with Alembic migrations and Stripe Checkout, plus a React + TypeScript + Vite frontend (`frontend/`). Development is on Windows; the Python virtualenv is `venv/` in the project root.

## Commands

All from the project root.

```bash
venv\Scripts\pip install -r requirements-dev.txt        # backend + test dependencies
venv\Scripts\alembic upgrade head                       # apply migrations (reads DATABASE_URL from .env)
venv\Scripts\alembic revision --autogenerate -m "..."   # after changing a model; review the file before upgrading
venv\Scripts\python -m uvicorn app.main:app --reload    # API on :8000 (docs at /docs)
npm --prefix frontend run dev                           # frontend on :5173
stripe listen --forward-to localhost:8000/api/payments/webhook --events checkout.session.completed
```

Run the API in its own terminal on Windows: when uvicorn auto-reloads, it sends Ctrl+C to every process in that terminal.

Tests (backend only; no MySQL, `.env` or network needed):

```bash
venv\Scripts\python -m pytest                                              # whole suite
venv\Scripts\python -m pytest tests/api/test_cart_api.py                   # one file
venv\Scripts\python -m pytest tests/api/test_cart_api.py::test_clear_cart  # one test
venv\Scripts\python -m pytest -k checkout -x                               # by name, stop at first failure
```

Frontend: `npm --prefix frontend run lint` (ESLint; `main` already has about 26 existing problems, so compare counts rather than expecting a clean run) and `npm --prefix frontend run build` (runs `tsc -b`, so it is also the type check). The frontend has no test runner.

`.claude/launch.json` defines the `api` and `dev` preview servers.

## Configuration

Settings come from the environment or `.env` (see `.env.example`). Required: `DATABASE_URL`, `JWT_SECRET_KEY` (at least 32 chars), `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`. Optional deployment settings are in `app/settings.py`: `FRONTEND_URL`, `PUBLIC_API_URL`, `CORS_ORIGINS`, `COOKIE_SAMESITE`, `COOKIE_SECURE`, `ENABLE_DOCS`, `SQL_ECHO` and `UPLOAD_DIR`. Their defaults suit local development. The frontend reads the API address from `VITE_API_URL` at build time (`frontend/.env.example`), falling back to the local API.

Deployment: the root `Dockerfile` builds the API (`docker/start-api.sh` migrates, then runs uvicorn), and `frontend/Dockerfile` builds the storefront served by nginx with an SPA fallback. CI is `.github/workflows/ci.yml`. The README's Deployment section lists the production settings.

The functions in `app/settings.py` read the environment each time they're called, which is how tests change settings with `monkeypatch.setenv`. Some values are still read once when a module is imported: `DATABASE_URL`/`engine` (`app/db/session.py`), `SECRET_KEY` (`app/auth/core.py`, which refuses to sign or verify tokens with a key under 32 characters), and the Stripe key and `WEBHOOK_SECRET` (`app/routes/payments.py`).

## Backend architecture

- **App setup:** `app/main.py` has `create_app()`, which mounts every router under `/api`, adds `GET /api/health` (503 when the database is unreachable) and serves the upload folder (`UPLOAD_DIR`, default `app/uploads`) at `/uploads`. It also adds the CORS middleware and a CSRF guard that rejects POST/PUT/PATCH/DELETE requests from an `Origin` outside `CORS_ORIGINS` (requests with no `Origin`, such as Stripe's webhook, pass). On startup it runs `check_required_settings()`, then `seed_database()`. The latter refuses to start unless the database is at the Alembic head revision, then seeds the default categories into an empty table.
- **Layers:**
  - `app/models/` holds the SQLModel tables.
  - `app/schemas/` holds the Pydantic request and response models.
  - `app/database/` holds shared query helpers, named `database_*`.
  - `app/routes/` holds the routers.
  - The schema is owned by Alembic (`alembic/versions/`, whose `env.py` imports every model). Never add `create_all` to the app.
- **Response shapes:** `ProductRead` nests the full `category`, so build products with `database_get_product_reads()` (`app/database/products.py`) instead of returning `Product` rows. Orders are built with `build_order_reads()` in `app/routes/order.py`.
- **Auth:**
  - Login sets an httponly `shop_token` JWT cookie through `set_auth_cookie`/`clear_auth_cookie` in `app/auth/core.py`. Use these helpers so the cookie attributes match. A `Bearer` header also works.
  - Use `CurrentUser` for a logged-in user and `Depends(admin_required)` (`app/auth/dependencies.py`) for admin routes.
  - Resources owned by a user return 404, not 403, to anyone other than the owner (or an admin).
- **Orders exist only through Stripe Checkout:**
  1. `POST /payments/create-checkout-session` validates the cart (positive quantities, active products, stock), totalling quantities per product.
  2. It stores a `[product_id, qty, unit_cents]` snapshot, one entry per product, in the session metadata (Stripe allows 500 characters per value).
  3. `fulfill_checkout()` creates the order from that snapshot, not from the current cart. Both the webhook and `GET /payments/session/{id}` call it as a fallback, so it is idempotent per `stripe_session_id` and takes row locks.

  There is deliberately no route that creates an order or charges an amount supplied by the client; tests in `tests/api/test_security.py` check that.
- **User deletion:** deleting a user goes through `database_user_has_orders`/`database_delete_user` (`app/database/users.py`). Users with orders are kept, since orders are financial records. Likewise, a product that appears in an order can't be deleted (409); admins set it inactive instead.
- **Cart:** adding a product already in the cart raises that row's quantity rather than adding a row. Quantities are 1 to `MAX_CART_QUANTITY` (`app/schemas/cart_item.py`) and can't exceed stock.
- **Uploads:** product images go through `save_uploads()` in `app/routes/product.py`. It checks every file (image extensions only, 5 MB each) before writing any, saves under random names in the module-level `UPLOAD_DIR` (from `upload_dir()` in `app/settings.py`), and returns absolute URLs built from `PUBLIC_API_URL` (falling back to the request's base URL). The product create/update routes are plain `def` so this I/O runs in FastAPI's threadpool.

## Frontend architecture

- `frontend/src/api/axiosClient.ts` calls `VITE_API_URL` (locally `http://127.0.0.1:8000/api`) with `withCredentials` (cookie auth). That is a different site from `localhost:5173`, which is why the cookie defaults to `SameSite=None`.
- API helpers live in `frontend/src/api/*`. Use `apiErrorMessage()` from `api/errors.ts` to show FastAPI `detail` errors (including the first 422 validation message).
- App-wide state (auth, cart, categories) is in `frontend/src/context/`. Routes and the public-only/protected/admin guards are in `frontend/src/router/AppRouter.tsx`.
- Styling is Tailwind, with MUI in the admin pages.

## Tests

- **Setup:** `tests/conftest.py` sets every environment variable before importing `app`. Each test gets a fresh in-memory SQLite database with foreign keys enforced (to behave like MySQL), wired in by overriding `get_session`. `TestClient` is not used as a context manager, so the startup checks don't run.
- **Fixtures:**
  - Factories: `make_user`, `make_category`, `make_product`, `make_address`, `add_to_cart` and `make_order`.
  - Clients: `user_client` and `admin_client` share a single `client`. For tests with several users, use `client` with `auth_headers(user)`.
  - `upload_dir` redirects uploads to a temp folder.
- **Stripe:** Stripe is never called. Tests build objects with `stripe.<Type>.construct_from(...)` and monkeypatch `stripe.checkout.Session.create/retrieve`, `stripe.Webhook.construct_event` and `stripe.PaymentIntent.retrieve` (see `tests/api/test_payments_api.py`).
- **Layout:** tests are split into `tests/unit/`, `tests/api/` and top-level files (app wiring, migrations). The test folders have no `__init__.py`, so test file names must be unique across folders. Import shared constants with `from conftest import TEST_PASSWORD`.
- **Warnings:** `pytest.ini` hides only the deprecations the app is known to use (`datetime.utcnow()`, `on_event`, class-based Pydantic `Config`); any other warning shows in the test summary.
- **Expiry gotcha:** after a request changes data, call `session.expire_all()` before reading it back through the test `session`. Keep ids in local variables, because expired ORM objects can't be read once their row is gone.
