#!/usr/bin/env bash
# Legger til en GVfs/Nautilus-snarvei ("bokmerke") til Real-Debrid sin WebDAV-tjeneste
# i sidepanelet til filbehandleren, slik at brukeren kan bla i Debrid-skyen uten terminal.
# Kjøres én gang ved første oppstart via debrid-webdav-bookmark.service.
set -euo pipefail

MARKER="/var/lib/debrid-webdav-bookmark.done"
TARGET_USER="deck"

# ENDRE DENNE om Real-Debrid sin WebDAV-adresse er annerledes i din konto
# (sjekk under "Innstillinger -> WebDAV" på real-debrid.com).
WEBDAV_URI="dav://${TARGET_USER}@dav.real-debrid.com/ Real-Debrid Cloud"

if [ -f "$MARKER" ]; then
    exit 0
fi

USER_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6 || true)"

if [ -z "${USER_HOME:-}" ] || [ ! -d "$USER_HOME" ]; then
    # Brukeren finnes ikke ennå (f.eks. helt første boot før home-mappen er opprettet).
    # Ikke skriv markørfilen, slik at tjenesten prøver på nytt ved neste oppstart.
    echo "Bruker $TARGET_USER er ikke klar ennå, prøver igjen ved neste oppstart."
    exit 0
fi

BOOKMARKS_DIR="$USER_HOME/.config/gtk-3.0"
BOOKMARKS_FILE="$BOOKMARKS_DIR/bookmarks"

mkdir -p "$BOOKMARKS_DIR"
touch "$BOOKMARKS_FILE"

if ! grep -qF "dav.real-debrid.com" "$BOOKMARKS_FILE" 2>/dev/null; then
    echo "$WEBDAV_URI" >> "$BOOKMARKS_FILE"
fi

chown -R "$TARGET_USER:$TARGET_USER" "$BOOKMARKS_DIR"

mkdir -p "$(dirname "$MARKER")"
touch "$MARKER"
