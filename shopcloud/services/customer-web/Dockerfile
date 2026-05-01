# Multi-stage Dockerfile for the React/Vite customer-web SPA.
# Build stage outputs static files; runtime stage serves them with nginx.
#
# Build (context must be this directory, not the repo root):
#   docker build -t <tag> --build-arg VITE_BACKEND_URL=https://your-site -f services/customer-web/Dockerfile services/customer-web

FROM node:20-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

# Empty = same-origin `/api` (production). Override for local API only.
ARG VITE_BACKEND_URL=
ENV VITE_BACKEND_URL=${VITE_BACKEND_URL}

COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS runtime

# SPA fallback so every route serves index.html.
RUN printf 'server {\n  listen 80;\n  root /usr/share/nginx/html;\n  index index.html;\n  location / { try_files $uri $uri/ /index.html; }\n}\n' \
  > /etc/nginx/conf.d/default.conf

COPY --from=build /app/dist /usr/share/nginx/html

USER nginx
EXPOSE 80
