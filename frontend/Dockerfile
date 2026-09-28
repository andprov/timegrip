# The build output is plain static files, so it is built once on the native
# platform of the builder, not under emulation for every target platform.
FROM --platform=$BUILDPLATFORM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build


FROM nginx:stable-alpine AS runtime

# SEO is instance-specific, so it is rendered at start, not baked in here
# (docker/40-timegrip-seo.sh).
RUN apk add --no-cache jq

COPY --from=builder /app/dist /usr/share/nginx/html
COPY --from=builder /app/dist/index.html /opt/timegrip/index.html
COPY docker/seo.jq /opt/timegrip/seo.jq
COPY --chmod=755 docker/40-timegrip-seo.sh /docker-entrypoint.d/
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
