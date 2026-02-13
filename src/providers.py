import g4f
from enum import Enum
from src.log import logger

class ProviderType(Enum):
    FREE = "free"

class ProviderManager:
    def __init__(self):
        # Gunakan huruf kecil 'bing'
        self.current_provider = g4f.Provider.bing

    async def chat_completion(self, messages, model=None):
        # Daftar provider dengan penulisan yang benar (huruf kecil)
        providers = [
            g4f.Provider.bing,
            g4f.Provider.DuckDuckGo,
            g4f.Provider.Liaobots,
            g4f.Provider.FreeNetfly
        ]
        
        for provider in providers:
            try:
                response = await g4f.ChatCompletion.create_async(
                    model=g4f.models.default,
                    messages=messages,
                    provider=provider
                )
                if response and len(response) > 0:
                    return response
            except Exception as e:
                logger.error(f"Provider {provider.__name__} gagal, mencoba yang lain...")
                continue
        
        raise Exception("Semua provider sedang sibuk.")

    def get_provider(self):
        return self

    def set_current_provider(self, provider_type):
        pass
