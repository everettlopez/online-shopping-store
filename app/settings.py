"""Deployment settings read from the environment (or .env).

Defaults match local development; production sets these in its environment.
Each setting is read when it is used, so tests can change them with monkeypatch.
"""
import logging
import os
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_FRONTEND_URL = "http://localhost:5173"
DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
MIN_JWT_SECRET_LENGTH = 32
DEFAULT_SHIPPING_FLAT_RATE = "6.95"
DEFAULT_FREE_SHIPPING_THRESHOLD = "75"
DEFAULT_PRODUCT_TAX_CODE = "txcd_30011000"
DEFAULT_STORE_NAME = "Online Store"
DEFAULT_EMAIL_FROM = "Online Store <onboarding@resend.dev>"
DEFAULT_PASSWORD_RESET_MINUTES = 30
DEFAULT_LOG_LEVEL = "INFO"
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
DEFAULT_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
ENVIRONMENTS = ("development", "production")
LOCAL_HOSTS = ("localhost", "127.0.0.1", "0.0.0.0", "::1")


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def environment() -> str:
    """development (the default) or production. Production refuses to start with
    settings that only suit a developer's computer (see production_problems)."""
    return (os.getenv("ENVIRONMENT", "").strip() or "development").lower()


def stripe_test_mode_allowed() -> bool:
    """Let production run on Stripe test keys, for a trial run before going live."""
    return env_bool("ALLOW_STRIPE_TEST_MODE", False)


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


def alert_email() -> str:
    """Where the store owner gets alerts about problems that need a person (an oversold
    item, a failed webhook, a server error). Empty turns alerts off."""
    return os.getenv("ALERT_EMAIL", "").strip()


def log_level() -> str:
    """How much the API logs: DEBUG, INFO (the default), WARNING, ERROR or CRITICAL."""
    return (os.getenv("LOG_LEVEL", "").strip() or DEFAULT_LOG_LEVEL).upper()


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


def is_public_https_url(url: str) -> bool:
    """An https address that isn't this computer."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and bool(host) and host not in LOCAL_HOSTS and not host.endswith(".localhost")


def production_problems() -> list[str]:
    """Settings that are fine on a developer's computer but wrong for a live store:
    each would quietly break checkout, email or logins, or expose something."""
    problems = []

    if docs_enabled():
        problems.append("ENABLE_DOCS must be false (it publishes /docs and /openapi.json)")
    if not cookie_secure():
        problems.append("COOKIE_SECURE must be true")

    if not is_public_https_url(frontend_url()):
        problems.append("FRONTEND_URL must be the storefront's https address (Stripe sends buyers back there)")
    if not is_public_https_url(os.getenv("PUBLIC_API_URL", "")):
        problems.append("PUBLIC_API_URL must be the API's https address (product image links use it)")
    origins = cors_origins()
    if not origins or not all(is_public_https_url(o) for o in origins):
        problems.append("CORS_ORIGINS must list only the storefront's https addresses")

    if not resend_api_key():
        problems.append("RESEND_API_KEY must be set (without it no email is sent and reset links are printed in the logs)")
    for name, sender in (("EMAIL_FROM", email_from()), ("ORDERS_EMAIL_FROM", orders_email_from()),
                         ("ACCOUNT_EMAIL_FROM", account_email_from())):
        if "@resend.dev" in sender.lower():
            problems.append(f"{name} must be an address on your own domain (Resend's test sender only delivers to you)")
            break

    stripe_key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    if stripe_key.startswith(("sk_test_", "rk_test_")) and not stripe_test_mode_allowed():
        problems.append("STRIPE_SECRET_KEY is a test key; use the live key, or set ALLOW_STRIPE_TEST_MODE=true for a trial run")

    return problems


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

    if log_level() not in LOG_LEVELS:
        problems.append("LOG_LEVEL must be one of " + ", ".join(LOG_LEVELS))

    if environment() not in ENVIRONMENTS:
        problems.append("ENVIRONMENT must be development or production")
    elif environment() == "production":
        problems.extend(production_problems())

    if problems:
        raise RuntimeError("Invalid configuration: " + "; ".join(problems) + ". See .env.example.")

    if not resend_api_key():
        logger.warning("RESEND_API_KEY is not set: emails are printed here instead of sent")
    if not alert_email():
        logger.warning("ALERT_EMAIL is not set: problems that need a person are only logged")
    if environment() == "production":
        if stripe_test_mode_allowed() and os.getenv("STRIPE_SECRET_KEY", "").strip().startswith(("sk_test_", "rk_test_")):
            logger.warning("Stripe is in test mode: checkout takes no real payments")
        if cookie_samesite() == "none":
            logger.warning("COOKIE_SAMESITE is none: use lax when the storefront and API share a domain")
