"""Input Form — Case data entry tab."""

import json
import streamlit as st
from pathlib import Path
from typing import Optional, Dict, Any

from modules.ui_components.persian_utils import get_persian_utils


def render_input_form() -> Optional[Dict[str, Any]]:
    """Render case input form. Returns dict with case data if submitted."""
    utils = get_persian_utils()

    sample = st.session_state.get("sample_case", {})

    with st.form("case_input_form", clear_on_submit=False):
        # Row 1: meta
        col1, col2 = st.columns(2)
        with col1:
            case_id = st.text_input(
                "شناسه پرونده",
                value=sample.get("case_id", f"1403-{st.session_state.get('case_counter', 1):03d}"),
            )
        with col2:
            case_date = st.text_input(
                "تاریخ",
                value=sample.get("date", utils.format_persian_date()),
            )

        # Row 2: parties
        col3, col4 = st.columns(2)
        with col3:
            plaintiff = st.text_input(
                "خواهان",
                value=sample.get("plaintiff", ""),
                placeholder="نام و نام خانوادگی",
            )
        with col4:
            defendant = st.text_input(
                "خوانده",
                value=sample.get("defendant", ""),
                placeholder="نام و نام خانوادگی",
            )

        # Description
        case_description = st.text_area(
            "شرح پرونده",
            value=sample.get("description", ""),
            height=220,
            placeholder=(
                "شرح کامل پرونده شامل واقعیات، ادعاها و شواهد را بنویسید…"
            ),
        )

        submitted = st.form_submit_button(
            "شروع تحلیل",
            use_container_width=True,
            type="primary",
        )

        if submitted:
            errors = []
            if not case_description or len(case_description.strip()) < 50:
                errors.append("شرح پرونده باید حداقل ۵۰ کاراکتر باشد.")
            if not plaintiff and not defendant:
                errors.append("حداقل یکی از طرفین را وارد کنید.")
            if errors:
                for e in errors:
                    st.error(e)
                return None

            st.session_state.case_counter = st.session_state.get("case_counter", 1) + 1

            return {
                "case_id": case_id,
                "date": case_date,
                "plaintiff": plaintiff or "نامشخص",
                "defendant": defendant or "نامشخص",
                "description": case_description.strip(),
            }

    return None


def load_sample_case() -> Optional[Dict[str, Any]]:
    """Load first sample case from data file."""
    sample_path = Path(__file__).resolve().parent.parent.parent / "data" / "sample_cases.json"
    try:
        with open(sample_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("cases"):
                s = data["cases"][0]
                return {
                    "case_id": s["case_id"],
                    "date": s["date"],
                    "plaintiff": s["plaintiff"],
                    "defendant": s["defendant"],
                    "description": s["description"],
                }
    except Exception:
        pass
    return None


def render_sample_case_loader():
    """Button to load a demo case."""
    if st.button("بارگذاری پرونده نمونه"):
        sample = load_sample_case()
        if sample:
            st.session_state.sample_case = sample
            st.toast("پرونده نمونه بارگذاری شد")
            st.rerun()
        else:
            st.error("فایل نمونه یافت نشد.")
