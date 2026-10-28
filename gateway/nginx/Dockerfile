FROM nginxinc/nginx-unprivileged:stable-alpine AS runtime

USER root
RUN apk upgrade --no-cache
USER 101

ENV NGINX_ENVSUBST_FILTER=^DOMAIN

COPY default.conf.template tls.inc.template /etc/nginx/templates/
COPY --chmod=755 25-timegrip-ssl.sh /docker-entrypoint.d/

HEALTHCHECK --interval=5s --timeout=3s --retries=12 CMD test -s /tmp/nginx.pid
