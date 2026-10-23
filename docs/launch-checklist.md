# Launch checklist

Run this before a store takes its first real order, and the shorter [after every deploy](#after-every-deploy) list each time you update it. It assumes the store is set up with the deploy kit following [hosting.md](hosting.md). Commands run from the project root on the server.

Tip: copy this file into a GitHub issue or a note so you can tick the boxes as you go.

## Before launch day

- [ ] [hosting.md](hosting.md) steps 1–8 are done: server, DNS, database, email, Stripe in live mode, settings, the store is running, and you're the admin.
- [ ] The policy pages (Privacy Policy, Terms, Shipping & Returns, Contact) have been read and reviewed for your business, or the footer links to your own policies.
- [ ] Stripe Tax has a registration for every state where you collect sales tax (or `STRIPE_AUTOMATIC_TAX=false` is a deliberate choice).
- [ ] Slow-settling payment methods (ACH Direct Debit, other bank debits) are off in Stripe.
- [ ] Every sender address (`ORDERS_EMAIL_FROM`, `ACCOUNT_EMAIL_FROM`, `EMAIL_REPLY_TO`) receives mail.
- [ ] Products, categories, prices and stock are entered.
- [ ] Copies of `deploy/.env` and `deploy/.env.api` are stored somewhere safe, such as a password manager.
- [ ] `ALLOW_STRIPE_TEST_MODE` is not in `deploy/.env.api`, and `STRIPE_SECRET_KEY` is the live key (`sk_live_...`). The API refuses a test key in production unless that setting allows it.

## 1. Deploy

- [ ] Mark the version you're launching, so you can return to it:
  ```bash
  git tag "deploy-$(date +%Y%m%d-%H%M)" && git push --tags
  ```
- [ ] Back up the store: `sh deploy/backup.sh` (the database and the product images; see [hosting.md](hosting.md#running-the-store)).
- [ ] Start or update the store:
  ```bash
  docker compose -f deploy/docker-compose.yml up -d --build
  docker compose -f deploy/docker-compose.yml ps
  ```

## 2. Automated checks

- [ ] Run the checks. They test HTTPS and redirects, the API's health and production settings (docs hidden, Stripe webhook secret, cross-site protection, CORS), the security headers, the store's name, and the rate limits:
  ```bash
  sh deploy/check.sh --rate-limit
  ```
  Every line should say PASS. The content security policy shows WARN until you enforce it in step 4. `--rate-limit` locks your own address out of order lookup for a minute.
- [ ] Test the storefront and the API at [SSL Labs](https://www.ssllabs.com/ssltest/): both should get an A or better.

## 3. Check it by hand

Use a normal browser window unless a step says otherwise. Keep the browser's console open (F12) throughout and note any `Content-Security-Policy` messages for step 4.

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
- [ ] Run `docker compose -f deploy/docker-compose.yml logs api | tail -20`. The requests show your own IP address, not a `172.x` Docker address. (If they show Cloudflare's addresses, see [Behind Cloudflare's proxy](hosting.md#behind-cloudflares-proxy).)

**Admin**
- [ ] Add a product with an image, then restart the API (`docker compose -f deploy/docker-compose.yml restart api`). The image still shows.

**A real purchase with an account** (your own card, an inexpensive item)
- [ ] Checkout shows the right shipping and sales tax, and the payment goes through.
- [ ] The success page shows the order, and *My orders* lists it.
- [ ] The confirmation email arrives from your orders sender, its link opens the order, and a reply to it reaches your inbox.
- [ ] The product's stock went down by the quantity bought.
- [ ] In Stripe, the webhook endpoint's recent deliveries show success (2xx).
- [ ] In the admin pages, add a tracking number: the shipping email arrives with it.

**A real purchase as a guest** (a private window, not logged in)
- [ ] Buy an item; Stripe asks for your email and addresses, and the confirmation email arrives.
- [ ] *Track order*: finding the order by its number and email works, and a wrong email doesn't.

**Refunds**
- [ ] Refund the account purchase with the **Refund** button in the admin pages (the full amount, with *Return the items to stock* ticked). The order shows *Refunded*, the product's stock goes back up, and the refund email arrives.
- [ ] Refund the guest purchase in the Stripe Dashboard instead. Within a minute the admin pages show the order as *Refunded* with its stock back, and the refund email arrives.
- [ ] In Stripe, the webhook endpoint's recent deliveries show the `charge.refunded` events succeeded (2xx).

## 4. Lock it down

- [ ] If the console showed no `Content-Security-Policy` messages, set `CSP_HEADER=Content-Security-Policy` in `deploy/.env`, run `docker compose -f deploy/docker-compose.yml up -d`, and click through the store, checkout and the admin pages once more. If something breaks, set it back to `Content-Security-Policy-Report-Only` and note what the console reports.
- [ ] Run `sh deploy/check.sh` again: all PASS, with no WARN.

## 5. Keep watch

- [ ] `ALERT_EMAIL` is set in `deploy/.env.api`, and `docker compose -f deploy/docker-compose.yml exec api python -m app.alerts` delivers a test alert to that inbox.
- [ ] An uptime monitor checks `https://<API_DOMAIN>/api/health` and the storefront and alerts you (for example UptimeRobot or Better Stack).
- [ ] Backups: `sh deploy/backup.sh` succeeds, `BACKUP_REMOTE` copies each backup off the server (check the bucket), and the nightly cron job is in `crontab -l` ([hosting.md](hosting.md#running-the-store)). A managed database also shows its own automatic backups.
- [ ] A failed backup reaches you: with `ALERT_EMAIL` set, temporarily set `BACKUP_REMOTE=missing:nowhere` in `deploy/.env`, run `sh deploy/backup.sh`, and check that the "Backup failed" alert arrives. Then put the setting back.
- [ ] You've practiced a restore once, before you have customers: `sh deploy/backup.sh --restore <date_time>` with the backup you just made, then look around the store. Products, images and accounts should be as they were.
- [ ] You know where to look when something goes wrong: `docker compose -f deploy/docker-compose.yml logs`, Stripe's webhook deliveries, Resend's email log, and [Troubleshooting](hosting.md#troubleshooting).

The store is live.

---

## After every deploy

- [ ] Before: tag the version (step 1), and run `sh deploy/backup.sh` if the update adds files to `alembic/versions/`.
- [ ] `docker compose -f deploy/docker-compose.yml up -d --build`
- [ ] `sh deploy/check.sh`: all PASS.
- [ ] Log in, add something to the cart and open checkout (stop before paying).
- [ ] If the update touched checkout, orders or emails: a real purchase and refund, as in step 3.

## Rolling back

If an update breaks the store and a quick fix isn't obvious, go back to the last good version:

1. Find it: `git tag --list 'deploy-*'` (or `git log --oneline`).
2. Run it:
   ```bash
   git checkout <tag>
   docker compose -f deploy/docker-compose.yml up -d --build
   sh deploy/check.sh
   ```
3. The database normally stays as it is. Migrations so far only add tables and columns, which older code ignores. Restore the backup from before the update (`sh deploy/backup.sh --restore <date_time>`) only if the update damaged data. A restore loses orders placed since the backup, so check Stripe for payments made in between.
4. Fix the problem on a branch, then deploy again with the checklist above. Run `git checkout main` before pulling new versions.
