"""
OpenAI API Client for Judicial Decision-Making Simulator.

This module provides a robust wrapper around OpenAI's API with:
- Rate limiting and exponential backoff
- Response caching for efficiency
- Token counting and budget management
- Persian error messages for UI

Now extends the abstract LLMClient base class so that OpenAI and Gemini
can be used interchangeably throughout the application.

Author: Master's Thesis Project - Mahsa Mirzaei
"""

import json
from typing import Optional, Dict, Any, List

import tiktoken
import streamlit as st
from openai import OpenAI, RateLimitError, APIError

from modules.legal_engine.base_client import LLMClient
from config.settings import get_settings


class OpenAIClient(LLMClient):
    """
    OpenAI LLM client with rate limiting, caching, and error handling.

    Implements the LLMClient interface for all interactions with OpenAI's API,
    optimized for legal reasoning tasks in Persian language.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key (overrides settings/env)
            model: Model name (overrides settings)
        """
        super().__init__()

        self.settings = get_settings()

        # Resolve API key: parameter > session_state > settings
        resolved_key = (
            api_key
            or st.session_state.get("openai_api_key")
            or self.settings.OPENAI_API_KEY
        )
        if not resolved_key:
            raise ValueError(
                "کلید API اوپن‌ای‌آی تنظیم نشده است. لطفاً در تنظیمات وارد کنید."
            )

        # Resolve model
        self._model_name = (
            model
            or st.session_state.get("ai_model")
            or self.settings.OPENAI_MODEL
        )

        self.client = OpenAI(api_key=resolved_key)

        try:
            self.encoding = tiktoken.encoding_for_model(self._model_name)
        except KeyError:
            self.encoding = tiktoken.encoding_for_model("gpt-4")

    # ─── Properties ───────────────────────────────────────────────────

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def embedding_dimension(self) -> int:
        return self.settings.EMBEDDING_DIMENSION

    # ─── Token counting ───────────────────────────────────────────────

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.

        Args:
            text: Input text (can be Persian)

        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))

    # ─── Chat completion ──────────────────────────────────────────────

    def get_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_cache: bool = True,
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
        temperature = temperature if temperature is not None else self.settings.OPENAI_TEMPERATURE
        max_tokens = max_tokens or self.settings.OPENAI_MAX_TOKENS

        # Check cache first
        cache_key = self._cache_key(prompt, temperature=temperature, max_tokens=max_tokens)
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        # API call with retry
        def _call():
            response = self.client.chat.completions.create(
                model=self._model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content

        result = self._retry_with_backoff(
            _call,
            rate_limit_exceptions=(RateLimitError,),
            api_exceptions=(APIError,),
        )

        if result and use_cache:
            self._cache[cache_key] = result
            self._save_cache()

        return result

    # ─── Structured JSON ──────────────────────────────────────────────

    def get_structured_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> Optional[Dict[str, Any]]:
        """
        Get structured JSON response using OpenAI's JSON mode.

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
                model=self._model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=temperature,
            )

            result_text = response.choices[0].message.content
            return json.loads(result_text)

        except json.JSONDecodeError as e:
            st.error(f"❌ خطا در پردازش JSON: {str(e)}")
            return None

        except Exception as e:
            st.error(f"❌ خطا در دریافت JSON: {str(e)}")
            return None

    # ─── Embeddings ───────────────────────────────────────────────────

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector for text.

        Args:
            text: Input text (Persian legal text)

        Returns:
            Embedding vector (1536 dimensions) or None if failed
        """
        try:
            response = self.client.embeddings.create(
                model=self.settings.EMBEDDING_MODEL,
                input=text,
            )
            return response.data[0].embedding

        except Exception as e:
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
                batch = texts[i : i + batch_size]
                response = self.client.embeddings.create(
                    model=self.settings.EMBEDDING_MODEL,
                    input=batch,
                )
                all_embeddings.extend([e.embedding for e in response.data])

            return all_embeddings

        except Exception as e:
            st.error(f"❌ خطا در تولید embeddings: {str(e)}")
            return None


# ─── Backward-compatible helper ──────────────────────────────────────
# Kept so that any stray imports of get_openai_client still work.

def get_openai_client() -> OpenAIClient:
    """
    Get an OpenAI client instance.

    .. deprecated::
        Use ``get_llm_client()`` from ``client_factory`` instead.
    """
    return OpenAIClient()
