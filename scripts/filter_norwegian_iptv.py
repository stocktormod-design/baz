#!/usr/bin/env python3
"""
filter_norwegian_iptv.py

Leser en global IPTV .m3u/.m3u8-spilleliste og filtrerer ut KUN norske kanaler.

Forskjellige IPTV-lister navngir norske kanaler helt ulikt, så dette skriptet
kombinerer flere uavhengige signaler i stedet for å stole på ett enkelt felt:

  1. tvg-country="NO" / "NOR" / "Norway" (eksakt match, ikke substreng)
  2. tvg-id som slutter på ".no" (vanlig konvensjon, f.eks. "NRK1.no")
  3. tvg-language="Norwegian" / "Norsk"
  4. group-title / tvg-name / kanalnavn som inneholder "norway", "norge",
     "norwegian", "norsk" eller det norske flagg-emojiet 🇳🇴
  5. #EXTGRP:-linjer (gruppe satt på egen linje i stedet for som attributt)
  6. Kjente, entydig norske kringkastere i selve kanalnavnet (NRK, TVNorge,
     TV 2 Norge, osv.) - brukt som sikkerhetsnett for lister uten
     land/språk-metadata i det hele tatt.

Resultatet lagres som en ren M3U-fil: /home/deck/IPTV/norway_channels.m3u

Bruk:
    python3 filter_norwegian_iptv.py <sti-eller-url-til-global-spilleliste.m3u>
"""

from __future__ import annotations

import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

OUTPUT_PATH = Path("/home/deck/IPTV/norway_channels.m3u")

# Attributter på formen key="value" ELLER key='value' (begge forekommer i praksis)
EXTINF_ATTR_RE = re.compile(r"""([a-zA-Z0-9_-]+)=(["'])(.*?)\2""")

# --- Signal 1: eksakte landkode-/navneverdier for tvg-country ------------------
NORWAY_COUNTRY_VALUES = {"no", "nor", "norway", "norge"}

# --- Signal 3: eksakte/substreng-verdier for tvg-language ---------------------
NORWAY_LANGUAGE_VALUES = {"norwegian", "norsk", "no", "nor"}

# --- Signal 4: nøkkelord som kan forekomme hvor som helst i tekstfelt ----------
NORWAY_TEXT_KEYWORDS = [
    "norway",
    "norge",
    "norwegian",
    "norsk",
    "🇳🇴",
]

# Varianter av "NO" omkranset av vanlige skilletegn i navn/grupper, f.eks.
# "NO | NRK1", "NRK1 (NO)", "NO- TV2", "[NO] TV2". Bruker ordgrense slik at vi
# ikke matcher "no" midt i et annet ord (f.eks. "Norton", "Anonymous").
NORWAY_CODE_PATTERN = re.compile(r"(?<![a-z0-9])no(?![a-z0-9])", re.IGNORECASE)

# --- Signal 6: entydig norske kringkastere/kanaler (sikkerhetsnett) ------------
# Kun navn som ikke er tvetydige med andre lands kanaler (f.eks. IKKE "TV2"
# eller "MAX" alene, siden de også finnes i Danmark/Sverige/andre land).
KNOWN_NORWEGIAN_CHANNELS = [
    r"\bnrk\s?1\b",
    r"\bnrk\s?2\b",
    r"\bnrk\s?3\b",
    r"\bnrk\s?super\b",
    r"\bnrk\s?sport\b",
    r"\bnrk\b",
    r"\btv\s?2\s?norge\b",
    r"\btv\s?2\s?direkte\b",
    r"\btvnorge\b",
    r"\btv\s?3\s?norge\b",
    r"\btv\s?6\s?norge\b",
    r"\bmax\s?norge\b",
    r"\bvox\s?norge\b",
    r"\bfem\s?norge\b",
    r"\bdplay\s?norge\b",
    r"\bviaplay\s?norge\b",
    r"\bnickelodeon\s?norge\b",
    r"\bdisney\s?channel\s?norge\b",
    r"\brikstoto\b",
    # Sportskanaler som har norske rettigheter til Premier League/La Liga/
    # Champions League m.m., selv om enkelte lister ikke merker dem med et
    # eget Norge/Norway-tagg (de er ofte delt nordisk). Inkludert eksplisitt
    # på brukerens ønske, siden risikoen for å miste disse er verre enn
    # risikoen for en sjelden falsk positiv fra et annet nordisk land.
    r"\btv\s?2\s?sport\b",
    r"\bviaplay\s?sport\b",
    r"\bviasat\s?sport\b",
    r"\bnent\s?sport\b",
]
KNOWN_NORWEGIAN_CHANNELS_RE = re.compile("|".join(KNOWN_NORWEGIAN_CHANNELS), re.IGNORECASE)


def normalize(text: str) -> str:
    """Lowercase og fjern diakritiske tegn/emoji-variasjonsselektorer for mer robust matching."""
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    return text


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
    return {key.lower(): value for key, _quote, value in EXTINF_ATTR_RE.findall(extinf_line)}


def get_display_name(extinf_line: str) -> str:
    """Henter visningsnavnet etter det siste kommaet på #EXTINF-linjen."""
    return extinf_line.rsplit(",", 1)[-1].strip()


def is_norwegian_channel(block: list[str]) -> bool:
    extinf_line = block[0]
    attrs = parse_extinf_attrs(extinf_line)
    display_name = get_display_name(extinf_line)

    # #EXTGRP:-linjer brukes av enkelte lister i stedet for group-title-attributtet
    extgrp = ""
    for line in block[1:]:
        if line.upper().startswith("#EXTGRP:"):
            extgrp = line.split(":", 1)[1]
            break

    tvg_country = normalize(attrs.get("tvg-country", ""))
    if tvg_country in NORWAY_COUNTRY_VALUES:
        return True

    tvg_id = normalize(attrs.get("tvg-id", ""))
    if tvg_id.endswith(".no"):
        return True

    tvg_language = normalize(attrs.get("tvg-language", ""))
    if tvg_language in NORWAY_LANGUAGE_VALUES:
        return True

    group_title = normalize(attrs.get("group-title", ""))
    tvg_name = normalize(attrs.get("tvg-name", ""))
    name = normalize(display_name)
    extgrp_norm = normalize(extgrp)

    haystack = " ".join([group_title, tvg_name, name, extgrp_norm])

    if any(keyword in haystack for keyword in NORWAY_TEXT_KEYWORDS):
        return True

    # Sjekk "NO" som egen landkode-token i gruppe-/tvg-id-felt (ikke i det frie
    # kanalnavnet, siden "no" som fritt ord der gir for mange falske treff).
    for field in (group_title, tvg_id, extgrp_norm):
        if field and NORWAY_CODE_PATTERN.search(field):
            return True

    # Sikkerhetsnett: entydig norsk kringkaster nevnt i navnet, selv uten
    # noen land-/språk-metadata i det hele tatt.
    if KNOWN_NORWEGIAN_CHANNELS_RE.search(haystack):
        return True

    return False


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

            # Ta med alle påfølgende linjer (f.eks. #EXTGRP, #EXTVLCOPT, selve URL-en)
            # fram til neste #EXTINF eller slutten av filen.
            while i < n and not lines[i].strip().startswith("#EXTINF"):
                if lines[i].strip():
                    block.append(lines[i].strip())
                i += 1

            if is_norwegian_channel(block):
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
