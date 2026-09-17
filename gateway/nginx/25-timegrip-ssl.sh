set -eu

ME=$(basename "$0")
CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"

if [ -f "$CERT_DIR/fullchain.pem" ] && [ -f "$CERT_DIR/privkey.pem" ]; then
    echo "$ME: certificate for ${DOMAIN} found, HTTPS enabled"
else
    rm -f /etc/nginx/conf.d/tls.inc
    echo "$ME: no certificate for ${DOMAIN}, serving HTTP only"
fi

(
    while :; do
        sleep 6h
        nginx -s reload || true
    done
) &
