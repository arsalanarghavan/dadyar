"""
LLM Client Factory.

Creates and manages the active LLM client instance based on user selection.
Supports switching between OpenAI and Gemini at runtime via the sidebar UI.

Author: Master's Thesis Project - Mahsa Mirzaei
"""

from typing import Optional

import streamlit as st

from modules.legal_engine.base_client import LLMClient
from config.settings import get_settings


# Module-level instance (NOT a singleton — rebuilt when provider changes)
_client_instance: Optional[LLMClient] = None
_current_provider: Optional[str] = None
_current_model: Optional[str] = None


def get_llm_client() -> LLMClient:
    """
    Get the active LLM client based on current provider selection.

    Priority: st.session_state > settings (.env)
    Automatically rebuilds the client when provider or model changes.

    Returns:
        An LLMClient instance (OpenAIClient or GeminiClient)
    """
    global _client_instance, _current_provider, _current_model

    settings = get_settings()

    # Resolve current provider and model from session_state or settings
    provider = st.session_state.get("ai_provider", settings.AI_PROVIDER).lower()
    model = st.session_state.get("ai_model", "")

    # Check if we need to rebuild
    if (
        _client_instance is None
        or _current_provider != provider
        or (_current_model and model and _current_model != model)
    ):
        _client_instance = _build_client(provider, model)
        _current_provider = provider
        _current_model = model or _client_instance.model_name

    return _client_instance


def _build_client(provider: str, model: str = "") -> LLMClient:
    """
    Build a new LLM client for the given provider.

    Args:
        provider: 'openai' or 'gemini'
        model: Optional model override

    Returns:
        LLMClient instance
    """
    if provider == "gemini":
        from modules.legal_engine.gemini_client import GeminiClient
        return GeminiClient(model=model or None)
    else:
        from modules.legal_engine.openai_client import OpenAIClient
        return OpenAIClient(model=model or None)


def reset_client():
    """
    Force-reset the cached client instance AND all downstream singletons.

    Call this when user changes provider/model/API-key in sidebar
    so that the next get_llm_client() call creates a fresh client.
    """
    global _client_instance, _current_provider, _current_model
    _client_instance = None
    _current_provider = None
    _current_model = None

    # Reset all downstream singletons that hold a reference to the old client
    _reset_downstream_singletons()


def _reset_downstream_singletons():
    """Clear cached singletons in entity_extractor, reasoning_engine, verdict_generator, knowledge_base."""
    import modules.legal_engine.entity_extractor as _ee
    import modules.legal_engine.reasoning_engine as _re
    import modules.legal_engine.verdict_generator as _vg

    _ee._extractor_instance = None
    _re._engine_instance = None
    _vg._verdict_instance = None

    # Clear the Streamlit-cached knowledge base so FAISS index is rebuilt
    try:
        from modules.legal_engine.knowledge_base import get_knowledge_base
        get_knowledge_base.clear()
    except Exception:
        pass
