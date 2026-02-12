"""
Reasoning Graph - NetworkX Graph Construction.

Builds a directed graph representing the judicial reasoning chain:
Facts → Articles → Deductions → Verdict

Node types:
- FACT (Blue #3b82f6): Observable facts from the case
- ARTICLE (Green #10b981): Legal articles applied
- DEDUCTION (Yellow #f59e0b): Intermediate conclusions
- VERDICT (Red #ef4444): Final decision

Author: Master's Thesis Project - Mahsa Mirzaei
"""

import networkx as nx
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from modules.legal_engine.reasoning_engine import ReasoningResult, ReasoningStep
from config.settings import get_settings


@dataclass
class GraphNode:
    """Represents a node in the reasoning graph."""
    node_id: str
    node_type: str  # FACT, ARTICLE, DEDUCTION, VERDICT
    text: str
    confidence: float = 0.0
    article_num: Optional[int] = None
    metadata: Dict[str, Any] = None


class ReasoningGraph:
    """
    Construct NetworkX directed graph from reasoning result.

    This graph represents the logical flow of judicial decision-making,
    enabling transparent visualization of the reasoning process.
    """

    def __init__(self):
        """Initialize graph builder."""
        self.settings = get_settings()
        self.graph: Optional[nx.DiGraph] = None
        self.node_counter = 0

    def build_from_reasoning(self, reasoning_result: ReasoningResult) -> nx.DiGraph:
        """
        Build graph from reasoning result.

        Creates hierarchical graph: Facts → Articles → Deductions → Verdict

        Args:
            reasoning_result: Complete reasoning analysis

        Returns:
            NetworkX directed graph
        """
        self.graph = nx.DiGraph()
        self.node_counter = 0

        # Add fact nodes
        fact_nodes = self._add_fact_nodes(reasoning_result.reasoning_steps)

        # Add article nodes and connect to facts
        article_nodes = self._add_article_nodes(
            reasoning_result.reasoning_steps,
            fact_nodes
        )

        # Add deduction nodes and connect to articles
        deduction_nodes = self._add_deduction_nodes(
            reasoning_result.deductions,
            article_nodes
        )

        # Add verdict node and connect to deductions
        verdict_node = self._add_verdict_node(
            reasoning_result,
            deduction_nodes
        )

        return self.graph

    def _add_fact_nodes(self, steps: List[ReasoningStep]) -> List[str]:
        """
        Add fact nodes to graph.

        Args:
            steps: All reasoning steps

        Returns:
            List of fact node IDs
        """
        fact_steps = [s for s in steps if s.step_type == "FACT"]
        node_ids = []

        for step in fact_steps:
            node_id = self._create_node_id("FACT")

            self.graph.add_node(
                node_id,
                node_type="FACT",
                text=step.content,
                confidence=step.confidence,
                color=self.settings.NODE_COLOR_FACT,
                size=20
            )

            node_ids.append(node_id)

        return node_ids

    def _add_article_nodes(
        self,
        steps: List[ReasoningStep],
        fact_nodes: List[str]
    ) -> List[str]:
        """
        Add article nodes and connect them to fact nodes.

        Args:
            steps: All reasoning steps
            fact_nodes: List of fact node IDs

        Returns:
            List of article node IDs
        """
        article_steps = [s for s in steps if s.step_type == "ARTICLE"]
        node_ids = []

        for step in article_steps:
            node_id = self._create_node_id("ARTICLE")

            # Create label with article number
            label = f"ماده {step.related_article}"

            self.graph.add_node(
                node_id,
                node_type="ARTICLE",
                text=step.content,
                label=label,
                article_number=step.related_article,
                confidence=step.confidence,
                color=self.settings.NODE_COLOR_ARTICLE,
                size=30  # Larger for articles
            )

            # Connect to all fact nodes (articles analyze facts)
            for fact_node in fact_nodes:
                self.graph.add_edge(
                    fact_node,
                    node_id,
                    relationship="تطبیق با"
                )

            node_ids.append(node_id)

        return node_ids

    def _add_deduction_nodes(
        self,
        deductions: List[str],
        article_nodes: List[str]
    ) -> List[str]:
        """
        Add deduction nodes and connect to article nodes.

        Args:
            deductions: List of deduction texts
            article_nodes: List of article node IDs

        Returns:
            List of deduction node IDs
        """
        node_ids = []

        for i, deduction in enumerate(deductions, 1):
            node_id = self._create_node_id("DEDUCTION")

            self.graph.add_node(
                node_id,
                node_type="DEDUCTION",
                text=deduction,
                label=f"نتیجه {i}",
                confidence=0.8,
                color=self.settings.NODE_COLOR_DEDUCTION,
                size=25
            )

            # Connect to article nodes (deductions derive from articles)
            for article_node in article_nodes:
                self.graph.add_edge(
                    article_node,
                    node_id,
                    relationship="منجر به"
                )

            node_ids.append(node_id)

        return node_ids

    def _add_verdict_node(
        self,
        reasoning_result: ReasoningResult,
        deduction_nodes: List[str]
    ) -> str:
        """
        Add final verdict node.

        Args:
            reasoning_result: Reasoning result
            deduction_nodes: List of deduction node IDs

        Returns:
            Verdict node ID
        """
        node_id = self._create_node_id("VERDICT")

        # Determine verdict text (simplified)
        verdict_text = f"حکم نهایی\nاطمینان: {reasoning_result.overall_confidence*100:.0f}%"

        self.graph.add_node(
            node_id,
            node_type="VERDICT",
            text=verdict_text,
            label="حکم نهایی",
            confidence=reasoning_result.overall_confidence,
            color=self.settings.NODE_COLOR_VERDICT,
            size=35  # Largest node
        )

        # Connect all deductions to verdict
        for deduction_node in deduction_nodes:
            self.graph.add_edge(
                deduction_node,
                node_id,
                relationship="منتهی به"
            )

        return node_id

    def _create_node_id(self, node_type: str) -> str:
        """
        Create unique node ID.

        Args:
            node_type: Type of node

        Returns:
            Unique node ID
        """
        self.node_counter += 1
        return f"{node_type}_{self.node_counter}"

    def get_node_layers(self) -> Dict[str, List[str]]:
        """
        Get nodes organized by layer (for hierarchical layout).

        Returns:
            Dict mapping layer name to list of node IDs
        """
        if not self.graph:
            return {}

        layers = {
            "FACT": [],
            "ARTICLE": [],
            "DEDUCTION": [],
            "VERDICT": []
        }

        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get('node_type')
            if node_type in layers:
                layers[node_type].append(node_id)

        return layers

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get graph statistics.

        Returns:
            Dict with graph metrics
        """
        if not self.graph:
            return {}

        return {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'num_facts': len([n for n, d in self.graph.nodes(data=True) if d.get('node_type') == 'FACT']),
            'num_articles': len([n for n, d in self.graph.nodes(data=True) if d.get('node_type') == 'ARTICLE']),
            'num_deductions': len([n for n, d in self.graph.nodes(data=True) if d.get('node_type') == 'DEDUCTION']),
            'has_verdict': any(d.get('node_type') == 'VERDICT' for _, d in self.graph.nodes(data=True)),
            'average_confidence': sum(d.get('confidence', 0) for _, d in self.graph.nodes(data=True)) / max(self.graph.number_of_nodes(), 1)
        }
