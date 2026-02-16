"""
Legal Knowledge Base with RAG (Retrieval-Augmented Generation).

This module manages Iranian Civil Code articles (308-327) about Ghasb,
providing semantic search capabilities using TF-IDF + cosine similarity
(local, no API calls needed for embeddings).

Author: Master's Thesis Project - Mahsa Mirzaei
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config.settings import get_settings


class LegalKnowledgeBase:
    """
    Knowledge base for Iranian Civil Code with semantic search.

    Features:
    - Load articles from JSON
    - TF-IDF local embeddings (no API calls)
    - Cosine similarity search
    - Hybrid search: TF-IDF + keyword matching
    """

    def __init__(self):
        """Initialize knowledge base and load articles."""
        self.settings = get_settings()

        # Paths – anchored to this file's location for portability
        _project_root = Path(__file__).resolve().parent.parent.parent
        self.articles_file = _project_root / "data" / "legal_articles.json"

        # Load articles
        self.articles = self._load_articles()
        self.article_texts = [self._article_to_text(a) for a in self.articles]

        # Build TF-IDF model (local, no API)
        self._vectorizer = TfidfVectorizer(
            analyzer="char_wb",   # char n-grams work well for Persian
            ngram_range=(2, 4),
            max_features=8000,
        )
        self._tfidf_matrix = self._vectorizer.fit_transform(self.article_texts)

    def _load_articles(self) -> List[Dict[str, Any]]:
        """Load legal articles from JSON file."""
        try:
            with open(self.articles_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data['articles']
        except Exception as e:
            st.error(f"❌ خطا در بارگذاری مواد قانونی: {str(e)}")
            return []

    def _article_to_text(self, article: Dict[str, Any]) -> str:
        """
        Convert article to searchable text.

        Combines title, text, keywords, and interpretation for better
        semantic search results.
        """
        parts = [
            f"ماده {article['article_number']}: {article['title']}",
            article['text'],
            " ".join(article.get('keywords', [])),
            article.get('interpretation_notes', '')
        ]
        return " ".join(parts)

    def retrieve_relevant_articles(
        self,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        use_hybrid: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve most relevant articles for a query using local TF-IDF.

        No API calls needed — everything runs locally.
        """
        top_k = top_k or self.settings.TOP_K_ARTICLES
        similarity_threshold = similarity_threshold or self.settings.SIMILARITY_THRESHOLD

        # TF-IDF similarity (local, no API)
        query_vec = self._vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self._tfidf_matrix).flatten()

        # Get top-k indices
        top_indices = similarities.argsort()[::-1][:top_k]

        results = []
        for idx in top_indices:
            article = self.articles[idx].copy()
            similarity = float(similarities[idx])

            # Keyword matching bonus (hybrid approach)
            if use_hybrid:
                keyword_score = self._keyword_match_score(query, article)
                final_score = 0.7 * similarity + 0.3 * keyword_score
            else:
                final_score = similarity

            article['relevance_score'] = final_score
            article['similarity'] = similarity

            if final_score >= similarity_threshold:
                results.append(article)

        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results

    def _keyword_match_score(self, query: str, article: Dict[str, Any]) -> float:
        """
        Calculate keyword match score between query and article.

        Simple but effective: count how many article keywords appear in query.
        """
        query_lower = query.lower()
        keywords = article.get('keywords', [])

        if not keywords:
            return 0.0

        matches = sum(1 for kw in keywords if kw.lower() in query_lower)
        return matches / len(keywords)

    def get_article_by_number(self, article_num: int) -> Optional[Dict[str, Any]]:
        """
        Get article by its number (308-327).

        Args:
            article_num: Article number

        Returns:
            Article dict or None if not found
        """
        for article in self.articles:
            if article['article_number'] == article_num:
                return article.copy()
        return None

    def get_related_articles(
        self,
        article_num: int,
        depth: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get articles related to a given article.

        Traverses the 'related_articles' graph to find connected articles.

        Args:
            article_num: Starting article number
            depth: How many levels to traverse

        Returns:
            List of related articles
        """
        visited = set()
        queue = [(article_num, 0)]  # (article_num, current_depth)
        results = []

        while queue:
            current_num, current_depth = queue.pop(0)

            if current_num in visited or current_depth > depth:
                continue

            visited.add(current_num)
            article = self.get_article_by_number(current_num)

            if article and current_num != article_num:  # Don't include starting article
                results.append(article)

            # Add related articles to queue
            if article and current_depth < depth:
                for related_num in article.get('related_articles', []):
                    if related_num not in visited:
                        queue.append((related_num, current_depth + 1))

        return results

    def get_all_articles(self) -> List[Dict[str, Any]]:
        """Get all articles in the knowledge base."""
        return [a.copy() for a in self.articles]

    def get_legal_concept(self, concept_name: str) -> Optional[Dict[str, Any]]:
        """
        Get definition and details of a legal concept.

        Args:
            concept_name: Name of concept (e.g., 'غصب', 'خلع_ید')

        Returns:
            Concept details or None
        """
        try:
            with open(self.articles_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                concepts = data.get('legal_concepts', {})
                return concepts.get(concept_name)
        except Exception:
            return None

    def search_by_keywords(self, keywords: List[str], match_all: bool = False) -> List[Dict[str, Any]]:
        """
        Search articles by keywords.

        Args:
            keywords: List of keywords to search for
            match_all: If True, article must contain all keywords

        Returns:
            Matching articles
        """
        results = []

        for article in self.articles:
            article_keywords = [kw.lower() for kw in article.get('keywords', [])]
            article_text = article['text'].lower()

            if match_all:
                # Must match all keywords
                if all(any(kw.lower() in article_text or kw.lower() in article_keywords
                          for kw in [keyword])
                      for keyword in keywords):
                    results.append(article.copy())
            else:
                # Match any keyword
                if any(kw.lower() in article_text or kw.lower() in article_keywords
                      for kw in keywords):
                    results.append(article.copy())

        return results


# Global instance
_kb_instance: Optional[LegalKnowledgeBase] = None

@st.cache_resource
def get_knowledge_base() -> LegalKnowledgeBase:
    """
    Get the global knowledge base instance (cached by Streamlit).

    Returns:
        LegalKnowledgeBase singleton
    """
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = LegalKnowledgeBase()
    return _kb_instance
