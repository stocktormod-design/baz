#!/usr/bin/env bash
# debrid-first-boot-dirs.sh
#
# Kjører én gang som root ved første oppstart (via debrid-first-boot-dirs.service)
# og oppretter mappestrukturen "deck"-brukeren og skriptene våre forventer,
# siden /home/deck ikke finnes ennå når selve OS-imaget bygges.
set -euo pipefail

MARKER="/var/lib/debrid-first-boot-dirs.done"
TARGET_USER="deck"

if [ -f "$MARKER" ]; then
    exit 0
fi

USER_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6 || true)"

if [ -z "${USER_HOME:-}" ] || [ ! -d "$USER_HOME" ]; then
    echo "Bruker $TARGET_USER er ikke klar ennå, prøver igjen ved neste oppstart."
    exit 0
fi

mkdir -p \
    "$USER_HOME/Games/DebridCloud" \
    "$USER_HOME/Games/LocalInstall" \
    "$USER_HOME/Emulation/roms/wiiu" \
    "$USER_HOME/Emulation/roms/switch" \
    "$USER_HOME/IPTV"

chown -R "$TARGET_USER:$TARGET_USER" \
    "$USER_HOME/Games" \
    "$USER_HOME/Emulation" \
    "$USER_HOME/IPTV"

mkdir -p "$(dirname "$MARKER")"
touch "$MARKER"
