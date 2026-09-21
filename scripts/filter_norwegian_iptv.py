#!/usr/bin/env python3
"""
filter_norwegian_iptv.py

Leser en global IPTV .m3u/.m3u8-spilleliste og filtrerer ut KUN norske kanaler,
basert på #EXTINF-attributtene tvg-country og group-title, samt norske
stedsnavn/nøkkelord i selve kanalnavnet.

Resultatet lagres som en ren M3U-fil: /home/deck/IPTV/norway_channels.m3u

Bruk:
    python3 filter_norwegian_iptv.py <sti-eller-url-til-global-spilleliste.m3u>
"""

from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

OUTPUT_PATH = Path("/home/deck/IPTV/norway_channels.m3u")

# Nøkkelord som identifiserer norske kanaler i group-title / tvg-name / kanalnavn
NORWAY_KEYWORDS = [
    "norway",
    "norge",
    "norwegian",
    "no |",
    "| no",
    "(no)",
]

EXTINF_ATTR_RE = re.compile(r'([a-zA-Z0-9_-]+)="([^"]*)"')


def load_playlist(source: str) -> list[str]:
    """Leser spillelisten enten fra en lokal fil eller en URL."""
    if source.startswith("http://") or source.startswith("https://"):
        with urllib.request.urlopen(source) as response:  # noqa: S310 - kilde er brukerstyrt
            raw = response.read()
    else:
        raw = Path(source).read_bytes()

    text = raw.decode("utf-8", errors="replace")
    return text.splitlines()


def parse_extinf_attrs(extinf_line: str) -> dict[str, str]:
    """Trekker ut attributter som tvg-country="NO" fra en #EXTINF-linje."""
    return {key.lower(): value for key, value in EXTINF_ATTR_RE.findall(extinf_line)}


def get_display_name(extinf_line: str) -> str:
    """Henter visningsnavnet etter det siste kommaet på #EXTINF-linjen."""
    return extinf_line.rsplit(",", 1)[-1].strip()


def is_norwegian_channel(extinf_line: str) -> bool:
    attrs = parse_extinf_attrs(extinf_line)
    display_name = get_display_name(extinf_line)

    tvg_country = attrs.get("tvg-country", "").strip().upper()
    if tvg_country == "NO":
        return True

    group_title = attrs.get("group-title", "").lower()
    tvg_name = attrs.get("tvg-name", "").lower()
    haystack = " ".join([group_title, tvg_name, display_name.lower()])

    return any(keyword in haystack for keyword in NORWAY_KEYWORDS)


def filter_norwegian_channels(lines: list[str]) -> list[str]:
    """
    Går gjennom M3U-linjene parvis: en #EXTINF-linje etterfulgt av én eller
    flere metadata-/URL-linjer, fram til neste #EXTINF eller filslutt.
    """
    output: list[str] = ["#EXTM3U"]

    i = 0
    n = len(lines)

    # Hopp over en eventuell #EXTM3U-header i kildefilen
    if n > 0 and lines[0].strip().startswith("#EXTM3U"):
        i = 1

    while i < n:
        line = lines[i].strip()

        if line.startswith("#EXTINF"):
            block = [line]
            i += 1

            # Ta med alle påfølgende linjer (f.eks. #EXTVLCOPT, #EXTGRP, selve URL-en)
            # fram til neste #EXTINF eller slutten av filen.
            while i < n and not lines[i].strip().startswith("#EXTINF"):
                if lines[i].strip():
                    block.append(lines[i].strip())
                i += 1

            if is_norwegian_channel(block[0]):
                output.extend(block)
        else:
            i += 1

    return output


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Bruk: {sys.argv[0]} <sti-eller-url-til-global-spilleliste.m3u>")
        sys.exit(1)

    source = sys.argv[1]

    print(f"Leser spilleliste fra: {source}")
    lines = load_playlist(source)

    print("Filtrerer ut norske kanaler...")
    norwegian_lines = filter_norwegian_channels(lines)

    channel_count = sum(1 for line in norwegian_lines if line.startswith("#EXTINF"))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(norwegian_lines) + "\n", encoding="utf-8")

    print(f"Ferdig! Fant {channel_count} norske kanaler.")
    print(f"Lagret til: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
