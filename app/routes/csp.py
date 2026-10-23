"""Where browsers report Content-Security-Policy violations on the storefront. Caddy's
CSP (deploy/Caddyfile) names this endpoint in report-uri, so while the policy is
report-only the owner can see in the API's logs what enforcing it would block:

    docker compose -f deploy/docker-compose.yml logs api | grep "csp violation"
"""
import json
import logging
from urllib.parse import urlsplit, urlunsplit

from fastapi import APIRouter, Request, Response

from app.rate_limit import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Reports"])

# A report is a few hundred bytes; anything far bigger isn't one
MAX_REPORT_BYTES = 16 * 1024
# A page that breaks the policy everywhere sends a burst at once; a few lines show it
MAX_LOGGED_PER_REQUEST = 5


def without_query(url) -> str:
    """The address without its query or fragment: a tracking link's token stays out of
    the logs. Keywords such as inline and eval pass through."""
    url = str(url or "")[:300]
    parts = urlsplit(url)
    if not parts.scheme or not parts.netloc:
        return url.split("?")[0].split("#")[0]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def violations(report) -> list[dict]:
    """The violations in either format browsers send: report-uri's {"csp-report": {...}}
    or the Reporting API's [{"type": "csp-violation", "body": {...}}, ...]."""
    if isinstance(report, dict) and isinstance(report.get("csp-report"), dict):
        r = report["csp-report"]
        return [{
            "directive": r.get("effective-directive") or r.get("violated-directive"),
            "blocked": r.get("blocked-uri"),
            "page": r.get("document-uri"),
            "source": r.get("source-file"),
        }]
    if isinstance(report, list):
        return [{
            "directive": body.get("effectiveDirective"),
            "blocked": body.get("blockedURL"),
            "page": body.get("documentURL"),
            "source": body.get("sourceFile"),
        } for item in report
            if isinstance(item, dict) and item.get("type") == "csp-violation"
            and isinstance(body := item.get("body"), dict)]
    return []


@router.post("/csp-report", status_code=204, dependencies=[rate_limit("reports")])
async def csp_report(request: Request):
    body = b""
    async for chunk in request.stream():
        body += chunk
        if len(body) > MAX_REPORT_BYTES:
            return Response(status_code=413)

    try:
        report = json.loads(body)
    except ValueError:
        return Response(status_code=204)

    for v in violations(report)[:MAX_LOGGED_PER_REQUEST]:
        logger.info("csp violation directive=%s blocked=%s page=%s source=%s",
                    str(v["directive"] or "")[:60], without_query(v["blocked"]),
                    without_query(v["page"]), without_query(v["source"]))
    return Response(status_code=204)
