import os
import discord
import asyncio
import logging
from typing import List, Dict, Optional

from src import personas
from src.log import logger
from src.providers import ProviderManager, ProviderType, ModelInfo
from utils.message_utils import send_split_message

from dotenv import load_dotenv
from discord import app_commands

load_dotenv()

class DiscordClient(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        
        self.tree = app_commands.CommandTree(self)
        self.provider_manager = ProviderManager()
        
        # Set default provider
        default_provider = os.getenv("DEFAULT_PROVIDER", "free")
        try:
            self.provider_manager.set_current_provider(ProviderType(default_provider))
        except ValueError:
            logger.warning(f"Invalid default provider {default_provider}, using free")
            self.provider_manager.set_current_provider(ProviderType.FREE)
        
        self.current_model = os.getenv("DEFAULT_MODEL", "auto")
        self.conversation_history = []
        self.current_channel = None
        self.current_persona = "standard"
        
        self.activity = discord.Activity(
            type=discord.ActivityType.listening, 
            name="/chat | /help | /provider"
        )
        self.isPrivate = False
        self.is_replying_all = os.getenv("REPLYING_ALL", "False") == "True"
        self.replying_all_discord_channel_id = os.getenv("REPLYING_ALL_DISCORD_CHANNEL_ID")
        
        # Load system prompt
        config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        prompt_path = os.path.join(config_dir, "system_prompt.txt")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.starting_prompt = f.read()
        except FileNotFoundError:
            self.starting_prompt = ""
        
        self.message_queue = asyncio.Queue()

    async def process_messages(self):
        while True:
            if self.current_channel is not None:
                while not self.message_queue.empty():
                    async with self.current_channel.typing():
                        message, user_message = await self.message_queue.get()
                        try:
                            await self.send_message(message, user_message)
                        except Exception as e:
                            logger.exception(f"Error: {e}")
                        finally:
                            self.message_queue.task_done()
            await asyncio.sleep(1)

    async def enqueue_message(self, message, user_message):
        await self.message_queue.put((message, user_message))

    async def send_message(self, message, user_message):
        """Kirim respon ke user dengan aman"""
        # Tentukan ID author (apakah dari Slash Command atau Chat Biasa)
        author = message.user.id if hasattr(message, 'user') else message.author.id
        
        try:
            # Ambil respon dari AI
            response = await self.handle_response(user_message)
            response_content = f'> **{user_message}** - <@{str(author)}> \n\n{response}'
            
            # Kirim pesan (split jika terlalu panjang)
            await send_split_message(self, response_content, message)
            
        except Exception as e:
            logger.exception(f"Error saat mengirim pesan: {e}")
            error_msg = f"❌ Terjadi kesalahan internal."
            
            # Cek cara kirim error yang benar supaya tidak muncul 'followup' error lagi
            if hasattr(message, 'channel'):
                await message.channel.send(error_msg)
            elif hasattr(message, 'followup'):
                await message.followup.send(error_msg)
