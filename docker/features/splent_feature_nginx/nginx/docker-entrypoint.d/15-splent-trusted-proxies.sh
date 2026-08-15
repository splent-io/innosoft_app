#!/bin/sh
# Build the geo entries that decide which peers may assert X-Forwarded-*
# headers. NGINX_TRUSTED_PROXY_CIDRS holds a comma or space separated list
# of CIDRs, for example "172.16.0.0/12, 127.0.0.1/32", and is empty by
# default. Empty means the file below stays empty, no peer is trusted and
# the server templates rewrite the forwarded headers from $scheme and
# $host. Only a host-level TLS terminator in front of this container
# justifies filling it in.
set -e

out_dir=/etc/nginx/trusted_proxies
out_file="$out_dir/trusted.conf"

mkdir -p "$out_dir"
: > "$out_file"

for cidr in $(printf '%s' "${NGINX_TRUSTED_PROXY_CIDRS:-}" | tr ',;' '  '); do
    printf '%s 1;\n' "$cidr" >> "$out_file"
    echo "15-splent-trusted-proxies.sh: trusting forwarded headers from $cidr"
done
