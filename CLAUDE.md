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

Frontend: `npm --prefix frontend run lint` (ESLint; `main` already has about 22 existing problems, so compare counts rather than expecting a clean run) and `npm --prefix frontend run build` (runs `tsc -b`, so it is also the type check). The frontend has no test runner.

`.claude/launch.json` defines the `api` and `dev` preview servers.

## Configuration

Settings come from the environment or `.env` (see `.env.example`). Required: `DATABASE_URL`, `JWT_SECRET_KEY` (at least 32 chars), `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`. Optional deployment settings are in `app/settings.py`: `FRONTEND_URL`, `PUBLIC_API_URL`, `CORS_ORIGINS`, `COOKIE_SAMESITE`, `COOKIE_SECURE`, `ENABLE_DOCS`, `SQL_ECHO` and `UPLOAD_DIR`, plus the shipping and tax settings `SHIPPING_FLAT_RATE`, `FREE_SHIPPING_THRESHOLD`, `STRIPE_AUTOMATIC_TAX` and `STRIPE_PRODUCT_TAX_CODE`, and the email settings `RESEND_API_KEY`, `EMAIL_FROM`, `ORDERS_EMAIL_FROM`, `ACCOUNT_EMAIL_FROM`, `EMAIL_REPLY_TO` and `PASSWORD_RESET_MINUTES`. Their defaults suit local development. The frontend reads the API address from `VITE_API_URL` at build time (`frontend/.env.example`), falling back to the local API.

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
  - Use `CurrentUser` for a logged-in user, `OptionalUser` where guests are welcome too (it gives `None` for no token or an invalid/expired one, so a stale cookie never blocks a guest), and `Depends(admin_required)` (`app/auth/dependencies.py`) for admin routes.
  - Resources owned by a user return 404, not 403, to anyone other than the owner (or an admin).
- **Orders exist only through Stripe Checkout:**
  1. `POST /payments/create-checkout-session` (`OptionalUser`) checks and prices what's being bought with `price_items()` (positive quantities, active products, stock), totalling quantities per product. A logged-in shopper checks out their server cart with two saved address ids. A guest sends `items` (their browser cart, product ids and quantities only), and Stripe Checkout collects their email, US shipping and billing addresses, and phone.
  2. It stores a `[product_id, qty, unit_cents]` snapshot, one entry per product, in the session metadata (Stripe allows 500 characters per value), with `user_id` and the address ids for an account or `guest: "1"` for a guest. It sends Stripe one line item per product (prices exclude tax), a flat shipping rate from `shipping_cents()` (free from `FREE_SHIPPING_THRESHOLD`), and, with `STRIPE_AUTOMATIC_TAX` on, `automatic_tax`, plus for accounts the user's Stripe Customer from `get_stripe_customer()`, whose shipping address Stripe Tax uses (for guests Stripe Tax uses the address they enter). Only US shipping addresses are accepted.
  3. `fulfill_checkout()` creates the order from that snapshot, not from the current cart, and records Stripe's subtotal, shipping, tax and total on it. A guest order has no `user_id` or address ids; its email, name and addresses come from the session's `customer_details` and shipping details (`collected_information.shipping_details` on newer Stripe API versions, top-level `shipping_details` on older ones such as the CLI's). Both the webhook and `GET /payments/session/{id}` call it as a fallback, so it is idempotent per `stripe_session_id`: accounts lock their cart row, and the unique `stripe_session_id` catches a racing guest fulfillment (`already_fulfilled()` rolls ours back).
  4. `GET /payments/session/{id}` shows an account's order only to its owner (or an admin), and a guest order to whoever has the session id, which only the buyer's browser gets back from Stripe. It also returns the order's `access_token` for the success page's tracking link.

  There is deliberately no route that creates an order or charges an amount supplied by the client; tests in `tests/api/test_security.py` check that.
- **Money:** prices and amounts are `DECIMAL(10,2)` columns (`Decimal` in the models) and cents when talking to Stripe; convert with `to_cents`/`from_cents` in `app/money.py` and never do money arithmetic in `float`. API schemas expose them as `float` so JSON keeps numbers. Order items keep the `unit_price` paid, which the order pages show instead of the product's current price.
- **Order tracking without an account:** every order gets a random `access_token`. The emails link to `/track/{order_number}?token=...` in the frontend, which calls `GET /orders/track/{order_number}?token=`. `POST /orders/lookup` turns an order number plus the order's email (case-insensitive) into that link, with the same 404 when either is wrong. `OrderRead` never includes the token. Guest orders never join an account, even one with the same email, because guest emails aren't verified.
- **Addresses on orders:** `fulfill_checkout()` copies both addresses onto the order (`Order.shipping_address`/`billing_address` JSON, shaped like `OrderAddress` in `app/schemas/address.py`, built with `address_snapshot()`, or `stripe_address_snapshot()` for a guest's Stripe-collected address; guest orders have no saved address ids). Responses show that copy, so editing a saved address never changes a past order. Deleting an address only sets `deleted_at` (listing, editing and checkout ignore it), because orders and checkouts in progress still reference the row.
- **User deletion:** deleting a user goes through `database_user_has_orders`/`database_delete_user` (`app/database/users.py`). Users with orders are kept, since orders are financial records. Likewise, a product that appears in an order can't be deleted (409); admins set it inactive instead.
- **Email:** `app/mail.py` builds messages (`build_*_email`) while the request still has the database, and routes queue `send_email` as a FastAPI `BackgroundTask`. `send_email` logs failures and never raises. It goes through Resend, or prints the message when `RESEND_API_KEY` is empty. Each builder sets the message's sender: order and shipping emails use `orders_email_from()` and account emails `account_email_from()`, both falling back to `EMAIL_FROM`; every email gets `EMAIL_REPLY_TO` as its reply-to when set. Order emails go to `Order.email` (the account's email at checkout, or the one a guest gave Stripe) and link to the order's tracking page via `order_link()`. Order confirmations go out only when `fulfill_checkout()` creates a paid order, so the webhook and success page don't send duplicates. Shipping notices go out from `PUT /orders/{id}/tracking`.
- **Password reset:** `POST /auth/forgot-password` gives the same answer for unknown emails and sends at most one link per user per minute. The `PasswordResetToken` table stores only the SHA-256 of the emailed token. `POST /auth/reset-password` uses a link once and cancels the user's other links. Existing JWTs stay valid until they expire.
- **Cart:** the server cart (`/cart`, login only) belongs to accounts; guests keep theirs in the browser. Adding a product already in the cart raises that row's quantity rather than adding a row. Quantities are 1 to `MAX_CART_QUANTITY` (`app/schemas/cart_item.py`) and can't exceed stock. `POST /cart/merge` adds a guest's browser cart after login, capping at stock and the maximum and skipping inactive or missing products.
- **Uploads:** product images go through `save_uploads()` in `app/routes/product.py`. It checks every file (image extensions only, 5 MB each) before writing any, saves under random names in the module-level `UPLOAD_DIR` (from `upload_dir()` in `app/settings.py`), and returns absolute URLs built from `PUBLIC_API_URL` (falling back to the request's base URL). The product create/update routes are plain `def` so this I/O runs in FastAPI's threadpool.

## Frontend architecture

- `frontend/src/api/axiosClient.ts` calls `VITE_API_URL` (locally `http://127.0.0.1:8000/api`) with `withCredentials` (cookie auth). That is a different site from `localhost:5173`, which is why the cookie defaults to `SameSite=None`.
- API helpers live in `frontend/src/api/*`. Use `apiErrorMessage()` from `api/errors.ts` to show FastAPI `detail` errors (including the first 422 validation message).
- App-wide state (auth, cart, categories) is in `frontend/src/context/`. `CartContext` is the one cart API for pages: it uses the server cart when logged in and localStorage (`guest_cart`) for guests, merges the guest cart through `/cart/merge` on login, and `reload()` re-runs its loader (cancelling any load in flight).
- Routes and the public-only/protected/admin guards are in `frontend/src/router/AppRouter.tsx`. Shopping is open to everyone: products, cart, checkout, `/order-success` and `/track` (lookup form) and `/track/:order_number` (token link). `/account` and `/orders` need a login, and `ProtectedRoute` passes `state.from` so login (and register, which forwards the state to login) returns there. `components/orders/OrderView.tsx` renders one order for both the account order page and the tracking page.
- Styling is Tailwind, with MUI in the admin pages.

## Tests

- **Setup:** `tests/conftest.py` sets every environment variable before importing `app`. Each test gets a fresh in-memory SQLite database with foreign keys enforced (to behave like MySQL), wired in by overriding `get_session`. `TestClient` is not used as a context manager, so the startup checks don't run.
- **Fixtures:**
  - Factories: `make_user`, `make_category`, `make_product`, `make_address`, `add_to_cart` and `make_order` (`make_order(None)` makes a guest order with an email and address copies but no saved addresses; every order gets an `access_token`).
  - Clients: `user_client` and `admin_client` share a single `client`. For tests with several users, use `client` with `auth_headers(user)`.
  - `upload_dir` redirects uploads to a temp folder.
- **Email:** the autouse `sent_emails` fixture replaces `app.mail.deliver` and returns the list of `EmailMessage`s the app sent.
- **Stripe:** Stripe is never called. The autouse `stripe_customers` fixture in `tests/conftest.py` fakes `stripe.Customer.create/modify` and records the calls. Tests build objects with `stripe.<Type>.construct_from(...)` and monkeypatch `stripe.checkout.Session.create/retrieve`, `stripe.Webhook.construct_event` and `stripe.PaymentIntent.retrieve` (see `tests/api/test_payments_api.py`, whose `guest_checkout_session()` builds a paid guest session).
- **Layout:** tests are split into `tests/unit/`, `tests/api/` and top-level files (app wiring, migrations). The test folders have no `__init__.py`, so test file names must be unique across folders. Import shared constants with `from conftest import TEST_PASSWORD`.
- **Warnings:** `pytest.ini` hides only the deprecations the app is known to use (`datetime.utcnow()`, `on_event`, class-based Pydantic `Config`); any other warning shows in the test summary.
- **Expiry gotcha:** after a request changes data, call `session.expire_all()` before reading it back through the test `session`. Keep ids in local variables, because expired ORM objects can't be read once their row is gone.
