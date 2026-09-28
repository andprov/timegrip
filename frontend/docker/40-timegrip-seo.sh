#!/bin/sh
# Applies the instance SEO config on every start, so one image serves any
# deployment: index.html is rebuilt from the copy shipped in the image,
# robots.txt and sitemap.xml are regenerated. Without a config (not mounted,
# or mounted from /dev/null) the page is served without SEO tags.
set -eu

ME=$(basename "$0")
CONFIG=/etc/timegrip/seo.config.json
SRC=/opt/timegrip
ROOT=/usr/share/nginx/html

render() {
    jq -j --arg mode "$1" --rawfile template "$SRC/index.html" \
        -f "$SRC/seo.jq" "$CONFIG"
}

rm -f "$ROOT/robots.txt" "$ROOT/sitemap.xml"

if [ ! -f "$CONFIG" ] || [ ! -s "$CONFIG" ]; then
    cp "$SRC/index.html" "$ROOT/index.html"
    echo "$ME: no $CONFIG, SEO tags are skipped"
    exit 0
fi

render html > "$ROOT/index.html.tmp"
mv "$ROOT/index.html.tmp" "$ROOT/index.html"
render robots > "$ROOT/robots.txt"
if jq -e '.indexing == true' "$CONFIG" > /dev/null; then
    render sitemap > "$ROOT/sitemap.xml"
fi
echo "$ME: SEO applied from $CONFIG"
