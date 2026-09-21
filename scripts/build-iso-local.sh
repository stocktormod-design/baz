#!/usr/bin/env bash
# Bygger en bootbar Anaconda-ISO av Debrid Livingroom OS LOKALT, for flashing
# til egen USB. Kjøres i en ekte Linux-container/-VM (f.eks. WSL2 Ubuntu på
# Windows) siden bootc-image-builder krever podman + /var/lib/containers/storage,
# som ikke finnes direkte på Windows.
#
# Bruk (fra WSL/Linux, med podman installert):
#   sudo bash scripts/build-iso-local.sh
#
# Resultat: output/bootiso/install.iso
set -euo pipefail

IMAGE="ghcr.io/stocktormod-design/debrid-livingroom-os:latest"
OUTPUT_DIR="$(pwd)/output"

mkdir -p "$OUTPUT_DIR"

cat > /tmp/bib-config.toml <<'EOF'
[[customizations.user]]
name = "deck"
groups = ["wheel"]
EOF

echo "==> Henter siste image fra ghcr.io ($IMAGE)..."
podman pull "$IMAGE"

echo "==> Bygger ISO med bootc-image-builder (--type iso --rootfs btrfs)..."
podman run \
  --rm \
  --privileged \
  --pull=always \
  --security-opt label=type:unconfined_t \
  -v /tmp/bib-config.toml:/config.toml:ro \
  -v "$OUTPUT_DIR":/output \
  -v /var/lib/containers/storage:/var/lib/containers/storage \
  quay.io/centos-bootc/bootc-image-builder:latest \
  --type iso \
  --rootfs btrfs \
  --config /config.toml \
  "$IMAGE"

echo "==> Ferdig! ISO ligger her:"
find "$OUTPUT_DIR" -name '*.iso'
