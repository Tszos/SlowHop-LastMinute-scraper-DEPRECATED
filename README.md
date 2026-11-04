# RAV4 watch

Powiadomienia na telefon o:

1. **nowych ofertach używanych Toyot RAV4** na [uzywanegrupacygan.pl](https://uzywanegrupacygan.pl/)
   w salonach **Toyota Warszawa Żerań** i **Toyota Warszawa Marki** – tylko hybrydy, rocznik **od 2023**
   (dodatkowo: o obniżce ceny już obserwowanej oferty),
2. **promocji na nowego RAV4** – gdy cena bazowa „od …” na
   [toyota.pl/nowe-samochody/rav4](https://www.toyota.pl/nowe-samochody/rav4) spadnie poniżej **175 000 zł**.

Skrypt uruchamia się co godzinę w GitHub Actions i zapisuje znane oferty w `state.json`.

## Konfiguracja (jednorazowo, ~5 minut)

1. Zainstaluj na telefonie darmową aplikację **ntfy** (Android: Google Play / F-Droid, iPhone: App Store).
2. W aplikacji „Subskrybuj temat” i wpisz trudną do zgadnięcia nazwę, np. `rav4-tomek-8f3k2q9x`
   (temat działa jak hasło – każdy, kto go zna, może czytać powiadomienia).
3. W repozytorium na GitHubie: **Settings → Secrets and variables → Actions → New repository secret**
   - nazwa: `NTFY_TOPIC`, wartość: ta sama nazwa tematu.
4. Upewnij się, że kod jest na domyślnej gałęzi (harmonogram działa tylko tam) i Actions są włączone
   (**Actions** → włącz workflow „RAV4 watch”).
5. Kliknij **Actions → RAV4 watch → Run workflow**. Pierwsze uruchomienie wyśle podsumowanie
   aktualnych ofert; kolejne – tylko nowości.

Opcjonalnie zamiast/obok ntfy: Telegram – sekrety `TELEGRAM_BOT_TOKEN` i `TELEGRAM_CHAT_ID`.

## Zmiana kryteriów

Wszystko w `carwatch/config.py`: salony (`DEALERS`, ID z filtra „Salon” na stronie), minimalny rocznik,
rodzaje napędu (domyślnie hybryda i hybryda plug-in), próg ceny nowego RAV4, powiadomienia o obniżkach.

## Uruchomienie lokalne

```bash
pip install -r requirements.txt
NTFY_TOPIC=twoj-temat python -m carwatch.main
python -m pytest   # testy parserów
```

> Repozytorium wcześniej zawierało scraper Slowhop (nieaktualny) – dostępny w historii gita.
