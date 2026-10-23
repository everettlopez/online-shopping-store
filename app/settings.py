"""Deployment settings read from the environment (or .env).

Defaults match local development; production sets these in its environment.
Each setting is read when it is used, so tests can change them with monkeypatch.
"""
import os
from decimal import Decimal, InvalidOperation
from dotenv import load_dotenv

load_dotenv()

DEFAULT_FRONTEND_URL = "http://localhost:5173"
DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
MIN_JWT_SECRET_LENGTH = 32
DEFAULT_SHIPPING_FLAT_RATE = "6.95"
DEFAULT_FREE_SHIPPING_THRESHOLD = "75"
DEFAULT_PRODUCT_TAX_CODE = "txcd_30011000"
DEFAULT_STORE_NAME = "Online Store"
DEFAULT_EMAIL_FROM = "Online Store <onboarding@resend.dev>"
DEFAULT_PASSWORD_RESET_MINUTES = 30
DEFAULT_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def store_name() -> str:
    """The store's name as customers see it, used in emails."""
    return os.getenv("STORE_NAME", "").strip() or DEFAULT_STORE_NAME


def frontend_url() -> str:
    """Where Stripe sends the customer back to after checkout."""
    return os.getenv("FRONTEND_URL", DEFAULT_FRONTEND_URL).rstrip("/")


def public_api_url(request) -> str:
    """The API's address as browsers see it, used in links to uploaded images.
    Behind a reverse proxy the request's own URL is the internal one (often plain
    http), so production sets PUBLIC_API_URL."""
    return (os.getenv("PUBLIC_API_URL") or str(request.base_url)).rstrip("/")


def upload_dir() -> str:
    """Where product images are saved. Most hosts wipe the app's own folder on every
    deploy, so production points UPLOAD_DIR at a persistent volume."""
    return os.getenv("UPLOAD_DIR") or DEFAULT_UPLOAD_DIR


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


def shipping_flat_rate() -> Decimal:
    """Shipping charged on orders below the free-shipping threshold, in dollars."""
    return Decimal(os.getenv("SHIPPING_FLAT_RATE") or DEFAULT_SHIPPING_FLAT_RATE)


def free_shipping_threshold() -> Decimal:
    """Orders whose items total at least this much (in dollars) ship free."""
    return Decimal(os.getenv("FREE_SHIPPING_THRESHOLD") or DEFAULT_FREE_SHIPPING_THRESHOLD)


def automatic_tax_enabled() -> bool:
    """Have Stripe Tax add sales tax at checkout. Needs Stripe Tax set up in the
    Dashboard; turn off only for local development before that."""
    return env_bool("STRIPE_AUTOMATIC_TAX", True)


def product_tax_code() -> str:
    """Stripe tax code for the products sold (default: General - Clothing)."""
    return os.getenv("STRIPE_PRODUCT_TAX_CODE") or DEFAULT_PRODUCT_TAX_CODE


def resend_api_key() -> str:
    """Resend API key. Without one, emails are printed to the console instead of sent
    (fine locally; production must set it)."""
    return os.getenv("RESEND_API_KEY", "").strip()


def email_from() -> str:
    """Default sender address. Resend's onboarding@resend.dev only delivers to the Resend
    account's own email; production uses an address on a domain verified in Resend."""
    return os.getenv("EMAIL_FROM") or DEFAULT_EMAIL_FROM


def orders_email_from() -> str:
    """Sender of order confirmations and shipping notices (falls back to EMAIL_FROM)."""
    return os.getenv("ORDERS_EMAIL_FROM") or email_from()


def account_email_from() -> str:
    """Sender of account emails such as password reset (falls back to EMAIL_FROM)."""
    return os.getenv("ACCOUNT_EMAIL_FROM") or email_from()


def email_reply_to() -> str | None:
    """Where customers' replies go, whichever address sent the email. Unset means
    replies go to the sender."""
    return os.getenv("EMAIL_REPLY_TO", "").strip() or None


def password_reset_minutes() -> int:
    """How long a password reset link works."""
    return int(os.getenv("PASSWORD_RESET_MINUTES") or DEFAULT_PASSWORD_RESET_MINUTES)


# Requests per minute each client may make to a group of endpoints (app/rate_limit.py).
# AUTH: login, register, forgot and reset password. LOOKUP: finding orders without an
# account. CHECKOUT: opening Stripe Checkout sessions. 0 turns a limit off.
DEFAULT_RATE_LIMITS = {"auth": 10, "lookup": 20, "checkout": 20}


def rate_limit_per_minute(group: str) -> int:
    value = os.getenv(f"{group.upper()}_RATE_LIMIT_PER_MINUTE", "").strip()
    return int(value) if value else DEFAULT_RATE_LIMITS[group]


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

    for name, read in (("SHIPPING_FLAT_RATE", shipping_flat_rate), ("FREE_SHIPPING_THRESHOLD", free_shipping_threshold)):
        try:
            if read() < 0:
                problems.append(f"{name} can't be negative")
        except InvalidOperation:
            problems.append(f"{name} must be a dollar amount such as 6.95")

    try:
        if password_reset_minutes() <= 0:
            problems.append("PASSWORD_RESET_MINUTES must be positive")
    except ValueError:
        problems.append("PASSWORD_RESET_MINUTES must be a whole number of minutes")

    for group in DEFAULT_RATE_LIMITS:
        name = f"{group.upper()}_RATE_LIMIT_PER_MINUTE"
        try:
            if rate_limit_per_minute(group) < 0:
                problems.append(f"{name} can't be negative")
        except ValueError:
            problems.append(f"{name} must be a whole number of requests (0 turns the limit off)")

    if problems:
        raise RuntimeError("Invalid configuration: " + "; ".join(problems) + ". See .env.example.")

    if not resend_api_key():
        print("RESEND_API_KEY is not set: emails are printed here instead of sent")
