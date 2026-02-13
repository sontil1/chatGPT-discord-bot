import os
from groq import Groq
from enum import Enum
from src.log import logger

class ProviderType(Enum):
    FREE = "free"

class ProviderManager:
    def __init__(self):
        # Mengambil API Key dari Environment Variable Koyeb
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    async def chat_completion(self, messages, model=None):
        try:
            # Menggunakan model llama-3.1-8b-instant yang super cepat
            completion = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                temperature=1,
                max_completion_tokens=1024,
                top_p=1,
                stream=False, # Kita matikan stream untuk bot Discord
                stop=None,
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq Error: {e}")
            return "❌ Aduh, Groq API Key kamu belum dimasukkan ke Koyeb atau ada masalah koneksi."

    def get_provider(self):
        return self

    def set_current_provider(self, provider_type):
        pass
