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
        logger.info(f'{self.user} aktif dengan sistem Backup AI!')

    async def on_message(self, message):
        # Jangan balas pesan sendiri
        if message.author == self.user:
            return

        is_mentioned = self.user in message.mentions
        is_dm = isinstance(message.channel, discord.DMChannel)
        
        if is_mentioned or is_dm:
            content = message.content.replace(f'<@{self.user.id}>', '').strip()
            if content:
                await self.send_message_logic(message, content)

    async def send_message_logic(self, message, user_message):
        author_id = message.author.id
        try:
            async with message.channel.typing():
                # Simpan riwayat chat (maksimal 8 pesan terakhir)
                self.conversation_history.append({'role': 'user', 'content': user_message})
                if len(self.conversation_history) > 8:
                    self.conversation_history = self.conversation_history[-8:]

                # Panggil fungsi Failover dari providers.py
                result = await self.provider_manager.get_response_with_backup(self.conversation_history)
                
                ai_name = result["name"]
                ai_text = result["text"]

                # Header informasi model
                header = f'> **{user_message}** - <@{author_id}> *(Model: {ai_name})*\n\n'
                full_text = header + ai_text

                # Logika Kirim: Cek apakah lebih dari 2000 karakter
                if len(full_text) <= 2000:
                    await message.channel.send(full_text)
                else:
                    # Pecah jadi beberapa halaman jika terlalu panjang
                    chunks = self.split_text(full_text, 1900)
                    for index, chunk in enumerate(chunks):
                        label = f"\n\n*(Lanjut ke hal. {index+2}...)*" if index < len(chunks) - 1 else ""
                        await message.channel.send(chunk + label)
                        await asyncio.sleep(1.2) # Jeda agar tidak kena rate limit

                # Simpan jawaban ke history jika sukses
                if result["success"]:
                    self.conversation_history.append({'role': 'assistant', 'content': ai_text})

        except Exception as e:
            logger.error(f"Gagal mengirim pesan: {e}")
            await message.channel.send("❌ Terjadi gangguan mendadak pada sistem bot.")

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
