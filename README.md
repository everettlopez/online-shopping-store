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
JWT_SECRET_KEY=a-long-random-string
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```
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
Run this again whenever you pull new files in `alembic/versions/`. After changing a model, generate a migration with `alembic revision --autogenerate -m "describe the change"`, review the generated file, then run `alembic upgrade head`.

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

## Author
Everett Lopez
Salt Lake City, UT