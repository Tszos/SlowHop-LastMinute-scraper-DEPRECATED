"""Wysyłka powiadomień na telefon.

Obsługiwane kanały (konfiguracja przez zmienne środowiskowe):
  * ntfy  – NTFY_TOPIC (wymagane), NTFY_SERVER (domyślnie https://ntfy.sh)
  * Telegram – TELEGRAM_BOT_TOKEN i TELEGRAM_CHAT_ID (opcjonalnie)
Bez żadnej konfiguracji powiadomienia są tylko wypisywane na konsolę.
"""

import os

import requests


MAX_MESSAGE = 3900  # limit ntfy to 4096 bajtów


def send(title: str, message: str, url: str | None = None, image: str | None = None,
         priority: int = 4, tags: list[str] | None = None,
         extra_actions: list[tuple[str, str]] | None = None) -> None:
    """extra_actions: dodatkowe przyciski (etykieta, url) w powiadomieniu ntfy."""
    if len(message.encode()) > MAX_MESSAGE:
        message = message.encode()[:MAX_MESSAGE].decode(errors="ignore") + "\n…"
    print(f"[powiadomienie] {title}\n{message}\n{url or ''}\n")
    sent = False

    topic = os.environ.get("NTFY_TOPIC")
    if topic:
        server = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
        payload = {"topic": topic, "title": title, "message": message,
                   "priority": priority, "tags": tags or ["red_car"]}
        if url:
            payload["click"] = url
            payload["actions"] = [{"action": "view", "label": "Otwórz ofertę", "url": url}]
        for label, link in (extra_actions or [])[:2]:
            payload.setdefault("actions", []).append({"action": "view", "label": label, "url": link})
        if image:
            payload["attach"] = image
        headers = {}
        if os.environ.get("NTFY_TOKEN"):
            headers["Authorization"] = f"Bearer {os.environ['NTFY_TOKEN']}"
        requests.post(server, json=payload, headers=headers, timeout=30).raise_for_status()
        sent = True

    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat:
        text = f"<b>{title}</b>\n{message}" + (f"\n{url}" if url else "")
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat, "text": text, "parse_mode": "HTML"},
                      timeout=30).raise_for_status()
        sent = True

    if not sent:
        print("(brak NTFY_TOPIC / TELEGRAM_* – nie wysłano na telefon)")
