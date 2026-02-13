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
        # Mengaktifkan intents agar bot bisa membaca pesan
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
            logger.warning(f"Invalid default provider {default_provider}, menggunakan free")
            self.provider_manager.set_current_provider(ProviderType.FREE)
        
        self.current_model = os.getenv("DEFAULT_MODEL", "auto")
        self.conversation_history = []
        self.current_channel = None
        
        self.activity = discord.Activity(
            type=discord.ActivityType.listening, 
            name="/chat | mention me"
        )

    async def setup_hook(self):
        # Membuat antrian pesan saat bot mulai
        self.loop.create_task(self.process_messages())

    async def process_messages(self):
        while True:
            await asyncio.sleep(1)

    async def on_ready(self):
        logger.info(f'{self.user} is now running!')
        try:
            await self.tree.sync()
            logger.info("Slash commands synced!")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def on_message(self, message):
        # Jangan merespon bot sendiri
        if message.author == self.user:
            return

        # Cek jika bot di-mention atau dichat lewat DM
        is_mentioned = self.user in message.mentions
        is_dm = isinstance(message.channel, discord.DMChannel)
        
        if is_mentioned or is_dm:
            content = message.content.replace(f'<@{self.user.id}>', '').strip()
            if not content:
                return
            
            await self.send_message(message, content)

    async def send_message(self, message, user_message):
        """Kirim respon ke user dengan aman (Fix untuk 'followup' error)"""
        author_id = message.user.id if hasattr(message, 'user') else message.author.id
        
        try:
            # Memberitahu user bahwa bot sedang berpikir
            async with message.channel.typing():
                response = await self.handle_response(user_message)
                response_content = f'> **{user_message}** - <@{str(author_id)}> \n\n{response}'
                
                # Menggunakan utilitas kirim pesan (mendukung pesan panjang)
                await send_split_message(self, response_content, message)
                
        except Exception as e:
            logger.exception(f"Error saat mengirim pesan: {e}")
            error_msg = f"❌ Maaf, terjadi kesalahan internal."
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
            return "❌ Maaf, AI sedang tidak bisa menjawab. Coba lagi nanti."

# BARIS PALING PENTING: Membuat instance bot
discordClient = DiscordClient()
