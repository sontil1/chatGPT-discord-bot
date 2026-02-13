import g4f
from enum import Enum
from src.log import logger

class ProviderType(Enum):
    FREE = "free"

class ProviderManager:
    def __init__(self):
        # Kita set ke None agar sistem otomatis memilih yang aktif
        self.current_provider = None

    async def chat_completion(self, messages, model=None):
        # Daftar nama provider dalam bentuk teks (string) agar tidak error attribute
        provider_names = ["Bing", "DuckDuckGo", "Blackbox", "Liaobots", "FreeChatgpt"]
        
        for name in provider_names:
            try:
                logger.info(f"Mencoba provider: {name}")
                # Memanggil provider berdasarkan nama string
                provider_obj = getattr(g4f.Provider, name, None)
                
                if provider_obj:
                    response = await g4f.ChatCompletion.create_async(
                        model=g4f.models.default,
                        messages=messages,
                        provider=provider_obj
                    )
                    if response and len(str(response)) > 0:
                        return response
                else:
                    continue
                    
            except Exception as e:
                logger.error(f"Provider {name} gagal: {e}")
                continue
        
        raise Exception("Semua provider sedang sibuk.")

    def get_provider(self):
        return self

    def set_current_provider(self, provider_type):
        pass
