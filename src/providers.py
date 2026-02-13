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
        self.working_providers = [
            {'provider': Blackbox, 'models': ['blackboxai'], 'name': 'Blackbox'},
            {'provider': Bing, 'models': ['gpt-4'], 'name': 'Bing'},
            {'provider': Liaobots, 'models': ['gpt-4o'], 'name': 'Liaobots'}
        ]
        providers_list = [p['provider'] for p in self.working_providers]
        self.client = Client(provider=RetryProvider(providers_list, shuffle=False))
        
    async def chat_completion(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        target_model = model if model and model != "auto" else "gpt-3.5-turbo"
        for provider_info in self.working_providers:
            try:
                client = Client(provider=provider_info['provider'])
                response = await asyncio.to_thread(
                    client.chat.completions.create,
                    model=provider_info['models'][0],
                    messages=messages,
                    timeout=30,
                    **kwargs
                )
                if response and response.choices:
                    return response.choices[0].message.content
            except:
                continue
        raise Exception("Semua provider gratis gagal.")

    async def generate_image(self, prompt: str, model: Optional[str] = None, **kwargs) -> str:
        raise NotImplementedError("Image generation disabled")

    def get_available_models(self) -> List[ModelInfo]:
        return [ModelInfo("blackboxai", ProviderType.FREE, "Free AI")]

    def supports_image_generation(self) -> bool:
        return False

class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = AsyncOpenAI(api_key=api_key)
    async def chat_completion(self, messages, model, **kwargs):
        res = await self.client.chat.completions.create(model=model or "gpt-4o-mini", messages=messages, **kwargs)
        return res.choices[0].message.content
    async def generate_image(self, prompt, model=None, **kwargs):
        res = await self.client.images.generate(model=model or "dall-e-3", prompt=prompt)
        return res.data[0].url
    def get_available_models(self):
        return [ModelInfo("gpt-4o-mini", ProviderType.OPENAI, "OpenAI")]
    def supports_image_generation(self): return True

class ClaudeProvider(BaseProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = AsyncAnthropic(api_key=api_key)
    async def chat_completion(self, messages, model, **kwargs):
        claude_msgs = [m for m in messages if m["role"] != "system"]
        sys = next((m["content"] for m in messages if m["role"] == "system"), None)
        res = await self.client.messages.create(model=model or "claude-3-5-haiku-latest", messages=claude_msgs, system=sys, max_tokens=4096)
        return res.content[0].text
    async def generate_image(self, p, m=None, **k): raise NotImplementedError()
    def get_available_models(self): return [ModelInfo("claude-3-5-sonnet-latest", ProviderType.CLAUDE, "Claude")]
    def supports_image_generation(self): return False

class GeminiProvider(BaseProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        genai.configure(api_key=api_key)
    async def chat_completion(self, messages, model, **kwargs):
        m = genai.GenerativeModel(model or "gemini-1.5-flash")
        res = await asyncio.to_thread(m.generate_content, messages[-1]["content"])
        return res.text
    async def generate_image(self, p, m=None, **k): raise NotImplementedError()
    def get_available_models(self): return [ModelInfo("gemini-1.5-flash", ProviderType.GEMINI, "Gemini")]
    def supports_image_generation(self): return False

class GrokProvider(BaseProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.url = "https://api.x.ai/v1/chat/completions"
    async def chat_completion(self, messages, model, **kwargs):
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with aiohttp.ClientSession() as s:
            async with s.post(self.url, headers=headers, json={"model": model or "grok-2-latest", "messages": messages}) as r:
                res = await r.json()
                return res["choices"][0]["message"]["content"]
    async def generate_image(self, p, m=None, **k): raise NotImplementedError()
    def get_available_models(self): return [ModelInfo("grok-2-latest", ProviderType.GROK, "Grok")]
    def supports_image_generation(self): return False

class ProviderManager:
    def __init__(self):
        self.providers: Dict[ProviderType, BaseProvider] = {ProviderType.FREE: FreeProvider()}
        self.current_provider = ProviderType.FREE
        self._initialize_extra()
        
    def _initialize_extra(self):
        mapping = [("OPENAI_KEY", ProviderType.OPENAI, OpenAIProvider), 
                   ("CLAUDE_KEY", ProviderType.CLAUDE, ClaudeProvider),
                   ("GEMINI_KEY", ProviderType.GEMINI, GeminiProvider),
                   ("GROK_KEY", ProviderType.GROK, GrokProvider)]
        for env, ptype, pclass in mapping:
            key = os.getenv(env)
            if key: self.providers[ptype] = pclass(key)

    def set_current_provider(self, provider_type: ProviderType):
        """Fungsi ini yang tadi hilang dan bikin error"""
        if provider_type in self.providers:
            self.current_provider = provider_type
        else:
            logger.warning(f"Provider {provider_type} tidak tersedia, tetap menggunakan {self.current_provider}")

    def get_provider(self, ptype: Optional[ProviderType] = None) -> BaseProvider:
        return self.providers.get(ptype or self.current_provider, self.providers[ProviderType.FREE])

    def get_all_models(self):
        return {pt: p.get_available_models() for pt, p in self.providers.items()}
