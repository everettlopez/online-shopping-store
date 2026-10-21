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
Tables are created automatically when the backend starts.

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

### 4. Frontend (React + TypeScript)
```bash
npm install                # root: dev runner (concurrently)
npm install --prefix frontend
```

### 5. Run both servers
From the project root:
```bash
npm run dev
```
- Frontend: http://localhost:5173
- API: http://localhost:8000/api (docs at http://localhost:8000/docs)

## Author
Everett Lopez
Salt Lake City, UT