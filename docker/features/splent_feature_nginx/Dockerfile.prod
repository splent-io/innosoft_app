FROM nginx:1.27
COPY nginx/templates/default.prod.conf.template /etc/nginx/templates/default.conf.template

# Location snippets shipped with the deployment. The compose file also bind
# mounts this directory, so snippets added after the build are picked up on
# a restart without rebuilding the image.
COPY nginx/locations/ /etc/nginx/conf.d/locations/

# Renders NGINX_TRUSTED_PROXY_CIDRS into the geo entries the server
# template includes. The empty file baked here keeps the config valid, and
# trusts no peer, even if the entrypoint scripts are ever skipped.
COPY nginx/docker-entrypoint.d/15-splent-trusted-proxies.sh /docker-entrypoint.d/15-splent-trusted-proxies.sh
RUN chmod +x /docker-entrypoint.d/15-splent-trusted-proxies.sh \
    && mkdir -p /etc/nginx/trusted_proxies \
    && touch /etc/nginx/trusted_proxies/trusted.conf
