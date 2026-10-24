#!/bin/sh
# Checks a running store from the outside: HTTPS, redirects, security headers, the
# API's health and production settings. Part of docs/launch-checklist.md; run it
# after every update. It reads the domains from deploy/.env. From the project root:
#
#   sh deploy/check.sh                 # the checks
#   sh deploy/check.sh --rate-limit    # also hits order lookup until it's refused
#                                      # (your address waits a minute afterwards)
#
# Exits non-zero when a check fails. For testing a local copy of the stack, set
# CHECK_RESOLVE_IP=127.0.0.1 (skip DNS) and CHECK_INSECURE=1 (Caddy's local certificates).

ENV_FILE="${ENV_FILE:-$(dirname "$0")/.env}"
RATE_LIMIT=false
[ "$1" = "--rate-limit" ] && RATE_LIMIT=true

if [ ! -f "$ENV_FILE" ]; then
    echo "No $ENV_FILE; copy deploy/.env.example to deploy/.env and fill it in first." >&2
    exit 2
fi

# A setting from deploy/.env (the last one wins, surrounding quotes dropped)
setting() {
    sed -n "s/^$1=//p" "$ENV_FILE" | tail -n 1 | tr -d '\r' | sed 's/^"\(.*\)"$/\1/; s/^'"'"'\(.*\)'"'"'$/\1/'
}

STORE_DOMAIN=$(setting STORE_DOMAIN)
API_DOMAIN=$(setting API_DOMAIN)
STORE_NAME=$(setting VITE_STORE_NAME)
if [ -z "$STORE_DOMAIN" ] || [ -z "$API_DOMAIN" ]; then
    echo "Set STORE_DOMAIN and API_DOMAIN in $ENV_FILE." >&2
    exit 2
fi
STORE="https://$STORE_DOMAIN"
API="https://$API_DOMAIN"

CURL_OPTS="-sS --max-time 20"
if [ -n "$CHECK_RESOLVE_IP" ]; then
    for host in "$STORE_DOMAIN" "www.$STORE_DOMAIN" "$API_DOMAIN"; do
        CURL_OPTS="$CURL_OPTS --resolve $host:443:$CHECK_RESOLVE_IP --resolve $host:80:$CHECK_RESOLVE_IP"
    done
fi
[ "$CHECK_INSECURE" = "1" ] && CURL_OPTS="$CURL_OPTS -k"

# shellcheck disable=SC2086  # CURL_OPTS is a list of options
fetch() { curl $CURL_OPTS "$@"; }
status() { fetch -o /dev/null -w '%{http_code}' "$@" 2>/dev/null; }
headers() { fetch -o /dev/null -D - "$@" 2>/dev/null | tr -d '\r'; }

FAILED=0
pass() { echo "  PASS  $1"; }
fail() { echo "  FAIL  $1"; FAILED=$((FAILED + 1)); }
warn() { echo "  WARN  $1"; }
check() {  # check <description> <actual> <expected>
    if [ "$2" = "$3" ]; then pass "$1"; else fail "$1 (got ${2:-nothing}, expected $3)"; fi
}

echo "Checking $STORE and $API"

echo "HTTPS and redirects"
check "storefront loads over HTTPS" "$(status "$STORE/")" 200
check "a storefront link like /cart loads (single-page app fallback)" "$(status "$STORE/cart")" 200
check "http:// redirects to https://" "$(status "http://$STORE_DOMAIN/")" 308
check "www redirects to the bare domain" "$(status "https://www.$STORE_DOMAIN/")" 301
check "API answers over HTTPS" "$(status "$API/api")" 200

echo "API"
health=$(fetch "$API/api/health" 2>/dev/null)
check "health check (database reachable)" "$health" '{"status":"ok"}'
check "API docs are hidden (ENABLE_DOCS=false)" "$(status "$API/docs")" 404
check "OpenAPI schema is hidden" "$(status "$API/openapi.json")" 404
check "shipping prices load" "$(status "$API/api/payments/shipping")" 200
check "active products load" "$(status "$API/api/products/active")" 200
# An unsigned event must be refused with 400; 503 means STRIPE_WEBHOOK_SECRET is empty
check "Stripe webhook refuses unsigned events" \
    "$(status -X POST -H 'Content-Type: application/json' -d '{}' "$API/api/payments/webhook")" 400

echo "Cross-site protection"
check "writes from another site are blocked" \
    "$(status -X POST -H 'Origin: https://attacker.example' -H 'Content-Type: application/json' -d '{}' "$API/api/auth/logout")" 403
cors=$(headers -X OPTIONS -H "Origin: $STORE" -H 'Access-Control-Request-Method: POST' "$API/api/auth/login")
check "the storefront may call the API (CORS_ORIGINS)" \
    "$(echo "$cors" | sed -n 's/^[Aa]ccess-[Cc]ontrol-[Aa]llow-[Oo]rigin: //p')" "$STORE"
check "the storefront may send the login cookie" \
    "$(echo "$cors" | sed -n 's/^[Aa]ccess-[Cc]ontrol-[Aa]llow-[Cc]redentials: //p')" true

echo "Security headers"
store_headers=$(headers "$STORE/")
api_headers=$(headers "$API/api/health")
for site in storefront API; do
    if [ "$site" = storefront ]; then h=$store_headers; else h=$api_headers; fi
    for name in Strict-Transport-Security X-Content-Type-Options X-Frame-Options Referrer-Policy Permissions-Policy; do
        if echo "$h" | grep -qi "^$name:"; then pass "$site sends $name"; else fail "$site is missing $name"; fi
    done
done
# HSTS_INCLUDE_SUBDOMAINS=true must reach browsers; otherwise it must not be there
hsts_subdomains=$(setting HSTS_INCLUDE_SUBDOMAINS | tr '[:upper:]' '[:lower:]')
if echo "$store_headers" | grep -i '^Strict-Transport-Security:' | grep -qi 'includeSubDomains'; then
    case "$hsts_subdomains" in
        true|1|yes|on) pass "HSTS covers subdomains (HSTS_INCLUDE_SUBDOMAINS)" ;;
        *) fail "HSTS covers subdomains although HSTS_INCLUDE_SUBDOMAINS is off" ;;
    esac
else
    case "$hsts_subdomains" in
        true|1|yes|on) fail "HSTS_INCLUDE_SUBDOMAINS is on but browsers don't get includeSubDomains (run up -d)" ;;
    esac
fi
if echo "$store_headers" | grep -qi '^Content-Security-Policy:'; then
    pass "storefront enforces its content security policy"
elif echo "$store_headers" | grep -qi '^Content-Security-Policy-Report-Only:'; then
    warn "content security policy is report-only; enforce it once the API logs no \"csp violation\" lines (CSP_HEADER in deploy/.env)"
else
    fail "storefront sends no content security policy"
fi

echo "Store identity"
home=$(fetch "$STORE/" 2>/dev/null)
title=$(echo "$home" | sed -n 's:.*<title>\(.*\)</title>.*:\1:p' | head -n 1)
if [ -z "$STORE_NAME" ] || [ "$STORE_NAME" = "Online Store" ]; then
    warn "the store is called \"${title:-Online Store}\"; set VITE_STORE_NAME in deploy/.env and rebuild"
else
    check "page title is the store's name" "$title" "$STORE_NAME"
fi
# Link previews and the browser tab use these; empty ones mean a broken build
if echo "$home" | grep -q '<meta name="description" content="[^"]'; then
    pass "the page has a description"
else
    fail "the page's description is empty (VITE_STORE_DESCRIPTION)"
fi
if echo "$home" | grep -q '<link rel="icon" href="[^"]'; then
    pass "the page has an icon"
else
    fail "the page's icon is empty (VITE_FAVICON_URL)"
fi
# The store's own photos live in frontend/public/custom/, which git ignores, so a fresh
# clone doesn't have them; a missing one gets the storefront's HTML instead of an image
for name in VITE_HERO_IMAGE_URL VITE_BANNER_IMAGE_URL VITE_FAVICON_URL VITE_SHARE_IMAGE_URL; do
    path=$(setting "$name")
    case "$path" in
        /*) ;;
        *) continue ;;
    esac
    type=$(headers "$STORE$path" | sed -n 's/^[Cc]ontent-[Tt]ype: *//p' | head -n 1)
    case "$type" in
        image/*) pass "$name ($path) is an image" ;;
        *) fail "$name ($path) isn't on the server (got ${type:-nothing}); copy it into frontend/public/custom/ and rebuild" ;;
    esac
done

if [ "$RATE_LIMIT" = true ]; then
    echo "Rate limits"
    code=""
    i=0
    while [ $i -lt 60 ]; do
        code=$(status -X POST -H "Origin: $STORE" -H 'Content-Type: application/json' \
            -d '{"order_number":"launch-check","email":"launch-check@example.com"}' "$API/api/orders/lookup")
        [ "$code" = 429 ] && break
        i=$((i + 1))
    done
    if [ "$code" = 429 ]; then
        pass "order lookup is refused after $i attempts (LOOKUP_RATE_LIMIT_PER_MINUTE)"
    else
        fail "order lookup was never refused in 60 attempts (got $code); is the limit set to 0?"
    fi
fi

echo
if [ "$FAILED" -gt 0 ]; then
    echo "$FAILED check(s) failed. docs/troubleshooting.md covers the usual causes."
    exit 1
fi
echo "All checks passed. Finish the manual steps in docs/launch-checklist.md."
