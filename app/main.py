import logging

from fastapi import Depends, FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlmodel import Session

from app.alerts import alert_admin
from app.db.session import get_session, seed_database
from app.logging_config import configure_logging
from app.settings import check_required_settings, cors_origins, docs_enabled
from app.routes.auth import router as auth_router
from app.routes.address import router as address_router
from app.routes.order import router as order_router
from app.routes.cart import router as cart_router
from app.routes.product import router as product_router
from app.routes.category import router as category_router
from app.routes.admin import router as admin_router
from app.routes.payments import router as payment_router
from fastapi.openapi.utils import get_openapi

from fastapi.staticfiles import StaticFiles

from app.routes.product import UPLOAD_DIR

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    configure_logging()

    # Docs are handy locally; turn them off in production with ENABLE_DOCS=false
    docs = docs_enabled()
    app = FastAPI(
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )

    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

    # CORS: allow the frontend to send cookies to the API
    origins = cors_origins()

    @app.middleware("http")
    async def report_server_errors(request: Request, call_next):
        # A bug or outage the routes didn't handle: log it with its traceback, tell the
        # owner (once per route every 15 minutes), and give the shopper a plain 500.
        # Added first so it sits inside the CORS middleware, which still adds its headers
        try:
            return await call_next(request)
        except Exception as e:
            route = getattr(request.scope.get("route"), "path", request.url.path)
            logger.exception("unhandled error method=%s route=%s", request.method, route)
            await run_in_threadpool(alert_admin, f"server-error {request.method} {route}", "The store hit a server error", [
                f"{request.method} {route} failed with {e!r}.",
                "The full error is in the API's logs (docker compose -f deploy/docker-compose.yml logs api).",
            ])
            return JSONResponse(status_code=500, content={"detail": "Something went wrong on our end. Please try again."})

    @app.middleware("http")
    async def reject_cross_site_writes(request: Request, call_next):
        # The auth cookie is sent with cross-site requests, so another site could submit
        # a form to the API as the logged-in user. Browsers always send Origin on such
        # requests; requests without one (Stripe's webhook, curl) aren't from a browser page.
        origin = request.headers.get("origin")
        if request.method in UNSAFE_METHODS and origin and origin.rstrip("/") not in origins:
            return JSONResponse(status_code=403, content={"detail": "Cross-site request blocked"})
        return await call_next(request)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,   # REQUIRED for cookies
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def on_startup():
        check_required_settings()
        seed_database()

    @app.get("/api")
    def root():
        return {"message": "API is running"}

    # For the host's health checks and uptime monitors: fails when the database is unreachable
    @app.get("/api/health")
    def health(session: Session = Depends(get_session)):
        try:
            session.exec(text("SELECT 1"))
        except Exception:
            return JSONResponse(status_code=503, content={"status": "database unavailable"})
        return {"status": "ok"}

    app.include_router(auth_router, prefix="/api")
    app.include_router(address_router, prefix="/api")
    app.include_router(order_router, prefix="/api")
    app.include_router(cart_router, prefix="/api")
    app.include_router(product_router, prefix="/api")
    app.include_router(category_router, prefix="/api")
    app.include_router(admin_router, prefix="/api")
    app.include_router(payment_router, prefix="/api")

    return app


app = create_app()
