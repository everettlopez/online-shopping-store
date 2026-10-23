"""Per-client request limits for the endpoints people could hammer: guessing passwords,
order numbers or reset links, or opening checkout sessions in a loop.

Counts live in this process's memory, which suits a single server. Each uvicorn worker
keeps its own counts, so with WEB_CONCURRENCY=2 a client can get up to twice the limit
before every worker refuses it. The client is identified by IP address, which behind a
reverse proxy needs uvicorn's --proxy-headers (docker/start-api.sh sets it).
"""
import math
import threading
import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, Request

from app.settings import rate_limit_per_minute

WINDOW_SECONDS = 60

_lock = threading.Lock()
_hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_last_cleanup = 0.0


def reset_rate_limits():
    """Forget every count (tests start each case with a clean slate)."""
    global _last_cleanup
    with _lock:
        _hits.clear()
        _last_cleanup = 0.0


def _drop_idle_clients(now: float):
    # Clients that stopped calling would otherwise stay in memory forever
    global _last_cleanup
    if now - _last_cleanup < WINDOW_SECONDS:
        return
    _last_cleanup = now
    for key in [key for key, times in _hits.items() if not times or now - times[-1] >= WINDOW_SECONDS]:
        del _hits[key]


def check_rate_limit(group: str, client: str):
    """Count a request from `client` against `group`'s limit, refusing it with a 429
    once the client has used up the last minute's allowance."""
    limit = rate_limit_per_minute(group)
    if limit <= 0:
        return

    now = time.monotonic()
    with _lock:
        _drop_idle_clients(now)
        times = _hits[(group, client)]
        while times and now - times[0] >= WINDOW_SECONDS:
            times.popleft()

        if len(times) >= limit:
            retry_after = max(1, math.ceil(WINDOW_SECONDS - (now - times[0])))
            raise HTTPException(
                status_code=429,
                detail="Too many attempts. Please wait a minute and try again.",
                headers={"Retry-After": str(retry_after)},
            )
        times.append(now)


def rate_limit(group: str):
    """Route dependency, e.g. @router.post("/login", dependencies=[rate_limit("auth")]).
    Groups share one allowance per client, so every login and password-reset route
    counts against the same "auth" limit."""
    def dependency(request: Request):
        check_rate_limit(group, request.client.host if request.client else "unknown")
    return Depends(dependency)
