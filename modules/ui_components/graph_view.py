"""
Graph View - Reasoning Graph Visualization Tab.

Displays interactive Plotly graph of judicial reasoning.

Author: Master's Thesis Project - Mahsa Mirzaei
"""

import streamlit as st
import networkx as nx

from modules.graph_builder.plotly_renderer import get_plotly_renderer


def render_graph_view():
    """Render reasoning graph tab."""
    st.markdown("## 🕸️ گراف استدلال قضایی")
    st.markdown("نمایش تصویری زنجیره استدلال از واقعیات تا حکم نهایی")

    # Check if graph exists in session state
    if 'current_case_graph' in st.session_state:
        graph = st.session_state['current_case_graph']
        display_graph(graph)
    else:
        st.info("📊 پس از تحلیل پرونده، گراف استدلال در این بخش نمایش داده می‌شود.")
        st.markdown("""
        ### درباره گراف استدلال

        این گراف نمایش بصری از فرآیند تصمیم‌گیری قضایی است که شامل:

        - 🔵 **واقعیات (آبی)**: واقعیات مشاهده شده از پرونده
        - 🟢 **مواد قانونی (سبز)**: مواد قانونی قابل اعمال
        - 🟡 **نتیجه‌گیری (زرد)**: استنتاج‌های حقوقی میانی
        - 🔴 **حکم نهایی (قرمز)**: تصمیم نهایی دادگاه

        **ویژگی‌های تعاملی:**
        - ✨ نگه‌داشتن موس روی هر گره: نمایش جزئیات
        - 🔍 زوم و جابجایی: کشیدن برای حرکت، اسکرول برای زوم
        - 📌 کلیک: انتخاب گره
        """)


def display_graph(graph: nx.DiGraph):
    """
    Display the reasoning graph.

    Args:
        graph: NetworkX directed graph
    """
    # Graph statistics
    from modules.graph_builder.reasoning_graph import ReasoningGraph
    graph_builder = ReasoningGraph()
    graph_builder.graph = graph
    stats = graph_builder.get_statistics()

    # Display stats in columns
    cols = st.columns(4)
    with cols[0]:
        st.metric("تعداد گره‌ها", stats['total_nodes'])
    with cols[1]:
        st.metric("تعداد یال‌ها", stats['total_edges'])
    with cols[2]:
        st.metric("مواد قانونی", stats['num_articles'])
    with cols[3]:
        st.metric("میانگین اطمینان", f"{stats['average_confidence']*100:.0f}%")

    st.markdown("---")

    # Render graph
    renderer = get_plotly_renderer()
    fig = renderer.render(graph)

    # Display with Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # Legend explanation
    with st.expander("📖 راهنمای گراف"):
        st.markdown("""
        ### راهنمای خواندن گراف

        **جریان استدلال:**
        1. گره‌های آبی (بالا): واقعیات پرونده
        2. فلش‌ها به پایین: ارتباط منطقی
        3. گره‌های سبز: مواد قانونی که بر واقعیات اعمال می‌شوند
        4. گره‌های زرد: نتیجه‌گیری‌های حقوقی
        5. گره قرمز (پایین): حکم نهایی

        **اعداد روی گره‌ها:**
        - عدد روی هر گره نشان‌دهنده سطح اطمینان (۰-۱۰۰٪) است
        - هرچه عدد بیشتر، اطمینان بالاتر

        **نحوه استفاده:**
        - موس را روی هر گره نگه دارید تا متن کامل نمایش داده شود
        - اسکرول برای زوم کنید
        - کلیک و کشیدن برای جابجایی نمای کلی
        """)

    # Download option
    if st.button("💾 دانلود گراف به صورت تصویر"):
        st.info("برای دانلود، از منوی Plotly در گوشه بالا سمت راست استفاده کنید")
