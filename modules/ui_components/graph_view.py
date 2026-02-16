"""Graph View — reasoning graph visualization tab."""

import streamlit as st
import networkx as nx

from modules.graph_builder.plotly_renderer import get_plotly_renderer


def render_graph_view():
    """Render reasoning graph tab."""

    if "current_case_graph" not in st.session_state or st.session_state.current_case_graph is None:
        st.info("پس از تحلیل پرونده، گراف استدلال اینجا نمایش داده می‌شود.")
        return

    graph: nx.DiGraph = st.session_state["current_case_graph"]

    # Stats
    from modules.graph_builder.reasoning_graph import ReasoningGraph
    gb = ReasoningGraph()
    gb.graph = graph
    stats = gb.get_statistics()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("گره‌ها", stats["total_nodes"])
    c2.metric("یال‌ها", stats["total_edges"])
    c3.metric("مواد قانونی", stats["num_articles"])
    c4.metric("اطمینان", f"{stats['average_confidence']*100:.0f}%")

    # Graph
    renderer = get_plotly_renderer()
    fig = renderer.render(graph)
    st.plotly_chart(fig, use_container_width=True)

    # Legend
    with st.expander("راهنمای رنگ‌ها"):
        st.markdown(
            "**آبی** واقعیات · **سبز** مواد قانونی · "
            "**زرد** نتیجه‌گیری · **قرمز** حکم نهایی"
        )
