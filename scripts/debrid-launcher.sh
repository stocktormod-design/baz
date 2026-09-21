#!/usr/bin/env bash
# debrid-launcher.sh
#
# Laster ned et spill fra Real-Debrid-mounten (rclone) til lokal NVMe-SSD
# ved behov, og starter det deretter via Proton.
#
# Brukes som "launch options" i Steam, f.eks.:
#   /home/deck/Scripts/debrid-launcher.sh "Half-Life 2" "/home/deck/Games/DebridCloud/Half-Life 2/hl2.exe" %command%
#
# Argumenter:
#   $1 = GAME_NAME  (mappenavn/visningsnavn, brukes til lokal undermappe)
#   $2 = EXE_PATH   (full sti til .exe INNE i DebridCloud-mounten)
#   $3.. = resten av Steams %command% (Proton-kommandoen som skal kjøre EXE-en)

set -euo pipefail

GAME_NAME="${1:?Mangler GAME_NAME som argument 1}"
EXE_PATH="${2:?Mangler EXE_PATH som argument 2}"
shift 2
PROTON_CMD=("$@")

DEBRID_CLOUD_ROOT="/home/deck/Games/DebridCloud"
LOCAL_INSTALL_ROOT="/home/deck/Games/LocalInstall"

LOCAL_GAME_DIR="${LOCAL_INSTALL_ROOT}/${GAME_NAME}"
LOG_FILE="/home/deck/Games/debrid-launcher.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Regn ut hvor EXE-en havner lokalt etter kopiering, ved å bytte ut
# DebridCloud-roten med LocalInstall-roten i stien.
if [[ "$EXE_PATH" != "$DEBRID_CLOUD_ROOT"* ]]; then
    log "FEIL: EXE_PATH ($EXE_PATH) ligger ikke under $DEBRID_CLOUD_ROOT"
    exit 1
fi

RELATIVE_EXE_PATH="${EXE_PATH#"$DEBRID_CLOUD_ROOT"/}"
LOCAL_EXE_PATH="${LOCAL_INSTALL_ROOT}/${RELATIVE_EXE_PATH}"

mkdir -p "$LOCAL_INSTALL_ROOT"

if [ -f "$LOCAL_EXE_PATH" ]; then
    log "Spillet '$GAME_NAME' finnes allerede lokalt: $LOCAL_EXE_PATH"
else
    SOURCE_DIR="${DEBRID_CLOUD_ROOT}/${GAME_NAME}"

    if [ ! -d "$SOURCE_DIR" ]; then
        log "FEIL: Fant ikke spillmappen i Debrid-skyen: $SOURCE_DIR"
        exit 1
    fi

    log "Spillet '$GAME_NAME' finnes ikke lokalt. Starter nedlasting fra Real-Debrid..."
    mkdir -p "$LOCAL_GAME_DIR"

    # Høy ytelse: mange parallelle overføringer/sjekkere, siden dette er en
    # lokal NVMe-SSD som mål og en rask nettverksmount som kilde.
    rclone copy "$SOURCE_DIR" "$LOCAL_GAME_DIR" \
        --transfers 8 \
        --checkers 16 \
        --progress \
        --stats 5s \
        --stats-one-line \
        2>&1 | tee -a "$LOG_FILE"

    if [ ! -f "$LOCAL_EXE_PATH" ]; then
        log "FEIL: Nedlasting fullført, men fant ikke $LOCAL_EXE_PATH etterpå."
        exit 1
    fi

    log "Nedlasting av '$GAME_NAME' fullført: $LOCAL_EXE_PATH"
fi

log "Starter '$GAME_NAME' lokalt via Proton: ${PROTON_CMD[*]:-} $LOCAL_EXE_PATH"

# Kjør resten av Steams %command%-kjede, men pek den mot den LOKALE exe-filen
# i stedet for originalstien i DebridCloud-mounten.
exec "${PROTON_CMD[@]}" "$LOCAL_EXE_PATH"
