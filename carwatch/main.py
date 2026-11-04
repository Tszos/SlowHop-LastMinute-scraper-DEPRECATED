"""Jedno sprawdzenie: nowe oferty używanych RAV4 + cena nowego RAV4."""

import json
import os
import sys
from datetime import datetime, timezone

import requests

from carwatch import config, notify
from carwatch.new_price import fetch_base_price
from carwatch.used_offers import Offer, fetch_all


def fmt_price(p: int | None) -> str:
    return f"{p:,} zł".replace(",", " ") if p else "cena ?"


def describe(o: Offer) -> str:
    km = f"{o.mileage_km:,} km".replace(",", " ") if o.mileage_km is not None else "? km"
    return f"{o.year}, {km}, {o.fuel}\n{o.title}\n{o.dealer}"


def load_state(path: str) -> dict:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(path: str, state: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def check_used(session: requests.Session, state: dict) -> None:
    offers = fetch_all(session)
    known: dict = state.get("offers", {})
    first_run = "offers" not in state

    if first_run:
        lines = [f"• {o.year} {fmt_price(o.price)} – {o.dealer.split()[-1]}" for o in offers]
        notify.send(
            f"Obserwuję RAV4 – obecnie {len(offers)} ofert",
            "\n".join(lines) or "Brak ofert spełniających kryteria.",
            url=config.USED_BASE_URL + config.USED_LISTING_PATH,
            priority=3,
        )
    else:
        for o in offers:
            prev = known.get(o.id)
            if prev is None:
                notify.send(f"Nowy RAV4: {fmt_price(o.price)}", describe(o),
                            url=o.url, image=o.image, priority=5)
            elif (config.NOTIFY_PRICE_DROPS and o.price and prev.get("price")
                  and o.price < prev["price"]):
                notify.send(
                    f"Obniżka RAV4: {fmt_price(prev['price'])} → {fmt_price(o.price)}",
                    describe(o), url=o.url, image=o.image, tags=["chart_with_downwards_trend"],
                )

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    state["offers"] = {
        o.id: {**o.to_dict(), "first_seen": known.get(o.id, {}).get("first_seen", now)}
        for o in offers
    }


def check_new_price(session: requests.Session, state: dict) -> None:
    price = fetch_base_price(session)
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


def main() -> int:
    state = load_state(config.STATE_FILE)
    errors = 0
    with requests.Session() as session:
        for check in (check_used, check_new_price):
            try:
                check(session, state)
            except Exception as e:  # jedna awaria nie blokuje drugiego sprawdzenia
                errors += 1
                print(f"Błąd w {check.__name__}: {e!r}", file=sys.stderr)
    # raz w miesiącu zmiana w pliku -> commit, żeby GitHub nie wyłączył harmonogramu
    state["heartbeat"] = datetime.now(timezone.utc).strftime("%Y-%m")
    save_state(config.STATE_FILE, state)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
