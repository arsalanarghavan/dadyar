"""
Sidebar - Case Metadata Display.

Shows current case information and quick navigation.

Author: Master's Thesis Project - Mahsa Mirzaei
"""

import streamlit as st
from typing import Optional, Dict, Any

from modules.ui_components.persian_utils import get_persian_utils


def render_sidebar(case_data: Optional[Dict[str, Any]] = None):
    """
    Render sidebar with case metadata.

    Args:
        case_data: Current case data (optional)
    """
    utils = get_persian_utils()

    with st.sidebar:
        # Logo/Title
        st.markdown("# ⚖️ سیستم قضایی هوشمند")
        st.markdown("شبیه‌ساز تصمیم‌گیری در پرونده‌های غصب و خلع ید")
        st.markdown("---")

        # Case metadata
        if case_data:
            st.markdown("### 📋 پرونده جاری")

            st.markdown(utils.create_card_html(
                "شناسه",
                case_data.get('case_id', 'نامشخص'),
                "#3b82f6"
            ), unsafe_allow_html=True)

            st.markdown(utils.create_card_html(
                "تاریخ",
                case_data.get('date', utils.format_persian_date()),
                "#10b981"
            ), unsafe_allow_html=True)

            st.markdown("**طرفین:**")
            st.markdown(f"👨‍⚖️ خواهان: {case_data.get('plaintiff', 'نامشخص')}")
            st.markdown(f"👤 خوانده: {case_data.get('defendant', 'نامشخص')}")

            st.markdown("---")

        # Quick stats
        st.markdown("### 📊 آمار")
        total_cases = st.session_state.get('case_counter', 0)
        st.metric("پرونده‌های تحلیل شده", total_cases)

        st.markdown("---")

        # Information
        st.markdown("### ℹ️ درباره سیستم")
        st.markdown("""
        این سیستم برای **پایان‌نامه کارشناسی ارشد** طراحی شده است:

        **موضوع:**
        طراحی چت‌بات هوشمند برای شبیه‌سازی تصمیم‌گیری قضایی

        **تکنولوژی‌ها:**
        - 🤖 OpenAI GPT-4
        - 📚 RAG با FAISS
        - 🕸️ NetworkX + Plotly
        - 💻 Streamlit

        **قابلیت‌ها:**
        - استخراج خودکار اطلاعات
        - تحلیل مواد قانونی (۳۰۸-۳۲۷)
        - استدلال گام‌به‌گام
        - گراف تعاملی استدلال
        - صدور حکم نهایی
        """)

        st.markdown("---")

        # Settings
        with st.expander("⚙️ تنظیمات"):
            st.markdown("**مدل هوش مصنوعی:**")
            st.code("GPT-4 Turbo", language=None)

            st.markdown("**تعداد مواد بازیابی:**")
            st.slider("Top-K Articles", 1, 10, 5, disabled=True)

            if st.button("🗑️ پاک کردن حافظه"):
                # Clear session state
                for key in list(st.session_state.keys()):
                    if key.startswith('analysis_'):
                        del st.session_state[key]
                st.success("✅ حافظه پاک شد")
                st.rerun()

        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #64748b; font-size: 0.875rem;'>
            ساخته شده با ❤️ برای پایان‌نامه<br>
            نسخه ۱.۰.۰
        </div>
        """, unsafe_allow_html=True)
