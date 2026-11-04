"""Ustawienia obserwatora ofert Toyoty RAV4."""

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
    ),
    "Accept-Language": "pl-PL,pl;q=0.9",
}

TIMEZONE = "Europe/Warsaw"

# --- Samochody używane (Grupa Cygan, platforma Toyota Pewne Auto) ---------
USED_BASE_URL = "https://uzywanegrupacygan.pl"
USED_LISTING_PATH = "/oferty/brand/toyota/model/rav4"

# ID salonów w filtrze "Salon" ("station-id") na stronie
DEALERS = {
    186: "Toyota Warszawa Żerań",
    188: "Toyota Warszawa Marki",
    13: "Lexus Warszawa Żerań",
}

MIN_YEAR = 2023
# Rodzaje napędu z karty oferty. Usuń "Hybryda Plug-in", jeśli interesują
# Cię wyłącznie zwykłe hybrydy.
ALLOWED_FUELS = {"Hybryda", "Hybryda Plug-in"}

# Powiadamiaj także o obniżce ceny już znanej oferty
NOTIFY_PRICE_DROPS = True

MAX_PAGES = 10  # zabezpieczenie przed nieskończoną paginacją

# --- Porównanie z rynkiem (wszystkie RAV4 w programie Toyota Pewne Auto) ---
MARKET_BASE_URL = "https://pewneauto.pl"
# wartości filtra "fuel" odpowiadające ALLOWED_FUELS
MARKET_FUEL_PARAMS = {"Hybryda": "hybrid", "Hybryda Plug-in": "hybrid-plug-in"}
MARKET_MAX_PAGES = 15
MIN_COMPARABLES = 4

# --- Cotygodniowe podsumowanie ---------------------------------------------
SUMMARY_WEEKDAY = 6  # 0 = poniedziałek ... 6 = niedziela
SUMMARY_HOUR = 18    # od tej godziny (czas polski) wysyłane jest podsumowanie

# --- Nowy RAV4 (toyota.pl) ------------------------------------------------
NEW_RAV4_URL = "https://www.toyota.pl/nowe-samochody/rav4"
NEW_PRICE_THRESHOLD = 175_000  # zł

# --- Pliki ----------------------------------------------------------------
STATE_FILE = "state.json"
