"""Szczegóły pojedynczej oferty (strona /oferta/...)."""

import re

import requests
from bs4 import BeautifulSoup

from carwatch import config

_TECH_FIELDS = {
    "Data pierwszej rejestracji": "first_registration",
    "Kolor nadwozia": "color",
    "Tapicerka": "upholstery",
    "Numer rejestracyjny": "plate",
    "VIN": "vin",
    "Moc": "power",
    "Kraj pochodzenia": "origin",
}

_TRIMS = ["GR Sport", "Executive", "Selection", "Adventure", "Prestige", "Comfort", "Style", "Active"]


def parse_details(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    out: dict = {}
    for li in soup.select("section.vdp-tech li"):
        label, value = li.find("span"), li.find("strong")
        if label and value and label.get_text(strip=True) in _TECH_FIELDS:
            out[_TECH_FIELDS[label.get_text(strip=True)]] = " ".join(value.get_text(" ", strip=True).split())

    headline = soup.select_one("h1 + strong")
    desc = soup.select_one(".vdp-description")
    desc_text = desc.get_text(" ", strip=True) if desc else ""
    # linia modelu z opisu, np. "Toyota RAV4 2.5 Hybrid Comfort 4x4 V (2018-)"
    model_line = re.search(r"Toyota RAV4 [^()]{0,80}\(\d{4}-\)", desc_text)
    # najpierw nagłówek oferty, potem linia modelu – reszta opisu to często szablon dilera
    sources = [x.lower().replace("_", " ").replace("|", " ")
               for x in (headline.get_text(" ", strip=True) if headline else "",
                         model_line.group(0) if model_line else "") if x]

    for src in sources:
        if "comfort" in src and "style" in src:
            out["trim"] = "Comfort+Style"
        else:
            out["trim"] = next((t for t in _TRIMS if t.lower() in src), None)
        if out["trim"]:
            break
    if not out.get("trim"):
        out.pop("trim", None)
    for src in sources:
        m = re.search(r"4\s*x\s*([24])|\b(awd|fwd)\b", src)
        if m:
            out["drive"] = "4x4" if (m.group(1) == "4" or m.group(2) == "awd") else "4x2"
            break

    low = " ".join(sources + [desc_text.lower()])
    flags = []
    if "bezwypadk" in low:
        flags.append("bezwypadkowy")
    head = " ".join(sources)
    if "pierwszy właściciel" in low or re.search(r"\b(1|i)(\.|-szy)?\s+właściciel", head):
        flags.append("1. właściciel")
    if "salon polska" in low or "salon pl" in low or out.get("origin") == "Polska":
        flags.append("salon PL")
    if "faktura vat" in low or "vat 23" in low:
        flags.append("FV 23%")
    if flags:
        out["flags"] = flags
    return out


def fetch_details(session: requests.Session, url: str) -> dict:
    resp = session.get(url, headers=config.HEADERS, timeout=30)
    resp.raise_for_status()
    return parse_details(resp.text)
