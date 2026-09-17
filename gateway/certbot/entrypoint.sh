set -eu

CONFIG=/etc/certbot/cli.ini

is_true() {
    case "$1" in
        [Tt]rue | 1) return 0 ;;
        *) return 1 ;;
    esac
}

obtain() {
    args="--cert-name $DOMAIN -d $DOMAIN"
    for alias in ${DOMAIN_ALIASES:-}; do
        args="$args -d $alias"
    done

    if [ -n "${CERTBOT_EMAIL:-}" ]; then
        args="$args --email $CERTBOT_EMAIL"
    else
        args="$args --register-unsafely-without-email"
    fi

    renewal_conf="/etc/letsencrypt/renewal/$DOMAIN.conf"
    if is_true "${CERTBOT_STAGING:-False}"; then
        args="$args --staging"
    elif [ -f "$renewal_conf" ] && grep -q "acme-staging" "$renewal_conf"; then
        args="$args --force-renewal"
    fi

    if [ "${1:-}" = "--force" ]; then
        args="$args --force-renewal"
    fi

    exec certbot certonly --config "$CONFIG" $args
}

renew() {
    trap exit TERM
    while :; do
        certbot renew --config "$CONFIG" || true
        sleep 12h &
        wait $!
    done
}

case "${1:-renew}" in
    renew)
        renew
        ;;
    obtain)
        shift
        obtain "$@"
        ;;
    *)
        exec certbot "$@"
        ;;
esac
