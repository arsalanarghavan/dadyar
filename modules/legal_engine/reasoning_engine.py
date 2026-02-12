"""
Reasoning Engine - Chain-of-Thought Legal Analysis.

This is the core of the judicial decision-making simulator. It implements
a multi-step reasoning process that mirrors how judges analyze cases:

1. Retrieve relevant legal articles (RAG)
2. Analyze each article's applicability to the case
3. Generate intermediate deductions
4. Build a structured reasoning chain
5. Return data for graph visualization

Author: Master's Thesis Project - Mahsa Mirzaei
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import streamlit as st

from modules.legal_engine.openai_client import get_openai_client
from modules.legal_engine.knowledge_base import get_knowledge_base
from modules.legal_engine.entity_extractor import CaseEntities
from config.prompts import (
    LEGAL_REASONING_PROMPT,
    ARTICLE_APPLICABILITY_PROMPT,
    DEDUCTION_GENERATION_PROMPT
)


@dataclass
class ReasoningStep:
    """
    A single step in the reasoning chain.

    Each step represents one phase of legal analysis:
    - FACT: An observed fact from the case
    - ARTICLE: Application of a legal article
    - DEDUCTION: A logical conclusion
    - VERDICT: The final decision
    """
    step_type: str  # FACT, ARTICLE, DEDUCTION, VERDICT
    content: str  # Persian text describing this step
    confidence: float = 0.0  # Confidence score (0-1)
    related_article: Optional[int] = None  # Article number if applicable
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningResult:
    """
    Complete result of legal reasoning process.

    Contains all steps, retrieved articles, deductions, and metadata
    needed for graph visualization and verdict generation.
    """
    case_id: str
    entities: CaseEntities
    retrieved_articles: List[Dict[str, Any]]
    reasoning_steps: List[ReasoningStep]
    deductions: List[str]
    graph_data: Optional[Dict[str, Any]] = None
    overall_confidence: float = 0.0


class ReasoningEngine:
    """
    Legal reasoning engine with Chain-of-Thought approach.

    This class implements the core judicial decision-making logic,
    demonstrating explainable AI (XAI) principles through transparent
    step-by-step reasoning.
    """

    def __init__(self):
        """Initialize reasoning engine with knowledge base and OpenAI client."""
        self.client = get_openai_client()
        self.kb = get_knowledge_base()

    def analyze_case(
        self,
        case_description: str,
        entities: CaseEntities,
        case_id: str = "CASE-001"
    ) -> Optional[ReasoningResult]:
        """
        Perform complete legal analysis of a case.

        This is the main entry point for case analysis. It orchestrates
        the entire reasoning process.

        Args:
            case_description: Full case description in Persian
            entities: Extracted entities from the case
            case_id: Unique case identifier

        Returns:
            ReasoningResult with complete analysis or None if failed
        """
        st.info("🔍 شروع تحلیل پرونده...")

        # Step 1: Retrieve relevant articles using RAG
        st.info("📚 بازیابی مواد قانونی مرتبط...")
        articles = self.kb.retrieve_relevant_articles(
            query=case_description,
            top_k=5
        )

        if not articles:
            st.error("❌ هیچ ماده قانونی مرتبطی یافت نشد")
            return None

        st.success(f"✅ {len(articles)} ماده قانونی بازیابی شد")

        # Step 2: Analyze each article's applicability
        st.info("⚖️ تحلیل کاربرد هر ماده...")
        reasoning_steps = []

        # Add initial facts as reasoning steps
        for fact in entities.key_facts:
            step = ReasoningStep(
                step_type="FACT",
                content=fact,
                confidence=1.0
            )
            reasoning_steps.append(step)

        # Analyze each retrieved article
        article_analyses = []
        for i, article in enumerate(articles, 1):
            with st.expander(f"📜 تحلیل ماده {article['article_number']}", expanded=(i == 1)):
                analysis = self._analyze_article_applicability(
                    article=article,
                    case_facts=entities.key_facts,
                    case_desc=case_description
                )

                if analysis:
                    article_analyses.append(analysis)

                    # Add as reasoning step
                    step = ReasoningStep(
                        step_type="ARTICLE",
                        content=analysis['analysis_text'],
                        confidence=analysis['confidence'],
                        related_article=article['article_number'],
                        metadata={'article': article}
                    )
                    reasoning_steps.append(step)

                    st.success(f"اطمینان: {analysis['confidence']*100:.0f}%")

        # Step 3: Generate deductions
        st.info("💡 استنتاج نتیجه‌گیری‌های حقوقی...")
        deductions = self._generate_deductions(
            articles=articles,
            analyses=article_analyses,
            case_facts=entities.key_facts
        )

        # Add deductions as reasoning steps
        for deduction in deductions:
            step = ReasoningStep(
                step_type="DEDUCTION",
                content=deduction,
                confidence=0.8  # Medium-high confidence for deductions
            )
            reasoning_steps.append(step)

        # Calculate overall confidence
        article_confidences = [s.confidence for s in reasoning_steps if s.step_type == "ARTICLE"]
        overall_confidence = sum(article_confidences) / len(article_confidences) if article_confidences else 0.5

        # Create result
        result = ReasoningResult(
            case_id=case_id,
            entities=entities,
            retrieved_articles=articles,
            reasoning_steps=reasoning_steps,
            deductions=deductions,
            overall_confidence=overall_confidence
        )

        st.success(f"✅ تحلیل کامل شد - اطمینان کلی: {overall_confidence*100:.0f}%")

        return result

    def _analyze_article_applicability(
        self,
        article: Dict[str, Any],
        case_facts: List[str],
        case_desc: str
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze how a specific article applies to the case.

        This implements the per-article reasoning step, asking GPT to
        determine relevance and explain the connection.

        Args:
            article: Legal article dict
            case_facts: List of case facts
            case_desc: Full case description

        Returns:
            Analysis dict with text, confidence, and applicability
        """
        # Format facts as numbered list
        facts_text = "\n".join([f"{i+1}. {fact}" for i, fact in enumerate(case_facts)])

        # Create prompt
        prompt = ARTICLE_APPLICABILITY_PROMPT.format(
            article_number=article['article_number'],
            article_title=article['title'],
            article_text=article['text'],
            case_facts=facts_text
        )

        # Get GPT analysis
        analysis_text = self.client.get_completion(
            prompt=prompt,
            temperature=0.3  # Low temperature for consistent legal analysis
        )

        if not analysis_text:
            return None

        # Extract confidence from response (simple heuristic)
        confidence = self._extract_confidence(analysis_text)

        return {
            'article_number': article['article_number'],
            'analysis_text': analysis_text,
            'confidence': confidence,
            'is_applicable': confidence > 0.6  # Threshold for applicability
        }

    def _extract_confidence(self, text: str) -> float:
        """
        Extract confidence score from analysis text.

        Uses keyword matching to infer confidence level.
        In a production system, this would be more sophisticated.

        Args:
            text: Analysis text in Persian

        Returns:
            Confidence score (0-1)
        """
        text_lower = text.lower()

        # High confidence keywords
        if any(kw in text_lower for kw in ['قطعاً', 'حتماً', 'بدون شک', 'کاملاً']):
            return 0.95

        # Good confidence keywords
        if any(kw in text_lower for kw in ['احتمالاً', 'به نظر می‌رسد', 'مرتبط است']):
            return 0.80

        # Medium confidence keywords
        if any(kw in text_lower for kw in ['ممکن است', 'شاید', 'می‌تواند']):
            return 0.60

        # Low confidence keywords
        if any(kw in text_lower for kw in ['نامحتمل', 'بعید', 'کمتر مرتبط']):
            return 0.30

        # Default medium confidence
        return 0.70

    def _generate_deductions(
        self,
        articles: List[Dict[str, Any]],
        analyses: List[Dict[str, Any]],
        case_facts: List[str]
    ) -> List[str]:
        """
        Generate intermediate legal deductions.

        Synthesizes article analyses into logical conclusions.

        Args:
            articles: Retrieved articles
            analyses: Article applicability analyses
            case_facts: Case facts

        Returns:
            List of deduction strings
        """
        # Format analyses for prompt
        analyses_text = "\n\n".join([
            f"ماده {a['article_number']}:\n{a['analysis_text']}"
            for a in analyses if a['is_applicable']
        ])

        facts_text = "\n".join([f"- {fact}" for fact in case_facts])

        # Create prompt
        prompt = DEDUCTION_GENERATION_PROMPT.format(
            analyses=analyses_text,
            case_facts=facts_text
        )

        # Get deductions from GPT
        result = self.client.get_completion(
            prompt=prompt,
            temperature=0.3
        )

        if not result:
            return []

        # Parse deductions (simple line-based parsing)
        # In production, would use more sophisticated parsing
        deductions = []
        for line in result.split('\n'):
            line = line.strip()
            # Look for numbered or bulleted deductions
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Clean up formatting
                deduction = line.lstrip('0123456789.-•) ').strip()
                if deduction:
                    deductions.append(deduction)

        return deductions

    def get_reasoning_chain_text(self, result: ReasoningResult) -> str:
        """
        Format reasoning chain as readable text.

        Args:
            result: Reasoning result

        Returns:
            Formatted Persian text showing the reasoning flow
        """
        parts = []

        # Facts section
        parts.append("## واقعیات پرونده")
        fact_steps = [s for s in result.reasoning_steps if s.step_type == "FACT"]
        for i, step in enumerate(fact_steps, 1):
            parts.append(f"{i}. {step.content}")

        parts.append("")

        # Articles section
        parts.append("## مواد قانونی قابل اعمال")
        article_steps = [s for s in result.reasoning_steps if s.step_type == "ARTICLE"]
        for i, step in enumerate(article_steps, 1):
            parts.append(f"### ماده {step.related_article}")
            parts.append(step.content)
            parts.append(f"**اطمینان:** {step.confidence*100:.0f}%")
            parts.append("")

        # Deductions section
        parts.append("## نتیجه‌گیری‌های حقوقی")
        for i, deduction in enumerate(result.deductions, 1):
            parts.append(f"{i}. {deduction}")

        return "\n".join(parts)


# Global instance
_engine_instance: Optional[ReasoningEngine] = None

def get_reasoning_engine() -> ReasoningEngine:
    """
    Get global reasoning engine instance.

    Returns:
        ReasoningEngine singleton
    """
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = ReasoningEngine()
    return _engine_instance
