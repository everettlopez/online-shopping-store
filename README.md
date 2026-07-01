# Online Shopping Application 
A full-stack, database-driven online shopping platform designed to demonstrate modern web development practices, scalable architecture, and production-style engineering. This project is currently in active development, with core modules already implemented and additional features planned. 

## Overview
This application models a real‑world e‑commerce workflow, including product browsing, dynamic filtering, user authentication, and administrative management. The system is built with a modular architecture that supports future expansion into checkout, payments, analytics, and user‑centric features.

## Current Features
### Completed 
- **Dynamic Product Filtering** - Users can filter products by category, price, tags, and availability. Filters are mapped to efficient backend queries to ensure fast response times.
- **Admin User Management** - Administrative users can create, update, and manage platform users through secure backend routes and a dedicated UI.
- **Authentication and Authorization** - JWT‑based authentication with role‑based access control for both users and administrators.
- **Modular API Architecture** - Separation of concerns using controller, service, and repository layers.
- **Responsive Frontend** - Built with reusable components and clean state management patterns.

### In Progress 
- Shopping cart and checkout workflow
- Order dashboard and user dashboard backend wiring
- Payment gateway integratioin (Stripe)

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
- Node.js (v18+)
- Python (3.10+)
- MySQL server
- Git
- Recommended: VS Code with REST client or Bruno

### Running the Frontend (React + TypeScript)
1. Navigate to the frontend directory: ```cd frontend```
2. Install dependencies: ```npm install```
3. Start the development server: ```npm run dev```
4. The application will be available at: ```http://localhost:5173```

### Running the Backend (FastAPI)
1. Navigate to the root of the project.
2. Create and activate a virtual environment: 
```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```
3. Install dependencies: ```pip install -r requirements.txt```
4. Start the FastAPI development server: ```uvicorn main:app --reload```
5. The API will be available at: ```http://localhost:8000```

### Database Setup (MySQL)
1. Ensure MySQL is running locally
2. Create a database: 
```sql
CREATE DATABASE online_store; 
```
3. Update your backend ```.env``` or configuration file with your MySQL credentials: 
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=shopping_app
```
4. Run initial migrations or allow SQLAlchemy to generate tables on startup (depending on your configuration).

## Author
Everett Lopez
Salt Lake City, UT