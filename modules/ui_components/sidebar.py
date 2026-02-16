"""Sidebar — Case metadata display & AI settings."""

import streamlit as st
from typing import Optional, Dict, Any

from modules.ui_components.persian_utils import get_persian_utils

# ── Model catalogues ──

PROVIDER_MODELS = {
    "OpenAI": [
        "gpt-4-turbo-preview",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-3.5-turbo",
    ],
    "Gemini": [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ],
}


def _init_ai_defaults():
    """Ensure AI-related session state keys exist."""
    from config.settings import get_settings
    settings = get_settings()

    defaults = {
        "ai_provider": settings.AI_PROVIDER,
        "ai_model": "",
        "openai_api_key": settings.OPENAI_API_KEY,
        "gemini_api_key": settings.GEMINI_API_KEY,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def render_sidebar(case_data: Optional[Dict[str, Any]] = None):
    """Render sidebar with case info & AI settings."""
    _init_ai_defaults()
    utils = get_persian_utils()

    with st.sidebar:
        # Brand
        st.markdown(
            "<div style='text-align:center; padding: 0.5rem 0 0.75rem;'>"
            "<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 24 24' fill='none' "
            "stroke='#2563eb' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round' "
            "style='display:inline-block; margin-bottom:0.375rem;'>"
            "<path d='M5.7 15l1.3-2.6 1.3 2.6'/>"
            "<path d='M12 3l0 18'/>"
            "<path d='M9 3h6'/>"
            "<path d='M15.7 15l1.3-2.6 1.3 2.6'/>"
            "<path d='M4 15h4'/>"
            "<path d='M16 15h4'/>"
            "<path d='M12 15a4 4 0 0 1-4 4h8a4 4 0 0 1-4-4'/>"
            "</svg>"
            "<h3 style='margin:0; font-size:1.0625rem; font-weight:600; color:#fafafa;'>دادیار هوشمند</h3>"
            "<p style='color:#71717a; font-size:0.75rem; margin:0.125rem 0 0;'>تحلیل پرونده‌های حقوقی</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        # ── Current case ──
        if case_data:
            st.markdown("##### پرونده فعال")

            col1, col2 = st.columns(2)
            with col1:
                st.caption("شناسه")
                st.markdown(f"**{case_data.get('case_id', '—')}**")
            with col2:
                st.caption("تاریخ")
                st.markdown(f"**{case_data.get('date', '—')}**")

            st.caption("طرفین")
            st.markdown(
                f"خواهان: {case_data.get('plaintiff', '—')}  \n"
                f"خوانده: {case_data.get('defendant', '—')}"
            )
            st.markdown("---")

        # ── AI Settings ──
        with st.expander("تنظیمات مدل", expanded=False):
            _render_ai_settings()

        st.markdown("---")

        # ── Info ──
        provider = st.session_state.get("ai_provider", "openai")
        provider_label = "OpenAI" if provider == "openai" else "Gemini"
        model = st.session_state.get("ai_model", "") or "پیش‌فرض"

        st.caption("مدل فعال")
        st.markdown(f"**{provider_label}** · {model}")

        st.markdown("")
        st.caption("قابلیت‌ها")
        st.markdown(
            "استخراج اطلاعات · تحلیل مواد قانونی  \n"
            "استدلال گام‌به‌گام · گراف تعاملی  \n"
            "صدور حکم نهایی"
        )

        st.markdown("---")
        st.markdown(
            "<div style='text-align:center; color:#52525b; font-size:0.7rem; line-height:1.6;'>"
            "توسعه‌دهنده: مهسا میرزایی<br>"
            "نسخه ۱.۲.۰"
            "</div>",
            unsafe_allow_html=True,
        )


# ── AI Settings Panel ──

def _render_ai_settings():
    """Interactive AI provider / model / API‑key controls."""
    from modules.legal_engine.client_factory import reset_client

    # Provider
    provider_options = list(PROVIDER_MODELS.keys())
    current_provider = st.session_state.get("ai_provider", "openai")
    current_idx = 0 if current_provider == "openai" else 1

    selected_provider = st.selectbox(
        "ارائه‌دهنده",
        provider_options,
        index=current_idx,
        key="_provider_select",
    )
    provider_key = selected_provider.lower()

    # API Key
    if provider_key == "openai":
        api_key = st.text_input(
            "کلید API",
            value=st.session_state.get("openai_api_key", ""),
            type="password",
            key="_openai_key_input",
            help="platform.openai.com",
        )
        st.session_state["openai_api_key"] = api_key
    else:
        api_key = st.text_input(
            "کلید API",
            value=st.session_state.get("gemini_api_key", ""),
            type="password",
            key="_gemini_key_input",
            help="aistudio.google.com",
        )
        st.session_state["gemini_api_key"] = api_key

    # Model
    models = PROVIDER_MODELS[selected_provider]
    current_model = st.session_state.get("ai_model", "")
    try:
        default_idx = models.index(current_model)
    except ValueError:
        default_idx = 0

    selected_model = st.selectbox(
        "مدل",
        models,
        index=default_idx,
        key="_model_select",
    )

    # Detect changes
    changed = False
    if provider_key != st.session_state.get("ai_provider"):
        st.session_state["ai_provider"] = provider_key
        st.session_state["ai_model"] = models[0]
        changed = True
    if selected_model != st.session_state.get("ai_model"):
        st.session_state["ai_model"] = selected_model
        changed = True

    if changed:
        reset_client()
        st.toast("تنظیمات ذخیره شد")

    # Tip
    if provider_key == "gemini":
        st.caption("Gemini 2.0 Flash: رایگان · ۱۵ درخواست/دقیقه")
    else:
        st.caption("GPT-4 Turbo: بهترین کیفیت استدلال")

    st.markdown("")
    if st.button("پاک‌سازی حافظه نهان", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key.startswith("analysis_"):
                del st.session_state[key]
        reset_client()
        st.toast("حافظه پاک شد")
        st.rerun()
