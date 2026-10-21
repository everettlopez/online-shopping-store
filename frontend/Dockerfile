# Storefront image. Build from frontend/:
#   docker build --build-arg VITE_API_URL=https://api.example.com/api -t shop-web .
FROM node:24-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# Vite bakes the API address into the bundle, so it's a build argument, not a runtime setting
ARG VITE_API_URL
RUN test -n "$VITE_API_URL" || (echo "Pass --build-arg VITE_API_URL=https://<api host>/api" && exit 1)
RUN npm run build

FROM nginx:1.29-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
