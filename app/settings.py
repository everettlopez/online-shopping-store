"""Deployment settings read from the environment (or .env).

Defaults match local development; production sets these in its environment.
Each setting is read when it is used, so tests can change them with monkeypatch.
"""
import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_FRONTEND_URL = "http://localhost:5173"
DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
MIN_JWT_SECRET_LENGTH = 32


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def frontend_url() -> str:
    """Where Stripe sends the customer back to after checkout."""
    return os.getenv("FRONTEND_URL", DEFAULT_FRONTEND_URL).rstrip("/")


def public_api_url(request) -> str:
    """The API's address as browsers see it, used in links to uploaded images.
    Behind a reverse proxy the request's own URL is the internal one (often plain
    http), so production sets PUBLIC_API_URL."""
    return (os.getenv("PUBLIC_API_URL") or str(request.base_url)).rstrip("/")


def cors_origins() -> list[str]:
    """Origins allowed to call the API with cookies (comma-separated CORS_ORIGINS)."""
    origins = os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
    return [o.strip().rstrip("/") for o in origins.split(",") if o.strip()]


def cookie_samesite() -> str:
    # "none" lets the dev frontend (localhost:5173) call the API on 127.0.0.1:8000;
    # use "lax" when the frontend and API share a site in production
    return os.getenv("COOKIE_SAMESITE", "none").strip().lower()


def cookie_secure() -> bool:
    return env_bool("COOKIE_SECURE", True)


def docs_enabled() -> bool:
    return env_bool("ENABLE_DOCS", True)


def sql_echo() -> bool:
    return env_bool("SQL_ECHO", False)


def check_required_settings():
    """Stop startup with a clear message instead of running with secrets that
    are missing or too weak to be safe."""
    problems = []

    if len(os.getenv("JWT_SECRET_KEY", "")) < MIN_JWT_SECRET_LENGTH:
        problems.append(f"JWT_SECRET_KEY must be at least {MIN_JWT_SECRET_LENGTH} characters")

    for name in ("STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"):
        if not os.getenv(name, "").strip():
            problems.append(f"{name} is not set")

    if cookie_samesite() not in ("lax", "strict", "none"):
        problems.append("COOKIE_SAMESITE must be lax, strict or none")

    if problems:
        raise RuntimeError("Invalid configuration: " + "; ".join(problems) + ". See .env.example.")
