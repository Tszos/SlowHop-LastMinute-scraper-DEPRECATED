"""Porównanie ceny oferty z podobnymi RAV4 z całej Polski."""

import re
from dataclasses import dataclass
from statistics import median

from carwatch import config
from carwatch.used_offers import Offer


@dataclass
class MarketComparison:
    median_price: int
    count: int
    pct: float  # (cena - mediana) / mediana * 100; ujemne = taniej niż rynek
    basis: str  # jakie auta porównano


def title_drive(text: str | None) -> str | None:
    m = re.search(r"4\s*x\s*([24])|\b(awd|fwd)\b", (text or "").lower().replace("_", " "))
    if not m:
        return None
    return "4x4" if (m.group(1) == "4" or m.group(2) == "awd") else "4x2"


def compare(offer: Offer, market: list[Offer], drive: str | None = None) -> MarketComparison | None:
    """drive: napęd oferty ("4x4"/"4x2"); jeśli znany, najpierw porównuje z autami o tym samym napędzie."""
    if not offer.price:
        return None
    base = [m for m in market if m.id != offer.id and m.price and m.fuel == offer.fuel
            and m.year is not None and m.mileage_km is not None]
    drive = drive or title_drive(offer.title)
    pools = []
    if drive:
        pools.append(([m for m in base if title_drive(m.title) == drive], f", napęd {drive}"))
    pools.append((base, ""))
    for pool, suffix in pools:
        result = _compare_in(offer, pool, suffix)
        if result:
            return result
    return None


def _compare_in(offer: Offer, pool: list[Offer], suffix: str) -> MarketComparison | None:
    km = offer.mileage_km
    # od najściślejszego kryterium do najluźniejszego
    steps = [
        (lambda m: m.year == offer.year and km is not None and abs(m.mileage_km - km) <= 25_000,
         f"rocznik {offer.year}, przebieg ±25 tys. km"),
        (lambda m: m.year == offer.year and km is not None and abs(m.mileage_km - km) <= 50_000,
         f"rocznik {offer.year}, przebieg ±50 tys. km"),
        (lambda m: m.year == offer.year, f"rocznik {offer.year}"),
        (lambda m: abs(m.year - (offer.year or 0)) <= 1, f"rocznik {offer.year}±1"),
    ]
    for pred, basis in steps:
        prices = [m.price for m in pool if pred(m)]
        if len(prices) >= config.MIN_COMPARABLES:
            med = int(median(prices))
            return MarketComparison(med, len(prices), (offer.price - med) / med * 100, basis + suffix)
    return None


def fmt_pct(c: MarketComparison | None) -> str:
    if c is None:
        return ""
    pct = round(c.pct)
    return "≈ rynek" if pct == 0 else f"{pct:+d}% vs rynek".replace("-", "−")
