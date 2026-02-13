import os
import asyncio
from src.aclient import discordClient
from src.log import logger

async def run_discord_bot():
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        logger.error("DISCORD_BOT_TOKEN is not set in environment variables.")
        return

    try:
        # Menjalankan bot
        await discordClient.start(token)
    except Exception as e:
        logger.exception(f"Error starting bot: {e}")

# Fungsi on_ready dipindahkan ke aclient.py untuk menghindari tabrakan
