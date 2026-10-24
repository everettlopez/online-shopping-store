# Online Shopping Store

[![CI](https://github.com/everettlopez/online-shopping-store/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/everettlopez/online-shopping-store/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/everettlopez/online-shopping-store)](https://github.com/everettlopez/online-shopping-store/releases/latest)
[![License: MIT](https://img.shields.io/github/license/everettlopez/online-shopping-store)](LICENSE)
![Python 3.15](https://img.shields.io/badge/python-3.15-3776AB?logo=python&logoColor=white)
![Node 24](https://img.shields.io/badge/node-24-5FA04E?logo=nodedotjs&logoColor=white)
![Deploy with Docker Compose](https://img.shields.io/badge/deploy-Docker%20Compose-2496ED?logo=docker&logoColor=white)

An open-source online store you can host yourself: a FastAPI + MySQL backend, a React storefront, Stripe Checkout for payments, and Resend for email. Everything that makes a store yours, its name, domain, policies, photos, shipping prices and email addresses, is a setting, so you run your own store without changing any code.

## Features
- **Shopping without an account:** customers browse, filter and sort products and keep a cart in the browser. They pay through Stripe Checkout, which collects a guest's email and US shipping and billing addresses.
- **Accounts:** saved addresses, order history, and a cart that follows the customer between devices (a guest's cart joins it on login).
- **Payments, tax and shipping:** Stripe Checkout with optional Stripe Tax for sales tax, a flat shipping rate with free shipping above a threshold, and orders created only from completed payments.
- **Order tracking:** confirmation and shipping emails link to a private tracking page, and customers can find an order from its number and email.
- **Admin pages:** products (with images, sizes, colors and stock), categories, orders (status, tracking numbers and refunds) and users.
- **Policy pages:** Privacy, Terms, Shipping & Returns and Contact, filled in from your settings.
- **Built for production:** a one-command deploy kit with automatic HTTPS and security headers, rate limiting, a CSRF guard, database migrations, backups with restore, email alerts, a health check, and an automated launch check.

## Quick start for store owners
You don't need to write code to run a store. You need:
- a Linux server with at least 2 GB of RAM (a VPS from DigitalOcean, Hetzner, Linode or similar, from about $12 a month),
- a domain name whose DNS you can edit,
- a [Stripe](https://stripe.com) account (payments) and a [Resend](https://resend.com) account (email),
- a mailbox at your domain that receives replies from customers,
- about two hours of work (plus waiting for DNS and account checks), and some comfort copying commands into a terminal.

**[docs/hosting.md](docs/hosting.md)** walks you through every step, from a fresh server to a live store, and says what you should see after each one. Then work through **[docs/launch-checklist.md](docs/launch-checklist.md)** before your first real order. If something goes wrong, **[docs/troubleshooting.md](docs/troubleshooting.md)** lists the common problems and their fixes.

Stores run a **[release](https://github.com/everettlopez/online-shopping-store/releases)**, not the latest `main`, so you only ever install a tested version. Each release's notes say what changed and whether you need to do anything before updating.

## Documentation
| | |
| --- | --- |
| [docs/hosting.md](docs/hosting.md) | Host a live store on your own server, update it and back it up |
| [docs/launch-checklist.md](docs/launch-checklist.md) | Checks before your first order, after every update, and how to roll back |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common problems, how to ask for help, and trusted references |
| [Make It Your Store](#make-it-your-store) | Your name, photos, policies and prices |
| [Development Setup](#development-setup) | Run the store on your computer |
| [CHANGELOG.md](CHANGELOG.md) | What changed in each release |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Report bugs and contribute changes |
| [SECURITY.md](SECURITY.md) | Report a vulnerability privately |
| [CLAUDE.md](CLAUDE.md) | Architecture and conventions in detail |

## Getting help
- **Setting up or running a store:** read [docs/troubleshooting.md](docs/troubleshooting.md), then ask in [Discussions](https://github.com/everettlopez/online-shopping-store/discussions) (Q&A).
- **Found a bug, or have an idea:** [open an issue](https://github.com/everettlopez/online-shopping-store/issues/new/choose). The forms ask for what helps fix it.
- **A security problem:** don't post it publicly. Report it privately as described in [SECURITY.md](SECURITY.md).

Never post your settings files, API keys, passwords or customers' details. See [what to collect before asking](docs/troubleshooting.md#collect-this-before-asking-for-help).

## Tech Stack
- **Backend:** FastAPI, SQLModel/SQLAlchemy, Pydantic, Alembic migrations, JWT cookie auth, Stripe, Resend, pytest.
- **Frontend:** React, TypeScript, Vite, React Router, Tailwind CSS 4, MUI (admin pages), Axios. The storefront supports current browsers: Safari 16.4+, Chrome and Edge 111+, Firefox 128+ (Tailwind 4's minimum).
- **Database:** MySQL 8.
- **Deployment:** Docker, Docker Compose, Caddy, nginx, GitHub Actions CI.

## Development Setup
This section is for people changing the code. To run a store, follow [docs/hosting.md](docs/hosting.md) instead.

The API and the storefront are separate services. During development each runs on its own and they talk over HTTP.

### Prerequisites
- Python 3.15 and Node.js 24 (the versions CI and the Docker images use)
- MySQL 8
- Git
- The [Stripe CLI](https://docs.stripe.com/stripe-cli), to forward test payments to your computer
- Recommended: VS Code with a REST client, or Bruno

The commands below are for Windows, where the project is developed. On macOS and Linux, use `venv/bin/` in place of `venv\Scripts\`.

### 1. Database (MySQL)
1. Make sure MySQL is running locally.
2. Create the database:
   ```sql
   CREATE DATABASE online_store;
   ```
The database migrations in step 3 create the tables. When the backend starts, it only adds a few starter categories.

### 2. Environment variables
Copy `.env.example` to `.env` in the project root and fill in these four values; the API refuses to start without them:
```
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/online_store
JWT_SECRET_KEY=<at least 32 random characters>
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```
- Generate `JWT_SECRET_KEY` with `venv\Scripts\python -c "import secrets; print(secrets.token_urlsafe(48))"` (after step 3 creates the virtualenv).
- Use your Stripe **test** key locally. `STRIPE_WEBHOOK_SECRET` comes from `stripe listen` in step 5.
- Percent-encode special characters in the database password (`@` becomes `%40`; see the [table in the hosting guide](docs/hosting.md#percent-encoding-a-password)).
- Unless you've set up Stripe Tax in test mode, also set `STRIPE_AUTOMATIC_TAX=false`, or checkout fails.

Every other setting in `.env.example` has a comment and a default that suits local development. Without `RESEND_API_KEY`, the API prints emails (password reset links, order confirmations, shipping notices) in its terminal instead of sending them.

`.env` is gitignored. Never commit real keys.

### 3. Backend (FastAPI)
From the project root:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt
```
`requirements-dev.txt` installs the app plus the tests and auto-reload.

Then create or update the database tables (Alembic reads `DATABASE_URL` from `.env`):
```bash
venv\Scripts\alembic upgrade head
```
Run this again whenever you pull new files in `alembic/versions/`; the backend refuses to start until the database is up to date. If your database was created before the project used Alembic, the same command works: the first migration sees the existing tables and leaves them alone.

After changing a model, generate a migration with `venv\Scripts\alembic revision --autogenerate -m "describe the change"`, review the generated file (including its `downgrade()`), then run `alembic upgrade head`.

### 4. Frontend (React + TypeScript)
```bash
npm install --prefix frontend
```

### 5. Run the servers
Use a separate terminal for each, from the project root:
```bash
venv\Scripts\python -m uvicorn app.main:app --reload
```
```bash
npm --prefix frontend run dev
```
```bash
stripe listen --forward-to localhost:8000/api/payments/webhook --events checkout.session.completed,checkout.session.async_payment_succeeded,checkout.session.async_payment_failed,charge.refunded
```
Copy the `whsec_...` secret that `stripe listen` prints into `STRIPE_WEBHOOK_SECRET` and restart the API. The Stripe CLI must be logged in (`stripe login`) to the same account as `STRIPE_SECRET_KEY`. Pay with Stripe's [test card](https://docs.stripe.com/testing) `4242 4242 4242 4242`, any future date and any CVC.

> [!NOTE]
> **Windows:** keep the API in its own terminal and start it with Python directly, not through npm. When uvicorn auto-reloads after a `.py` change, it sends Ctrl+C to every process in its terminal, which would stop anything else running there and leave the old API process in the background.

- Storefront: http://localhost:5173
- API: http://localhost:8000/api (docs at http://localhost:8000/docs)

To use the admin pages, register an account on the storefront, then make it an admin from the project root:
```bash
venv\Scripts\python -m app.create_admin you@example.com
```
Log out and in again to see the admin pages. After that, admins can make other users admins from the admin **Users** page.

### 6. Run the tests
The backend tests in `tests/` run against a throwaway in-memory SQLite database and mock Stripe, so they need no MySQL, `.env` or network access:
```bash
venv\Scripts\python -m pytest
```
Add `-x` to stop at the first failure, or pass a path to run part of the suite (for example `venv\Scripts\python -m pytest tests/api/test_cart_api.py`). Shared fixtures and test-data factories are in `tests/conftest.py`. [CONTRIBUTING.md](CONTRIBUTING.md#check-it) lists the lint and build checks too.

## Make It Your Store
Everything that identifies a store is a setting, so you run your own store without changing any code. On a live store, these go in the two settings files described in [hosting.md step 6](docs/hosting.md#6-get-the-code-and-fill-in-the-settings).

- **Storefront** (`frontend/.env.example`, set at build time): `VITE_STORE_NAME` (page title, footer and policy pages), `VITE_STORE_LOGO_TEXT` (the wordmark at the top, default the name in capitals), `VITE_STORE_DESCRIPTION` (meta description), `VITE_SUPPORT_EMAIL`, and for the policy pages `VITE_BUSINESS_NAME`, `VITE_BUSINESS_ADDRESS`, `VITE_BUSINESS_STATE` and `VITE_RETURN_DAYS`. Locally, put them in `frontend/.env.local`.
- **Emails** (`.env.example`): `STORE_NAME` appears in email subjects and signatures. The senders are `EMAIL_FROM`, `ORDERS_EMAIL_FROM`, `ACCOUNT_EMAIL_FROM` and `EMAIL_REPLY_TO`.
- **Shipping:** `SHIPPING_FLAT_RATE` and `FREE_SHIPPING_THRESHOLD` set what checkout charges, and the Shipping & Returns page shows the same numbers.
- **Home page** (`frontend/.env.example`):
  - `VITE_HERO_HEADLINE` and `VITE_HERO_IMAGE_URL` set the headline and photo at the top.
  - `VITE_BANNER_IMAGE_URL` adds a full-width photo further down.
  - `VITE_EVENTS_URL` adds an Events link and button.
- **Icon and link previews:** `VITE_FAVICON_URL` sets the browser-tab icon (default: a shopping bag). Links shared on social media and in messages preview with the store name, `VITE_STORE_DESCRIPTION` and `VITE_SHARE_IMAGE_URL` (default: the hero photo).
  - Put your photos (and icon) in [`frontend/public/custom/`](frontend/public/custom/README.md) (git ignores them) and use `/custom/<file name>`. On a live store they must be copied to the server too, or kept in [your own private copy](docs/hosting.md#run-from-your-own-private-copy) of the code.
- **Your accounts and data:** the store talks only to your Stripe and Resend accounts and keeps everything else on your own server and database; see [Accounts and access](docs/hosting.md#accounts-and-access).
- **Categories and products** come from the admin pages. A new store starts with a few example categories, which you can rename or delete.

### Policy pages
The storefront has Privacy Policy, Terms of Service, Shipping & Returns and Contact pages (`/privacy`, `/terms`, `/shipping-returns`, `/contact`), linked from the footer and filled in from the settings above.

> [!IMPORTANT]
> **Their wording is a general starting point, not legal advice.** Read them and have them reviewed for your business before you take real orders. If you have your own policies (from a lawyer or a policy service), set `VITE_PRIVACY_POLICY_URL`, `VITE_TERMS_URL` and `VITE_SHIPPING_POLICY_URL`, and the footer links there instead. Stripe expects a live store to show a refund policy and a way to contact you.

## Deployment
The quickest way to run a live store is the deploy kit in `deploy/`: one server running the API, the storefront and [Caddy](https://caddyserver.com) (which gets HTTPS certificates and adds security headers) with Docker Compose. CI (`.github/workflows/ci.yml`) runs the tests, builds the frontend and both images, and checks the kit's files on every push and pull request. It also runs the migrations on MySQL 8.4 (up, a model check, down and up again), audits the Python and npm dependencies and both images for known vulnerabilities, scans the history for committed secrets and lints the shell scripts.

### Host your store on a server
**[docs/hosting.md](docs/hosting.md)** walks through the whole setup on any Linux server (a VPS with at least 2 GB of RAM), using only settings files:
1. Server.
2. DNS.
3. Managed MySQL or MySQL on the same server.
4. Resend email with SPF, DKIM and DMARC.
5. Stripe live mode, Stripe Tax and the webhook.
6. The code at the latest release, and the two settings files.
7. Start.
8. First admin.
9. Checks before you take orders.

It also covers updating to a new release, backups, Cloudflare's proxy and running from your own private copy. Before taking orders, and after every update, work through **[docs/launch-checklist.md](docs/launch-checklist.md)**:
- `sh deploy/check.sh` runs the automated checks.
- The rest are checks by hand, a real purchase and refund, and rolling back.

In short, on the server:
```bash
git clone https://github.com/everettlopez/online-shopping-store.git
cd online-shopping-store
git checkout "$(git tag --list 'v*' --sort=-v:refname | head -n 1)"   # the latest release
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
- Set `ENVIRONMENT=production` (the deploy kit does). The API then refuses to start with development settings: docs on, insecure cookies, local or plain-http addresses, no `RESEND_API_KEY`, Resend's test sender, or a Stripe test key (`ALLOW_STRIPE_TEST_MODE=true` allows one for a trial run).
- Set `FRONTEND_URL`, `PUBLIC_API_URL` and `CORS_ORIGINS` to the real addresses, and set `ENABLE_DOCS=false`. Set `COOKIE_SAMESITE=lax` if the storefront and API share a site (for example `shop.example.com` and `api.example.com`).
- Email goes through [Resend](https://resend.com). Add your domain in the Resend dashboard, create the DNS records it lists (SPF and DKIM) so mail isn't marked as spam, then set `RESEND_API_KEY` and `EMAIL_FROM` (for example `Your Store <orders@example.com>`). Optionally send order and shipping emails from `ORDERS_EMAIL_FROM` and password resets from `ACCOUNT_EMAIL_FROM`, and set `EMAIL_REPLY_TO` to an inbox people read, since Resend only sends and replies to an address with no mailbox bounce. The default sender, `onboarding@resend.dev`, only delivers to your own Resend account's email. Without `RESEND_API_KEY`, customers get no emails and reset links end up in the logs.
- **Mount a persistent volume at `/data/uploads`** (the image sets `UPLOAD_DIR` to it; the deploy kit does this). Without one, product images are lost on every deploy.
- Use a managed MySQL with automated backups, and also run `deploy/backup.sh` nightly with an off-site `BACKUP_REMOTE`: it backs up the database and the product images, and restores them with `--restore` (see the hosting guide's [Backups](docs/hosting.md#backups) section).
- Set `ALERT_EMAIL` to an inbox you read. The store emails it about problems that need a person: an oversold item, a failed Stripe webhook, checkout or a refund failing, or a server error (each at most once every 15 minutes). Check it works with `python -m app.alerts` inside the API container. Logs are one line per event (`time level logger message key=value`) at `LOG_LEVEL` (default `INFO`).
- Create the first admin once the API is running: register on the storefront, then run `python -m app.create_admin you@example.com` inside the API container.
- Login, registration, password reset, order lookup and checkout are rate limited per visitor IP (an IPv6 visitor per /64 network) (`AUTH_RATE_LIMIT_PER_MINUTE` and the others in `.env.example`). The counts live in each worker's memory, so they suit a single server. The limits need the visitor's real IP, so keep `--proxy-headers` and trust only your proxy in `FORWARDED_ALLOW_IPS` if the API port is reachable from anywhere else.
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
Contributions are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md). Please report security problems privately as described in [SECURITY.md](SECURITY.md).

## License
The code is released under the [MIT License](LICENSE). The default home page photo has its own license; see [frontend/src/assets/CREDITS.md](frontend/src/assets/CREDITS.md).

Created by Everett Lopez, Salt Lake City, UT.
