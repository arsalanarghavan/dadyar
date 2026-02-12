"""
OpenAI API Client for Judicial Decision-Making Simulator.

This module provides a robust wrapper around OpenAI's API with:
- Rate limiting and exponential backoff
- Response caching for efficiency
- Token counting and budget management
- Persian error messages for UI
- Singleton pattern for API client

Author: Master's Thesis Project - Mahsa Mirzaei
"""

import openai
from openai import OpenAI, RateLimitError, APIError
import tiktoken
import time
import hashlib
import json
from typing import Optional, Dict, Any, List
import streamlit as st
from pathlib import Path
from config.settings import get_settings


class OpenAIClient:
    """
    Singleton OpenAI client with rate limiting, caching, and error handling.

    This class manages all interactions with OpenAI's API, optimized for
    legal reasoning tasks in Persian language.
    """

    _instance: Optional['OpenAIClient'] = None
    _cache: Dict[str, Any] = {}
    _cache_file: Path = Path("data/openai_cache.json")

    def __new__(cls):
        """Ensure singleton pattern - only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize OpenAI client with settings."""
        if hasattr(self, '_initialized'):
            return

        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
        self.encoding = tiktoken.encoding_for_model("gpt-4")

        # Load cache from disk if exists
        self._load_cache()

        self._initialized = True

    def _load_cache(self):
        """Load response cache from disk."""
        try:
            if self._cache_file.exists():
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
        except Exception as e:
            print(f"Failed to load cache: {e}")
            self._cache = {}

    def _save_cache(self):
        """Save response cache to disk."""
        try:
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save cache: {e}")

    def _cache_key(self, prompt: str, **kwargs) -> str:
        """Generate cache key from prompt and parameters."""
        key_data = f"{prompt}_{kwargs.get('temperature', 0.3)}_{kwargs.get('max_tokens', 2000)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.

        Args:
            text: Input text (can be Persian)

        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))

    def get_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Get completion from OpenAI with retry logic and caching.

        Args:
            prompt: User prompt (in Persian)
            system_prompt: System prompt (optional, defaults to legal expert)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            use_cache: Whether to use cached responses

        Returns:
            Generated text or None if failed
        """
        # Use default system prompt if not provided
        if system_prompt is None:
            from config.prompts import LEGAL_EXPERT_SYSTEM_PROMPT
            system_prompt = LEGAL_EXPERT_SYSTEM_PROMPT

        # Use settings defaults if not specified
        temperature = temperature or self.settings.OPENAI_TEMPERATURE
        max_tokens = max_tokens or self.settings.OPENAI_MAX_TOKENS

        # Check cache first
        cache_key = self._cache_key(prompt, temperature=temperature, max_tokens=max_tokens)
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        # Retry logic with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                result = response.choices[0].message.content

                # Cache the result
                if use_cache:
                    self._cache[cache_key] = result
                    self._save_cache()

                return result

            except RateLimitError:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                if 'st' in globals():
                    st.warning(f"⏳ به حد مجاز API رسیدیم. {wait_time} ثانیه صبر کنید...")
                time.sleep(wait_time)

            except APIError as e:
                if attempt == max_retries - 1:
                    if 'st' in globals():
                        st.error(f"❌ خطا در ارتباط با OpenAI: {str(e)}")
                    return None
                time.sleep(2 ** attempt)

            except Exception as e:
                if 'st' in globals():
                    st.error(f"❌ خطای غیرمنتظره: {str(e)}")
                return None

        return None

    def get_structured_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1
    ) -> Optional[Dict[str, Any]]:
        """
        Get structured JSON response using OpenAI's JSON mode.

        Useful for entity extraction and structured data.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            temperature: Low temperature for consistency

        Returns:
            Parsed JSON dict or None if failed
        """
        if system_prompt is None:
            system_prompt = "شما باید خروجی را به صورت JSON معتبر ارائه دهید."

        try:
            response = self.client.chat.completions.create(
                model=self.settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=temperature
            )

            result_text = response.choices[0].message.content
            return json.loads(result_text)

        except json.JSONDecodeError as e:
            if 'st' in globals():
                st.error(f"❌ خطا در پردازش JSON: {str(e)}")
            return None

        except Exception as e:
            if 'st' in globals():
                st.error(f"❌ خطا در دریافت JSON: {str(e)}")
            return None

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector for text.

        Used for RAG (Retrieval-Augmented Generation) to find similar
        legal articles.

        Args:
            text: Input text (Persian legal text)

        Returns:
            Embedding vector (1536 dimensions) or None if failed
        """
        try:
            response = self.client.embeddings.create(
                model=self.settings.EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding

        except Exception as e:
            if 'st' in globals():
                st.error(f"❌ خطا در تولید embedding: {str(e)}")
            return None

    def get_embeddings_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors or None if failed
        """
        try:
            # Process in batches of 100 (OpenAI limit)
            batch_size = 100
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                response = self.client.embeddings.create(
                    model=self.settings.EMBEDDING_MODEL,
                    input=batch
                )
                all_embeddings.extend([e.embedding for e in response.data])

            return all_embeddings

        except Exception as e:
            if 'st' in globals():
                st.error(f"❌ خطا در تولید embeddings: {str(e)}")
            return None

    def clear_cache(self):
        """Clear the response cache."""
        self._cache = {}
        if self._cache_file.exists():
            self._cache_file.unlink()


# Global instance getter
_client_instance: Optional[OpenAIClient] = None

def get_openai_client() -> OpenAIClient:
    """
    Get the global OpenAI client instance.

    Returns:
        OpenAIClient singleton
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = OpenAIClient()
    return _client_instance
