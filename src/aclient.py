import os
import discord
import asyncio
from src.log import logger
from src.providers import ProviderManager

class DiscordClient(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        self.provider_manager = ProviderManager()
        self.conversation_history = []

    async def on_ready(self):
        logger.info(f'{self.user} sudah online! Mode: Dual AI Response.')

    async def on_message(self, message):
        if message.author == self.user:
            return

        is_mentioned = self.user in message.mentions
        is_dm = isinstance(message.channel, discord.DMChannel)
        
        if is_mentioned or is_dm:
            content = message.content.replace(f'<@{self.user.id}>', '').strip()
            if content:
                await self.send_dual_response(message, content)

    async def send_dual_response(self, message, user_message):
        author_id = message.author.id
        try:
            async with message.channel.typing():
                # Simpan history
                self.conversation_history.append({'role': 'user', 'content': user_message})
                if len(self.conversation_history) > 10:
                    self.conversation_history = self.conversation_history[-10:]

                # Ambil jawaban dari semua AI
                all_answers = await self.provider_manager.get_all_responses(self.conversation_history)
                
                # Kirim header pertanyaan
                await message.channel.send(f'> **{user_message}** - <@{author_id}>')

                # Kirim jawaban masing-masing AI
                for ai_name, ai_text in all_answers.items():
                    full_response = f"**🤖 MODEL: {ai_name}**\n{ai_text}"
                    
                    # Cek limit 2000 karakter per AI
                    if len(full_response) <= 2000:
                        await message.channel.send(full_response)
                    else:
                        chunks = self.split_text(full_response, 1900)
                        for index, chunk in enumerate(chunks):
                            label = f"\n*(Bersambung {ai_name}...)*" if index < len(chunks)-1 else ""
                            await message.channel.send(chunk + label)
                            await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Gagal kirim dual response: {e}")
            await message.channel.send("❌ Terjadi kesalahan teknis saat memanggil para AI.")

    def split_text(self, text, limit):
        chunks = []
        while len(text) > limit:
            split_at = text.rfind('\n', 0, limit)
            if split_at == -1: split_at = text.rfind(' ', 0, limit)
            if split_at == -1: split_at = limit
            chunks.append(text[:split_at])
            text = text[split_at:].lstrip()
        chunks.append(text)
        return chunks

discordClient = DiscordClient()
