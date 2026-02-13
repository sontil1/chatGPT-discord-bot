import os
import logging
import re
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import asyncio

import g4f
from g4f.client import Client
from g4f.Provider import RetryProvider, Blackbox, Bing, Liaobots
from openai import AsyncOpenAI
import google.generativeai as genai
from anthropic import AsyncAnthropic
import aiohttp

logger = logging.getLogger(__name__)

class ProviderType(Enum):
    FREE = "free"
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"
    GROK = "grok"

@dataclass
class ModelInfo:
    name: str
    provider: ProviderType
    description: str = ""
    supports_vision: bool = False
    supports_image_generation: bool = False

class BaseProvider(ABC):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.models: List[ModelInfo] = []
        
    @abstractmethod
    async def chat_completion(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    async def generate_image(self, prompt: str, model: Optional[str] = None, **kwargs) -> str:
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[ModelInfo]:
        pass
    
    @abstractmethod
    def supports_image_generation(self) -> bool:
        pass

class FreeProvider(BaseProvider):
    def __init__(self):
        super().__init__()
        
        # HANYA gunakan provider yang benar-benar ada di library g4f terbaru
        self.working_providers = [
            {
                'provider': Blackbox,
                'models': ['blackboxai'],
                'name': 'Blackbox'
            },
            {
                'provider': Bing,
                'models': ['gpt-4'],
                'name': 'Bing'
            },
            {
                'provider': Liaobots,
                'models': ['gpt-4o', 'gpt-4o-mini'],
                'name': 'Liaobots'
            }
        ]
        
        providers_list = [p['provider'] for p in self.working_providers]
        self.client = Client(provider=RetryProvider(providers_list, shuffle=False))
        
    async def chat_completion(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        target_model = self._select_model(model)
        for attempt in range(len(self.working_providers)):
            provider_info = self.working_providers[attempt]
            try:
                provider_model = self._get_provider_model(provider_info, target_model)
                client = Client(provider=provider_info['provider'])
                response = await asyncio.to_thread(
                    client.chat.completions.create,
                    model=provider_model,
                    messages=messages,
                    timeout=30,
                    **kwargs
                )
                if response and response.choices:
                    return response.choices[0].message.content
            except Exception as e:
                continue
        raise Exception("Semua provider gratis gagal.")

    def _select_model(self, model: Optional[str]) -> str:
        return model if model and model != "auto" else "gpt-3.5-turbo"

    def _get_provider_model(self, provider_info: dict, target_model: str) -> str:
        return provider_info['models'][0]

    async def generate_image(self, prompt: str, model: Optional[str] = None, **kwargs) -> str:
        raise NotImplementedError("Image generation disabled for stability")

    def get_available_models(self) -> List[ModelInfo]:
        return [ModelInfo("blackboxai", ProviderType.FREE, "Blackbox AI")]

    def supports_image_generation(self) -> bool:
        return False

# ... (Sisa kode OpenAIProvider, ClaudeProvider, dll tetap sama di bawah) ...
# Agar pesan tidak terlalu panjang, saya asumsikan kamu bisa menempelkan sisa kodenya 
# atau cukup ganti bagian FreeProvider saja jika kamu mengerti strukturnya.
