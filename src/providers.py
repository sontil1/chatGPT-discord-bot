import os
from groq import Groq
from src.log import logger

class ProviderManager:
    def __init__(self):
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        # Daftar model yang wajib jawab
        self.models = {
            "Llama 3.3": "llama-3.3-70b-versatile",
            "GPT-OSS": "openai/gpt-oss-safeguard-20b"
        }

    async def get_all_responses(self, messages):
        results = {}
        for name, model_id in self.models.items():
            try:
                completion = self.client.chat.completions.create(
                    model=model_id,
                    messages=messages,
                    temperature=0.7,
                    max_completion_tokens=2048,
                    stream=False,
                )
                results[name] = completion.choices[0].message.content
            except Exception as e:
                logger.error(f"Error pada {name}: {e}")
                results[name] = "⚠️ Maaf, model ini sedang penuh sesak."
        return results

    def get_provider(self):
        return self
