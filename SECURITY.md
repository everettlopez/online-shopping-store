# Security policy

This project takes payments and stores customers' names, addresses and order history, so security reports are welcome and taken seriously.

## Reporting a vulnerability

**Please don't open a public issue for a security problem.** Report it privately through GitHub instead: go to the repository's **Security** tab and choose **Report a vulnerability**.

Include what you found, how to reproduce it, and what an attacker could do with it. The maintainers aim to reply within a week. Once a fix is released, you'll be credited in the release notes unless you'd rather not be.

## Supported versions

Fixes go into the `main` branch. If you run a store from this project, update to the latest `main` regularly ([docs/launch-checklist.md](docs/launch-checklist.md#after-every-deploy) covers how).

## Scope

In scope: the API (`app/`), the storefront (`frontend/`), and the deploy kit (`deploy/`, `docker/`, the Dockerfiles).

Out of scope: problems in a particular store's hosting or settings (for example a weak `JWT_SECRET_KEY` or `CORS_ORIGINS` set too wide), and vulnerabilities in Stripe, Resend or other services the project uses. Report those to the store's owner or to the service.

## For store owners

Your store's security also depends on how it's hosted. [docs/hosting.md](docs/hosting.md) covers the server, secrets and HTTPS, and `sh deploy/check.sh` checks the most important settings from the outside.
