#!/bin/sh
# Backs up the running store: a dump of the database (managed, or the kit's own MySQL)
# and the product images in the uploads volume. Each run writes a pair of timestamped
# files, checks them, deletes local copies older than BACKUP_KEEP_DAYS and, with
# BACKUP_REMOTE set, copies the new files off the server with rclone. If anything
# fails it exits non-zero and emails ALERT_EMAIL. From the project root:
#
#   sh deploy/backup.sh                              # back up now
#   sh deploy/backup.sh --restore 2026-10-23_0300    # put that backup back
#
# A restore stops the API, replaces the database and the product images with the
# backup's (anything newer is lost; check Stripe for payments made since), and starts
# the API again. It asks you to type "restore" first.
#
# Run backups nightly from cron (docs/hosting.md, "Backups"). Settings, all optional, go
# in deploy/.env: BACKUP_DIR (default deploy/backups), BACKUP_KEEP_DAYS (default 14) and
# BACKUP_REMOTE (an rclone destination such as b2:my-bucket/store).

set -u

DEPLOY_DIR=$(cd "$(dirname "$0")" && pwd)
ENV_FILE="${ENV_FILE:-$DEPLOY_DIR/.env}"
COMPOSE_FILE="$DEPLOY_DIR/docker-compose.yml"
# The compose file names the project, so its network has a fixed name
NETWORK=online-store_default
MYSQL_IMAGE=mysql:8.4

# A setting from deploy/.env (the last one wins, surrounding quotes dropped)
setting() {
    [ -f "$ENV_FILE" ] || return 0
    sed -n "s/^$1=//p" "$ENV_FILE" | tail -n 1 | tr -d '\r' | sed 's/^"\(.*\)"$/\1/; s/^'"'"'\(.*\)'"'"'$/\1/'
}

BACKUP_DIR=$(setting BACKUP_DIR)
BACKUP_DIR=${BACKUP_DIR:-$DEPLOY_DIR/backups}
KEEP_DAYS=$(setting BACKUP_KEEP_DAYS)
KEEP_DAYS=${KEEP_DAYS:-14}
REMOTE=$(setting BACKUP_REMOTE)

compose() { docker compose -f "$COMPOSE_FILE" "$@"; }

RESTORE=""
if [ "${1:-}" = "--restore" ]; then
    RESTORE=${2:-}
    if [ -z "$RESTORE" ]; then
        echo "Usage: sh deploy/backup.sh --restore <date_time>. Backups here:" >&2
        for file in "$BACKUP_DIR"/database-*.sql.gz; do
            [ -f "$file" ] && basename "$file" .sql.gz | sed 's/^database-/  /' >&2
        done
        exit 2
    fi
fi

STAMP=${RESTORE:-$(date +%Y-%m-%d_%H%M)}
DB_FILE="$BACKUP_DIR/database-$STAMP.sql.gz"
UPLOADS_FILE="$BACKUP_DIR/uploads-$STAMP.tgz"
SECRETS=""

cleanup() {
    [ -n "$SECRETS" ] && rm -f "$SECRETS"
    rm -f "$DB_FILE.partial" "$UPLOADS_FILE.partial"
}
trap cleanup EXIT

# Stop and exit non-zero (so cron reports it). A failed nightly backup also emails the
# owner, when the API is up and ALERT_EMAIL is set; someone running a restore is watching
fail() {
    if [ -n "$RESTORE" ]; then
        echo "Restore failed: $1" >&2
    else
        echo "Backup failed: $1" >&2
        compose exec -T api python -m app.alerts "Backup failed" \
            "The backup on $(hostname) failed: $1" \
            "Run sh deploy/backup.sh on the server to see the error." >/dev/null 2>&1
    fi
    exit 1
}

# The database's address and login, read from the API's own DATABASE_URL so they
# can't drift apart. One value per line; the password comes last
fields=$(compose run --rm --no-deps -T api python -c "
import os
from sqlalchemy.engine import make_url
url = make_url(os.environ['DATABASE_URL'])
print(url.host); print(url.port or 3306); print(url.username); print(url.database)
print(url.query.get('ssl_ca', '')); print(url.password or '')
" < /dev/null 2>/dev/null) || fail "couldn't read DATABASE_URL from the API's settings (is deploy/.env.api there?)"

field() { printf '%s\n' "$fields" | sed -n "$1p"; }
DB_HOST=$(field 1)
DB_PORT=$(field 2)
DB_USER=$(field 3)
DB_NAME=$(field 4)
DB_SSL_CA=$(field 5)
{ [ -n "$DB_HOST" ] && [ -n "$DB_NAME" ]; } || fail "DATABASE_URL has no host or database name"

# The password reaches the MySQL tools in a private file, never on a command line
SECRETS=$(mktemp) || fail "can't create a temporary file"
chmod 600 "$SECRETS"
printf 'MYSQL_PWD=%s\n' "$(field 6)" > "$SECRETS"

# Runs a MySQL client program (mysqldump, mysql) against the store's database
mysql_client() {  # mysql_client <program> [options...]
    program=$1
    shift
    set -- --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" "$@"
    [ -n "$DB_SSL_CA" ] && set -- "$@" --ssl-ca="$DB_SSL_CA" --ssl-mode=VERIFY_CA
    docker run --rm -i --network "$NETWORK" --env-file "$SECRETS" \
        -v "$DEPLOY_DIR/certs:/srv/certs:ro" "$MYSQL_IMAGE" "$program" "$@"
}

if [ -n "$RESTORE" ]; then
    { [ -f "$DB_FILE" ] && [ -f "$UPLOADS_FILE" ]; } || fail "no backup from $RESTORE in $BACKUP_DIR"
    { gzip -t "$DB_FILE" && gzip -t "$UPLOADS_FILE"; } || fail "the backup from $RESTORE is damaged"

    echo "This replaces the database $DB_NAME on $DB_HOST and every product image with"
    echo "the backup from $RESTORE. Orders, accounts and images added since then are lost."
    printf 'Type restore to go ahead: '
    read -r answer
    [ "$answer" = "restore" ] || { echo "Nothing was changed."; exit 1; }

    # Nothing may write to the store while it's replaced
    compose stop api || fail "couldn't stop the API"
    echo "  database"
    gzip -dc "$DB_FILE" | mysql_client mysql "$DB_NAME" \
        || fail "restoring the database failed; the API is stopped"
    echo "  product images"
    compose run --rm --no-deps -T api sh -c 'find /data/uploads -mindepth 1 -delete && tar xzf - -C /data/uploads' \
        < "$UPLOADS_FILE" || fail "restoring the product images failed; the API is stopped"
    compose start api || fail "the backup is restored, but the API didn't start"
    echo "Restored the backup from $RESTORE. Check the store, and Stripe for payments made since."
    exit 0
fi

mkdir -p "$BACKUP_DIR" || fail "can't create $BACKUP_DIR"
chmod 700 "$BACKUP_DIR" 2>/dev/null

echo "Backing up to $BACKUP_DIR"
echo "  database $DB_NAME on $DB_HOST"
mysql_client mysqldump --single-transaction --routines --triggers --no-tablespaces --set-gtid-purged=OFF \
    "$DB_NAME" < /dev/null | gzip > "$DB_FILE.partial" \
    || fail "mysqldump couldn't dump $DB_NAME"
# mysqldump ends a complete dump with this line; anything else was cut short
gzip -dc "$DB_FILE.partial" | tail -n 1 | grep -q "Dump completed" \
    || fail "the database dump is incomplete"
mv "$DB_FILE.partial" "$DB_FILE"

# Product images, read through the API's container so the files keep its user
echo "  product images"
compose run --rm --no-deps -T api tar czf - -C /data/uploads . > "$UPLOADS_FILE.partial" \
    || fail "couldn't read the uploads volume"
gzip -t "$UPLOADS_FILE.partial" || fail "the uploads archive is damaged"
mv "$UPLOADS_FILE.partial" "$UPLOADS_FILE"

chmod 600 "$DB_FILE" "$UPLOADS_FILE"
echo "  wrote $(basename "$DB_FILE") and $(basename "$UPLOADS_FILE")"

if [ -n "$REMOTE" ]; then
    command -v rclone >/dev/null 2>&1 || fail "BACKUP_REMOTE is set but rclone isn't installed"
    { rclone copy "$DB_FILE" "$REMOTE" && rclone copy "$UPLOADS_FILE" "$REMOTE"; } \
        || fail "couldn't copy the backup to $REMOTE"
    echo "  copied to $REMOTE"
fi

# Local copies older than BACKUP_KEEP_DAYS; the off-site copies follow the remote's
# own rules (set a lifecycle rule there)
find "$BACKUP_DIR" \( -name 'database-*.sql.gz' -o -name 'uploads-*.tgz' \) -mtime +"$KEEP_DAYS" -exec rm -f {} +

echo "Backup complete"
