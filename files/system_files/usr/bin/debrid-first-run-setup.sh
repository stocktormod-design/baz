#!/usr/bin/env bash
# debrid-first-run-setup.sh
#
# Grafisk (terminal-fri) førstegangs-veiviser for å koble Real-Debrid til
# systemet. Startes automatisk ved innlogging på skrivebordet via
# /etc/xdg/autostart/debrid-first-run-setup.desktop. Gjør ingenting etter
# at oppsettet er fullført én gang (styrt av markørfilen under).
set -euo pipefail

MARKER="$HOME/.config/debrid-onboarding-done"
RCLONE_CONF_DIR="$HOME/.config/rclone"
RCLONE_CONF="$RCLONE_CONF_DIR/rclone.conf"
DEBRID_MOUNT_DIR="$HOME/Games/DebridCloud"
BOOKMARKS_DIR="$HOME/.config/gtk-3.0"
BOOKMARKS_FILE="$BOOKMARKS_DIR/bookmarks"

if [ -f "$MARKER" ]; then
    exit 0
fi

if ! command -v zenity >/dev/null 2>&1; then
    # Ingen GUI-verktøy tilgjengelig - ikke stopp innloggingen, bare avslutt stille.
    exit 0
fi

zenity --info \
    --title="Velkommen til Debrid Livingroom OS" \
    --text="La oss koble til Real-Debrid.\n\nDu trenger brukernavnet og WebDAV-passordet ditt fra real-debrid.com (Konto-innstillinger -> WebDAV)." \
    --width=400 || exit 0

CREDS=$(zenity --forms \
    --title="Logg inn på Real-Debrid" \
    --text="Skriv inn WebDAV-påloggingen din:" \
    --add-entry="Brukernavn" \
    --add-password="Passord" \
    --separator="|") || {
        zenity --warning --text="Hoppet over Real-Debrid-oppsett. Du kan starte veiviseren på nytt fra Programmer-menyen senere." --width=350
        exit 0
    }

RD_USER="$(echo "$CREDS" | cut -d'|' -f1)"
RD_PASS="$(echo "$CREDS" | cut -d'|' -f2)"

if [ -z "$RD_USER" ] || [ -z "$RD_PASS" ]; then
    zenity --warning --text="Brukernavn eller passord var tomt. Prøver på nytt neste gang du logger inn." --width=350
    exit 0
fi

mkdir -p "$RCLONE_CONF_DIR"
OBSCURED_PASS="$(rclone obscure "$RD_PASS")"

cat >> "$RCLONE_CONF" <<EOF
[realdebrid]
type = webdav
url = https://dav.real-debrid.com
vendor = other
user = ${RD_USER}
pass = ${OBSCURED_PASS}
EOF

mkdir -p "$DEBRID_MOUNT_DIR"

systemctl --user daemon-reload
systemctl --user enable --now rclone-mount-debrid.service

# Legg til snarvei i Filer-sidepanelet til den nå faktisk monterte mappen.
mkdir -p "$BOOKMARKS_DIR"
touch "$BOOKMARKS_FILE"
if ! grep -qF "$DEBRID_MOUNT_DIR" "$BOOKMARKS_FILE" 2>/dev/null; then
    echo "file://${DEBRID_MOUNT_DIR} Real-Debrid Cloud" >> "$BOOKMARKS_FILE"
fi

mkdir -p "$(dirname "$MARKER")"
touch "$MARKER"

zenity --info \
    --title="Ferdig!" \
    --text="Real-Debrid er nå koblet til. Debrid-skyen din dukker opp som 'Real-Debrid Cloud' i sidepanelet i Filer om et par sekunder." \
    --width=400 || true
