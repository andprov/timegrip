FROM nginx:stable-alpine AS runtime

RUN apk upgrade --no-cache

ENV NGINX_ENVSUBST_FILTER=^DOMAIN

COPY default.conf.template tls.inc.template /etc/nginx/templates/
COPY --chmod=755 25-timegrip-ssl.sh /docker-entrypoint.d/

HEALTHCHECK --interval=5s --timeout=3s --retries=12 CMD test -s /run/nginx.pid
