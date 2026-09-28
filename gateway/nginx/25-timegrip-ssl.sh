#!/bin/sh
# Serves HTTP only until a certificate for DOMAIN exists, then switches to
# HTTPS without a restart: a background loop watches the certificate and
# reloads nginx when certbot issues or renews it.
set -eu

ME=$(basename "$0")
CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"
TLS=/etc/nginx/conf.d/tls.inc
# Outside conf.d, so default.conf does not include it
TLS_OFF=/etc/nginx/tls.inc.off

has_cert() {
    [ -f "$CERT_DIR/fullchain.pem" ] && [ -f "$CERT_DIR/privkey.pem" ]
}

# live/ holds symlinks that certbot repoints to new files on every issue
cert_stamp() {
    stat -L -c %Y "$CERT_DIR/fullchain.pem" "$CERT_DIR/privkey.pem" \
        2>/dev/null || echo none
}

if has_cert; then
    echo "$ME: certificate for ${DOMAIN} found, HTTPS enabled"
else
    mv "$TLS" "$TLS_OFF"
    echo "$ME: no certificate for ${DOMAIN} yet, serving HTTP only"
fi

(
    stamp=$(cert_stamp)
    while :; do
        sleep 60
        has_cert || continue
        current=$(cert_stamp)
        [ "$current" != "$stamp" ] || continue
        stamp=$current
        if [ -f "$TLS_OFF" ]; then
            mv "$TLS_OFF" "$TLS"
            echo "$ME: certificate for ${DOMAIN} found, HTTPS enabled"
        fi
        nginx -s reload || true
    done
) &
