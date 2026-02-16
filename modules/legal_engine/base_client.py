"""
Abstract Base Client for LLM Providers.

Defines the interface that all LLM providers (OpenAI, Gemini, etc.) must implement.
Includes shared caching logic and common utilities.

Author: Master's Thesis Project - Mahsa Mirzaei
"""

import hashlib
import json
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, List

import streamlit as st


class LLMClient(ABC):
    """
    Abstract base class for LLM API clients.

    All providers must implement:
    - get_completion(): Chat completions
    - get_structured_json(): JSON-mode completions
    - get_embedding(): Single text embedding
    - get_embeddings_batch(): Batch text embeddings
    - count_tokens(): Token counting
    - provider_name: Name of the provider
    - model_name: Current model name
    - embedding_dimension: Dimension of embedding vectors
    """

    _cache: Dict[str, Any] = {}
    _cache_file: Path = Path(__file__).resolve().parent.parent.parent / "data" / "llm_cache.json"

    def __init__(self):
        """Initialize shared cache."""
        self._load_cache()

    # ─── Abstract properties ──────────────────────────────────────────

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier, e.g. 'openai' or 'gemini'."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return current model name."""
        ...

    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Return embedding vector dimension for this provider."""
        ...

    # ─── Abstract methods ─────────────────────────────────────────────

    @abstractmethod
    def get_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_cache: bool = True,
    ) -> Optional[str]:
        """Get text completion from the LLM."""
        ...

    @abstractmethod
    def get_structured_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> Optional[Dict[str, Any]]:
        """Get structured JSON response from the LLM."""
        ...

    @abstractmethod
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding vector for a single text."""
        ...

    @abstractmethod
    def get_embeddings_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Generate embeddings for multiple texts."""
        ...

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        ...

    # ─── Shared cache helpers ─────────────────────────────────────────

    def _cache_key(self, prompt: str, **kwargs) -> str:
        """Generate a cache key that includes provider + model."""
        key_data = (
            f"{self.provider_name}_{self.model_name}_"
            f"{prompt}_{kwargs.get('temperature', 0.3)}_{kwargs.get('max_tokens', 2000)}"
        )
        return hashlib.md5(key_data.encode()).hexdigest()

    def _load_cache(self):
        """Load response cache from disk."""
        try:
            if self._cache_file.exists():
                with open(self._cache_file, "r", encoding="utf-8") as f:
                    LLMClient._cache = json.load(f)
        except Exception as e:
            print(f"Failed to load cache: {e}")
            LLMClient._cache = {}

    def _save_cache(self):
        """Save response cache to disk."""
        try:
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._cache_file, "w", encoding="utf-8") as f:
                json.dump(LLMClient._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save cache: {e}")

    def clear_cache(self):
        """Clear the response cache."""
        LLMClient._cache = {}
        if self._cache_file.exists():
            self._cache_file.unlink()

    # ─── Shared retry helper ─────────────────────────────────────────

    def _retry_with_backoff(self, func, max_retries: int = 3, rate_limit_exceptions=(), api_exceptions=()):
        """
        Execute *func* with exponential-backoff retry.

        Args:
            func: Callable that performs the API request and returns a result.
            max_retries: Maximum number of attempts.
            rate_limit_exceptions: Exception classes that indicate rate limiting.
            api_exceptions: Exception classes for generic API errors.

        Returns:
            The result of *func*, or None on total failure.
        """
        for attempt in range(max_retries):
            try:
                return func()
            except rate_limit_exceptions as e:
                err_msg = str(e).lower()
                # Don't retry on quota exhaustion — it won't resolve with waiting
                if "resource_exhausted" in err_msg or "quota" in err_msg:
                    st.error(
                        "❌ سهمیه API تمام شده. چند دقیقه صبر کنید یا "
                        "از تنظیمات سایدبار API Key دیگری وارد کنید."
                    )
                    return None
                wait_time = 2 ** attempt + 1
                st.warning(f"⏳ محدودیت نرخ API. {wait_time} ثانیه صبر کنید...")
                time.sleep(wait_time)
            except api_exceptions as e:
                if attempt == max_retries - 1:
                    st.error(f"❌ خطا در ارتباط با {self.provider_name}: {str(e)}")
                    return None
                time.sleep(2 ** attempt)
            except Exception as e:
                st.error(f"❌ خطای غیرمنتظره ({self.provider_name}): {str(e)}")
                return None
        return None
