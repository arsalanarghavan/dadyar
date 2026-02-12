"""
Persian Text Utilities - RTL and Formatting Helpers.

Provides utilities for handling Persian text in Streamlit:
- RTL text wrapping
- Persian number conversion
- Date formatting with jdatetime
- ZWNJ handling

Author: Master's Thesis Project - Mahsa Mirzaei
"""

import jdatetime
from typing import Optional
from hazm import Normalizer


class PersianUtils:
    """Utilities for Persian text processing and display."""

    def __init__(self):
        """Initialize with Hazm normalizer."""
        self.normalizer = Normalizer()

    @staticmethod
    def rtl_wrapper(text: str, tag: str = "div") -> str:
        """
        Wrap text in RTL container.

        Args:
            text: Persian text
            tag: HTML tag (div, span, p)

        Returns:
            HTML string with RTL direction
        """
        return f'<{tag} dir="rtl" style="text-align: right;">{text}</{tag}>'

    @staticmethod
    def to_persian_numbers(text: str) -> str:
        """
        Convert Latin numbers to Persian numbers.

        Args:
            text: Text with Latin numbers (0-9)

        Returns:
            Text with Persian numbers (۰-۹)
        """
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        latin_digits = '0123456789'

        translation_table = str.maketrans(latin_digits, persian_digits)
        return text.translate(translation_table)

    @staticmethod
    def to_latin_numbers(text: str) -> str:
        """
        Convert Persian numbers to Latin numbers.

        Args:
            text: Text with Persian numbers (۰-۹)

        Returns:
            Text with Latin numbers (0-9)
        """
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        latin_digits = '0123456789'

        translation_table = str.maketrans(persian_digits, latin_digits)
        return text.translate(translation_table)

    @staticmethod
    def format_persian_date(date: Optional[jdatetime.date] = None) -> str:
        """
        Format date in Persian calendar.

        Args:
            date: jdatetime date object (defaults to today)

        Returns:
            Formatted Persian date string (e.g., "۱۴۰۳/۱۱/۲۳")
        """
        if date is None:
            date = jdatetime.date.today()

        # Format as YYYY/MM/DD
        formatted = date.strftime("%Y/%m/%d")

        # Convert to Persian numbers
        return PersianUtils.to_persian_numbers(formatted)

    def normalize(self, text: str) -> str:
        """
        Normalize Persian text using Hazm.

        Fixes:
        - ZWNJ (Zero-Width Non-Joiner)
        - Arabic characters to Persian
        - Multiple spaces
        - Punctuation

        Args:
            text: Raw Persian text

        Returns:
            Normalized text
        """
        return self.normalizer.normalize(text)

    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """
        Truncate text to maximum length.

        Args:
            text: Input text
            max_length: Maximum length
            suffix: Suffix to add if truncated

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text

        return text[:max_length - len(suffix)] + suffix

    @staticmethod
    def format_confidence(confidence: float) -> str:
        """
        Format confidence score as Persian percentage.

        Args:
            confidence: Confidence score (0-1)

        Returns:
            Formatted percentage (e.g., "۸۵٪")
        """
        percentage = int(confidence * 100)
        persian_num = PersianUtils.to_persian_numbers(str(percentage))
        return f"{persian_num}٪"

    @staticmethod
    def create_card_html(title: str, content: str, color: str = "#3b82f6") -> str:
        """
        Create styled card HTML for Streamlit.

        Args:
            title: Card title
            content: Card content
            color: Accent color

        Returns:
            HTML string
        """
        return f"""
        <div style="
            background: #0f172a;
            border: 1px solid #334155;
            border-right: 4px solid {color};
            border-radius: 0.5rem;
            padding: 1.5rem;
            margin-bottom: 1rem;
            direction: rtl;
            text-align: right;
        ">
            <h3 style="
                color: #f8fafc;
                margin-top: 0;
                margin-bottom: 0.5rem;
                font-size: 1.25rem;
            ">{title}</h3>
            <p style="
                color: #cbd5e1;
                margin: 0;
                line-height: 1.6;
            ">{content}</p>
        </div>
        """

    @staticmethod
    def create_badge(text: str, color: str = "#3b82f6") -> str:
        """
        Create badge/chip HTML.

        Args:
            text: Badge text
            color: Background color

        Returns:
            HTML string
        """
        return f"""
        <span style="
            background: {color};
            color: #f8fafc;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 600;
            display: inline-block;
            margin: 0.25rem;
        ">{text}</span>
        """


# Global instance
_utils_instance: Optional[PersianUtils] = None

def get_persian_utils() -> PersianUtils:
    """
    Get global PersianUtils instance.

    Returns:
        PersianUtils singleton
    """
    global _utils_instance
    if _utils_instance is None:
        _utils_instance = PersianUtils()
    return _utils_instance
