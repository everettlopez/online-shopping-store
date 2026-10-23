# Your store's photos

Put your own images for the storefront here, for example `hero.jpg` and `banner.jpg`, and point the home page at them in `deploy/.env` (or `frontend/.env.local` for local development):

```
VITE_HERO_IMAGE_URL=/custom/hero.jpg
VITE_BANNER_IMAGE_URL=/custom/banner.jpg
# Optional: the browser-tab icon, and the image for link previews (default: the hero)
VITE_FAVICON_URL=/custom/favicon.png
VITE_SHARE_IMAGE_URL=/custom/share.jpg
```

Then rebuild the storefront (`docker compose -f deploy/docker-compose.yml up -d --build`).

Everything in this folder except this file is ignored by git, so each store keeps its own photos. Back them up yourself. Keep them reasonably small (around 1920 pixels wide and under 1 MB is plenty for the home page). A link-preview image works best at 1200x630, and an icon as an SVG or a square PNG of at least 64x64.
