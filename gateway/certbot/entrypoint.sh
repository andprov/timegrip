#!/bin/sh
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

    certbot certonly --config "$CONFIG" $args
}

# Default command. certonly issues the certificate on the first start, renews
# it close to expiry, reissues it after DOMAIN_ALIASES change or staging is
# turned off, and does nothing otherwise; nginx picks up the new files itself.
run() {
    trap exit TERM
    while :; do
        if obtain; then
            delay=12h
        else
            # Let's Encrypt allows 5 failed validations per hostname an hour
            echo "certbot: no certificate for $DOMAIN, retrying in 15 minutes"
            delay=15m
        fi
        sleep "$delay" &
        wait $!
    done
}

case "${1:-run}" in
    run)
        run
        ;;
    obtain)
        shift
        obtain "$@"
        ;;
    *)
        exec certbot "$@"
        ;;
esac
