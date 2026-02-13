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
                # Header pesan tetap muncul di awal pesan pertama
                header = f'> **{user_message}** - <@{author_id}>\n\n'
                full_text = header + response
                
                # JIKA LEBIH DARI 2000 KARAKTER, KIRIM KE HALAMAN/PESAN BARU
                if len(full_text) <= 2000:
                    await message.channel.send(full_text)
                else:
                    # Memecah pesan menjadi beberapa bagian (page baru)
                    chunks = self.split_text(full_text, 1900)
                    for index, chunk in enumerate(chunks):
                        # Tambahkan penanda halaman jika lebih dari 1
                        page_label = f"\n\n*(Lanjut ke hal. {index + 2}...)*" if index < len(chunks) - 1 else ""
                        await message.channel.send(chunk + page_label)
                        await asyncio.sleep(0.8) # Jeda aman biar gak kena ban Discord
                        
        except Exception as e:
            logger.error(f"Gagal kirim: {e}")
            await message.channel.send("❌ Waduh, jawabannya kepanjangan banget sampai saya capek ngetiknya. Coba tanya hal yang lebih spesifik!")

    def split_text(self, text, limit):
        """Fungsi untuk memotong teks menjadi beberapa halaman secara rapi"""
        chunks = []
        while len(text) > limit:
            # Cari spasi terakhir sebelum limit supaya kata tidak terpotong tengah-tengah
            split_at = text.rfind(' ', 0, limit)
            if split_at == -1: split_at = limit # Jika tidak ada spasi, potong paksa
            
            chunks.append(text[:split_at])
            text = text[split_at:].lstrip()
        chunks.append(text)
        return chunks

    async def handle_response(self, user_message: str) -> str:
        self.conversation_history.append({'role': 'user', 'content': user_message})
        if len(self.conversation_history) > 6:
            self.conversation_history = self.conversation_history[-6:]
            
        try:
            provider = self.provider_manager.get_provider()
            response = await provider.chat_completion(messages=self.conversation_history)
            if response:
                self.conversation_history.append({'role': 'assistant', 'content': response})
                return response
            return "Maaf, AI lagi melamun. Coba tanya lagi ya."
        except Exception as e:
            logger.error(f"AI Error: {e}")
            return f"❌ Terjadi kesalahan pada otak AI: {str(e)}"

discordClient = DiscordClient()
