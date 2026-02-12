"""
Configuration settings for the Judicial Decision-Making Simulator.

This module uses Pydantic Settings for type-safe configuration management.
All settings can be overridden via environment variables defined in .env file.

Author: Master's Thesis Project - Mahsa Mirzaei
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    For Master's Thesis: This centralizes all configuration, making the system
    easily adaptable for different deployment environments or experimental setups.
    """

    # =================================================================
    # OpenAI Configuration
    # =================================================================
    OPENAI_API_KEY: str  # Required: Your OpenAI API key
    OPENAI_MODEL: str = "gpt-4-turbo-preview"  # Default to GPT-4 Turbo for best reasoning
    OPENAI_TEMPERATURE: float = 0.3  # Low temperature for consistent legal reasoning
    OPENAI_MAX_TOKENS: int = 2000  # Maximum tokens per completion

    # =================================================================
    # Embedding Configuration (for RAG)
    # =================================================================
    EMBEDDING_MODEL: str = "text-embedding-3-small"  # OpenAI embedding model
    EMBEDDING_DIMENSION: int = 1536  # Dimension of embedding vectors

    # =================================================================
    # RAG (Retrieval-Augmented Generation) Configuration
    # =================================================================
    TOP_K_ARTICLES: int = 5  # Number of articles to retrieve from knowledge base
    SIMILARITY_THRESHOLD: float = 0.7  # Minimum similarity score for relevance

    # =================================================================
    # UI Configuration
    # =================================================================
    APP_TITLE: str = "سیستم هوشمند شبیه‌سازی تصمیم‌گیری قضایی"  # Persian title
    THEME_PRIMARY_COLOR: str = "#020617"  # Dark background (shadcn inspired)
    RTL_ENABLED: bool = True  # Enable Right-to-Left layout for Persian

    # =================================================================
    # Persian Font Configuration
    # =================================================================
    FONT_FAMILY: str = "Vazir, IRANSans, Tahoma"  # Font stack for Persian text

    # =================================================================
    # Graph Visualization Configuration
    # =================================================================
    GRAPH_WIDTH: int = 1200  # Width of reasoning graph in pixels
    GRAPH_HEIGHT: int = 800  # Height of reasoning graph in pixels

    # =================================================================
    # Node Colors for Reasoning Graph (shadcn color palette)
    # =================================================================
    NODE_COLOR_FACT: str = "#3b82f6"  # Blue for facts
    NODE_COLOR_ARTICLE: str = "#10b981"  # Green for legal articles
    NODE_COLOR_DEDUCTION: str = "#f59e0b"  # Yellow for deductions
    NODE_COLOR_VERDICT: str = "#ef4444"  # Red for final verdict

    class Config:
        """Pydantic configuration"""
        env_file = ".env"  # Load from .env file
        env_file_encoding = "utf-8"  # Support Persian text in .env
        case_sensitive = True  # Environment variable names are case-sensitive


# Global settings instance
# This singleton ensures configuration is loaded once and reused throughout the application
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance.

    Returns:
        Settings: The application settings singleton

    Note:
        For thesis purposes: This lazy initialization pattern ensures settings
        are validated once at startup and any missing required variables
        (like OPENAI_API_KEY) will raise clear errors immediately.
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
