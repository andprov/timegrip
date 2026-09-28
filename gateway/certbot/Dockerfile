FROM certbot/certbot:latest

COPY cli.ini /etc/certbot/cli.ini
COPY --chmod=755 entrypoint.sh /opt/certbot/entrypoint.sh

ENTRYPOINT ["/opt/certbot/entrypoint.sh"]
CMD ["run"]
