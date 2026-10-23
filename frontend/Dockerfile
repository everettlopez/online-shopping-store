# Storefront image. Build from frontend/:
#   docker build --build-arg VITE_API_URL=https://api.example.com/api -t shop-web .
FROM node:24-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# Vite bakes the API address into the bundle, so it's a build argument, not a runtime setting
ARG VITE_API_URL
# The store's identity (all optional; see .env.example)
ARG VITE_STORE_NAME
ARG VITE_STORE_LOGO_TEXT
ARG VITE_STORE_DESCRIPTION
ARG VITE_SUPPORT_EMAIL
ARG VITE_BUSINESS_NAME
ARG VITE_BUSINESS_ADDRESS
ARG VITE_BUSINESS_STATE
ARG VITE_RETURN_DAYS
ARG VITE_PRIVACY_POLICY_URL
ARG VITE_TERMS_URL
ARG VITE_SHIPPING_POLICY_URL
ARG VITE_HERO_HEADLINE
ARG VITE_HERO_IMAGE_URL
ARG VITE_BANNER_IMAGE_URL
ARG VITE_EVENTS_URL
# The icon and link previews; VITE_SITE_URL makes the preview image's address absolute
ARG VITE_FAVICON_URL
ARG VITE_SHARE_IMAGE_URL
ARG VITE_SITE_URL
RUN test -n "$VITE_API_URL" || (echo "Pass --build-arg VITE_API_URL=https://<api host>/api" && exit 1)
RUN npm run build

FROM nginx:1.29-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
