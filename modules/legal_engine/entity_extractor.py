"""
Entity Extractor for Legal Cases.

Extracts key information from Persian legal case descriptions using
OpenAI GPT with structured output (JSON mode).

Entities extracted:
- Plaintiff (خواهان)
- Defendant (خوانده)
- Case type (نوع پرونده)
- Property type (نوع ملک)
- Incident date (تاریخ وقوع)
- Claims (ادعاها)
- Evidence (شواهد)
- Key facts (واقعیات کلیدی)

Author: Master's Thesis Project - Mahsa Mirzaei
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import streamlit as st
from hazm import Normalizer

from modules.legal_engine.openai_client import get_openai_client
from config.prompts import ENTITY_EXTRACTION_PROMPT


class CaseEntities(BaseModel):
    """
    Structured representation of extracted case entities.

    Using Pydantic for type safety and validation.
    """
    plaintiff: Optional[str] = Field(None, description="نام خواهان")
    defendant: Optional[str] = Field(None, description="نام خوانده")
    case_type: Optional[str] = Field(None, description="نوع پرونده (غصب، خلع ید، ...)")
    property_type: Optional[str] = Field(None, description="نوع ملک یا مال")
    incident_date: Optional[str] = Field(None, description="تاریخ وقوع")
    claims: List[str] = Field(default_factory=list, description="ادعاهای خواهان")
    evidence: List[str] = Field(default_factory=list, description="شواهد و مدارک")
    key_facts: List[str] = Field(default_factory=list, description="واقعیات مهم")


class EntityExtractor:
    """
    Extract entities from Persian legal case descriptions.
    """

    def __init__(self):
        """Initialize extractor with OpenAI client and Persian normalizer."""
        self.client = get_openai_client()
        self.normalizer = Normalizer()

    def extract(self, case_description: str) -> Optional[CaseEntities]:
        """
        Extract entities from case description.

        Args:
            case_description: Persian text describing the legal case

        Returns:
            CaseEntities object or None if extraction failed
        """
        # Normalize Persian text
        normalized_text = self.normalizer.normalize(case_description)

        # Format prompt
        prompt = ENTITY_EXTRACTION_PROMPT.format(case_description=normalized_text)

        # Get structured JSON response
        result = self.client.get_structured_json(
            prompt=prompt,
            temperature=0.1  # Low temperature for consistency
        )

        if not result:
            st.error("❌ خطا در استخراج اطلاعات پرونده")
            return None

        try:
            # Parse into Pydantic model
            entities = CaseEntities(**result)
            return entities

        except Exception as e:
            st.error(f"❌ خطا در پردازش اطلاعات استخراج شده: {str(e)}")
            return None

    def extract_with_validation(self, case_description: str) -> tuple[Optional[CaseEntities], List[str]]:
        """
        Extract entities and return validation warnings.

        Args:
            case_description: Case description text

        Returns:
            Tuple of (entities, warnings)
        """
        entities = self.extract(case_description)
        warnings = []

        if not entities:
            return None, ["استخراج اطلاعات ناموفق بود"]

        # Validation warnings
        if not entities.plaintiff:
            warnings.append("⚠️ نام خواهان مشخص نیست")

        if not entities.defendant:
            warnings.append("⚠️ نام خوانده مشخص نیست")

        if not entities.case_type:
            warnings.append("⚠️ نوع پرونده مشخص نیست")

        if not entities.claims:
            warnings.append("⚠️ ادعاهای خواهان مشخص نیست")

        if not entities.key_facts:
            warnings.append("⚠️ واقعیات پرونده ناقص است")

        return entities, warnings

    def format_entities_display(self, entities: CaseEntities) -> str:
        """
        Format entities for display in UI.

        Args:
            entities: Extracted entities

        Returns:
            Formatted Persian text
        """
        parts = []

        if entities.plaintiff:
            parts.append(f"**خواهان:** {entities.plaintiff}")

        if entities.defendant:
            parts.append(f"**خوانده:** {entities.defendant}")

        if entities.case_type:
            parts.append(f"**نوع پرونده:** {entities.case_type}")

        if entities.property_type:
            parts.append(f"**نوع ملک/مال:** {entities.property_type}")

        if entities.incident_date:
            parts.append(f"**تاریخ وقوع:** {entities.incident_date}")

        if entities.claims:
            parts.append("**ادعاهای خواهان:**")
            for i, claim in enumerate(entities.claims, 1):
                parts.append(f"  {i}. {claim}")

        if entities.evidence:
            parts.append("**شواهد و مدارک:**")
            for i, ev in enumerate(entities.evidence, 1):
                parts.append(f"  {i}. {ev}")

        if entities.key_facts:
            parts.append("**واقعیات کلیدی:**")
            for i, fact in enumerate(entities.key_facts, 1):
                parts.append(f"  {i}. {fact}")

        return "\n\n".join(parts)


# Global instance
_extractor_instance: Optional[EntityExtractor] = None

def get_entity_extractor() -> EntityExtractor:
    """
    Get global entity extractor instance.

    Returns:
        EntityExtractor singleton
    """
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = EntityExtractor()
    return _extractor_instance
