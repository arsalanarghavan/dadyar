"""
Plotly Renderer - Interactive Graph Visualization with Persian Support.

Converts NetworkX reasoning graph to interactive Plotly figure.

Features:
- Hierarchical layout (Facts → Articles → Deductions → Verdict)
- Interactive hover tooltips with Persian text
- Zoom/pan capabilities
- Color-coded nodes by type
- Persian font rendering (Vazir)
- Dark theme compatible with shadcn aesthetic

Author: Master's Thesis Project - Mahsa Mirzaei
"""

import networkx as nx
import plotly.graph_objects as go
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

from config.settings import get_settings


class PlotlyRenderer:
    """
    Render NetworkX graph as interactive Plotly visualization.
    """

    def __init__(self):
        """Initialize renderer with settings."""
        self.settings = get_settings()

    def render(
        self,
        graph: nx.DiGraph,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> go.Figure:
        """
        Render graph as Plotly figure.

        Args:
            graph: NetworkX directed graph
            width: Figure width in pixels
            height: Figure height in pixels

        Returns:
            Plotly Figure object
        """
        width = width or self.settings.GRAPH_WIDTH
        height = height or self.settings.GRAPH_HEIGHT

        # Calculate hierarchical layout
        pos = self._calculate_hierarchical_layout(graph)

        # Create edge traces
        edge_trace = self._create_edge_trace(graph, pos)

        # Create node traces (one per node type for legend)
        node_traces = self._create_node_traces(graph, pos)

        # Combine all traces
        fig = go.Figure(data=[edge_trace] + node_traces)

        # Configure layout
        fig = self._configure_layout(fig, width, height)

        return fig

    def _calculate_hierarchical_layout(self, graph: nx.DiGraph) -> Dict[str, Tuple[float, float]]:
        """
        Calculate hierarchical node positions.

        Arranges nodes in layers: FACT → ARTICLE → DEDUCTION → VERDICT

        Args:
            graph: NetworkX graph

        Returns:
            Dict mapping node ID to (x, y) position
        """
        # Define layer order and Y positions
        layers = {
            'FACT': (0, 0.9),
            'ARTICLE': (1, 0.6),
            'DEDUCTION': (2, 0.3),
            'VERDICT': (3, 0.0)
        }

        # Group nodes by type
        nodes_by_layer = {}
        for node_id, data in graph.nodes(data=True):
            node_type = data.get('node_type')
            if node_type not in nodes_by_layer:
                nodes_by_layer[node_type] = []
            nodes_by_layer[node_type].append(node_id)

        # Calculate positions
        pos = {}
        for node_type, (layer_index, y_base) in layers.items():
            nodes = nodes_by_layer.get(node_type, [])
            num_nodes = len(nodes)

            if num_nodes == 0:
                continue

            # Distribute nodes horizontally across the layer
            for i, node_id in enumerate(nodes):
                # Center nodes if only one or two
                if num_nodes == 1:
                    x = 0.5
                else:
                    # Spread nodes evenly
                    x = 0.1 + (i / (num_nodes - 1)) * 0.8

                pos[node_id] = (x, y_base)

        return pos

    def _create_edge_trace(self, graph: nx.DiGraph, pos: Dict) -> go.Scatter:
        """
        Create edge trace for graph connections.

        Args:
            graph: NetworkX graph
            pos: Node positions

        Returns:
            Plotly Scatter trace for edges
        """
        edge_x = []
        edge_y = []

        for edge in graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]

            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            mode='lines',
            line=dict(
                width=2,
                color='#475569'  # Subtle gray for edges
            ),
            hoverinfo='none',
            showlegend=False
        )

        return edge_trace

    def _create_node_traces(self, graph: nx.DiGraph, pos: Dict) -> List[go.Scatter]:
        """
        Create node traces (one per node type for legend).

        Args:
            graph: NetworkX graph
            pos: Node positions

        Returns:
            List of Plotly Scatter traces
        """
        # Group nodes by type
        node_groups = {
            'FACT': {'nodes': [], 'color': self.settings.NODE_COLOR_FACT, 'label': 'واقعیات'},
            'ARTICLE': {'nodes': [], 'color': self.settings.NODE_COLOR_ARTICLE, 'label': 'مواد قانونی'},
            'DEDUCTION': {'nodes': [], 'color': self.settings.NODE_COLOR_DEDUCTION, 'label': 'نتیجه‌گیری'},
            'VERDICT': {'nodes': [], 'color': self.settings.NODE_COLOR_VERDICT, 'label': 'حکم نهایی'}
        }

        for node_id, data in graph.nodes(data=True):
            node_type = data.get('node_type')
            if node_type in node_groups:
                node_groups[node_type]['nodes'].append((node_id, data))

        # Create trace for each node type
        traces = []
        for node_type, group_data in node_groups.items():
            if not group_data['nodes']:
                continue

            node_x = []
            node_y = []
            node_text = []
            node_sizes = []
            hover_text = []

            for node_id, data in group_data['nodes']:
                x, y = pos[node_id]
                node_x.append(x)
                node_y.append(y)

                # Node label
                label = data.get('label', node_id)
                node_text.append(label)

                # Node size
                size = data.get('size', 20)
                node_sizes.append(size)

                # Hover text
                text = data.get('text', '')
                confidence = data.get('confidence', 0.0)
                article_num = data.get('article_number')

                hover_parts = [f"<b>{label}</b>"]
                if article_num:
                    hover_parts.append(f"شماره ماده: {article_num}")
                hover_parts.append(f"اطمینان: {confidence*100:.0f}%")

                # Truncate text for hover
                text_preview = text[:150] + "..." if len(text) > 150 else text
                hover_parts.append(f"<br>{text_preview}")

                hover_text.append("<br>".join(hover_parts))

            trace = go.Scatter(
                x=node_x,
                y=node_y,
                mode='markers+text',
                name=group_data['label'],
                text=node_text,
                textposition='bottom center',
                textfont=dict(
                    family=self.settings.FONT_FAMILY,
                    size=12,
                    color='#f8fafc'
                ),
                marker=dict(
                    size=node_sizes,
                    color=group_data['color'],
                    line=dict(width=2, color='#1e293b')
                ),
                hovertext=hover_text,
                hoverinfo='text',
                hoverlabel=dict(
                    bgcolor='#1e293b',
                    font=dict(
                        family=self.settings.FONT_FAMILY,
                        size=13,
                        color='#f8fafc'
                    ),
                    bordercolor=group_data['color']
                )
            )

            traces.append(trace)

        return traces

    def _configure_layout(self, fig: go.Figure, width: int, height: int) -> go.Figure:
        """
        Configure figure layout with Persian font and dark theme.

        Args:
            fig: Plotly figure
            width: Width in pixels
            height: Height in pixels

        Returns:
            Configured figure
        """
        fig.update_layout(
            title=dict(
                text="گراف استدلال قضایی",
                font=dict(
                    family=self.settings.FONT_FAMILY,
                    size=24,
                    color='#f8fafc'
                ),
                x=0.5,
                xanchor='center'
            ),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(
                    family=self.settings.FONT_FAMILY,
                    size=14,
                    color='#f8fafc'
                ),
                bgcolor='#0f172a',
                bordercolor='#334155',
                borderwidth=1
            ),
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=80),
            plot_bgcolor='#0f172a',  # Dark background
            paper_bgcolor='#020617',  # Darker outer background
            width=width,
            height=height,
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-0.05, 1.05]
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-0.1, 1.0]
            ),
            font=dict(
                family=self.settings.FONT_FAMILY,
                color='#f8fafc'
            )
        )

        # Enable drag mode for better interaction
        fig.update_layout(
            dragmode='pan',
            modebar=dict(
                bgcolor='#1e293b',
                color='#94a3b8',
                activecolor='#3b82f6'
            )
        )

        return fig


# Global instance
_renderer_instance: Optional[PlotlyRenderer] = None

def get_plotly_renderer() -> PlotlyRenderer:
    """
    Get global Plotly renderer instance.

    Returns:
        PlotlyRenderer singleton
    """
    global _renderer_instance
    if _renderer_instance is None:
        _renderer_instance = PlotlyRenderer()
    return _renderer_instance
