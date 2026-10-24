# Launch checklist

Run this before a store takes its first real order, and the shorter [after every update](#after-every-update) list each time you update it. It assumes the store is set up with the deploy kit following [hosting.md](hosting.md). Commands run **on the server**, from the project folder (`cd ~/online-shopping-store`).

**How to use it:** copy this file into a GitHub issue in your own repository, or a note, so you can tick the boxes as you go. Do the sections in order. If a check fails, stop and fix it before going on: [troubleshooting.md](troubleshooting.md) covers the usual causes.

## Before launch day

- [ ] [hosting.md](hosting.md) steps 1–8 are done: server, DNS, database, email, Stripe in live mode, settings, the store is running, and you're the admin.
- [ ] The policy pages (Privacy Policy, Terms, Shipping & Returns, Contact) have been read and reviewed for your business, or the footer links to your own policies.
- [ ] Stripe Tax has a registration for every state where you collect sales tax (or `STRIPE_AUTOMATIC_TAX=false` is a deliberate choice).
- [ ] Slow-settling payment methods (ACH Direct Debit, other bank debits) are off in Stripe.
- [ ] Every sender address (`ORDERS_EMAIL_FROM`, `ACCOUNT_EMAIL_FROM`, `EMAIL_REPLY_TO`) receives mail: you've sent each one a test email from another account and it arrived.
- [ ] Products, categories, prices and stock are entered.
- [ ] Copies of `deploy/.env` and `deploy/.env.api` are stored somewhere safe, such as a password manager.
- [ ] Your home page photos and icon are in `frontend/public/custom/` on the server, and you keep copies of them (or they're committed to your [private copy](hosting.md#run-from-your-own-private-copy)).
- [ ] The store's owner holds every account (server, database, domain, Stripe, Resend, mailbox), each with two-factor authentication on, and helpers are members of them ([Accounts and access](hosting.md#accounts-and-access)).
- [ ] `ALLOW_STRIPE_TEST_MODE` is not in `deploy/.env.api`, and `STRIPE_SECRET_KEY` is the live key (`sk_live_...`). The API refuses a test key in production unless that setting allows it. After a trial run on test keys, follow [Going live with Stripe](hosting.md#going-live-with-stripe).
- [ ] `HSTS_INCLUDE_SUBDOMAINS` in `deploy/.env` is `false`, or every subdomain of your domain serves HTTPS.

## 1. Deploy

- [ ] Note the release you're launching, so you can return to it. Write it in your checklist copy:
  ```bash
  git describe --tags
  ```
  **You should see** a release such as `v1.0.1`. If it shows something like `v1.0.1-3-gabc1234`, you're not on a release; go back to [hosting.md step 6](hosting.md#6-get-the-code-and-fill-in-the-settings). (In a [private copy](hosting.md#run-from-your-own-private-copy), tag the version on your computer instead, as described there.)
- [ ] Back up the store: `sh deploy/backup.sh` (the database and the product images; see [Backups](hosting.md#backups)).
- [ ] Start or update the store:
  ```bash
  docker compose -f deploy/docker-compose.yml up -d --build
  docker compose -f deploy/docker-compose.yml ps
  ```
  **You should see** `api`, `web` and `caddy` as `Up ... (healthy)`.

## 2. Automated checks

- [ ] Run the checks. They test HTTPS and redirects, the API's health and production settings (docs hidden, Stripe webhook secret, cross-site protection, CORS), the security headers, the store's name, description, icon and photos, and the rate limits:
  ```bash
  sh deploy/check.sh --rate-limit
  ```
  Every line should say PASS. The content security policy shows WARN until you enforce it in step 4. `--rate-limit` locks your own address out of order lookup for a minute, which is expected.
- [ ] Test the storefront and the API at [SSL Labs](https://www.ssllabs.com/ssltest/): both should get an A or better.

## 3. Check it by hand

Use a normal browser window unless a step says otherwise. Keep the browser's console open (F12, then the **Console** tab) throughout and note any `Content-Security-Policy` messages for step 4. Browsers also send each policy violation to the API, which logs it, so step 4 can check every visitor's browser, not only yours.

**Storefront**
- [ ] The header, page title and footer show your store's name; the policy and contact pages show your details, with no `example.com` or blank spots.
- [ ] Browse categories and products, filter and sort, and open a product page. Images load. Its back link returns to the same filters, and its address works when pasted into a new tab.
- [ ] On a phone, the header menu and the products page's Filter button open and close, and nothing in the header overlaps.
- [ ] The browser tab shows your icon, and pasting the store's address into a message (or a checker such as opengraph.xyz) previews its name, description and image.

**Accounts**
- [ ] Register a new customer account, log in, refresh the page, and you're still logged in. Do this in **Chrome and Safari** (Safari, including on an iPhone, is strictest about cookies).
- [ ] Log out.
- [ ] *Forgot password*: the email arrives from your account sender, its link sets a new password, and the same link doesn't work a second time.

**Real visitor addresses**
- [ ] Run `docker compose -f deploy/docker-compose.yml logs api | tail -20`. The requests show your own IP address (search "what is my IP" to see it), not a `172.x` Docker address. (If they show Cloudflare's addresses, see [Behind Cloudflare's proxy](hosting.md#behind-cloudflares-proxy).)

**Admin**
- [ ] Add a product with an image, then restart the API (`docker compose -f deploy/docker-compose.yml restart api`). The image still shows.

**A real purchase with an account** (your own card, an inexpensive item; you'll refund it below)
- [ ] Checkout shows the right shipping and sales tax, and the payment goes through.
- [ ] The success page shows the order, and *My orders* lists it.
- [ ] The confirmation email arrives from your orders sender, its link opens the order, and a reply to it reaches your inbox.
- [ ] The product's stock went down by the quantity bought.
- [ ] In Stripe (Developers → Webhooks → your endpoint), the recent deliveries show success (2xx).
- [ ] In the admin pages, add a tracking number: the shipping email arrives with it.

**A real purchase as a guest** (a private window, not logged in)
- [ ] Buy an item; Stripe asks for your email and addresses, and the confirmation email arrives.
- [ ] *Track order*: finding the order by its number and email works, and a wrong email doesn't.

**Refunds**
- [ ] Refund the account purchase with the **Refund** button in the admin pages (the full amount, with *Return the items to stock* ticked). The order shows *Refunded*, the product's stock goes back up, and the refund email arrives.
- [ ] Refund the guest purchase in the Stripe Dashboard instead. Within a minute the admin pages show the order as *Refunded* with its stock back, and the refund email arrives.
- [ ] In Stripe, the webhook endpoint's recent deliveries show the `charge.refunded` events succeeded (2xx).

## 4. Lock it down

- [ ] After a few days of real visitors, check what the policy would block:
  ```bash
  docker compose -f deploy/docker-compose.yml logs --since 72h api | grep "csp violation"
  ```
  Each line names the rule (`directive=`), what it blocked and on which page. Lines blocking browser extensions (`blocked=chrome-extension` and similar) are harmless; anything blocking the store's own pages, Stripe or your image host needs fixing first. No output means nothing was blocked.
- [ ] If the log and your console showed no `Content-Security-Policy` problems, set `CSP_HEADER=Content-Security-Policy` in `deploy/.env`, run `docker compose -f deploy/docker-compose.yml up -d`, and click through the store, checkout and the admin pages once more. If something breaks, set it back to `Content-Security-Policy-Report-Only`, run `up -d` again, and note what the console reports.
- [ ] Run `sh deploy/check.sh` again: all PASS, with no WARN.

## 5. Keep watch

- [ ] `ALERT_EMAIL` is set in `deploy/.env.api`, and `docker compose -f deploy/docker-compose.yml exec api python -m app.alerts` delivers a test alert to that inbox.
- [ ] An uptime monitor checks `https://<API_DOMAIN>/api/health` and the storefront and alerts you (for example UptimeRobot or Better Stack).
- [ ] You're watching the repository's releases (**Watch → Custom → Releases** on GitHub), so you hear about updates and security fixes.
- [ ] Backups: `sh deploy/backup.sh` succeeds and its last lines say `copied to <your BACKUP_REMOTE>`. In the bucket's own web page (or `rclone ls <BACKUP_REMOTE>`), both new files are there with the same sizes as in `deploy/backups`. The nightly cron job is in `crontab -l` ([Backups](hosting.md#backups)), and a managed database also shows its own automatic backups.
- [ ] A failed backup reaches you: with `ALERT_EMAIL` set, temporarily set `BACKUP_REMOTE=missing:nowhere` in `deploy/.env` and run `sh deploy/backup.sh`. It should end with `Backup failed: couldn't copy the backup to missing:nowhere`, and an email with the subject "Backup failed" should reach `ALERT_EMAIL` within a few minutes (check spam, then Resend's email log if it doesn't). **Put the setting back afterwards.**
- [ ] You've practiced a restore once, before you have customers: `sh deploy/backup.sh --restore <date_time>` with the backup you just made, then look around the store. Products, images and accounts should be as they were. (Once you have customers, a restore loses everything since the backup; see the warning in [Backups](hosting.md#backups).)
- [ ] You know where to look when something goes wrong: `docker compose -f deploy/docker-compose.yml logs`, Stripe's webhook deliveries, Resend's email log, and [troubleshooting.md](troubleshooting.md).

The store is live.

---

## After every update

Follow [Updating to a new release](hosting.md#updating-to-a-new-release) in the hosting guide, then:

- [ ] Before: note the release you ran (`git describe --tags`), read the new release's notes, and run `sh deploy/backup.sh`.
- [ ] `sh deploy/check.sh`: all PASS.
- [ ] Log in, add something to the cart and open checkout (stop before paying).
- [ ] If the release notes say it touched checkout, orders or emails: a real purchase and refund, as in step 3.

## Rolling back

If an update breaks the store and a quick fix isn't obvious, go back to the release you ran before. The order of these steps matters.

1. **Find the release to return to:** the one you noted before updating, or list them with `git tag --list 'v*' --sort=-v:refname | head -n 5`. In a private copy, use your own `store-...` tags (`git tag --list 'store-*'`) after `git fetch --tags`.
2. **If the update added database migrations, undo them first, while the newer code is still checked out.** The older version refuses to start on a database it doesn't recognize (its log says `Can't locate revision`). Count the update's migrations (replace `v1.0.1` with the release you're returning to):
   ```bash
   git diff --name-only --diff-filter=A v1.0.1 HEAD -- alembic/versions
   ```
   Each line is one migration. If the list is empty, skip to step 3. Otherwise, back up, then step the database back by that many (replace `2` with the number of lines):
   ```bash
   sh deploy/backup.sh
   docker compose -f deploy/docker-compose.yml run --rm --no-deps api alembic downgrade -2
   ```
   > [!WARNING]
   > Undoing a migration removes what it added, such as a new column and anything stored in it since the update. That's why you back up first. CI checks that every migration can be undone.
3. **Run the older release:**
   ```bash
   git checkout v1.0.1
   docker compose -f deploy/docker-compose.yml up -d --build
   sh deploy/check.sh
   ```
4. **Restore the backup from before the update** (`sh deploy/backup.sh --restore <date_time>`) only if the update damaged data. A restore loses orders placed since the backup, so check Stripe for payments made in between.
5. **Report what broke** (see [Reporting a bug](troubleshooting.md#reporting-a-bug)), and update again once a fixed release is out, with the [after every update](#after-every-update) list. In a private copy, `git checkout main` before you `git pull` again.
