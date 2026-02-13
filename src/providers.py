import os
from groq import Groq
from src.log import logger

class ProviderManager:
    def __init__(self):
        # Mengambil API Key dari Environment Variable Koyeb
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        
        # Urutan Model: Yang pertama adalah prioritas utama
        self.models = [
            {"name": "Llama 3.3", "id": "llama-3.3-70b-versatile"},
            {"name": "GPT-OSS", "id": "openai/gpt-oss-safeguard-20b"}
        ]

    async def get_response_with_backup(self, messages):
        """Mencoba model utama, jika gagal pindah ke backup"""
        for model in self.models:
            try:
                completion = self.client.chat.completions.create(
                    model=model["id"],
                    messages=messages,
                    temperature=0.7,
                    max_completion_tokens=2048,
                    stream=False,
                )
                # Jika sukses, kirim hasilnya dan stop pencarian
                return {
                    "name": model["name"],
                    "text": completion.choices[0].message.content,
                    "success": True
                }
            except Exception as e:
                logger.error(f"Model {model['name']} gagal: {e}")
                # Jika ini model terakhir dan masih gagal, baru nyerah
                continue
        
        return {
            "name": "System", 
            "text": "❌ Maaf, semua otak AI (Llama & GPT) sedang tidak bisa menjawab. Coba lagi nanti.",
            "success": False
        }

    def get_provider(self):
        return self
