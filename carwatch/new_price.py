"""Odczyt ceny bazowej nowego RAV4 z toyota.pl."""

import re

import requests

from carwatch import config

_NUM = r"(\d{1,3}(?:[\s ]|&nbsp;)\d{3})"

# Kolejność: od najbardziej konkretnego źródła.
_PATTERNS = [
    # dane karty modelu w JSON-ie strony: "promoCardDetails":"Od <strong>181 600 zł..."
    r'"productModelPage":"[^"]*/rav4"[^{}]*?"promoCardDetails":"Od \\u003cstrong\\u003e' + _NUM,
    r'"title":"Nowy RAV4","description":"Od \\u003cstrong\\u003e' + _NUM,
    # tekst nagłówka strony: "Specjalna cena od 181 600 zł" / "Cena od ..."
    r"(?i)cena\s+od\s*(?:<[^>]+>\s*)*" + _NUM + r"\s*(?:&nbsp;)?\s*zł",
]


def parse_base_price(html: str) -> int | None:
    for pat in _PATTERNS:
        m = re.search(pat, html)
        if m:
            return int(re.sub(r"\D", "", m.group(1)))
    return None


def fetch_base_price(session: requests.Session) -> int | None:
    resp = session.get(config.NEW_RAV4_URL, headers=config.HEADERS, timeout=30)
    resp.raise_for_status()
    return parse_base_price(resp.text)
