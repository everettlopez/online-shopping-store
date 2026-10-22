# Online Shopping Application 
A full-stack, database-driven online shopping platform designed to demonstrate modern web development practices, scalable architecture, and production-style engineering. This project is currently in active development, with core modules already implemented and additional features planned. 

## Table of Contents
1. [Overview](#overview)
2. [Tech Stack](#tech-stack)
3. [Development Setup](#development-setup)
4. [Author](#author)

## Overview
This application models a real‑world e‑commerce workflow, including product browsing, dynamic filtering, user authentication, and administrative management. The system is built with a modular architecture that supports future expansion into checkout, payments, analytics, and user‑centric features.

## Tech Stack
### Frontend
- React
- TypeScript
- Axios for API communication

### Backend
- FastAPI
- SQLAlchemy ORM
- Pydantic models for validation
- JWT Authentication
- Modular routing and dependency injection

### Database
- MySQL
- Relational schema with indexing for product and user queries

### Tooling
- GitHub for version control 
- Custom Swagger-style API documentation
- pytest for the backend test suite
- Bruno for endpoint testing

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
`JWT_SECRET_KEY` must be at least 32 characters (generate one with `venv\Scripts\python -c "import secrets; print(secrets.token_urlsafe(48))"`), and both Stripe keys must be set, or the API refuses to start. `.env.example` also lists optional deployment settings (`FRONTEND_URL`, `PUBLIC_API_URL`, `CORS_ORIGINS`, `COOKIE_SAMESITE`, `COOKIE_SECURE`, `ENABLE_DOCS`, `SQL_ECHO`) the shipping and tax settings (`SHIPPING_FLAT_RATE`, `FREE_SHIPPING_THRESHOLD`, `STRIPE_AUTOMATIC_TAX`, `STRIPE_PRODUCT_TAX_CODE`) and the email settings (`RESEND_API_KEY`, `EMAIL_FROM`, `ORDERS_EMAIL_FROM`, `ACCOUNT_EMAIL_FROM`, `EMAIL_REPLY_TO`, `PASSWORD_RESET_MINUTES`); their defaults suit local development. Without `RESEND_API_KEY`, the API prints emails (password reset links, order confirmations, shipping notices) in its terminal instead of sending them. For production, set `FRONTEND_URL`, `PUBLIC_API_URL` and `CORS_ORIGINS` to your real addresses, `ENABLE_DOCS=false`, and `COOKIE_SAMESITE=lax` if the frontend and API share a site.

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
stripe listen --forward-to localhost:8000/api/payments/webhook --events checkout.session.completed    # Terminal 3: Stripe webhooks
```
Copy the `whsec_...` secret that `stripe listen` prints into `STRIPE_WEBHOOK_SECRET`, and make sure the Stripe CLI is logged in to the same account as `STRIPE_SECRET_KEY`.

> **Windows:** keep the API in its own terminal and start it with Python directly, not through npm. When uvicorn auto-reloads after a `.py` change, it sends Ctrl+C to every process in its terminal, which would stop anything else running there and leave the old API process in the background.

- Frontend: http://localhost:5173
- API: http://localhost:8000/api (docs at http://localhost:8000/docs)

### 6. Run the tests
The backend test suite lives in `tests/`. It runs against a throwaway in-memory SQLite database and mocks Stripe, so it doesn't need MySQL, a `.env` file or network access. From the project root:
```bash
venv\Scripts\pip install -r requirements-dev.txt
venv\Scripts\python -m pytest
```
Add `-x` to stop at the first failure, or pass a path to run part of the suite (for example `venv\Scripts\python -m pytest tests/api/test_cart_api.py`). Shared fixtures and test-data factories are in `tests/conftest.py`.

## Deployment
The API and the storefront deploy separately, each as its own Docker image. CI (`.github/workflows/ci.yml`) runs the tests, builds the frontend and builds both images on every push and pull request.

### API
```bash
docker build -t shop-api .
```
The image runs `alembic upgrade head` and then uvicorn (`docker/start-api.sh`). Configure it with the environment variables from `.env.example`. For production:
- Use live Stripe keys, and the `whsec_...` secret of a webhook endpoint registered in the Stripe Dashboard for `https://<api host>/api/payments/webhook`.
- Set up Stripe Tax in the live Dashboard (business address, and a registration for every state where you collect sales tax). Checkout asks Stripe Tax for the tax, and Stripe refuses the checkout if Stripe Tax isn't set up. Sales tax is charged only where you're registered.
- Set `FRONTEND_URL`, `PUBLIC_API_URL` and `CORS_ORIGINS` to the real addresses, and set `ENABLE_DOCS=false`. Set `COOKIE_SAMESITE=lax` if the storefront and API share a site (for example `shop.example.com` and `api.example.com`).
- Email goes through [Resend](https://resend.com). Add your domain in the Resend dashboard, create the DNS records it lists (SPF and DKIM) so mail isn't marked as spam, then set `RESEND_API_KEY` and `EMAIL_FROM` (for example `Your Store <orders@example.com>`). Optionally send order and shipping emails from `ORDERS_EMAIL_FROM` and password resets from `ACCOUNT_EMAIL_FROM`, and set `EMAIL_REPLY_TO` to an inbox people read, since Resend only sends and replies to an address with no mailbox bounce. The default sender, `onboarding@resend.dev`, only delivers to your own Resend account's email. Without `RESEND_API_KEY`, customers get no emails and reset links end up in the logs.
- **Mount a persistent volume at `/data/uploads`** (the image sets `UPLOAD_DIR` to it). Without one, product images are lost on every deploy.
- Use a managed MySQL with automated backups.
- Optional: `PORT` (default 8000), `WEB_CONCURRENCY` (worker processes, default 2) and `FORWARDED_ALLOW_IPS` (proxies trusted for `X-Forwarded-*`, default all). With several replicas, set `RUN_MIGRATIONS=false` on all but one, or run `alembic upgrade head` as a release step.

The host should terminate HTTPS. `GET /api/health` returns 200 when the database is reachable and 503 when it isn't, for health checks and uptime monitors.

### Storefront
```bash
docker build --build-arg VITE_API_URL=https://api.example.com/api -t shop-web frontend
```
`VITE_API_URL` is baked into the bundle at build time (see `frontend/.env.example`). The image serves the built site with nginx (`frontend/nginx.conf`), sending every unknown path to `index.html` so links like `/orders/abc` work. If you use a static host (Netlify, Vercel, Cloudflare Pages) instead, run `npm run build` with `VITE_API_URL` set, publish `frontend/dist`, and add the host's single-page-app rewrite to `/index.html`.

## Author
Everett Lopez
Salt Lake City, UT