FROM nginx:stable-alpine

# DOMAIN and DOMAIN_ALIASES come from the environment at start; the filter
# keeps nginx variables like $host out of envsubst.
ENV NGINX_ENVSUBST_FILTER=^DOMAIN

COPY default.conf.template tls.inc.template /etc/nginx/templates/
COPY --chmod=755 25-timegrip-ssl.sh /docker-entrypoint.d/

# Set once nginx has bound its ports, so certbot can pass the HTTP challenge.
HEALTHCHECK --interval=5s --timeout=3s --retries=12 CMD test -s /run/nginx.pid
