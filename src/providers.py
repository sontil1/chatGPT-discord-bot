import g4f
from enum import Enum
from src.log import logger

class ProviderType(Enum):
    FREE = "free"

class ProviderManager:
    def __init__(self):
        # Gunakan huruf kecil semua
        self.current_provider = g4f.Provider.bing

    async def chat_completion(self, messages, model=None):
        # Daftar provider stabil dengan format huruf kecil semua
        providers = [
            g4f.Provider.bing,
            g4f.Provider.duckduckgo,
            g4f.Provider.blackbox,
            g4f.Provider.liaobots,
            g4f.Provider.yqcloud
        ]
        
        for provider in providers:
            try:
                logger.info(f"Mencoba provider: {provider.__name__}")
                response = await g4f.ChatCompletion.create_async(
                    model=g4f.models.default,
                    messages=messages,
                    provider=provider
                )
                if response and len(str(response)) > 0:
                    return response
            except Exception as e:
                logger.error(f"Provider {provider.__name__} gagal, geser ke berikutnya...")
                continue
        
        raise Exception("Semua provider sedang sibuk.")

    def get_provider(self):
        return self

    def set_current_provider(self, provider_type):
        pass
