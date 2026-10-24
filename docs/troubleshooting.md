# Troubleshooting

Each problem below lists what you see, the usual causes, and the fix. Commands run **on the server**, from the project folder (`cd ~/online-shopping-store`). The examples use `shop.example.com` and `api.shop.example.com`; use your own domains.

If your problem isn't here, [collect the details below](#collect-this-before-asking-for-help) and ask in [Discussions](https://github.com/everettlopez/online-shopping-store/discussions), or [report a bug](#reporting-a-bug).

## Start here

Three commands find most problems:
```bash
sh deploy/check.sh
docker compose -f deploy/docker-compose.yml ps
docker compose -f deploy/docker-compose.yml logs --tail 100 api
```
- `check.sh` tests the live store from outside. A FAIL line names what's wrong.
- `ps` shows each service. All of `api`, `web` and `caddy` should be `Up ... (healthy)`. A service that's `Restarting` or `unhealthy` is where to look; swap `api` in the third command for `web` or `caddy` to see its logs.
- An API log line starting `Invalid configuration:` names each setting to fix in `deploy/.env.api`.

After changing `deploy/.env.api`, restart with `docker compose -f deploy/docker-compose.yml up -d`. After changing `deploy/.env` or a photo, rebuild with `up -d --build`.

---

## Getting the code and updating

### `git checkout` says local changes would be overwritten
**Cause:** a file that's part of the code was edited on the server. Your settings files and photos aren't affected; git ignores them.
**Fix:** see which files changed with `git status`. If you didn't mean to change them, put them back with `git restore <file>` and run the checkout again. If you meant to change the code, keep your changes in a [private copy](hosting.md#run-from-your-own-private-copy) instead, so updates merge them.

### `git describe --tags` shows something like `v1.0.1-3-gabc1234`, or "fatal: No names found"
**Cause:** the server isn't on a release. It's a few commits past one (the first case), or the clone has no tags (the second).
**Fix:** `git fetch --tags`, then check out a release as in [hosting.md step 6](hosting.md#6-get-the-code-and-fill-in-the-settings). A [private copy](hosting.md#run-from-your-own-private-copy) is on your own `main`, so this is expected there.

### "Can't locate revision" in the API's logs after going back to an older version
**Cause:** the database has a migration the older code doesn't know.
**Fix:** follow [Rolling back](launch-checklist.md#rolling-back), which undoes the newer migrations first, while the newer code is still checked out. If you've already switched to the older code, check out the newer release again, undo its migrations, then switch back.

## Starting the store

### The API keeps restarting
**Cause:** usually a setting the API checks at startup, or the database.
**Fix:** run `docker compose -f deploy/docker-compose.yml logs api`.
- **`Invalid configuration:`** names each setting. Common ones: a `localhost` or `http://` address in `FRONTEND_URL`, `PUBLIC_API_URL` or `CORS_ORIGINS`; `ENABLE_DOCS` not `false`; no `RESEND_API_KEY`; a `sk_test_` key without `ALLOW_STRIPE_TEST_MODE=true`; a `JWT_SECRET_KEY` under 32 characters.
- **Database errors** (`Can't connect`, `Access denied`, SSL or certificate errors): see [The API can't reach the database](#the-api-cant-reach-the-database).
- **`Database schema is at revision ... but the code expects ...`**: the migrations didn't finish. The API runs them at start; the log lines just above say why they failed.

### Nothing answers after `up -d`, but the containers exist
**Cause:** Caddy starts only once the API and the storefront report healthy, so a broken API keeps the whole site offline.
**Fix:** `docker compose -f deploy/docker-compose.yml ps` shows which one isn't healthy, and its logs say why.

### The build stops with "Killed" or runs out of memory
**Cause:** building the storefront needs about 2 GB of memory.
**Fix:** add swap ([hosting.md step 1](hosting.md#1-prepare-the-server)), or use a server with more RAM, then run `up -d --build` again. `free -h` shows memory and swap.

### `docker compose` says "permission denied" on the Docker socket
**Cause:** your user isn't in the `docker` group yet, or you haven't logged in again since adding it.
**Fix:** `sudo usermod -aG docker $USER`, then log out and back in. `groups` should list `docker`.

### `docker compose ... config` reports an error
**Cause:** a typo in `deploy/.env` or `deploy/.env.api`, or one of them is missing.
**Fix:** the message names the file and line. Each line must be `NAME=value`, with no spaces around `=`. Put a value with spaces in quotes (`VITE_STORE_NAME="My Store"`).

## HTTPS and the domain

### No HTTPS certificate, or "connection refused"
**Cause:** DNS doesn't point at the server yet, the firewall blocks ports 80 and 443, or Caddy couldn't get a certificate.
**Fix:**
1. On your computer, `nslookup shop.example.com` (and the `api.` and `www.` names) must show the server's IP.
2. On the server, `sudo ufw status` must allow `80,443/tcp`.
3. `docker compose -f deploy/docker-compose.yml logs caddy` shows why a certificate failed. [Let's Debug](https://letsdebug.net/) tests a domain the way Let's Encrypt does.

Let's Encrypt [limits repeated failures](https://letsencrypt.org/docs/rate-limits/), so fix the cause before retrying many times.

### Too many redirects, or a certificate error, with Cloudflare
**Cause:** Cloudflare's SSL mode isn't **Full (strict)**.
**Fix:** set it as in [Behind Cloudflare's proxy](hosting.md#behind-cloudflares-proxy), or switch the records to **DNS only** (grey cloud).

## Database

### The API can't reach the database
**Cause:** a wrong `DATABASE_URL`, the server isn't allowed to connect, or the CA certificate is missing.
**Fix:**
- Check the host, port, user and database name in `DATABASE_URL` against your provider's connection details.
- [Percent-encode](hosting.md#percent-encoding-a-password) symbols in the password (`@` becomes `%40`).
- Add the server to the database's *Trusted sources* (or your provider's allowed IPs).
- For a managed database, `ls deploy/certs/db-ca.crt` must show the file, and `DATABASE_URL` must end with `?ssl_ca=/srv/certs/db-ca.crt`.
- With MySQL on the server, every command needs `--profile mysql`, and the host is `db`.

## Logging in

### Logging in doesn't stick, or you're logged out on refresh
**Cause:** the browser didn't keep the login cookie.
**Fix:** `CORS_ORIGINS` must list the storefront's exact address (with `https://` and no trailing `/`), `COOKIE_SAMESITE` should be `lax`, and both sites must share a domain (`shop.example.com` and `api.shop.example.com`). Restart the API after changing them.

### "Too many attempts"
**Cause:** the rate limits (`AUTH_RATE_LIMIT_PER_MINUTE` and the others in `.env.example`), which reset after a minute.
**Fix:** wait a minute. If every visitor hits them together, the API isn't seeing real addresses; see *Real visitor addresses* in the [launch checklist](launch-checklist.md#3-check-it-by-hand) and [Behind Cloudflare's proxy](hosting.md#behind-cloudflares-proxy).

### You don't see the admin pages after `create_admin`
**Fix:** log out and in again; admin rights apply to new logins. The email given to `create_admin` must be one already registered on the storefront.

## Checkout and payments

### Checkout fails
**Cause:** the API logs say why (`docker compose -f deploy/docker-compose.yml logs --tail 100 api`). Common causes:
- Stripe Tax isn't set up in this mode (live or test). Set it up, or set `STRIPE_AUTOMATIC_TAX=false`.
- A test key is used with live mode, or the other way around.
- The shipping address isn't in the US; the store ships only to US addresses.

### Orders don't appear after payment
**Cause:** Stripe's webhook isn't reaching the store.
**Fix:** check the endpoint's recent deliveries in Stripe (Developers → Webhooks).
- A **400** means `STRIPE_WEBHOOK_SECRET` doesn't match that endpoint's signing secret.
- A **timeout or connection error** means the address is wrong or the API is down.

Check the endpoint's address is `https://<API_DOMAIN>/api/payments/webhook` and that it has the four events from [hosting.md step 5](hosting.md#5-set-up-stripe). The success page also creates the order, so customers who return to the store are covered either way. Stripe retries failed deliveries for a few days, so orders appear once the problem is fixed.

### A refund made in Stripe doesn't show in the store
**Fix:** the webhook endpoint needs the `charge.refunded` event. Add it, then use **Resend** on the failed delivery in Stripe.

## Email

### Emails don't arrive
**Cause:** no `RESEND_API_KEY` (the API then only prints emails in its logs), an unverified domain, or the mail went to spam.
**Fix:**
- Check that the domain is **Verified** in Resend and that every sender address uses it.
- Resend's dashboard (Emails) shows each email and whether it was delivered, bounced or marked as spam.
- For mail going to spam, check SPF, DKIM and DMARC ([hosting.md step 4](hosting.md#4-set-up-email)) and Resend's [deliverability guide](https://resend.com/guides/email/deliverability/avoid-gmail-spam-folder).

### Replies to the store's emails bounce
**Fix:** `EMAIL_REPLY_TO` (and each sender) must be an address that receives mail. Resend only sends.

### No alert emails
**Fix:** `ALERT_EMAIL` must be set in `deploy/.env.api` (restart the API after changing it), and alerts are sent through Resend like the store's other email. Run `docker compose -f deploy/docker-compose.yml exec api python -m app.alerts`; it says whether sending failed.

## Images

### A home page photo or the icon is missing
**Cause:** the file isn't in `frontend/public/custom/` on the server (a fresh clone doesn't have it), its name doesn't match the `VITE_*_URL` setting (names are case-sensitive), or the storefront wasn't rebuilt after it was added.
**Fix:** `ls frontend/public/custom/`, fix the name or the setting, then `up -d --build`. `sh deploy/check.sh` names each missing one.

### Product images disappear after a restart or update
**Cause:** the uploads volume isn't mounted. The deploy kit mounts it; a changed compose file, or a host outside the kit, may not.
**Fix:** use the kit's `deploy/docker-compose.yml` unchanged. Elsewhere, mount a persistent volume at `/data/uploads`.

## Backups

### `backup.sh` fails
**Fix:** the last lines say why, and with `ALERT_EMAIL` set you get an email. Common causes:
- `BACKUP_REMOTE` names an rclone remote that doesn't exist: `rclone listremotes` lists yours.
- The disk is full: `df -h`.
- The database can't be reached: see [The API can't reach the database](#the-api-cant-reach-the-database).

### The nightly backup doesn't run
**Fix:** `crontab -l` must show the line from [Backups](hosting.md#backups), with the right project path. `deploy/backups/backup.log` shows each night's output.

---

## Collect this before asking for help

Gather these, so whoever helps you can see what's happening:
```bash
git describe --tags
docker compose -f deploy/docker-compose.yml ps
sh deploy/check.sh
docker compose -f deploy/docker-compose.yml logs --tail 100 api
```
Also note what you did, what you expected, what happened instead, and the browser and device if it's a storefront problem.

> [!WARNING]
> **Remove private details before you post anything.** Never share `deploy/.env`, `deploy/.env.api`, API keys (`sk_live_`, `whsec_`, `re_`), passwords, `DATABASE_URL`, or customers' names, emails and addresses. The store's logs don't contain secrets, but check what you paste and replace your domain with `example.com` if you prefer.

## Reporting a bug

1. Check it isn't already reported: search the [open and closed issues](https://github.com/everettlopez/online-shopping-store/issues?q=is%3Aissue).
2. Make sure you're on the latest release ([Updating to a new release](hosting.md#updating-to-a-new-release)); it may already be fixed.
3. [Open a bug report](https://github.com/everettlopez/online-shopping-store/issues/new/choose) and fill in the form with the details above.

Questions about setting up or running a store go to [Discussions](https://github.com/everettlopez/online-shopping-store/discussions) instead. **Security problems** (anything that could let someone see others' data, pay less, or take over the store) must be reported privately, as described in [SECURITY.md](../SECURITY.md), never in a public issue.

## Verified resources

Official documentation for each part of the setup. These links were checked when this guide was written; if one has moved, search the provider's docs for its title.

| Topic | Resource |
| --- | --- |
| SSH keys | [GitHub: Generating a new SSH key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent) |
| Server setup | [DigitalOcean: Initial server setup with Ubuntu](https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu) |
| Firewall | [Ubuntu Server: Firewall (ufw)](https://ubuntu.com/server/docs/how-to/security/firewalls/) |
| Security updates | [Ubuntu Server: Automatic updates](https://ubuntu.com/server/docs/how-to/software/automatic-updates/) |
| Docker | [Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/), [Linux post-installation steps](https://docs.docker.com/engine/install/linux-postinstall/), [`docker compose logs`](https://docs.docker.com/reference/cli/docker/compose/logs/) |
| Managed MySQL | [DigitalOcean: MySQL](https://docs.digitalocean.com/products/databases/mysql/) |
| HTTPS | [Caddy: Automatic HTTPS](https://caddyserver.com/docs/automatic-https), [Let's Encrypt: Rate limits](https://letsencrypt.org/docs/rate-limits/), [Let's Debug](https://letsdebug.net/), [SSL Labs server test](https://www.ssllabs.com/ssltest/) |
| Stripe | [Webhooks](https://docs.stripe.com/webhooks), [Test cards](https://docs.stripe.com/testing), [Set up Stripe Tax](https://docs.stripe.com/tax/set-up), [Product tax codes](https://docs.stripe.com/tax/tax-codes), [Go-live checklist](https://docs.stripe.com/get-started/checklist/go-live), [Stripe CLI](https://docs.stripe.com/stripe-cli) |
| Email | [Resend: Domains](https://resend.com/docs/dashboard/domains/introduction), [Resend: Avoiding the spam folder](https://resend.com/guides/email/deliverability/avoid-gmail-spam-folder), [Google: Set up DMARC](https://knowledge.workspace.google.com/admin/security/set-up-dmarc) |
| Cloudflare | [SSL mode Full (strict)](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/full-strict/), [IP ranges](https://www.cloudflare.com/ips/) |
| Backups | [rclone: Install](https://rclone.org/install/), [rclone: Documentation](https://rclone.org/docs/) |
| Git | [`git checkout`](https://git-scm.com/docs/git-checkout) (including "detached HEAD") |
