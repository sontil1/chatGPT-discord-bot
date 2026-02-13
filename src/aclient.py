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
        author = message.user.id if hasattr(message, 'user') else message.author.id
        try:
            response = await self.handle_response(user_message)
            response_content = f'> **{user_message}** - <@{str(author)}> \n\n{response}'
            await send_split_message(self, response_content, message)
        except Exception as e:
            logger.exception(f"Error while sending: {e}")
            error_msg = f"❌ Error: {str(e)}"
            await message.channel.send(error_msg)

    async def handle_response(self, user_message: str) -> str:
        self.conversation_history.append({'role': 'user', 'content': user_message})
        provider = self.provider_manager.get_provider()
        try:
            response = await provider.chat_completion(
                messages=self.conversation_history,
                model=self.current_model if self.current_model != "auto" else None
            )
            self.conversation_history.append({'role': 'assistant', 'content': response})
            return response
        except Exception as e:
            logger.error(f"Provider error: {e}")
            return "❌ Maaf, sedang terjadi gangguan pada koneksi AI."

    def switch_provider(self, provider_type: ProviderType, model: Optional[str] = None):
        self.provider_manager.set_current_provider(provider_type)
        if model: self.current_model = model

    # --- BAGIAN YANG TADI HILANG ---
    async def on_ready(self):
        logger.info(f'{self.user} is now running!')
        await self.tree.sync()
        self.loop.create_task(self.process_messages())

    async def on_message(self, message):
        if message.author == self.user:
            return

        is_mentioned = self.user in message.mentions
        is_dm = isinstance(message.channel, discord.DMChannel)
        
        if is_mentioned or is_dm:
            content = message.content.replace(f'<@{self.user.id}>', '').strip()
            if not content: return
            self.current_channel = message.channel
            await self.enqueue_message(message, content)

# Baris terakhir tetap mepet kiri
discordClient = DiscordClient()
