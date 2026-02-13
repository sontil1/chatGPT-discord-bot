import os
import discord
import asyncio
from src.log import logger
from src.providers import ProviderManager, ProviderType
from discord import app_commands

class DiscordClient(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        
        self.tree = app_commands.CommandTree(self)
        self.provider_manager = ProviderManager()
        
        # Atribut wajib
        self.is_replying_all = os.getenv("REPLYING_ALL", "False") == "True"
        self.replying_all_discord_channel_id = os.getenv("REPLYING_ALL_DISCORD_CHANNEL_ID")
        
        self.provider_manager.set_current_provider(ProviderType.FREE)
        self.conversation_history = []

    async def setup_hook(self):
        pass

    async def on_ready(self):
        logger.info(f'{self.user} sudah online dan siap!')
        await self.tree.sync()

    async def on_message(self, message):
        if message.author == self.user:
            return

        is_mentioned = self.user in message.mentions
        is_dm = isinstance(message.channel, discord.DMChannel)
        
        if is_mentioned or is_dm:
            content = message.content.replace(f'<@{self.user.id}>', '').strip()
            if content:
                await self.send_message(message, content)

    async def send_message(self, message, user_message):
        author_id = message.author.id
        try:
            async with message.channel.typing():
                response = await self.handle_response(user_message)
                await message.channel.send(f'> **{user_message}** - <@{author_id}> \n\n{response}')
        except Exception as e:
            logger.error(f"Gagal: {e}")
            await message.channel.send("❌ Sedang gangguan, coba tanya lagi ya.")

    async def handle_response(self, user_message: str) -> str:
        self.conversation_history.append({'role': 'user', 'content': user_message})
        if len(self.conversation_history) > 4:
            self.conversation_history = self.conversation_history[-4:]
            
        try:
            provider = self.provider_manager.get_provider()
            response = await provider.chat_completion(messages=self.conversation_history)
            if response:
                self.conversation_history.append({'role': 'assistant', 'content': response})
                return response
            return "AI tidak merespon, coba lagi."
        except Exception as e:
            logger.error(f"AI Error: {e}")
            return "❌ Provider penuh, coba tanya sekali lagi."

discordClient = DiscordClient()
