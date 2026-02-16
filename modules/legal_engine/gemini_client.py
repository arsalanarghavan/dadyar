"""
Google Gemini API Client for Judicial Decision-Making Simulator.

Implements LLMClient interface using Google's new GenAI SDK (google-genai).
Gemini 2.0 Flash is free-tier and provides a great alternative to GPT-4.

Author: Master's Thesis Project - Mahsa Mirzaei
"""

import json
from typing import Optional, Dict, Any, List

import streamlit as st

from modules.legal_engine.base_client import LLMClient
from config.settings import get_settings


class GeminiClient(LLMClient):
    """
    Gemini LLM client with rate limiting, caching, and error handling.

    Free-tier limits (Gemini 2.0 Flash):
    - 15 requests per minute
    - 1 million tokens per day
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Gemini client.

        Args:
            api_key: Gemini API key (overrides settings/env)
            model: Model name (overrides settings)
        """
        super().__init__()

        self.settings = get_settings()

        # Resolve API key: parameter > session_state > settings
        self._api_key = (
            api_key
            or st.session_state.get("gemini_api_key")
            or self.settings.GEMINI_API_KEY
        )
        if not self._api_key:
            raise ValueError(
                "کلید API جمینای تنظیم نشده است. لطفاً در تنظیمات وارد کنید."
            )

        # Resolve model
        self._model_name = (
            model
            or st.session_state.get("ai_model")
            or self.settings.GEMINI_MODEL
        )

        self._embedding_model = self.settings.GEMINI_EMBEDDING_MODEL

        # Import and configure SDK (new google-genai package)
        try:
            from google import genai
            from google.genai import types as genai_types
            from google.api_core import exceptions as google_exceptions
        except ImportError:
            raise ImportError(
                "پکیج google-genai نصب نیست. "
                "لطفاً اجرا کنید: pip install google-genai"
            )

        self._google_exceptions = google_exceptions
        self._genai_types = genai_types

        # Create client instance (replaces old genai.configure() pattern)
        try:
            self._client = genai.Client(api_key=self._api_key)
        except ImportError as e:
            if "socks" in str(e).lower():
                raise ImportError(
                    "پروکسی SOCKS شناسایی شد ولی پکیج socksio نصب نیست. "
                    "لطفاً اجرا کنید: pip install httpx[socks]"
                ) from e
            raise

    # ─── Properties ───────────────────────────────────────────────────

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def embedding_dimension(self) -> int:
        return self.settings.GEMINI_EMBEDDING_DIMENSION

    # ─── Chat completion ──────────────────────────────────────────────

    def get_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_cache: bool = True,
    ) -> Optional[str]:
        """Get text completion from Gemini."""
        if system_prompt is None:
            from config.prompts import LEGAL_EXPERT_SYSTEM_PROMPT
            system_prompt = LEGAL_EXPERT_SYSTEM_PROMPT

        temperature = temperature if temperature is not None else self.settings.OPENAI_TEMPERATURE  # shared default
        max_tokens = max_tokens or self.settings.OPENAI_MAX_TOKENS  # shared default

        # Check cache
        cache_key = self._cache_key(prompt, temperature=temperature, max_tokens=max_tokens)
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        def _call():
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=prompt,
                config=self._genai_types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            return response.text

        result = self._retry_with_backoff(
            _call,
            rate_limit_exceptions=(self._google_exceptions.ResourceExhausted,),
            api_exceptions=(
                self._google_exceptions.GoogleAPIError,
                self._google_exceptions.InvalidArgument,
            ),
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
        """Get structured JSON response from Gemini."""
        if system_prompt is None:
            system_prompt = "شما باید خروجی را به صورت JSON معتبر ارائه دهید."

        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=prompt,
                config=self._genai_types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    response_mime_type="application/json",
                ),
            )
            return json.loads(response.text)

        except json.JSONDecodeError as e:
            st.error(f"❌ خطا در پردازش JSON: {str(e)}")
            return None
        except self._google_exceptions.ResourceExhausted as e:
            st.error(
                "❌ سهمیه API تمام شده. چند دقیقه صبر کنید یا "
                "از تنظیمات سایدبار API Key دیگری وارد کنید."
            )
            return None
        except Exception as e:
            st.error(f"❌ خطا در دریافت JSON از Gemini: {str(e)}")
            return None

    # ─── Embeddings ───────────────────────────────────────────────────

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding vector using Gemini embedding model."""
        try:
            result = self._client.models.embed_content(
                model=self._embedding_model,
                contents=text,
                config=self._genai_types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                ),
            )
            return result.embeddings[0].values
        except Exception as e:
            st.error(f"❌ خطا در تولید embedding (Gemini): {str(e)}")
            return None

    def get_embeddings_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Generate embeddings for multiple texts."""
        try:
            all_embeddings = []
            for text in texts:
                emb = self.get_embedding(text)
                if emb:
                    all_embeddings.append(emb)
                else:
                    all_embeddings.append([0.0] * self.embedding_dimension)
            return all_embeddings
        except Exception as e:
            st.error(f"❌ خطا در تولید embeddings (Gemini): {str(e)}")
            return None

    # ─── Token counting ───────────────────────────────────────────────

    def count_tokens(self, text: str) -> int:
        """Count tokens using Gemini's built-in tokenizer."""
        try:
            result = self._client.models.count_tokens(
                model=self._model_name,
                contents=text,
            )
            return result.total_tokens
        except Exception:
            # Rough estimate: ~4 chars per token for Persian
            return len(text) // 4
