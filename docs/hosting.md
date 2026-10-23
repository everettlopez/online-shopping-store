# Host your own store

This guide takes you from a fresh server to a live store using the deploy kit in [`deploy/`](../deploy). You change only settings files, never code. Every store follows the same steps; only the values differ.

The examples use `shop.example.com` for the storefront and `api.shop.example.com` for the API. Replace them with your own domains everywhere. Keeping both on one domain (the store on the bare domain or a subdomain, the API on a subdomain of it) lets the login cookie work in every browser.

**What you end up with:** one server running three containers. Caddy answers on ports 80 and 443, gets HTTPS certificates by itself and adds security headers. The storefront and the API sit behind it, and the API is not reachable any other way. The database is a managed MySQL (or, if you prefer, a fourth container on the same server). Payments go through Stripe Checkout and email through Resend.

**What you need:**
- A Linux server with at least 2 GB of RAM (building the storefront needs it). This guide assumes Ubuntu LTS; a DigitalOcean droplet, Hetzner, Linode or any other VPS works.
- A domain whose DNS you can edit.
- A [Stripe](https://stripe.com) account and a [Resend](https://resend.com) account.
- A mailbox that can receive mail at your domain (for customer replies), for example Google Workspace, Fastmail, or free forwarding such as Cloudflare Email Routing.

Steps 1–5 set up accounts and services and can be done in any order. Steps 6–9 bring the store up.

---

## 1. Prepare the server

1. Create the server with your SSH key, then log in as root and create your own user:
   ```bash
   adduser deploy && usermod -aG sudo deploy
   rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy
   ```
2. Log in as that user. In `/etc/ssh/sshd_config`, set `PasswordAuthentication no` and `PermitRootLogin no`, then `sudo systemctl restart ssh`. Keep your current session open until you've confirmed a new one can log in.
3. Turn on the firewall and automatic security updates:
   ```bash
   sudo ufw allow OpenSSH && sudo ufw allow 80,443/tcp && sudo ufw allow 443/udp && sudo ufw enable
   sudo apt update && sudo apt install -y unattended-upgrades && sudo dpkg-reconfigure -plow unattended-upgrades
   ```
   Docker's published ports bypass ufw's rules. The kit publishes only 80 and 443, which are open anyway; don't add `ports:` to the API or database in the compose file, or they become reachable from the internet.
4. Install Docker Engine with the Compose plugin by following [Docker's guide for Ubuntu](https://docs.docker.com/engine/install/ubuntu/), then let your user run it: `sudo usermod -aG docker $USER` (log out and back in).
5. With only 1–2 GB of RAM, add swap so image builds don't run out of memory:
   ```bash
   sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```
6. Turn on your provider's server backups or snapshots if it offers them.

## 2. Point your domain at the server

Create three DNS **A records** with the server's IP address: `shop.example.com`, `www.shop.example.com` and `api.shop.example.com`. If the server has an IPv6 address, add AAAA records too.

On Cloudflare, leave them **DNS only** (grey cloud) at first. Caddy then gets its certificates directly, and the API sees visitors' real addresses. To use Cloudflare's proxy later, see [Behind Cloudflare's proxy](#behind-cloudflares-proxy).

## 3. Set up the database

**Managed MySQL (recommended).** A managed database backs itself up and can restore to a point in time. On DigitalOcean:
1. Create a MySQL 8 cluster in the same region as the server.
2. Add a database named `online_store` and a user for the store (don't use the admin user).
3. Under *Trusted sources*, allow only your server.
4. Download the cluster's **CA certificate** from its *Connection details*. You'll save it on the server in step 6.

Your connection setting will look like this (port 25060 on DigitalOcean; the password must be percent-encoded if it has symbols, `@` becomes `%40`):
```
DATABASE_URL=mysql+pymysql://store:<password>@<host>:25060/online_store?ssl_ca=/srv/certs/db-ca.crt
```
Other providers work the same way: download their CA certificate and keep the `?ssl_ca=` part. Managed MySQL often requires a primary key on every table; all of the store's tables have one.

**MySQL on the same server.** Cheaper, but backups are up to you. See [MySQL on the server](#mysql-on-the-server).

## 4. Set up email

The store sends order confirmations, shipping notices and password reset links through Resend.

1. In Resend, add your domain and create the DNS records it lists (SPF and DKIM). Wait until Resend shows the domain as verified.
2. Add a **DMARC** record, so mail providers trust your domain's mail. Start in monitoring mode:
   ```
   _dmarc.example.com   TXT   "v=DMARC1; p=none; rua=mailto:dmarc@example.com"
   ```
   Once reports show your mail passing, change `p=none` to `p=quarantine`.
3. Create an API key in Resend (one just for this server).
4. Decide on your sender addresses, for example `orders@example.com` for order emails and `support@example.com` for account emails and replies. **Make sure each one receives mail** (a mailbox, an alias on your mailbox, or forwarding). Resend only sends, so a reply to an address with no mailbox bounces.

## 5. Set up Stripe

Do this in **live mode** (test mode is for development).

1. Activate your account: business details and the bank account for payouts.
2. In the public business details and branding settings, set the name customers see on their card statement (statement descriptor), your support email, and your logo and colors for the Checkout page.
3. **Stripe Tax:** enter your business address and add a registration for every state where you collect sales tax (at least your home state). Checkout asks Stripe Tax for the tax and fails if Stripe Tax isn't set up. To launch before that, set `STRIPE_AUTOMATIC_TAX=false` and charge no tax, if that's right for your business.
4. In the payment methods settings, **turn off methods that take days to settle** (ACH Direct Debit and other bank debits). The store handles them correctly (the order waits as pending until the money arrives, and a failed payment cancels it and returns its stock), but the item is held for days and may never be paid for.
5. Add a **webhook endpoint** for `https://api.shop.example.com/api/payments/webhook` with these four events: `checkout.session.completed`, `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed` and `charge.refunded` (the last one keeps refunds you make in the Stripe Dashboard in step with the store). Copy its signing secret (`whsec_...`).
6. Copy your live **secret key** (`sk_live_...`).

## 6. Get the code and fill in the settings

```bash
git clone https://github.com/<owner>/online-shopping-store.git
cd online-shopping-store
cp deploy/.env.example deploy/.env
cp .env.example deploy/.env.api
chmod 600 deploy/.env.api
```
If you use a managed database, save its CA certificate as `deploy/certs/db-ca.crt` (`mkdir -p deploy/certs`, then copy it there).

**`deploy/.env`** holds the domains and the storefront's identity:

| Setting | Value |
| --- | --- |
| `STORE_DOMAIN` / `API_DOMAIN` | `shop.example.com` / `api.shop.example.com` |
| `ACME_EMAIL` | Your email, for certificate problems |
| `VITE_STORE_NAME`, `VITE_SUPPORT_EMAIL` | Shown in the header, title, footer and policy pages |
| `VITE_BUSINESS_NAME`, `VITE_BUSINESS_ADDRESS`, `VITE_BUSINESS_STATE`, `VITE_RETURN_DAYS` | Used on the policy and contact pages |
| `VITE_STORE_LOGO_TEXT`, `VITE_STORE_DESCRIPTION`, `VITE_*_URL` | Optional; see the comments in the file |

**`deploy/.env.api`** holds the API's secrets and settings (the comments in the file explain each one):

| Setting | Value |
| --- | --- |
| `DATABASE_URL` | From step 3 |
| `JWT_SECRET_KEY` | A new random value: `python3 -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` | From step 5 |
| `STORE_NAME` | Your store's name, for emails |
| `FRONTEND_URL` | `https://shop.example.com` |
| `PUBLIC_API_URL` | `https://api.shop.example.com` |
| `CORS_ORIGINS` | `https://shop.example.com,https://www.shop.example.com` |
| `COOKIE_SAMESITE` | `lax` |
| `ENABLE_DOCS` | `false` |
| `RESEND_API_KEY`, `EMAIL_FROM`, `ORDERS_EMAIL_FROM`, `ACCOUNT_EMAIL_FROM`, `EMAIL_REPLY_TO` | From step 4, for example `Your Store <orders@example.com>` |
| `SHIPPING_FLAT_RATE`, `FREE_SHIPPING_THRESHOLD` | Your shipping prices |
| `ALERT_EMAIL` | An inbox you read. The store emails it when something needs you: an item sold twice, a failed Stripe webhook, checkout or a refund failing, or a server error |

Leave `UPLOAD_DIR` out; the kit sets it. Both files stay on the server; git ignores them.

## 7. Start the store

```bash
docker compose -f deploy/docker-compose.yml up -d --build
```
The first build takes a few minutes. The API applies the database migrations, then starts, and Caddy gets certificates for your domains. Check:
```bash
curl https://api.shop.example.com/api/health      # {"status":"ok"}
docker compose -f deploy/docker-compose.yml ps    # every service running
docker compose -f deploy/docker-compose.yml logs -f api
```
Then open `https://shop.example.com`.

## 8. Make yourself the admin

Register an account on the storefront, then:
```bash
docker compose -f deploy/docker-compose.yml exec api python -m app.create_admin you@example.com
```
Log in again to see the admin pages. From there you can make other users admins, add categories and products.

## 9. Before you take orders

Work through the **[launch checklist](launch-checklist.md)**:
- **Automated checks:** `sh deploy/check.sh` tests HTTPS, redirects, security headers, the API's production settings and the rate limits from the outside.
- **By hand:**
  - Policy review.
  - Login in Chrome and Safari, and password reset.
  - Real visitor addresses in the logs.
  - A real purchase with an account and as a guest, then refunds.
- **Lock it down:** enforce the content security policy.
- **Keep watch:** monitoring and a backup restore you've practiced.

Run its short [after every deploy](launch-checklist.md#after-every-deploy) list on each update.

---

## Running the store

**Updating:** take a database backup when the update adds files to `alembic/versions/`, then:
```bash
git pull
docker compose -f deploy/docker-compose.yml up -d --build
sh deploy/check.sh
```

**Rolling back:** see [Rolling back](launch-checklist.md#rolling-back) in the launch checklist.

**Changing settings:** after editing `deploy/.env.api`, run `up -d` to restart the API. After editing a `VITE_*` setting in `deploy/.env`, run `up -d --build`, because the storefront bakes them in when it's built.

**Backups:**
- A managed database backs itself up; check how long your plan keeps backups.
- Product images live in the `online-store_uploads` volume. Server snapshots cover it, or copy it off the server regularly:
  ```bash
  docker run --rm -v online-store_uploads:/data -v "$PWD":/backup alpine tar czf /backup/uploads-$(date +%F).tgz -C /data .
  ```
- Keep a copy of `deploy/.env` and `deploy/.env.api` somewhere safe (a password manager), since they aren't in git.

**Logs:** `docker compose -f deploy/docker-compose.yml logs --tail 200 api` (or `web`, `caddy`). Logs rotate automatically. Each API line reads `time level logger message`, with details as `key=value`, so `... logs api | grep ERROR` or `grep order_id=42` finds things. `LOG_LEVEL=DEBUG` in `deploy/.env.api` shows more.

**Alerts:** with `ALERT_EMAIL` set, the store emails you about problems that need a person, at most once per problem every 15 minutes. Send a test with `docker compose -f deploy/docker-compose.yml exec api python -m app.alerts`. The email names what happened; the logs around that time have the details.

### MySQL on the server

The kit can run MySQL 8.4 alongside the store:
1. Set `MYSQL_PASSWORD` and `MYSQL_ROOT_PASSWORD` in `deploy/.env` to long random values.
2. Set `DATABASE_URL=mysql+pymysql://store:<MYSQL_PASSWORD>@db:3306/online_store` in `deploy/.env.api`.
3. Add `--profile mysql` to every `docker compose` command, for example `docker compose -f deploy/docker-compose.yml --profile mysql up -d --build`.

The database is stored in the `online-store_mysql` volume and isn't reachable from outside the server. Back it up every night and copy the dumps off the server:
```bash
docker compose -f deploy/docker-compose.yml --profile mysql exec -T db \
  sh -c 'mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" --single-transaction online_store' | gzip > backup-$(date +%F).sql.gz
```
To restore: `gunzip -c backup.sql.gz | docker compose -f deploy/docker-compose.yml --profile mysql exec -T db sh -c 'mysql -u root -p"$MYSQL_ROOT_PASSWORD" online_store'`.

### Behind Cloudflare's proxy

To put Cloudflare's proxy (orange cloud) in front of the server:
1. In Cloudflare's SSL/TLS settings, choose **Full (strict)**.
2. Set `TRUSTED_PROXIES` in `deploy/.env` to Cloudflare's IP ranges from [cloudflare.com/ips](https://www.cloudflare.com/ips/), separated by spaces, and run `up -d`. Caddy then takes visitors' addresses from Cloudflare's `CF-Connecting-IP` header. Without this, every visitor looks like Cloudflare to the rate limits. Don't trust any other addresses, or visitors could fake theirs.
3. Recheck the ranges now and then; Cloudflare occasionally adds new ones.

---

## Troubleshooting

- **No HTTPS certificate / "connection refused":** check that the DNS records point at the server (`dig +short shop.example.com`), that ports 80 and 443 are open, and look at `docker compose -f deploy/docker-compose.yml logs caddy`. Let's Encrypt limits repeated failures, so fix the cause before retrying many times.
- **The API keeps restarting:** `docker compose -f deploy/docker-compose.yml logs api` shows why. Usually it's a setting the API checks at startup (it names the setting), or the database: a wrong `DATABASE_URL`, the server not in the database's trusted sources, or a missing `deploy/certs/db-ca.crt`.
- **Logging in doesn't stick:** `CORS_ORIGINS` must list the storefront's exact address (with `https://`), `COOKIE_SAMESITE` should be `lax`, and both sites must share a domain.
- **Checkout fails:** the API logs say why. Common causes: Stripe Tax isn't set up (or set `STRIPE_AUTOMATIC_TAX=false`), or a test key is used with live mode.
- **Orders don't appear after payment:** check the webhook's recent deliveries in Stripe. A 400 means `STRIPE_WEBHOOK_SECRET` doesn't match that endpoint. The success page also creates the order, so customers who return to the store are covered either way.
- **No alert emails:** `ALERT_EMAIL` must be set in `deploy/.env.api` (restart the API after changing it), and alerts are sent through Resend like the store's other email. Run `docker compose -f deploy/docker-compose.yml exec api python -m app.alerts`; it says whether sending failed.
- **Emails don't arrive:** without `RESEND_API_KEY` the API only prints them in its logs. Check that the domain is verified in Resend and the sender addresses use it. Resend's dashboard shows each email's delivery.
- **Start here:** `sh deploy/check.sh` points at most setup mistakes (a FAIL line names what's wrong).
- **"Too many attempts":** the rate limits (`AUTH_RATE_LIMIT_PER_MINUTE` and the others in `.env.example`) reset after a minute. If every visitor hits them together, the API isn't seeing real addresses; see *Real visitor addresses* in the [launch checklist](launch-checklist.md) and [Behind Cloudflare's proxy](#behind-cloudflares-proxy).
