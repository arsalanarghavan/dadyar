"""
Judicial Decision-Making Simulator - Main Application

A Glass-Box AI system for simulating judicial reasoning in Iranian property law cases.

Features:
- Entity extraction from case descriptions
- RAG-based retrieval of relevant legal articles
- Chain-of-Thought reasoning visualization
- Interactive reasoning graph
- Formal verdict generation

Technology Stack:
- Streamlit (UI)
- OpenAI GPT-4 (LLM)
- FAISS (Vector store for RAG)
- NetworkX + Plotly (Graph visualization)
- Hazm (Persian NLP)

Author: Master's Thesis Project - Mahsa Mirzaei
Topic: Designing an Intelligent Chatbot for Simulating Judicial Decision-Making
       in Property Lawsuits (Ghasb & Khal-e Yad)
"""

import streamlit as st
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import get_settings
from modules.ui_components import sidebar, input_form, analysis_view, graph_view


# ===== Page Configuration =====
st.set_page_config(
    page_title="سیستم هوشمند شبیه‌سازی تصمیم‌گیری قضایی",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "سیستم شبیه‌سازی تصمیم‌گیری قضایی - پایان‌نامه کارشناسی ارشد"
    }
)


# ===== Load Custom CSS =====
def load_css():
    """Load custom CSS for shadcn aesthetic and RTL support."""
    css_files = [
        "assets/styles/main.css",
        "assets/styles/rtl.css"
    ]

    for css_file in css_files:
        css_path = Path(css_file)
        if css_path.exists():
            with open(css_path, encoding='utf-8') as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ فایل CSS یافت نشد: {css_file}")


load_css()


# ===== Initialize Settings =====
@st.cache_resource
def init_app():
    """Initialize application settings and components."""
    try:
        settings = get_settings()
        return settings
    except Exception as e:
        st.error(f"❌ خطا در بارگذاری تنظیمات: {str(e)}")
        st.info("لطفاً فایل .env را بر اساس .env.example ایجاد کرده و OPENAI_API_KEY خود را وارد کنید.")
        st.stop()


settings = init_app()


# ===== Initialize Session State =====
def init_session_state():
    """Initialize session state variables."""
    if 'case_counter' not in st.session_state:
        st.session_state.case_counter = 1

    if 'current_case' not in st.session_state:
        st.session_state.current_case = None

    if 'current_case_graph' not in st.session_state:
        st.session_state.current_case_graph = None


init_session_state()


# ===== Main Application =====
def main():
    """Main application logic."""

    # Render sidebar
    sidebar.render_sidebar(st.session_state.current_case)

    # Main content header
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 3rem; margin-bottom: 0.5rem;'>⚖️ شبیه‌ساز هوشمند تصمیم‌گیری قضایی</h1>
        <p style='font-size: 1.25rem; color: #94a3b8;'>
            سیستم تحلیل و شبیه‌سازی پرونده‌های غصب و خلع ید با هوش مصنوعی
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs([
        "📝 ورودی پرونده",
        "🔍 تحلیل قضایی",
        "🕸️ گراف استدلال"
    ])

    # Tab 1: Case Input
    with tab1:
        st.markdown("## ورودی اطلاعات پرونده")

        # Sample case loader button
        input_form.render_sample_case_loader()

        st.markdown("---")

        # Render input form
        case_data = input_form.render_input_form()

        if case_data:
            # Store in session state
            st.session_state.current_case = case_data

            # Show success message
            st.success("✅ اطلاعات پرونده ثبت شد! به تب 'تحلیل قضایی' بروید.")

            # Auto-switch to analysis tab hint
            st.info("💡 برای مشاهده تحلیل، روی تب 'تحلیل قضایی' کلیک کنید.")

    # Tab 2: Judicial Analysis
    with tab2:
        if st.session_state.current_case:
            # Perform and display analysis
            analysis_view.render_analysis(st.session_state.current_case)

            # After analysis, update graph in session state
            cache_key = f"analysis_{st.session_state.current_case['case_id']}"
            if cache_key in st.session_state:
                cached_analysis = st.session_state[cache_key]
                if 'graph' in cached_analysis:
                    st.session_state.current_case_graph = cached_analysis['graph']

        else:
            # No case entered yet
            st.info("📋 لطفاً ابتدا در تب 'ورودی پرونده'، اطلاعات پرونده را وارد کنید.")

            # Show sample case info
            st.markdown("""
            ### چگونه استفاده کنیم؟

            1. **ورود اطلاعات**: به تب 'ورودی پرونده' بروید
            2. **پرونده نمونه**: می‌توانید از دکمه 'بارگذاری پرونده نمونه' استفاده کنید
            3. **شرح پرونده**: شرح کامل پرونده را وارد کنید (حداقل ۵۰ کاراکتر)
            4. **تحلیل**: روی دکمه 'شروع تحلیل' کلیک کنید
            5. **نتایج**: نتایج تحلیل در این تب نمایش داده می‌شود

            ### قابلیت‌های سیستم

            ✨ **استخراج خودکار**: نام طرفین، نوع پرونده، واقعیات کلیدی
            📚 **بازیابی مواد**: جستجوی هوشمند در مواد ۳۰۸ تا ۳۲۷ قانون مدنی
            🧠 **تحلیل Chain-of-Thought**: استدلال گام‌به‌گام منطقی
            🕸️ **گراف تعاملی**: نمایش بصری زنجیره استدلال
            ⚖️ **حکم نهایی**: تولید رأی با فرمت رسمی حقوقی
            """)

    # Tab 3: Reasoning Graph
    with tab3:
        graph_view.render_graph_view()


# ===== Footer =====
def render_footer():
    """Render application footer."""
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0; color: #64748b;'>
        <p style='margin-bottom: 0.5rem;'>
            <strong>پایان‌نامه کارشناسی ارشد</strong><br>
            طراحی چت‌بات هوشمند برای شبیه‌سازی تصمیم‌گیری قضایی در پرونده‌های مالکیت (غصب و خلع ید)
        </p>
        <p style='font-size: 0.875rem;'>
            نسخه ۱.۰.۰ | تکنولوژی: GPT-4, RAG, NetworkX, Streamlit
        </p>
        <p style='font-size: 0.875rem;'>
            ساخته شده با ❤️ برای پیشرفت حقوق و فناوری
        </p>
    </div>
    """, unsafe_allow_html=True)


# ===== Run Application =====
if __name__ == "__main__":
    try:
        main()
        render_footer()

    except Exception as e:
        st.error(f"❌ خطای غیرمنتظره: {str(e)}")

        # Show debug info in expander
        with st.expander("🐛 اطلاعات دیباگ"):
            import traceback
            st.code(traceback.format_exc())

        st.info("""
        ### رفع مشکل

        اگر با خطا مواجه شدید، لطفاً موارد زیر را بررسی کنید:

        1. **API Key**: آیا OPENAI_API_KEY در فایل .env تنظیم شده است؟
        2. **فایل‌ها**: آیا تمام فایل‌های پروژه در جای خود هستند؟
        3. **وابستگی‌ها**: آیا تمام پکیج‌های requirements.txt نصب شدهاند؟
        4. **اتصال**: آیا اتصال اینترنت برقرار است؟

        برای نصب وابستگی‌ها:
        ```bash
        pip install -r requirements.txt
        ```

        برای اجرای برنامه:
        ```bash
        streamlit run app.py
        ```
        """)
