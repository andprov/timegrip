FROM --platform=$BUILDPLATFORM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:stable-alpine AS runtime

RUN apk upgrade --no-cache && apk add --no-cache jq

COPY --from=builder /app/dist /usr/share/nginx/html
COPY --from=builder /app/dist/index.html /opt/timegrip/index.html
COPY docker/seo.jq /opt/timegrip/seo.jq
COPY --chmod=755 docker/40-timegrip-seo.sh /docker-entrypoint.d/
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
