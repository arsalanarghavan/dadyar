"""
Analysis View - Judicial Analysis Tab Component.

Displays:
- Extracted entities
- Retrieved legal articles
- Chain-of-Thought reasoning
- Final verdict

Author: Master's Thesis Project - Mahsa Mirzaei
"""

import streamlit as st
from typing import Dict, Any

from modules.legal_engine.entity_extractor import get_entity_extractor
from modules.legal_engine.reasoning_engine import get_reasoning_engine
from modules.legal_engine.verdict_generator import get_verdict_generator
from modules.graph_builder.reasoning_graph import ReasoningGraph
from modules.graph_builder.plotly_renderer import get_plotly_renderer
from modules.ui_components.persian_utils import get_persian_utils


def render_analysis(case_data: Dict[str, Any]):
    """
    Render complete case analysis.

    Args:
        case_data: Dict with case information
    """
    utils = get_persian_utils()

    st.markdown("## 🔍 تحلیل قضایی پرونده")
    st.markdown(f"**شناسه پرونده:** {case_data['case_id']}")
    st.markdown("---")

    # Check if analysis already exists in session state
    cache_key = f"analysis_{case_data['case_id']}"

    if cache_key not in st.session_state:
        # Perform analysis
        with st.spinner("در حال تحلیل..."):
            perform_analysis(case_data, cache_key)

    # Display results from cache
    if cache_key in st.session_state:
        display_analysis_results(st.session_state[cache_key], utils)


def perform_analysis(case_data: Dict[str, Any], cache_key: str):
    """Perform complete analysis and cache results."""

    # Step 1: Extract entities
    st.info("### گام ۱: استخراج اطلاعات")
    extractor = get_entity_extractor()
    entities = extractor.extract(case_data['description'])

    if not entities:
        st.error("❌ استخراج اطلاعات ناموفق بود")
        return

    # Step 2: Perform reasoning
    st.info("### گام ۲: تحلیل حقوقی")
    engine = get_reasoning_engine()
    reasoning_result = engine.analyze_case(
        case_description=case_data['description'],
        entities=entities,
        case_id=case_data['case_id']
    )

    if not reasoning_result:
        st.error("❌ تحلیل ناموفق بود")
        return

    # Step 3: Build graph
    st.info("### گام ۳: ساخت گراف استدلال")
    graph_builder = ReasoningGraph()
    graph = graph_builder.build_from_reasoning(reasoning_result)

    # Step 4: Generate verdict
    st.info("### گام ۴: صدور حکم")
    verdict_gen = get_verdict_generator()
    verdict = verdict_gen.generate_verdict(reasoning_result)

    # Cache results
    st.session_state[cache_key] = {
        'entities': entities,
        'reasoning_result': reasoning_result,
        'graph': graph,
        'verdict': verdict
    }

    st.success("✅ تحلیل کامل شد!")
    st.rerun()


def display_analysis_results(results: Dict[str, Any], utils):
    """Display cached analysis results."""

    entities = results['entities']
    reasoning_result = results['reasoning_result']
    verdict = results.get('verdict')

    # Display extracted entities
    with st.expander("📋 اطلاعات استخراج شده", expanded=True):
        display_entities(entities, utils)

    # Display retrieved articles
    with st.expander("📚 مواد قانونی مرتبط", expanded=False):
        display_articles(reasoning_result.retrieved_articles, utils)

    # Display reasoning chain
    with st.expander("💡 زنجیره استدلال (Chain of Thought)", expanded=True):
        display_reasoning_chain(reasoning_result, utils)

    # Display verdict
    if verdict:
        with st.expander("⚖️ حکم نهایی", expanded=True):
            from modules.legal_engine.verdict_generator import get_verdict_generator
            verdict_gen = get_verdict_generator()
            verdict_text = verdict_gen.format_verdict_display(verdict)
            st.markdown(verdict_text)


def display_entities(entities, utils):
    """Display extracted entities."""
    cols = st.columns(2)

    with cols[0]:
        st.markdown(utils.create_card_html(
            "خواهان",
            entities.plaintiff or "نامشخص",
            "#3b82f6"
        ), unsafe_allow_html=True)

    with cols[1]:
        st.markdown(utils.create_card_html(
            "خوانده",
            entities.defendant or "نامشخص",
            "#ef4444"
        ), unsafe_allow_html=True)

    if entities.case_type:
        st.markdown(utils.create_badge(f"نوع: {entities.case_type}", "#10b981"), unsafe_allow_html=True)

    if entities.property_type:
        st.markdown(utils.create_badge(f"ملک: {entities.property_type}", "#f59e0b"), unsafe_allow_html=True)

    if entities.key_facts:
        st.markdown("**واقعیات کلیدی:**")
        for i, fact in enumerate(entities.key_facts, 1):
            st.markdown(f"{i}. {fact}")


def display_articles(articles, utils):
    """Display retrieved articles."""
    for article in articles:
        relevance = article.get('relevance_score', 0)
        color = "#10b981" if relevance > 0.8 else "#f59e0b" if relevance > 0.6 else "#94a3b8"

        with st.container():
            st.markdown(f"### ماده {article['article_number']}: {article['title']}")
            st.markdown(f"**ارتباط:** {utils.format_confidence(relevance)}")
            st.markdown(f"**متن:** {article['text']}")
            st.markdown("---")


def display_reasoning_chain(reasoning_result, utils):
    """Display reasoning steps."""
    # Facts
    st.markdown("#### واقعیات")
    fact_steps = [s for s in reasoning_result.reasoning_steps if s.step_type == "FACT"]
    for step in fact_steps:
        st.markdown(f"- {step.content}")

    st.markdown("")

    # Articles
    st.markdown("#### تحلیل مواد قانونی")
    article_steps = [s for s in reasoning_result.reasoning_steps if s.step_type == "ARTICLE"]
    for step in article_steps:
        st.markdown(f"**ماده {step.related_article}** ({utils.format_confidence(step.confidence)})")
        st.markdown(step.content)
        st.markdown("")

    # Deductions
    if reasoning_result.deductions:
        st.markdown("#### نتیجه‌گیری‌ها")
        for i, ded in enumerate(reasoning_result.deductions, 1):
            st.markdown(f"{i}. {ded}")
