#!/bin/sh
# Starts the API in the container: migrate, then serve.
set -e

# Bring the schema to the latest revision before serving (the API refuses to start
# otherwise). With several replicas, set RUN_MIGRATIONS=false on all but one, or run
# `alembic upgrade head` as a separate release step.
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    alembic upgrade head
fi

# --proxy-headers: the host's load balancer terminates HTTPS, so trust its
# X-Forwarded-* headers for the client address and scheme
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-2}" \
    --proxy-headers \
    --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-*}"
