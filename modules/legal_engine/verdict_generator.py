"""
Verdict Generator - Final Judicial Decision Synthesis.

Generates formal legal verdicts based on reasoning chain analysis.
Outputs structured verdict with:
- Case summary
- Proven facts
- Legal analysis
- Final ruling
- Implementation details

Author: Master's Thesis Project - Mahsa Mirzaei
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
import streamlit as st

from modules.legal_engine.openai_client import get_openai_client
from modules.legal_engine.reasoning_engine import ReasoningResult
from config.prompts import VERDICT_GENERATION_PROMPT


@dataclass
class Verdict:
    """
    Structured verdict document.
    """
    case_id: str
    summary: str  # خلاصه پرونده
    proven_facts: str  # واقعیات اثبات شده
    legal_analysis: str  # تحلیل حقوقی
    ruling: str  # حکم نهایی
    implementation: str  # جزئیات اجرایی
    appealable: str  # قابلیت اعتراض
    confidence: float  # سطح اطمینان


class VerdictGenerator:
    """
    Generate formal legal verdicts from reasoning results.
    """

    def __init__(self):
        """Initialize verdict generator with OpenAI client."""
        self.client = get_openai_client()

    def generate_verdict(self, reasoning_result: ReasoningResult) -> Optional[Verdict]:
        """
        Generate formal verdict from reasoning result.

        Args:
            reasoning_result: Complete reasoning analysis

        Returns:
            Verdict object or None if generation failed
        """
        st.info("📜 در حال تولید حکم نهایی...")

        # Prepare reasoning chain text
        reasoning_chain = self._format_reasoning_chain(reasoning_result)

        # Prepare case facts
        case_facts = "\n".join([f"- {fact}" for fact in reasoning_result.entities.key_facts])

        # Get plaintiff and defendant
        plaintiff = reasoning_result.entities.plaintiff or "نامشخص"
        defendant = reasoning_result.entities.defendant or "نامشخص"

        # Format prompt
        prompt = VERDICT_GENERATION_PROMPT.format(
            reasoning_chain=reasoning_chain,
            case_facts=case_facts,
            plaintiff=plaintiff,
            defendant=defendant
        )

        # Generate verdict
        verdict_text = self.client.get_completion(
            prompt=prompt,
            temperature=0.2,  # Very low temperature for formal legal language
            max_tokens=3000  # Allow longer response for complete verdict
        )

        if not verdict_text:
            st.error("❌ خطا در تولید حکم")
            return None

        # Parse verdict into structured format
        verdict = self._parse_verdict(
            verdict_text=verdict_text,
            case_id=reasoning_result.case_id,
            confidence=reasoning_result.overall_confidence
        )

        if verdict:
            st.success("✅ حکم نهایی صادر شد")

        return verdict

    def _format_reasoning_chain(self, result: ReasoningResult) -> str:
        """
        Format reasoning chain for verdict generation.

        Args:
            result: Reasoning result

        Returns:
            Formatted text
        """
        parts = []

        # Facts
        parts.append("واقعیات:")
        fact_steps = [s for s in result.reasoning_steps if s.step_type == "FACT"]
        for step in fact_steps:
            parts.append(f"- {step.content}")

        parts.append("")

        # Articles
        parts.append("مواد قانونی:")
        article_steps = [s for s in result.reasoning_steps if s.step_type == "ARTICLE"]
        for step in article_steps:
            parts.append(f"ماده {step.related_article}: {step.content[:200]}...")

        parts.append("")

        # Deductions
        parts.append("نتیجه‌گیری‌ها:")
        for deduction in result.deductions:
            parts.append(f"- {deduction}")

        return "\n".join(parts)

    def _parse_verdict(self, verdict_text: str, case_id: str, confidence: float) -> Optional[Verdict]:
        """
        Parse GPT-generated verdict into structured format.

        Uses simple section-based parsing. In production, would use
        more sophisticated NLP or structured output.

        Args:
            verdict_text: Raw verdict text from GPT
            case_id: Case identifier
            confidence: Overall confidence score

        Returns:
            Verdict object
        """
        try:
            # Simple section extraction based on headers
            sections = {
                'summary': self._extract_section(verdict_text, ['خلاصه پرونده', 'خلاصه']),
                'proven_facts': self._extract_section(verdict_text, ['واقعیات اثبات شده', 'واقعیات']),
                'legal_analysis': self._extract_section(verdict_text, ['تحلیل حقوقی', 'استدلال حقوقی']),
                'ruling': self._extract_section(verdict_text, ['حکم', 'رأی']),
                'implementation': self._extract_section(verdict_text, ['جزئیات اجرایی', 'اجرا']),
                'appealable': self._extract_section(verdict_text, ['قابل اعتراض', 'اعتراض'])
            }

            # If section extraction failed, use full text
            if not any(sections.values()):
                sections = {
                    'summary': 'خلاصه در متن حکم ذکر شده است',
                    'proven_facts': 'واقعیات در متن حکم ذکر شده است',
                    'legal_analysis': verdict_text,
                    'ruling': 'حکم در متن ذکر شده است',
                    'implementation': 'طبق مفاد حکم',
                    'appealable': 'این رأی ظرف ۲۰ روز قابل اعتراض است'
                }

            verdict = Verdict(
                case_id=case_id,
                summary=sections['summary'],
                proven_facts=sections['proven_facts'],
                legal_analysis=sections['legal_analysis'],
                ruling=sections['ruling'],
                implementation=sections['implementation'],
                appealable=sections['appealable'] or 'این رأی ظرف ۲۰ روز قابل اعتراض است',
                confidence=confidence
            )

            return verdict

        except Exception as e:
            st.error(f"❌ خطا در پردازش حکم: {str(e)}")
            return None

    def _extract_section(self, text: str, headers: list) -> str:
        """
        Extract a section from verdict text based on headers.

        Args:
            text: Full verdict text
            headers: Possible header variations

        Returns:
            Section content or empty string
        """
        lines = text.split('\n')
        section_lines = []
        capturing = False

        for line in lines:
            line_stripped = line.strip()

            # Check if this line contains a header
            is_header = any(header in line_stripped for header in headers)

            if is_header:
                capturing = True
                continue

            # Stop if we hit another section header (starts with ##, **, or numbers)
            if capturing and line_stripped:
                if line_stripped.startswith(('##', '**', '۱.', '۲.', '۳.', '۴.', '۵.')):
                    # Check if it's not a list item
                    if not any(h in line_stripped for h in headers):
                        break

            if capturing and line_stripped:
                section_lines.append(line_stripped)

        return '\n'.join(section_lines).strip()

    def format_verdict_display(self, verdict: Verdict) -> str:
        """
        Format verdict for display in UI.

        Args:
            verdict: Verdict object

        Returns:
            Formatted markdown text
        """
        parts = []

        # Header
        parts.append(f"# رأی نهایی - {verdict.case_id}")
        parts.append(f"**سطح اطمینان:** {verdict.confidence*100:.0f}%")
        parts.append("---")

        # Summary
        parts.append("## ۱. خلاصه پرونده")
        parts.append(verdict.summary)
        parts.append("")

        # Proven facts
        parts.append("## ۲. واقعیات اثبات شده")
        parts.append(verdict.proven_facts)
        parts.append("")

        # Legal analysis
        parts.append("## ۳. تحلیل حقوقی")
        parts.append(verdict.legal_analysis)
        parts.append("")

        # Ruling
        parts.append("## ۴. حکم")
        parts.append(verdict.ruling)
        parts.append("")

        # Implementation
        if verdict.implementation:
            parts.append("## ۵. جزئیات اجرایی")
            parts.append(verdict.implementation)
            parts.append("")

        # Appealable
        parts.append("## ۶. قابلیت اعتراض")
        parts.append(verdict.appealable)

        return "\n".join(parts)


# Global instance
_generator_instance: Optional[VerdictGenerator] = None

def get_verdict_generator() -> VerdictGenerator:
    """
    Get global verdict generator instance.

    Returns:
        VerdictGenerator singleton
    """
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = VerdictGenerator()
    return _generator_instance
