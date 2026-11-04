from pathlib import Path

from carwatch.new_price import parse_base_price
from carwatch.used_offers import parse_listing

FIX = Path(__file__).parent / "fixtures"


def test_parse_listing():
    offers = parse_listing((FIX / "listing.html").read_text(encoding="utf-8"), "Toyota Warszawa Żerań")
    assert len(offers) == 3
    o = offers[0]
    assert o.id.isdigit()
    assert o.url.startswith("https://uzywanegrupacygan.pl/oferta/toyota-rav4/")
    assert o.year and 2000 < o.year < 2100
    assert o.price and o.price > 10_000
    assert o.mileage_km is not None
    assert o.fuel.startswith("Hybryda")


def test_parse_base_price_json():
    html = ('"productModelPage":"https://www.toyota.pl/nowe-samochody/rav4","productModelTitle":"x",'
            '"promoCardDetails":"Od \\u003cstrong\\u003e181 600 zł\\u003c/strong\\u003e"')
    assert parse_base_price(html) == 181_600


def test_parse_base_price_text():
    assert parse_base_price("<p>Specjalna cena od <b>172&nbsp;900&nbsp;zł</b></p>") == 172_900
