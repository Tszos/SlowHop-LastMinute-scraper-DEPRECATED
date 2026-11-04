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


def test_parse_details():
    from carwatch.details import parse_details
    d = parse_details((FIX / "offer.html").read_text(encoding="utf-8"))
    assert d["vin"] == "JTMR63FV50D106592"
    assert d["plate"] == "WZ879GT"
    assert d["first_registration"] == "27-09-2023"
    assert d["color"] == "Czarny"
    assert d["trim"] == "Comfort"
    assert d["drive"] == "4x4"
    assert "salon PL" in d["flags"]


def _offer(i, year, km, price, fuel="Hybryda"):
    from carwatch.used_offers import Offer
    return Offer(str(i), "", "", year, km, fuel, price, "", None)


def test_market_compare():
    from carwatch.market import compare
    market = [_offer(i, 2023, 70_000 + i * 1000, 150_000 + i * 1000) for i in range(6)]
    market.append(_offer(99, 2023, 70_000, 100_000, fuel="Hybryda Plug-in"))  # inny napęd
    c = compare(_offer(1000, 2023, 72_000, 140_000), market)
    assert c.count == 6 and c.median_price == 152_500
    assert round(c.pct) == -8


def test_market_compare_too_few():
    from carwatch.market import compare
    assert compare(_offer(1, 2024, 10_000, 1), [_offer(2, 2020, 1, 1)]) is None


def test_parse_details_comfort_style_4x2():
    from carwatch.details import parse_details
    html = ("<h1>Toyota RAV4</h1><strong>Comfort+Style_4x2 2,5 Hybrid 218 KM</strong>"
            "<div class='vdp-description'>Toyota RAV4 2.5 Hybrid Comfort 4x2 V (2018-) "
            "Szablon dilera: oferujemy też auta 4x4.</div>")
    d = parse_details(html)
    assert d["trim"] == "Comfort+Style" and d["drive"] == "4x2"


def test_market_compare_prefers_same_drive():
    from carwatch.market import compare
    from carwatch.used_offers import Offer
    mk = lambda i, t, p: Offer(str(i), "", t, 2023, 60_000, "Hybryda", p, "", None)
    market = [mk(i, "2.5 Hybrid Comfort 4x2", 140_000) for i in range(4)]
    market += [mk(10 + i, "2.5 Hybrid Executive 4x4", 180_000) for i in range(6)]
    c = compare(mk(99, "x", 140_000), market, drive="4x2")
    assert c.median_price == 140_000 and "4x2" in c.basis
