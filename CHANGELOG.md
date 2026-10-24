# Changelog

What changed in each release, for store owners. Each release's notes on the [releases page](https://github.com/everettlopez/online-shopping-store/releases) also say what to do **before you update**. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.1] - 2026-10-24

A documentation release: nothing in the running store changes, and there are no migrations or new settings.

### Changed
- Stores now run a release instead of the latest `main`. The hosting guide's setup, [updating](docs/hosting.md#updating-to-a-new-release) and private-copy steps, and the launch checklist's rollback, use release tags. **If you set up from `main`:** run `git fetch --tags && git checkout v1.0.1` on the server once, then update as the guide describes from then on.
- The launch checklist no longer pushes a `deploy-*` tag (which failed without push rights to this repository); note the release with `git describe --tags` instead.
- The hosting guide and launch checklist are rewritten for first-time self-hosters: what you should see after each step, warnings before risky ones, and safer SSH hardening that also overrides the provider's settings.

### Added
- [docs/troubleshooting.md](docs/troubleshooting.md): problems by symptom, what to collect before asking for help, how to report a bug, and checked links to official docs.
- Issue forms for bug reports and feature requests, a pull request template, a Code of Conduct and this changelog.

## [1.0.0] - 2026-10-24

The first release: guest checkout and customer accounts, Stripe Checkout with optional Stripe Tax and flat-rate shipping, order, shipping and refund emails through Resend, private order tracking, admin pages for products, categories, orders, refunds and users, and a Docker deploy kit with automatic HTTPS, security headers, rate limiting, backups and a launch check.

[Unreleased]: https://github.com/everettlopez/online-shopping-store/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/everettlopez/online-shopping-store/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/everettlopez/online-shopping-store/releases/tag/v1.0.0
