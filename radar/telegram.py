"""Telegram delivery through the Bot API."""
import requests

from radar import config

MAX_MESSAGE_LENGTH = 4000  # Telegram's hard limit is 4096 characters


def split_message(text: str) -> list[str]:
    """Split text on blank lines into chunks that fit Telegram's size limit."""
    chunks: list[str] = []
    current = ""
    for block in text.split("\n\n"):
        if current and len(current) + len(block) + 2 > MAX_MESSAGE_LENGTH:
            chunks.append(current)
            current = ""
        current += ("\n\n" if current else "") + block
    if current:
        chunks.append(current)
    return chunks


def send(text: str) -> int:
    """Send ``text`` to the configured chat and return the number of messages sent.

    The Bot API URL embeds the token, so request errors are re-raised without
    their original message to keep the token out of logs.
    """
    token = config.require("TELEGRAM_BOT_TOKEN")
    chat_id = config.require("TELEGRAM_CHAT_ID")
    sent = 0
    for chunk in split_message(text):
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": chunk, "disable_web_page_preview": True},
                timeout=30,
            )
        except requests.RequestException as exc:
            raise RuntimeError(f"Could not reach Telegram ({type(exc).__name__})") from None
        if not response.ok:
            try:
                detail = response.json().get("description", "")
            except ValueError:
                detail = ""
            raise RuntimeError(
                f"Telegram rejected the message: HTTP {response.status_code} {detail}"
            )
        sent += 1
    return sent
