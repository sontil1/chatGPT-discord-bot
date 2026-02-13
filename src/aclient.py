import os
import discord
import asyncio
from src.log import logger
from src.providers import ProviderManager, ProviderType
from utils.message_utils import send_split_message
from discord import app_commands

class DiscordClient(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        
        self.tree = app_commands.CommandTree(self)
        self.provider_manager = ProviderManager()
        
        # Paksa gunakan provider FREE yang paling stabil
        self.provider_manager.set_current_provider(ProviderType.FREE)
        self.current_model = "gpt-3.5-turbo"
        self.conversation_history = []

    async def setup_hook(self):
        self.loop.create_task(self.process_messages())

    async def process_messages(self):
        while True:
            await asyncio.sleep(1)

    async def on_ready(self):
        logger.info(f'{self.user} sudah online!')
        await self.tree.sync()

    async def on_message(self, message):
        if message.author == self.user:
            return

        # Cek mention atau DM
        if self.user in message.mentions or isinstance(message.channel, discord.DMChannel):
            content = message.content.replace(f'<@{self.user.id}>', '').strip()
            if content:
                await self.send_message(message, content)

    async def send_message(self, message, user_message):
        author_id = message.user.id if hasattr(message, 'user') else message.author.id
        
        try:
            # Bot mengetik di Discord agar terlihat prosesnya
            async with message.channel.typing():
                response = await self.handle_response(user_message)
                final_text = f'> **{user_message}** - <@{author_id}> \n\n{response}'
                await send_split_message(self, final_text, message)
        except Exception as e:
            logger.error(f"Error kirim: {e}")
            await message.channel.send("❌ Provider AI sibuk, coba tanya lagi sekali lagi.")

    async def handle_response(self, user_message: str) -> str:
        # Batasi riwayat agar tidak lemot
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
            
        self.conversation_history.append({'role': 'user', 'content': user_message})
        
        try:
            provider = self.provider_manager.get_provider()
            response = await provider.chat_completion(
                messages=self.conversation_history,
                model=None # Biarkan auto-select
            )
            
            if not response or len(response) < 1:
                return "Maaf, AI tidak memberikan jawaban. Coba ulangi pertanyaannya."
                
            self.conversation_history.append({'role': 'assistant', 'content': response})
            return response
        except Exception as e:
            logger.error(f"AI Error: {e}")
            return "Maaf, koneksi ke otak AI terputus. Coba lagi ya!"

# Instance bot
discordClient = DiscordClient()
