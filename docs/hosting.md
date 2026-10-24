# Host your own store

This guide takes you from a fresh server to a live store using the deploy kit in [`deploy/`](../deploy). You change only settings files, never code. Every store follows the same steps; only the values differ.

**What you end up with:** one server running three containers (a container is a packaged program that Docker runs on its own). Caddy answers on ports 80 and 443, gets HTTPS certificates by itself and adds security headers. The storefront and the API sit behind it, and the API is not reachable any other way. The database is a managed MySQL (or, if you prefer, a fourth container on the same server). Payments go through Stripe Checkout and email through Resend.

**What you need:**
- A Linux server with at least 2 GB of RAM (building the storefront needs it). This guide assumes Ubuntu 24.04 LTS; a DigitalOcean droplet, Hetzner, Linode or any other VPS works.
- A domain whose DNS you can edit.
- A [Stripe](https://stripe.com) account and a [Resend](https://resend.com) account.
- A mailbox that can receive mail at your domain (for customer replies), for example Google Workspace, Fastmail, or free forwarding such as Cloudflare Email Routing.
- An SSH key on your computer. If you don't have one, follow [GitHub's guide to generating an SSH key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent) (only the "generating" part).

## Before you start

- **Time:** about two hours of work. Waiting for DNS, Resend's domain check and Stripe's account review can add a few hours to a day, so start steps 2, 4 and 5 early.
- **Cost:** roughly $25–45 a month for a server and a managed database (less with MySQL on the server), a domain (about $10–20 a year), and Stripe's fee on each sale. Resend has a free tier that suits a small store. Prices change, so check each provider's pricing page.
- **Where commands run:** each command block says whether it runs **on your computer** or **on the server**. After you log in to the server with `ssh`, your terminal's prompt changes to something like `deploy@store:~$`; that's the server. Server commands run from the project folder (`cd ~/online-shopping-store`) unless a step says otherwise.
- **Example values:** the examples use `shop.example.com` for the storefront and `api.shop.example.com` for the API. Replace them with your own domains everywhere. Keeping both on one domain (the store on the bare domain or a subdomain, the API on a subdomain of it) lets the login cookie work in every browser. Text in angle brackets, like `<server-ip>`, is a placeholder: replace the whole thing, brackets included.
- **Editing files on the server:** `nano <file>` opens a simple editor. Save with Ctrl+O then Enter, and quit with Ctrl+X.
- **When something doesn't match:** each step says what you should see. If you don't see it, stop and check [troubleshooting.md](troubleshooting.md) before going on; later steps depend on earlier ones.

Steps 1–5 set up accounts and services and can be done in any order. Steps 6–9 bring the store up.

## Accounts and access

Create every account in the **store owner's** name and billing: the server host, the database, the domain and its DNS, Stripe, Resend and the mailbox. Payouts, customers' details and the store's data then belong to the owner, and nobody else can lock them out. Anyone who helps run the store joins as a member instead of holding the account: a Stripe team member, a DigitalOcean team member, a Cloudflare member, a Resend team member, and an admin in the store's own admin pages. Turn on two-factor authentication for every one of these accounts.

Where the store's data lives:

| What | Where | Kept safe by |
| --- | --- | --- |
| Orders, customers, accounts, products | The MySQL database | The managed database's backups and `deploy/backup.sh` |
| Product images | The `online-store_uploads` volume on the server | `deploy/backup.sh` |
| Home page photos and icon | `frontend/public/custom/` on the server | Your own copies, or your [private copy](#run-from-your-own-private-copy) of the code |
| Payments, refunds, payouts | Stripe | Stripe |
| Sent email | Resend | Resend |
| Secrets and settings | `deploy/.env` and `deploy/.env.api` on the server | The owner's password manager |

Give each server its own new secrets: a new `JWT_SECRET_KEY` and a Resend API key made for it, never ones copied from a development `.env`. Customers' data never goes anywhere else: the store has no analytics or tracking, and it talks only to Stripe and Resend.

---

## 1. Prepare the server

1. Create the server in your provider's dashboard: Ubuntu 24.04 LTS, at least 2 GB of RAM, and your SSH key added. Note its **IP address**.
2. **On your computer**, log in as root:
   ```bash
   ssh root@<server-ip>
   ```
   The first time, it asks whether to trust the server's fingerprint; type `yes`.
3. **On the server**, create your own user and give it your SSH key. `adduser` asks for a password (you'll need it for `sudo`) and some optional details you can leave blank:
   ```bash
   adduser deploy && usermod -aG sudo deploy
   rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy
   ```
4. **On your computer**, open a **second** terminal and check the new user can log in and use `sudo`:
   ```bash
   ssh deploy@<server-ip>
   ```
   Then, in that session, `sudo -v` asks for the password you just set and prints nothing if it worked.

   > [!WARNING]
   > Keep the root session from step 2 open until this works. The next step turns off password and root logins; if your key doesn't work for `deploy`, you'd be locked out and need your provider's web console to get back in.
5. **On the server, as `deploy`**, turn off password and root logins. Ubuntu reads files in `/etc/ssh/sshd_config.d/` first, and the first value it reads wins, so this file overrides the provider's defaults:
   ```bash
   printf 'PasswordAuthentication no\nPermitRootLogin no\n' | sudo tee /etc/ssh/sshd_config.d/00-hardening.conf
   sudo sshd -t && sudo systemctl restart ssh
   sudo sshd -T | grep -E '^(passwordauthentication|permitrootlogin) '
   ```
   **You should see** `passwordauthentication no` and `permitrootlogin no`. Open one more terminal and log in as `deploy` again to be sure, then close the root session.
6. Turn on the firewall. Allow SSH **before** enabling it, or the firewall cuts off your session. `ufw enable` warns that it may disrupt SSH connections; type `y`:
   ```bash
   sudo ufw allow OpenSSH
   sudo ufw allow 80,443/tcp
   sudo ufw allow 443/udp
   sudo ufw enable
   sudo ufw status
   ```
   **You should see** `Status: active` with OpenSSH, `80,443/tcp` and `443/udp` allowed.

   Docker's published ports bypass ufw's rules. The kit publishes only 80 and 443, which are open anyway; don't add `ports:` to the API or database in the compose file, or they become reachable from the internet.
7. Turn on automatic security updates (answer **Yes** when asked):
   ```bash
   sudo apt update && sudo apt install -y unattended-upgrades && sudo dpkg-reconfigure -plow unattended-upgrades
   ```
8. Install Docker Engine with the Compose plugin by following [Docker's guide for Ubuntu](https://docs.docker.com/engine/install/ubuntu/) ("Install using the apt repository"). Then let your user run it, and **log out and back in** so the change applies:
   ```bash
   sudo usermod -aG docker $USER
   ```
   After logging back in, check:
   ```bash
   docker run --rm hello-world
   docker compose version
   ```
   **You should see** "Hello from Docker!" and a Compose version (v2 or newer). If `docker` says "permission denied", you haven't logged out and back in yet.
9. With only 1–2 GB of RAM, add swap so image builds don't run out of memory:
   ```bash
   sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   free -h
   ```
   **You should see** a `Swap:` line of about 2.0Gi. Run this only once; running it again adds a second line to `/etc/fstab`.
10. Turn on your provider's server backups or snapshots if it offers them.

## 2. Point your domain at the server

DNS turns your domain name into the server's address. An **A record** points a name at an IPv4 address; an **AAAA record** does the same for IPv6.

In your domain's DNS settings (at your registrar, or Cloudflare if it manages your DNS), create three A records with the server's IP address:

| Type | Name | Value |
| --- | --- | --- |
| A | `shop.example.com` | `<server-ip>` |
| A | `www.shop.example.com` | `<server-ip>` |
| A | `api.shop.example.com` | `<server-ip>` |

Most DNS dashboards want only the part before your domain in the name field (`shop`, `www.shop`, `api.shop`). If the server has an IPv6 address, add matching AAAA records too.

On Cloudflare, leave them **DNS only** (grey cloud) at first. Caddy then gets its certificates directly, and the API sees visitors' real addresses. To use Cloudflare's proxy later, see [Behind Cloudflare's proxy](#behind-cloudflares-proxy).

**Check it, on your computer:**
```bash
nslookup api.shop.example.com
```
**You should see** your server's IP address in the answer, for each of the three names. New records usually appear within minutes but can take a few hours. Don't start the store (step 7) until all three answer, or Caddy can't get certificates.

## 3. Set up the database

**Managed MySQL (recommended).** A managed database backs itself up and can restore to a point in time. On [DigitalOcean](https://docs.digitalocean.com/products/databases/mysql/):
1. Create a MySQL 8 cluster in the same region as the server.
2. Add a database named `online_store` and a user for the store (don't use the admin user).
3. Under *Trusted sources*, allow only your server.
4. Download the cluster's **CA certificate** from its *Connection details*. You'll save it on the server in step 6.

Your connection setting will look like this (port 25060 on DigitalOcean):
```
DATABASE_URL=mysql+pymysql://store:<password>@<host>:25060/online_store?ssl_ca=/srv/certs/db-ca.crt
```
Other providers work the same way: download their CA certificate and keep the `?ssl_ca=` part. Managed MySQL often requires a primary key on every table; all of the store's tables have one.

### Percent-encoding a password

`DATABASE_URL` is a web address, so some symbols in the password must be written as codes, or the API can't connect. Replace each one:

| Symbol | Write | Symbol | Write |
| --- | --- | --- | --- |
| `@` | `%40` | `#` | `%23` |
| `:` | `%3A` | `%` | `%25` |
| `/` | `%2F` | `&` | `%26` |
| `?` | `%3F` | `+` | `%2B` |

For example, the password `p@ss#1` becomes `p%40ss%231`. Letters, digits, `-`, `_`, `.` and `~` stay as they are. A long password of only letters and digits avoids the question entirely.

**MySQL on the same server.** Cheaper, but backups are up to you. See [MySQL on the server](#mysql-on-the-server).

## 4. Set up email

The store sends order confirmations, shipping notices and password reset links through Resend.

1. In Resend, [add your domain](https://resend.com/docs/dashboard/domains/introduction) and create the DNS records it lists (SPF and DKIM) at your DNS provider.
   **You should see** the domain marked **Verified** in Resend. This can take from minutes to a few hours; Resend's page shows which record it's still waiting for.
2. Add a **DMARC** record, so mail providers trust your domain's mail. Start in monitoring mode, with your own domain and an address that receives mail:
   ```
   _dmarc.example.com   TXT   "v=DMARC1; p=none; rua=mailto:dmarc@example.com"
   ```
   Check it on your computer with `nslookup -type=TXT _dmarc.example.com`. Once reports show your mail passing (after a few weeks), change `p=none` to `p=quarantine`. [Google's DMARC guide](https://knowledge.workspace.google.com/admin/security/set-up-dmarc) explains the reports.
3. Create an API key in Resend (one just for this server, with "Sending access"). Copy it now (`re_...`); Resend shows it only once.
4. Decide on your sender addresses, for example `orders@example.com` for order emails and `support@example.com` for account emails and replies. **Make sure each one receives mail** (a mailbox, an alias on your mailbox, or forwarding): send each a test email from another account. Resend only sends, so a reply to an address with no mailbox bounces.

## 5. Set up Stripe

Do this in **live mode** (test mode is for development). If you'd rather try the whole store on test keys first, you can, and switch later with [Going live with Stripe](#going-live-with-stripe).

1. Activate your account: business details and the bank account for payouts. Stripe may take a while to review them.
2. In the public business details and branding settings, set the name customers see on their card statement (statement descriptor), your support email, and your logo and colors for the Checkout page.
3. **[Stripe Tax](https://docs.stripe.com/tax/set-up):** enter your business address and add a registration for every state where you collect sales tax (at least your home state). Checkout asks Stripe Tax for the tax and fails if Stripe Tax isn't set up. To launch before that, set `STRIPE_AUTOMATIC_TAX=false` and charge no tax, if that's right for your business.
4. In the payment methods settings, **turn off methods that take days to settle** (ACH Direct Debit and other bank debits). The store handles them correctly (the order waits as pending until the money arrives, and a failed payment cancels it and returns its stock), but the item is held for days and may never be paid for.
5. Add a **webhook endpoint** (Developers → Webhooks). A webhook is how Stripe tells the store a payment went through. Use `https://api.shop.example.com/api/payments/webhook` and select these four events:
   - `checkout.session.completed`
   - `checkout.session.async_payment_succeeded`
   - `checkout.session.async_payment_failed`
   - `charge.refunded` (keeps refunds you make in the Stripe Dashboard in step with the store)

   Copy its **signing secret** (`whsec_...`). Deliveries fail until the store is running in step 7; that's expected.
6. Copy your live **secret key** (`sk_live_...`, under Developers → API keys).

> [!WARNING]
> The live secret key can move money. Paste it only into `deploy/.env.api` on the server and your password manager, never into chat, email, an issue or a commit.

## 6. Get the code and fill in the settings

**On the server**, download the code and switch to the latest release. Stores run a [release](https://github.com/everettlopez/online-shopping-store/releases), a version that has been tested and has notes on what changed, rather than the newest work in progress on `main`:
```bash
cd ~
git clone https://github.com/everettlopez/online-shopping-store.git
cd online-shopping-store
git checkout "$(git tag --list 'v*' --sort=-v:refname | head -n 1)"
git describe --tags
```
**You should see** a version such as `v1.0.1`. Git also prints a note about being in a "detached HEAD" state: that's expected. It means the folder holds that exact release rather than a branch. Don't commit changes on the server.

To run your store from a private repository of your own instead, set that up first and clone it here; see [Run from your own private copy](#run-from-your-own-private-copy).

Now create the two settings files from their examples, and make them readable only by you:
```bash
cp deploy/.env.example deploy/.env
cp .env.example deploy/.env.api
chmod 600 deploy/.env deploy/.env.api
```

> [!WARNING]
> These two files hold your store's secrets. Git ignores them, so they're never uploaded by accident; keep it that way. Never commit them, even to a private repository, and never paste them anywhere public. Keep a copy of both in your password manager once they're filled in.

If you use a managed database, save its CA certificate as `deploy/certs/db-ca.crt`. On your computer, from the folder you downloaded it to (the file name varies by provider):
```bash
ssh deploy@<server-ip> "mkdir -p online-shopping-store/deploy/certs"
scp ca-certificate.crt deploy@<server-ip>:online-shopping-store/deploy/certs/db-ca.crt
```

**Your photos:** copy the home page photos and icon into `frontend/public/custom/` on the server. On your computer:
```bash
scp hero.jpg banner.jpg deploy@<server-ip>:online-shopping-store/frontend/public/custom/
```
Then point the `VITE_*_URL` settings below at them (`VITE_HERO_IMAGE_URL=/custom/hero.jpg`). Git ignores that folder, so a fresh clone doesn't have them, and `deploy/backup.sh` doesn't back them up: keep your own copies. Without your own photos the store uses its default hero image.

Open each file with `nano` and fill in the values below. Each setting in the files has a comment explaining it; lines starting with `#` are off until you remove the `#`.

**`deploy/.env`** (`nano deploy/.env`) holds the domains and the storefront's identity:

| Setting | Value |
| --- | --- |
| `STORE_DOMAIN` / `API_DOMAIN` | `shop.example.com` / `api.shop.example.com` |
| `ACME_EMAIL` | Your email, for certificate problems |
| `VITE_STORE_NAME`, `VITE_SUPPORT_EMAIL` | Shown in the header, title, footer and policy pages |
| `VITE_BUSINESS_NAME`, `VITE_BUSINESS_ADDRESS`, `VITE_BUSINESS_STATE`, `VITE_RETURN_DAYS` | Used on the policy and contact pages |
| `VITE_STORE_LOGO_TEXT`, `VITE_STORE_DESCRIPTION`, `VITE_*_URL` | Optional; see the comments in the file |
| `CSP_HEADER` | Leave as `Content-Security-Policy-Report-Only` until step 4 of the [launch checklist](launch-checklist.md#4-lock-it-down) |
| `HSTS_INCLUDE_SUBDOMAINS` | `false`. Set `true` only when every subdomain of your domain (mail, blog, and any you'll add) serves HTTPS: browsers then refuse plain HTTP on all of them for a year, and that can't be undone early |
| `TRUSTED_PROXIES` | Only behind Cloudflare's proxy; see [Behind Cloudflare's proxy](#behind-cloudflares-proxy) |
| `BACKUP_DIR`, `BACKUP_KEEP_DAYS`, `BACKUP_REMOTE` | Optional; see [Backups](#backups) |

**`deploy/.env.api`** (`nano deploy/.env.api`) holds the API's secrets and settings:

| Setting | Value |
| --- | --- |
| `DATABASE_URL` | From step 3, with the password [percent-encoded](#percent-encoding-a-password) |
| `JWT_SECRET_KEY` | A new random value. Make one with `python3 -c "import secrets; print(secrets.token_urlsafe(48))"` and paste it in |
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

These have defaults that suit most stores; set one only to change it:

| Setting | Default and when to change it |
| --- | --- |
| `STRIPE_AUTOMATIC_TAX` | `true`: Stripe Tax adds sales tax. Set `false` only if you deliberately charge none (step 5) |
| `STRIPE_PRODUCT_TAX_CODE` | `txcd_30011000`, Stripe's code for **clothing**. If you sell something else, use your products' code from [Stripe's tax codes](https://docs.stripe.com/tax/tax-codes), or tax is worked out as if you sold clothes |
| `COOKIE_SECURE` | `true`; production refuses `false` |
| `PASSWORD_RESET_MINUTES` | `30`: how long a reset link works |
| `LOG_LEVEL` | `INFO`; `DEBUG` shows more while you investigate something |
| `AUTH_RATE_LIMIT_PER_MINUTE`, `LOOKUP_RATE_LIMIT_PER_MINUTE`, `CHECKOUT_RATE_LIMIT_PER_MINUTE`, `REPORTS_RATE_LIMIT_PER_MINUTE` | `10`, `20`, `20`, `30` requests a minute per visitor (an IPv6 visitor counts per /64 network). Each API worker counts separately, so a visitor gets up to twice that with the default two workers. `0` turns a limit off |
| `SQL_ECHO` | `false`. Never turn it on in production: it logs every query, with customers' details |
| `ALLOW_STRIPE_TEST_MODE` | Unset. `true` lets the store run on Stripe test keys for a trial run; see [Going live with Stripe](#going-live-with-stripe) |

Leave `UPLOAD_DIR` and `ENVIRONMENT` out; the kit sets them.

The kit runs the API with `ENVIRONMENT=production`, so the API refuses to start with a setting that only suits development: `ENABLE_DOCS` on, `COOKIE_SECURE` off, a `localhost` or plain-`http` address in `FRONTEND_URL`, `PUBLIC_API_URL` or `CORS_ORIGINS`, no `RESEND_API_KEY`, Resend's `onboarding@resend.dev` sender, or a Stripe test key (`sk_test_...`). Its log names every setting to fix. To try the whole store with Stripe's test keys before taking real payments, add `ALLOW_STRIPE_TEST_MODE=true`, and remove it when you switch to the live key.

**Check the files**, still in the project folder:
```bash
docker compose -f deploy/docker-compose.yml config --quiet
```
**You should see** nothing: no output means Docker could read both files. An error names the file and line to fix. (The API checks the values themselves when it starts, in step 7.)

## 7. Start the store

```bash
docker compose -f deploy/docker-compose.yml up -d --build
```
The first build takes several minutes. The API applies the database migrations, then starts, and Caddy gets certificates for your domains once the API and storefront report healthy. Then check:
```bash
docker compose -f deploy/docker-compose.yml ps
```
**You should see** `api`, `web` and `caddy` with a status of `Up ... (healthy)`. `(health: starting)` means wait a minute and run it again. Then:
```bash
curl https://api.shop.example.com/api/health
```
**You should see** `{"status":"ok"}`. Then open `https://shop.example.com` in your browser: your store's name is in the header, and the address bar shows a padlock.

**If it didn't work**, look at the logs of the service that isn't healthy (press Ctrl+C to stop following them):
```bash
docker compose -f deploy/docker-compose.yml logs -f api
```
A line starting `Invalid configuration:` names each setting to fix in `deploy/.env.api`; fix them and run the `up -d` command again. See [troubleshooting.md](troubleshooting.md) for the other common causes.

## 8. Make yourself the admin

Register an account on the storefront with your email, then on the server:
```bash
docker compose -f deploy/docker-compose.yml exec api python -m app.create_admin you@example.com
```
**You should see** a message that the account is now an admin. Log out and in again to see the admin pages. From there you can make other users admins, add categories and products.

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

Run its short [after every update](launch-checklist.md#after-every-update) list each time you update.

---

## Running the store

### Updating to a new release

New releases are listed on the [releases page](https://github.com/everettlopez/online-shopping-store/releases). Watch the repository (**Watch → Custom → Releases**) to get an email when one comes out. Each release's notes have a **Before you update** part that says whether it changes the database or adds settings.

1. **See what you run and what's new**, on the server:
   ```bash
   git describe --tags
   git fetch --tags
   git tag --list 'v*' --sort=-v:refname | head -n 5
   ```
   The first line is the release you run now; the list shows the newest releases first.
2. **Read the release notes** for every release between yours and the new one, and do anything they ask before updating.
3. **See whether new settings were added** (replace both versions with yours and the new one). Anything new shows with a `+`; copy the lines you need into `deploy/.env` or `deploy/.env.api`:
   ```bash
   git diff v1.0.1 v1.1.0 -- .env.example deploy/.env.example
   ```
4. **Back up** the database and product images, so you can return to this point:
   ```bash
   sh deploy/backup.sh
   ```
5. **Switch to the new release and rebuild:**
   ```bash
   git checkout v1.1.0
   docker compose -f deploy/docker-compose.yml up -d --build
   sh deploy/check.sh
   ```
   **You should see** every line of `check.sh` say PASS. Then run the launch checklist's [after every update](launch-checklist.md#after-every-update) list.

If `git checkout` says your local changes would be overwritten, a file in the code was edited on the server; see [troubleshooting.md](troubleshooting.md#git-checkout-says-local-changes-would-be-overwritten). If the update breaks something, see [Rolling back](launch-checklist.md#rolling-back).

### Changing settings

After editing `deploy/.env.api`, run `docker compose -f deploy/docker-compose.yml up -d` to restart the API. After editing a `VITE_*` setting in `deploy/.env`, or changing a photo in `frontend/public/custom/`, run `up -d --build`, because the storefront bakes them in when it's built.

### Backups

`deploy/backup.sh` backs up both things the store can't rebuild: the database (a managed one, or MySQL on the server) and the product images in the `online-store_uploads` volume. It reads the database's address and login from `deploy/.env.api`, so it needs no settings of its own:
```bash
sh deploy/backup.sh
```
Each run writes `database-<date_time>.sql.gz` and `uploads-<date_time>.tgz` to `deploy/backups` (or `BACKUP_DIR`), checks that both are complete, and deletes local copies older than 14 days (`BACKUP_KEEP_DAYS`). If a backup fails, the script exits with an error and emails `ALERT_EMAIL`.

1. **Off the server:** a backup on the same server is lost with it. Install [rclone](https://rclone.org/install/), run `rclone config` to add a storage bucket (Backblaze B2, S3, Google Drive and others; see [rclone's docs](https://rclone.org/docs/)), and set `BACKUP_REMOTE` in `deploy/.env`, for example `BACKUP_REMOTE=b2:my-store-backups/store`. Each backup is then copied there too. Give the bucket a lifecycle rule that deletes old copies (for example after 90 days).
2. **Every night:** once a run by hand has worked (it creates `deploy/backups`, where this line keeps its log), add it to the server's crontab (`crontab -e`, then add the line at the end), with the project's path:
   ```
   0 3 * * * cd /home/deploy/online-shopping-store && sh deploy/backup.sh >> deploy/backups/backup.log 2>&1
   ```
   `crontab -l` shows the line afterwards. The server's clock is usually UTC, so `0 3` is 3:00 UTC.
3. **Restore** a backup, for example after a bad update or lost data:
   ```bash
   sh deploy/backup.sh --restore                    # lists the backups on the server
   sh deploy/backup.sh --restore 2026-10-23_0300    # puts that one back
   ```
   > [!WARNING]
   > A restore replaces the store's database and product images with the backup's. **Everything added since that backup is lost**: orders, accounts and products. Check Stripe for payments made in between, and take a fresh backup first if you might want today's data back.

   It asks you to type `restore`, then stops the API, replaces the database and the product images, and starts the API again. To restore from the off-site copy, first copy both files back: `rclone copy b2:my-store-backups/store/database-2026-10-23_0300.sql.gz deploy/backups/` (and the `uploads-` file).

A managed database also keeps its own backups; check how long your plan keeps them. Neither covers `deploy/.env` and `deploy/.env.api`: keep a copy of both somewhere safe (a password manager), since they aren't in git. A managed database's CA certificate (`deploy/certs/`) can be downloaded again, and Caddy gets new HTTPS certificates by itself.

### Logins, logs and alerts

**Logins:** a login lasts 60 minutes. Changing a password (or resetting it) logs that account out everywhere else, and customers can log out of all their devices from their account page. To end someone's sessions yourself, set a new password for them in the admin pages. Changing `JWT_SECRET_KEY` logs everyone out.

**Logs:** `docker compose -f deploy/docker-compose.yml logs --tail 200 api` (or `web`, `caddy`). Logs rotate automatically. Each API line reads `time level logger message`, with details as `key=value`, so `... logs api | grep ERROR` or `grep order_id=42` finds things. `LOG_LEVEL=DEBUG` in `deploy/.env.api` shows more.

**Alerts:** with `ALERT_EMAIL` set, the store emails you about problems that need a person, at most once per problem every 15 minutes. Send a test with `docker compose -f deploy/docker-compose.yml exec api python -m app.alerts`. The email names what happened; the logs around that time have the details.

### Run from your own private copy

A private repository of your own keeps your store's photos, and any changes of your own, in version control, while you still take this project's releases. GitHub can't make a private fork of a public repository, so duplicate it instead. On your computer:

1. Create an empty **private** repository on GitHub (no README or license), for example `my-store`.
2. Copy this project into it, with its history and release tags:
   ```bash
   git clone --bare https://github.com/everettlopez/online-shopping-store.git
   cd online-shopping-store.git
   git push --mirror git@github.com:<you>/my-store.git
   cd .. && rm -rf online-shopping-store.git
   ```
3. Clone your copy, and keep this project as `upstream` for updates (the last line stops you pushing to it by mistake):
   ```bash
   git clone git@github.com:<you>/my-store.git && cd my-store
   git remote add upstream https://github.com/everettlopez/online-shopping-store.git
   git remote set-url --push upstream DISABLE
   ```
4. Start your `main` from the latest release, so your store runs only released code:
   ```bash
   git fetch upstream --tags
   git reset --hard v1.0.1
   git push --force origin main
   ```
   Use the newest version from the [releases page](https://github.com/everettlopez/online-shopping-store/releases). This is the only time you force-push; it's safe now because the copy holds nothing of yours yet.
5. Commit your photos. Leave `.gitignore` as it is (so updates merge cleanly) and add them with `-f`:
   ```bash
   git add -f frontend/public/custom/hero.jpg frontend/public/custom/banner.jpg
   git commit -m "Add the store's photos" && git push
   ```
   **Never commit** `deploy/.env`, `deploy/.env.api`, `deploy/certs/` or backups, even to a private repository.
6. Let the server read it. On the server, make a key with `ssh-keygen -t ed25519 -f ~/.ssh/store_deploy -N ""`, add the contents of `~/.ssh/store_deploy.pub` (`cat ~/.ssh/store_deploy.pub`) to your repository's **Settings → Deploy keys** (read-only, the default), then clone with it in step 6 instead of the public address. Stay on `main`; skip the `git checkout` of a release there:
   ```bash
   GIT_SSH_COMMAND="ssh -i ~/.ssh/store_deploy" git clone git@github.com:<you>/my-store.git online-shopping-store
   cd online-shopping-store && git config core.sshCommand "ssh -i ~/.ssh/store_deploy"
   ```

**Taking a release:** on your computer, merge the new release's tag, not upstream's `main`:
```bash
git fetch upstream --tags
git merge v1.1.0
git push && git push --tags
```
Then on the server, follow [Updating to a new release](#updating-to-a-new-release) with `git pull` in place of `git checkout <version>` (your server stays on your own `main`, which brings your photos too).

**Mark each version you deploy** in your copy, so you can roll back to it with your photos included: `git tag store-$(date +%Y%m%d) && git push --tags` on your computer after merging. The launch checklist's [Rolling back](launch-checklist.md#rolling-back) uses these tags for a private copy.

Private repositories have a monthly allowance of free GitHub Actions minutes, which the CI workflow uses. Dependabot's pull requests are optional in your copy, since updates arrive from `upstream`; you can turn it off under the repository's security settings.

### MySQL on the server

The kit can run MySQL 8.4 alongside the store:
1. Set `MYSQL_PASSWORD` and `MYSQL_ROOT_PASSWORD` in `deploy/.env` to long random values of letters and digits (`python3 -c "import secrets; print(secrets.token_hex(24))"` makes one).
2. Set `DATABASE_URL=mysql+pymysql://store:<MYSQL_PASSWORD>@db:3306/online_store` in `deploy/.env.api`.
3. Add `--profile mysql` to every `docker compose` command, for example `docker compose -f deploy/docker-compose.yml --profile mysql up -d --build`.

The database is stored in the `online-store_mysql` volume and isn't reachable from outside the server. Nothing backs it up for you: set up `deploy/backup.sh` with an off-site `BACKUP_REMOTE` and a nightly cron job (see [Backups](#backups)). It works the same with this database.

### Going live with Stripe

If you tried the store with Stripe's test keys first (`ALLOW_STRIPE_TEST_MODE=true`), switch to live mode before you announce it. Settings made in test mode don't carry over to live mode. Stripe's own [go-live checklist](https://docs.stripe.com/get-started/checklist/go-live) is a good companion.

1. **Decide what happens to the trial's orders.** Paid orders can't be deleted (they're financial records), so test orders stay in the admin pages and the order numbers you saw. For a clean start, make a new empty database before launch, point `DATABASE_URL` at it, and enter the catalog again (or do the trial before you enter the real catalog). Otherwise, keep a note of the test orders' numbers. Customers' saved test-mode Stripe details are replaced on their next checkout without anything for you to do.
2. **In the Stripe Dashboard, in live mode:**
   - Business details, payouts, branding and the statement descriptor are done (step 5).
   - **Stripe Tax:** add the business address and every registration again; test-mode registrations don't apply to live payments.
   - Slow-settling payment methods are off.
   - Add the **live webhook endpoint** for `https://<API_DOMAIN>/api/payments/webhook` with the four events from step 5, and copy its signing secret.
3. **Delete the test-mode webhook endpoint** (in test mode), and stop any `stripe listen` you ran, so test events stop arriving.
4. **On the server,** in `deploy/.env.api`: set `STRIPE_SECRET_KEY` to the live key (`sk_live_...`) and `STRIPE_WEBHOOK_SECRET` to the live endpoint's secret, and delete the `ALLOW_STRIPE_TEST_MODE` line. Then:
   ```bash
   docker compose -f deploy/docker-compose.yml up -d
   sh deploy/check.sh
   ```
   With the line gone, the API refuses to start on a test key, so a key you forgot to change shows up now rather than as a checkout that takes no money.
5. **Make one real purchase** with your own card, for the cheapest item. Check that the order appears, the confirmation email arrives, and the live webhook's recent deliveries show success (2xx). Then refund it from the order's admin page and check that the refund email arrives and the money shows as refunded in Stripe.

### Behind Cloudflare's proxy

To put Cloudflare's proxy (orange cloud) in front of the server:
1. In Cloudflare's SSL/TLS settings, choose **[Full (strict)](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/full-strict/)**. Any other mode either breaks HTTPS or sends traffic unencrypted to your server.
2. Set `TRUSTED_PROXIES` in `deploy/.env` to Cloudflare's IP ranges from [cloudflare.com/ips](https://www.cloudflare.com/ips/), separated by spaces, and run `up -d`. Caddy then takes visitors' addresses from Cloudflare's `CF-Connecting-IP` header. Without this, every visitor looks like Cloudflare to the rate limits. Don't trust any other addresses, or visitors could fake theirs.
3. Recheck the ranges now and then; Cloudflare occasionally adds new ones.

---

## Troubleshooting

Common problems, their causes and fixes, what to collect before asking for help, and a list of trusted references are in **[troubleshooting.md](troubleshooting.md)**. Start with `sh deploy/check.sh`: a FAIL line names what's wrong.
