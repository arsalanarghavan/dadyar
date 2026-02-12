"""
Input Form - Case Input Tab Component.

Provides form for entering case details:
- Case metadata (ID, date, parties)
- Case description (large text area)
- Validation
- Submit button

Author: Master's Thesis Project - Mahsa Mirzaei
"""

import streamlit as st
import jdatetime
from typing import Optional, Dict, Any

from modules.ui_components.persian_utils import get_persian_utils


def render_input_form() -> Optional[Dict[str, Any]]:
    """
    Render case input form.

    Returns:
        Dict with case data if submitted, None otherwise
    """
    utils = get_persian_utils()

    st.markdown("### ورودی اطلاعات پرونده")
    st.markdown("لطفاً اطلاعات پرونده را با دقت وارد کنید.")

    with st.form("case_input_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            case_id = st.text_input(
                "شناسه پرونده",
                value=f"1403-{st.session_state.get('case_counter', 1):03d}",
                help="شناسه منحصربه‌فرد پرونده"
            )

        with col2:
            # Use Persian date
            today = utils.format_persian_date()
            case_date = st.text_input(
                "تاریخ ثبت",
                value=today,
                help="تاریخ ثبت پرونده (تقویم شمسی)"
            )

        col3, col4 = st.columns(2)

        with col3:
            plaintiff = st.text_input(
                "نام خواهان",
                placeholder="نام و نام خانوادگی خواهان",
                help="شخص یا نهادی که شکایت را مطرح کرده است"
            )

        with col4:
            defendant = st.text_input(
                "نام خوانده",
                placeholder="نام و نام خانوادگی خوانده",
                help="شخص یا نهادی که علیه او شکایت شده است"
            )

        # Case description
        st.markdown("### شرح پرونده")
        case_description = st.text_area(
            "شرح کامل پرونده",
            height=300,
            placeholder="لطفاً شرح کامل پرونده شامل واقعیات، ادعاها، و شواهد را به تفصیل بنویسید...\n\nمثال:\nخواهان ادعا می‌کند که خوانده بدون اجازه وارد ملک مسکونی او شده و در آن سکونت دارد...",
            help="هرچه شرح دقیق‌تر باشد، تحلیل بهتر خواهد بود"
        )

        # Submit button
        submitted = st.form_submit_button(
            "🔍 شروع تحلیل پرونده",
            use_container_width=True,
            type="primary"
        )

        if submitted:
            # Validation
            errors = []

            if not case_description or len(case_description.strip()) < 50:
                errors.append("⚠️ شرح پرونده باید حداقل ۵۰ کاراکتر باشد")

            if not plaintiff and not defendant:
                errors.append("⚠️ لطفاً حداقل یکی از طرفین (خواهان یا خوانده) را وارد کنید")

            if errors:
                for error in errors:
                    st.error(error)
                return None

            # Increment counter for next case
            if 'case_counter' not in st.session_state:
                st.session_state.case_counter = 1
            st.session_state.case_counter += 1

            # Return case data
            return {
                'case_id': case_id,
                'date': case_date,
                'plaintiff': plaintiff or "نامشخص",
                'defendant': defendant or "نامشخص",
                'description': case_description.strip()
            }

    return None


def load_sample_case():
    """Load a sample case for demonstration."""
    import json
    from pathlib import Path

    try:
        with open(Path("data/sample_cases.json"), 'r', encoding='utf-8') as f:
            data = json.load(f)
            if data.get('cases'):
                sample = data['cases'][0]
                return {
                    'case_id': sample['case_id'],
                    'date': sample['date'],
                    'plaintiff': sample['plaintiff'],
                    'defendant': sample['defendant'],
                    'description': sample['description']
                }
    except Exception:
        pass

    return None


def render_sample_case_loader():
    """Render button to load sample case."""
    if st.button("📋 بارگذاری پرونده نمونه", help="یک پرونده آزمایشی را بارگذاری کنید"):
        sample = load_sample_case()
        if sample:
            st.session_state.sample_case = sample
            st.success("✅ پرونده نمونه بارگذاری شد! اطلاعات را در فرم زیر مشاهده کنید.")
            st.rerun()
