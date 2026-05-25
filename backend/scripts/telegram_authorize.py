import asyncio
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from telethon import TelegramClient

from app.core.config import settings

SESSION_NAME = "telegram_scraper_session"


async def main() -> None:
    client = TelegramClient(SESSION_NAME, int(settings.telegram_api_id), settings.telegram_api_hash)
    try:
        await client.start()
        me = await client.get_me()
        username = getattr(me, "username", None)
        phone = getattr(me, "phone", None)
        print("Telegram authorization completed.")
        if username:
            print(f"Authorized as: @{username}")
        elif phone:
            print(f"Authorized phone: +{phone}")
        else:
            print("Authorized account has no public username.")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
