"""دادیار هوشمند — Intelligent Legal Case Analyzer."""

import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import get_settings
from modules.ui_components import sidebar, input_form, analysis_view, graph_view


# ── Page config ──
st.set_page_config(
    page_title="دادیار هوشمند",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── CSS ──
def _load_css():
    base = Path(__file__).parent / "assets" / "styles"
    for name in ("main.css", "rtl.css"):
        p = base / name
        if p.exists():
            st.markdown(f"<style>{p.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


_load_css()


# ── Settings ──
@st.cache_resource
def _init_settings():
    try:
        return get_settings()
    except Exception:
        import os
        os.environ.setdefault("AI_PROVIDER", "gemini")
        from config.settings import Settings
        return Settings()


_init_settings()


# ── Session state ──
for _k, _v in {"case_counter": 1, "current_case": None, "current_case_graph": None}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── Main ──
def main():
    sidebar.render_sidebar(st.session_state.current_case)

    # Header
    st.markdown(
        "<div style='text-align:center; padding:1rem 0 0.5rem;'>"
        "<svg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 24 24' fill='none' "
        "stroke='#a1a1aa' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round' "
        "style='display:inline-block; margin-bottom:0.5rem;'>"
        "<path d='M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446a9 9 0 1 1 -8.313-12.454z'/>"
        "<path d='M17 4a2 2 0 0 0 2 2a2 2 0 0 0 -2 2a2 2 0 0 0 -2 -2a2 2 0 0 0 2 -2'/>"
        "<path d='M19 11h2m-1 -1v2'/>"
        "</svg>"
        "<h1 style='margin:0; font-size:1.75rem; font-weight:700; color:#fafafa;'>دادیار هوشمند</h1>"
        "<p style='color:#71717a; font-size:0.9rem; margin:0.25rem 0 0;'>"
        "تحلیل هوشمند پرونده‌های غصب و خلع ید"
        "</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Tabs
    tab_input, tab_analysis, tab_graph = st.tabs([
        "ورودی پرونده",
        "تحلیل قضایی",
        "گراف استدلال",
    ])

    with tab_input:
        input_form.render_sample_case_loader()
        case_data = input_form.render_input_form()
        if case_data:
            st.session_state.current_case = case_data
            st.success("اطلاعات ثبت شد — به تب «تحلیل قضایی» بروید.")

    with tab_analysis:
        if st.session_state.current_case:
            analysis_view.render_analysis(st.session_state.current_case)
            # Sync graph
            cache_key = f"analysis_{st.session_state.current_case['case_id']}"
            cached = st.session_state.get(cache_key, {})
            if "graph" in cached:
                st.session_state.current_case_graph = cached["graph"]
        else:
            st.info("ابتدا اطلاعات پرونده را در تب «ورودی پرونده» وارد کنید.")

    with tab_graph:
        graph_view.render_graph_view()

    # Footer
    st.markdown("---")
    provider = st.session_state.get("ai_provider", "openai")
    provider_label = "OpenAI" if provider == "openai" else "Gemini"
    model_label = st.session_state.get("ai_model", "") or "default"
    st.markdown(
        f"<div style='text-align:center; padding:0.5rem 0; color:#52525b; font-size:0.8rem;'>"
        f"توسعه‌دهنده: مهسا میرزایی &middot; "
        f"{provider_label} ({model_label}) &middot; "
        f"نسخه ۱.۲.۰"
        f"</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"خطای غیرمنتظره: {e}")
        with st.expander("جزئیات خطا"):
            import traceback
            st.code(traceback.format_exc())
