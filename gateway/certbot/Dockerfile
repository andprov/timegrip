FROM certbot/certbot:v5.8.0 AS runtime

RUN apk upgrade --no-cache

COPY cli.ini /etc/certbot/cli.ini
COPY --chmod=755 entrypoint.sh /opt/certbot/entrypoint.sh

ENTRYPOINT ["/opt/certbot/entrypoint.sh"]
CMD ["run"]
