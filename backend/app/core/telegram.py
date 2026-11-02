import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_telegram_message(text: str) -> None:
    """Сообщение менеджеру. Ошибка отправки не должна ломать заказ, поэтому только пишем в лог."""
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                url,
                json={"chat_id": settings.TELEGRAM_CHAT_ID, "text": text, "disable_web_page_preview": True},
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        # Токен бота в адресе, поэтому в лог только тип ошибки
        logger.warning("Telegram notification failed: %s", type(exc).__name__)
