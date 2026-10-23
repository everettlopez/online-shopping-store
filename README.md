# Online Shopping Store
An open-source online store you can host yourself: a FastAPI + MySQL backend, a React storefront, Stripe Checkout for payments, and Resend for email. Everything that makes a store yours, its name, domain, policies, photos, shipping prices and email addresses, is a setting, so you run your own store without changing any code.

## Features
- **Shopping without an account:** customers browse, filter and sort products and keep a cart in the browser. They pay through Stripe Checkout, which collects a guest's email and US shipping and billing addresses.
- **Accounts:** saved addresses, order history, and a cart that follows the customer between devices (a guest's cart joins it on login).
- **Payments, tax and shipping:** Stripe Checkout with optional Stripe Tax for sales tax, a flat shipping rate with free shipping above a threshold, and orders created only from completed payments.
- **Order tracking:** confirmation and shipping emails link to a private tracking page, and customers can find an order from its number and email.
- **Admin pages:** products (with images, sizes, colors and stock), categories, orders (status and tracking numbers) and users.
- **Policy pages:** Privacy, Terms, Shipping & Returns and Contact, filled in from your settings.
- **Built for production:** a one-command deploy kit with automatic HTTPS and security headers, rate limiting, a CSRF guard, database migrations, a health check, and an automated launch check.

## Documentation
| | |
| --- | --- |
| [Development Setup](#development-setup) | Run the store on your computer |
| [Make It Your Store](#make-it-your-store) | Your name, photos, policies and prices |
| [docs/hosting.md](docs/hosting.md) | Host a live store on your own server |
| [docs/launch-checklist.md](docs/launch-checklist.md) | Checks before your first order and after every update |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Report bugs and contribute changes |
| [SECURITY.md](SECURITY.md) | Report a vulnerability privately |
| [CLAUDE.md](CLAUDE.md) | Architecture and conventions in detail |

## Tech Stack
- **Backend:** FastAPI, SQLModel/SQLAlchemy, Pydantic, Alembic migrations, JWT cookie auth, Stripe, Resend, pytest.
- **Frontend:** React, TypeScript, Vite, React Router, Tailwind CSS, MUI (admin pages), Axios.
- **Database:** MySQL 8.
- **Deployment:** Docker, Docker Compose, Caddy, nginx, GitHub Actions CI.

## Development Setup
This project uses a decoupled architecture with separate frontend and backend services. Each service runs independently during development and communicates over HTTP. The following instructions describe how to run the application locally.

### Prerequisites
- Node.js (v20+)
- Python (3.14+)
- MySQL server
- Git
- Recommended: VS Code with REST client or Bruno

### 1. Database (MySQL)
1. Make sure MySQL is running locally.
2. Create the database:
```sql
CREATE DATABASE online_store;
```
Tables are created by the database migrations in step 3 (the backend only seeds starter categories when it starts).

### 2. Environment variables
Copy `.env.example` to `.env` in the project root and fill in your values:
```
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/online_store
JWT_SECRET_KEY=<at least 32 random characters>
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```
`JWT_SECRET_KEY` must be at least 32 characters (generate one with `venv\Scripts\python -c "import secrets; print(secrets.token_urlsafe(48))"`), and both Stripe keys must be set, or the API refuses to start. `.env.example` also lists the store's name for emails (`STORE_NAME`), optional deployment settings (`FRONTEND_URL`, `PUBLIC_API_URL`, `CORS_ORIGINS`, `COOKIE_SAMESITE`, `COOKIE_SECURE`, `ENABLE_DOCS`, `SQL_ECHO`) the shipping and tax settings (`SHIPPING_FLAT_RATE`, `FREE_SHIPPING_THRESHOLD`, `STRIPE_AUTOMATIC_TAX`, `STRIPE_PRODUCT_TAX_CODE`) and the email settings (`RESEND_API_KEY`, `EMAIL_FROM`, `ORDERS_EMAIL_FROM`, `ACCOUNT_EMAIL_FROM`, `EMAIL_REPLY_TO`, `PASSWORD_RESET_MINUTES`), alerts and logging (`ALERT_EMAIL`, `LOG_LEVEL`) and the rate limits (`AUTH_RATE_LIMIT_PER_MINUTE`, `LOOKUP_RATE_LIMIT_PER_MINUTE`, `CHECKOUT_RATE_LIMIT_PER_MINUTE`); their defaults suit local development. Without `RESEND_API_KEY`, the API prints emails (password reset links, order confirmations, shipping notices) in its terminal instead of sending them. For production, set `FRONTEND_URL`, `PUBLIC_API_URL` and `CORS_ORIGINS` to your real addresses, `ENABLE_DOCS=false`, and `COOKIE_SAMESITE=lax` if the frontend and API share a site.

`.env` is gitignored, so never commit real keys. Percent-encode special characters in the DB password (for example, `@` becomes `%40`).

### 3. Backend (FastAPI)
From the project root:
```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

Then create or update the database tables with Alembic (it reads `DATABASE_URL` from `.env`):
```bash
venv\Scripts\alembic upgrade head      # Windows
venv/bin/alembic upgrade head          # macOS/Linux
```
If your database was created before the project used Alembic (when tables were created automatically at startup), the same command works: the first migration sees the existing tables and leaves them alone. Run this again whenever you pull new files in `alembic/versions/`; the backend refuses to start until the database is up to date. After changing a model, generate a migration with `alembic revision --autogenerate -m "describe the change"`, review the generated file, then run `alembic upgrade head`.

### 4. Frontend (React + TypeScript)
```bash
npm install --prefix frontend
```

### 5. Run the servers
Use a separate terminal for each, from the project root:
```bash
venv\Scripts\python -m uvicorn app.main:app --reload    # Terminal 1: API
npm --prefix frontend run dev                           # Terminal 2: frontend
stripe listen --forward-to localhost:8000/api/payments/webhook --events checkout.session.completed,checkout.session.async_payment_succeeded,checkout.session.async_payment_failed,charge.refunded    # Terminal 3: Stripe webhooks
```
Copy the `whsec_...` secret that `stripe listen` prints into `STRIPE_WEBHOOK_SECRET`, and make sure the Stripe CLI is logged in to the same account as `STRIPE_SECRET_KEY`. Use your Stripe **test** keys locally, and pay with Stripe's test card `4242 4242 4242 4242`. Unless you've set up Stripe Tax in test mode, set `STRIPE_AUTOMATIC_TAX=false` in `.env`, or checkout fails.

> **Windows:** keep the API in its own terminal and start it with Python directly, not through npm. When uvicorn auto-reloads after a `.py` change, it sends Ctrl+C to every process in its terminal, which would stop anything else running there and leave the old API process in the background.

- Frontend: http://localhost:5173
- API: http://localhost:8000/api (docs at http://localhost:8000/docs)

To use the admin pages, register an account on the storefront, then make it an admin from the project root:
```bash
venv\Scripts\python -m app.create_admin you@example.com
```
After that, admins can make other users admins from the admin **Users** page.

### 6. Run the tests
The backend test suite lives in `tests/`. It runs against a throwaway in-memory SQLite database and mocks Stripe, so it doesn't need MySQL, a `.env` file or network access. From the project root:
```bash
venv\Scripts\pip install -r requirements-dev.txt
venv\Scripts\python -m pytest
```
Add `-x` to stop at the first failure, or pass a path to run part of the suite (for example `venv\Scripts\python -m pytest tests/api/test_cart_api.py`). Shared fixtures and test-data factories are in `tests/conftest.py`.

## Make It Your Store
Everything that identifies a store is a setting, so you run your own store without changing any code.

- **Storefront** (`frontend/.env.example`, set at build time): `VITE_STORE_NAME` (page title, footer and policy pages), `VITE_STORE_LOGO_TEXT` (the wordmark at the top, default the name in capitals), `VITE_STORE_DESCRIPTION` (meta description), `VITE_SUPPORT_EMAIL`, and for the policy pages `VITE_BUSINESS_NAME`, `VITE_BUSINESS_ADDRESS`, `VITE_BUSINESS_STATE` and `VITE_RETURN_DAYS`. Locally, put them in `frontend/.env.local`.
- **Emails** (`.env.example`): `STORE_NAME` appears in email subjects and signatures. The senders are `EMAIL_FROM`, `ORDERS_EMAIL_FROM`, `ACCOUNT_EMAIL_FROM` and `EMAIL_REPLY_TO`.
- **Shipping:** `SHIPPING_FLAT_RATE` and `FREE_SHIPPING_THRESHOLD` set what checkout charges, and the Shipping & Returns page shows the same numbers.
- **Home page** (`frontend/.env.example`):
  - `VITE_HERO_HEADLINE` and `VITE_HERO_IMAGE_URL` set the headline and photo at the top.
  - `VITE_BANNER_IMAGE_URL` adds a full-width photo further down.
  - `VITE_EVENTS_URL` adds an Events link and button.
  - Put your photos in [`frontend/public/custom/`](frontend/public/custom/README.md) (git ignores them) and use `/custom/<file name>`.
- **Categories and products** come from the admin pages. A new store starts with a few example categories, which you can rename or delete.

### Policy pages
The storefront has Privacy Policy, Terms of Service, Shipping & Returns and Contact pages (`/privacy`, `/terms`, `/shipping-returns`, `/contact`), linked from the footer and filled in from the settings above. **Their wording is a general starting point, not legal advice.** Read them and have them reviewed for your business before you take real orders. If you have your own policies (from a lawyer or a policy service), set `VITE_PRIVACY_POLICY_URL`, `VITE_TERMS_URL` and `VITE_SHIPPING_POLICY_URL`, and the footer links there instead. Stripe expects a live store to show a refund policy and a way to contact you.

## Deployment
The quickest way to run a live store is the deploy kit in `deploy/`: one server running the API, the storefront and [Caddy](https://caddyserver.com) (which gets HTTPS certificates and adds security headers) with Docker Compose. CI (`.github/workflows/ci.yml`) runs the tests, builds the frontend and both images, and checks the kit's files on every push and pull request.

### Host your store on a server
**[docs/hosting.md](docs/hosting.md)** walks through the whole setup on any Linux server (a VPS with at least 2 GB of RAM), using only settings files:
1. Server.
2. DNS.
3. Managed MySQL or MySQL on the same server.
4. Resend email with SPF, DKIM and DMARC.
5. Stripe live mode, Stripe Tax and the webhook.
6. The two settings files.
7. Start.
8. First admin.
9. Checks before you take orders.

It also covers updating, backups, Cloudflare's proxy and troubleshooting. Before taking orders, and after every update, work through **[docs/launch-checklist.md](docs/launch-checklist.md)**:
- `sh deploy/check.sh` runs the automated checks.
- The rest are checks by hand, a real purchase and refund, and rolling back.

In short:
```bash
cp deploy/.env.example deploy/.env       # domains and the storefront's name and details
cp .env.example deploy/.env.api          # the API's secrets and settings
docker compose -f deploy/docker-compose.yml up -d --build
docker compose -f deploy/docker-compose.yml exec api python -m app.create_admin you@example.com
```

### Production settings
The API image runs `alembic upgrade head` and then uvicorn (`docker/start-api.sh`). Configure it with the environment variables from `.env.example`. For production:
- Use live Stripe keys, and the `whsec_...` secret of a webhook endpoint registered in the Stripe Dashboard for `https://<api host>/api/payments/webhook` with the events `checkout.session.completed`, `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed` and `charge.refunded`.
- Set up Stripe Tax in the live Dashboard (business address, and a registration for every state where you collect sales tax). Checkout asks Stripe Tax for the tax, and Stripe refuses the checkout if Stripe Tax isn't set up. Sales tax is charged only where you're registered.
- In the Stripe Dashboard's payment method settings, turn off methods that take days to settle (ACH Direct Debit and other bank debits). The store handles them (the order waits as pending, then becomes placed when the money arrives, or cancelled with its stock returned when the payment fails), but the item is held for days and may never be paid for.
- Set `FRONTEND_URL`, `PUBLIC_API_URL` and `CORS_ORIGINS` to the real addresses, and set `ENABLE_DOCS=false`. Set `COOKIE_SAMESITE=lax` if the storefront and API share a site (for example `shop.example.com` and `api.example.com`).
- Email goes through [Resend](https://resend.com). Add your domain in the Resend dashboard, create the DNS records it lists (SPF and DKIM) so mail isn't marked as spam, then set `RESEND_API_KEY` and `EMAIL_FROM` (for example `Your Store <orders@example.com>`). Optionally send order and shipping emails from `ORDERS_EMAIL_FROM` and password resets from `ACCOUNT_EMAIL_FROM`, and set `EMAIL_REPLY_TO` to an inbox people read, since Resend only sends and replies to an address with no mailbox bounce. The default sender, `onboarding@resend.dev`, only delivers to your own Resend account's email. Without `RESEND_API_KEY`, customers get no emails and reset links end up in the logs.
- **Mount a persistent volume at `/data/uploads`** (the image sets `UPLOAD_DIR` to it; the deploy kit does this). Without one, product images are lost on every deploy.
- Use a managed MySQL with automated backups.
- Set `ALERT_EMAIL` to an inbox you read. The store emails it about problems that need a person: an oversold item, a failed Stripe webhook, checkout or a refund failing, or a server error (each at most once every 15 minutes). Check it works with `python -m app.alerts` inside the API container. Logs are one line per event (`time level logger message key=value`) at `LOG_LEVEL` (default `INFO`).
- Create the first admin once the API is running: register on the storefront, then run `python -m app.create_admin you@example.com` inside the API container.
- Login, registration, password reset, order lookup and checkout are rate limited per visitor IP (`AUTH_RATE_LIMIT_PER_MINUTE` and the others in `.env.example`). The counts live in each worker's memory, so they suit a single server. The limits need the visitor's real IP, so keep `--proxy-headers` and trust only your proxy in `FORWARDED_ALLOW_IPS` if the API port is reachable from anywhere else.
- Optional: `PORT` (default 8000), `WEB_CONCURRENCY` (worker processes, default 2) and `FORWARDED_ALLOW_IPS` (proxies trusted for `X-Forwarded-*`, default all). With several replicas, set `RUN_MIGRATIONS=false` on all but one, or run `alembic upgrade head` as a release step.

Outside the deploy kit, the host must terminate HTTPS. `GET /api/health` returns 200 when the database is reachable and 503 when it isn't, for health checks and uptime monitors.

### Other hosts
The API and storefront are separate Docker images, so they also run on container platforms. Build the API image from the project root with `docker build -t shop-api .`, and give it the settings above.

The storefront image is built with:
```bash
docker build --build-arg VITE_API_URL=https://api.example.com/api -t shop-web frontend
```
`VITE_API_URL` is baked into the bundle at build time (see `frontend/.env.example`), as are the store's name and policy details: pass them as more build arguments, for example `--build-arg VITE_STORE_NAME="Your Store" --build-arg VITE_SUPPORT_EMAIL=support@example.com`. The image serves the built site with nginx (`frontend/nginx.conf`), sending every unknown path to `index.html` so links like `/orders/abc` work. If you use a static host (Netlify, Vercel, Cloudflare Pages) instead, run `npm run build` with `VITE_API_URL` set, publish `frontend/dist`, and add the host's single-page-app rewrite to `/index.html`.

## Contributing
Contributions are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md). Please report security problems privately as described in [SECURITY.md](SECURITY.md).

## License
The code is released under the [MIT License](LICENSE). The default home page photo has its own license; see [frontend/src/assets/CREDITS.md](frontend/src/assets/CREDITS.md).

Created by Everett Lopez, Salt Lake City, UT.