#!/usr/bin/env bash
set -euo pipefail

# terra-mesa er aktivert (enabled=1) som standard i Bazzite, og gir ferske
# Mesa-GPU-drivere. Den bruker "gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-...",
# og bootc-image-builder klarer ikke å oversette denne file://-stien til
# kildeavtrykkets rotmappe under depsolve når vi bygger ISO - dette er en kjent,
# uløst bug i selve verktøyet (osbuild/bootc-image-builder#1188), ikke noe galt
# med selve repo-konfigurasjonen. Deaktiverer repoet for å unngå at ISO-bygget
# feiler. Fedora/Bazzite sine egne Mesa-pakker oppdateres fortsatt jevnlig.
sed -i 's/^enabled=1/enabled=0/' /etc/yum.repos.d/terra-mesa.repo
