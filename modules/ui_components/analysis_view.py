"""Analysis View — judicial analysis tab."""

import streamlit as st
from typing import Dict, Any

from modules.legal_engine.entity_extractor import get_entity_extractor
from modules.legal_engine.reasoning_engine import get_reasoning_engine
from modules.legal_engine.verdict_generator import get_verdict_generator
from modules.graph_builder.reasoning_graph import ReasoningGraph
from modules.ui_components.persian_utils import get_persian_utils


def render_analysis(case_data: Dict[str, Any]):
    """Render complete case analysis."""
    utils = get_persian_utils()
    cache_key = f"analysis_{case_data['case_id']}"

    if cache_key not in st.session_state:
        st.info("برای شروع تحلیل پرونده، دکمه زیر را بزنید.")
        if st.button("شروع تحلیل", type="primary", use_container_width=True):
            with st.spinner("در حال تحلیل پرونده…"):
                _perform_analysis(case_data, cache_key)
        return

    if cache_key in st.session_state:
        if st.button("تحلیل مجدد", type="secondary"):
            del st.session_state[cache_key]
            st.rerun()
        _display_results(st.session_state[cache_key], utils)


def _perform_analysis(case_data: Dict[str, Any], cache_key: str):
    """Run the full analysis pipeline and cache results."""

    progress = st.progress(0, text="استخراج اطلاعات…")

    # 1 — Extract entities
    extractor = get_entity_extractor()
    entities = extractor.extract(case_data["description"])
    if not entities:
        st.error("استخراج اطلاعات ناموفق بود.")
        return
    progress.progress(25, text="تحلیل حقوقی…")

    # 2 — Reasoning
    engine = get_reasoning_engine()
    reasoning = engine.analyze_case(
        case_description=case_data["description"],
        entities=entities,
        case_id=case_data["case_id"],
    )
    if not reasoning:
        st.error("تحلیل ناموفق بود.")
        return
    progress.progress(50, text="ساخت گراف…")

    # 3 — Graph
    graph_builder = ReasoningGraph()
    graph = graph_builder.build_from_reasoning(reasoning)
    progress.progress(75, text="صدور حکم…")

    # 4 — Verdict
    verdict_gen = get_verdict_generator()
    verdict = verdict_gen.generate_verdict(reasoning)
    progress.progress(100, text="تحلیل کامل شد")

    st.session_state[cache_key] = {
        "entities": entities,
        "reasoning_result": reasoning,
        "graph": graph,
        "verdict": verdict,
    }
    st.rerun()


def _display_results(results: Dict[str, Any], utils):
    """Display cached analysis results."""
    entities = results["entities"]
    reasoning = results["reasoning_result"]
    verdict = results.get("verdict")

    # ── Entities ──
    with st.expander("اطلاعات استخراج‌شده", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**خواهان:** {entities.plaintiff or '—'}")
        with col2:
            st.markdown(f"**خوانده:** {entities.defendant or '—'}")

        tags = []
        if entities.case_type:
            tags.append(entities.case_type)
        if entities.property_type:
            tags.append(entities.property_type)
        if tags:
            tag_html = " ".join(
                f"<span style='background:#27272a;color:#a1a1aa;padding:2px 10px;"
                f"border-radius:9999px;font-size:0.8rem;margin-left:4px;'>{t}</span>"
                for t in tags
            )
            st.markdown(tag_html, unsafe_allow_html=True)

        if entities.key_facts:
            st.markdown("**واقعیات کلیدی:**")
            for i, fact in enumerate(entities.key_facts, 1):
                st.markdown(f"{i}. {fact}")

    # ── Articles ──
    with st.expander("مواد قانونی مرتبط", expanded=False):
        for article in reasoning.retrieved_articles:
            relevance = article.get("relevance_score", 0)
            pct = utils.format_confidence(relevance)
            st.markdown(
                f"**ماده {article['article_number']}** — {article['title']}  \n"
                f"ارتباط: {pct}"
            )
            st.caption(article["text"])
            st.markdown("")

    # ── Reasoning chain ──
    with st.expander("زنجیره استدلال", expanded=True):
        facts = [s for s in reasoning.reasoning_steps if s.step_type == "FACT"]
        articles = [s for s in reasoning.reasoning_steps if s.step_type == "ARTICLE"]

        if facts:
            st.markdown("**واقعیات**")
            for s in facts:
                st.markdown(f"- {s.content}")

        if articles:
            st.markdown("")
            st.markdown("**تحلیل مواد**")
            for s in articles:
                pct = utils.format_confidence(s.confidence)
                st.markdown(f"ماده {s.related_article} ({pct}): {s.content}")

        if reasoning.deductions:
            st.markdown("")
            st.markdown("**نتیجه‌گیری**")
            for i, d in enumerate(reasoning.deductions, 1):
                st.markdown(f"{i}. {d}")

    # ── Verdict ──
    if verdict:
        with st.expander("حکم نهایی", expanded=True):
            verdict_gen = get_verdict_generator()
            st.markdown(verdict_gen.format_verdict_display(verdict))
