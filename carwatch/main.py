"""Jedno sprawdzenie: oferty używanych RAV4, cena nowego RAV4, podsumowanie tygodniowe."""

import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from carwatch import config, notify
from carwatch.details import fetch_details
from carwatch.market import MarketComparison, compare, fmt_pct
from carwatch.new_price import fetch_base_price
from carwatch.used_offers import Offer, fetch_all, fetch_market

TZ = ZoneInfo(config.TIMEZONE)
HISTORY_URL = "https://historiapojazdu.gov.pl/"


def now() -> datetime:
    return datetime.now(TZ)


def fmt_price(p: int | None) -> str:
    return f"{p:,} zł".replace(",", " ") if p else "cena ?"


def fmt_km(km: int | None) -> str:
    return f"{km / 1000:.0f} tys. km" if km is not None else "? km"


def short_dealer(dealer: str) -> str:
    return dealer.replace("Toyota Warszawa ", "").replace("Lexus Warszawa ", "Lexus ")


class Context:
    """Dane pobierane leniwie, najwyżej raz na uruchomienie."""

    def __init__(self, session: requests.Session):
        self.session = session
        self._market: list[Offer] | None = None

    def market(self) -> list[Offer]:
        if self._market is None:
            try:
                self._market = fetch_market(self.session)
                print(f"Rynek: {len(self._market)} porównywalnych ofert RAV4 w Polsce")
            except Exception as e:
                print(f"Nie udało się pobrać ofert rynkowych: {e!r}", file=sys.stderr)
                self._market = []
        return self._market

    def compare(self, offer: Offer, details: dict | None = None) -> MarketComparison | None:
        return compare(offer, self.market(), (details or {}).get("drive"))


def offer_from_record(rec: dict) -> Offer:
    return Offer(**{k: rec.get(k) for k in Offer.__dataclass_fields__})


def describe(o: Offer, details: dict, cmp: MarketComparison | None) -> str:
    variant = " ".join(x for x in (details.get("trim"), details.get("drive")) if x)
    lines = [
        f"{o.year} · {fmt_km(o.mileage_km)} · {o.fuel}" + (f" · {variant}" if variant else ""),
        o.title,
    ]
    extras = [details.get("color"), details.get("upholstery") and f"tapicerka {details['upholstery'].lower()}"]
    extras += details.get("flags", [])
    if any(extras):
        lines.append(", ".join(x for x in extras if x))
    lines.append(o.dealer)
    if cmp:
        lines.append(f"Rynek: mediana {fmt_price(cmp.median_price)} z {cmp.count} ofert "
                     f"({cmp.basis}) → {fmt_pct(cmp)}")
    if details.get("vin"):
        lines.append("Do historiapojazdu.gov.pl: "
                     f"{details.get('plate', '?')} · VIN {details['vin']} · "
                     f"1. rej. {details.get('first_registration', '?')}")
    return "\n".join(lines)


def get_details(ctx: Context, offer: Offer, prev: dict | None) -> dict:
    if prev and prev.get("details"):
        return prev["details"]
    try:
        return fetch_details(ctx.session, offer.url)
    except Exception as e:
        print(f"Brak szczegółów {offer.url}: {e!r}", file=sys.stderr)
        return {}


def check_used(ctx: Context, state: dict) -> None:
    offers = fetch_all(ctx.session)
    known: dict = state.get("offers", {})
    first_run = "offers" not in state
    today = now().date().isoformat()
    stamp = now().isoformat(timespec="seconds")

    new_records = {}
    for o in offers:
        prev = known.get(o.id)
        details = get_details(ctx, o, prev)
        history = list(prev.get("price_history", [])) if prev else []
        if not history and prev and prev.get("price"):
            history = [[prev.get("first_seen", stamp)[:10], prev["price"]]]
        if o.price and (not history or history[-1][1] != o.price):
            history.append([today, o.price])

        if not first_run and prev is None:
            cmp = ctx.compare(o, details)
            pct = f" ({fmt_pct(cmp)})" if cmp else ""
            notify.send(f"Nowy RAV4: {fmt_price(o.price)}{pct}", describe(o, details, cmp),
                        url=o.url, image=o.image, priority=5,
                        extra_actions=[("Historia pojazdu", HISTORY_URL)] if details.get("vin") else None)
        elif (prev and config.NOTIFY_PRICE_DROPS and o.price and prev.get("price")
              and o.price < prev["price"]):
            cmp = ctx.compare(o, details)
            notify.send(
                f"Obniżka RAV4: {fmt_price(prev['price'])} → {fmt_price(o.price)}",
                describe(o, details, cmp), url=o.url, image=o.image,
                tags=["chart_with_downwards_trend"],
            )

        new_records[o.id] = {
            **o.to_dict(),
            "first_seen": prev.get("first_seen", stamp) if prev else stamp,
            "details": details,
            "price_history": history,
        }

    if first_run:
        lines = [f"• {o.year} {fmt_price(o.price)} – {short_dealer(o.dealer)}" for o in offers]
        notify.send(f"Obserwuję RAV4 – obecnie {len(offers)} ofert",
                    "\n".join(lines) or "Brak ofert spełniających kryteria.",
                    url=config.USED_BASE_URL + config.USED_LISTING_PATH, priority=3)

    # oferty, które zniknęły (sprzedane / zdjęte) – do podsumowania tygodniowego
    removed = state.get("removed", [])
    for oid, rec in known.items():
        if oid not in new_records:
            removed.append({"id": oid, "title": rec.get("title"), "year": rec.get("year"),
                            "price": rec.get("price"), "dealer": rec.get("dealer"),
                            "first_seen": rec.get("first_seen"), "removed_at": stamp})
    state["removed"] = removed[-50:]
    state["offers"] = new_records


def days_listed(rec: dict) -> int | None:
    try:
        return (now() - datetime.fromisoformat(rec["first_seen"]).astimezone(TZ)).days
    except (KeyError, ValueError, TypeError):
        return None


def build_summary(ctx: Context, state: dict) -> str:
    rows = []
    for rec in state.get("offers", {}).values():
        o = offer_from_record(rec)
        rows.append((ctx.compare(o, rec.get("details")), rec, o))
    rows.sort(key=lambda r: r[0].pct if r[0] else 999)

    lines = [f"Obserwowane oferty ({len(rows)}), od najlepszej względem rynku:"]
    for cmp, rec, o in rows:
        d = rec.get("details", {})
        variant = " ".join(x for x in (d.get("trim"), d.get("drive")) if x)
        hist = rec.get("price_history", [])
        drops = sum(1 for a, b in zip(hist, hist[1:]) if b[1] < a[1])
        days = days_listed(rec)
        parts = [fmt_price(o.price) + (f" ({fmt_pct(cmp)})" if cmp else ""),
                 str(o.year), fmt_km(o.mileage_km), variant, short_dealer(o.dealer),
                 f"{days} dni" if days is not None else "",
                 f"↓{drops}× od {fmt_price(hist[0][1])}" if drops else ""]
        lines.append("• " + " · ".join(p for p in parts if p))
        lines.append(f"  {o.url}")

    since = state.get("last_summary_at", "")
    gone = [r for r in state.get("removed", []) if r.get("removed_at", "") > since]
    if gone:
        lines.append("\nZniknęły w tym tygodniu (sprzedane/zdjęte):")
        lines += [f"• {r.get('year')} {fmt_price(r.get('price'))} – {short_dealer(r.get('dealer') or '')}"
                  for r in gone]

    new_price = state.get("new_rav4", {}).get("price")
    if new_price:
        lines.append(f"\nNowy RAV4 (cennik toyota.pl): od {fmt_price(new_price)}")
    return "\n".join(lines)


def maybe_send_summary(ctx: Context, state: dict) -> None:
    t = now()
    week = f"{t.isocalendar().year}-W{t.isocalendar().week:02d}"
    forced = os.environ.get("FORCE_SUMMARY") == "1"
    due = t.weekday() == config.SUMMARY_WEEKDAY and t.hour >= config.SUMMARY_HOUR
    if not forced and (not due or state.get("last_summary_week") == week):
        return
    notify.send("RAV4 – podsumowanie tygodnia", build_summary(ctx, state),
                url=config.USED_BASE_URL + config.USED_LISTING_PATH, priority=3,
                tags=["clipboard"])
    if not forced:
        state["last_summary_week"] = week
    state["last_summary_at"] = t.isoformat(timespec="seconds")


def check_new_price(ctx: Context, state: dict) -> None:
    price = fetch_base_price(ctx.session)
    if price is None:
        print("Nie udało się odczytać ceny nowego RAV4 – sprawdź parser.", file=sys.stderr)
        return
    print(f"Cena bazowa nowego RAV4: {fmt_price(price)}")
    prev = state.get("new_rav4", {})
    below = price < config.NEW_PRICE_THRESHOLD
    # powiadom przy pierwszym zejściu poniżej progu i przy każdej kolejnej obniżce
    if below and (not prev.get("below") or price < prev.get("price", price + 1)):
        notify.send(
            f"Nowy RAV4 od {fmt_price(price)}!",
            f"Cena bazowa spadła poniżej {fmt_price(config.NEW_PRICE_THRESHOLD)}.",
            url=config.NEW_RAV4_URL, priority=5, tags=["tada"],
        )
    state["new_rav4"] = {"price": price, "below": below}


def load_state(path: str) -> dict:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(path: str, state: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def main() -> int:
    state = load_state(config.STATE_FILE)
    errors = 0
    with requests.Session() as session:
        ctx = Context(session)
        for check in (check_used, check_new_price, maybe_send_summary):
            try:
                check(ctx, state)
            except Exception as e:  # jedna awaria nie blokuje pozostałych sprawdzeń
                errors += 1
                print(f"Błąd w {check.__name__}: {e!r}", file=sys.stderr)
    # raz w miesiącu zmiana w pliku -> commit, żeby GitHub nie wyłączył harmonogramu
    state["heartbeat"] = now().strftime("%Y-%m")
    save_state(config.STATE_FILE, state)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
