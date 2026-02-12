"""
Legal Knowledge Base with RAG (Retrieval-Augmented Generation).

This module manages Iranian Civil Code articles (308-327) about Ghasb,
providing semantic search capabilities using FAISS vector store and
OpenAI embeddings.

Author: Master's Thesis Project - Mahsa Mirzaei
"""

import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import streamlit as st
import faiss
from sklearn.metrics.pairwise import cosine_similarity

from modules.legal_engine.openai_client import get_openai_client
from config.settings import get_settings


class LegalKnowledgeBase:
    """
    Knowledge base for Iranian Civil Code with semantic search.

    Features:
    - Load articles from JSON
    - Generate embeddings for all articles
    - FAISS vector store for similarity search
    - Hybrid search: semantic + keyword matching
    - Cache embeddings to avoid repeated API calls
    """

    def __init__(self):
        """Initialize knowledge base and load articles."""
        self.settings = get_settings()
        self.client = get_openai_client()

        # Paths
        self.articles_file = Path("data/legal_articles.json")
        self.embeddings_cache = Path("data/embeddings_cache.pkl")

        # Load articles
        self.articles = self._load_articles()
        self.article_texts = [self._article_to_text(a) for a in self.articles]

        # Load or generate embeddings
        self.embeddings = self._load_or_generate_embeddings()

        # Build FAISS index
        self.index = self._build_faiss_index()

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

    def _load_or_generate_embeddings(self) -> np.ndarray:
        """
        Load embeddings from cache or generate new ones.

        For thesis: This caching strategy significantly reduces API costs
        and latency during development and demonstrations.
        """
        # Try to load from cache
        if self.embeddings_cache.exists():
            try:
                with open(self.embeddings_cache, 'rb') as f:
                    cached_data = pickle.load(f)
                    # Verify cache is valid
                    if len(cached_data) == len(self.articles):
                        st.success("✅ embeddings از حافظه بارگذاری شدند")
                        return np.array(cached_data)
            except Exception as e:
                st.warning(f"⚠️ خطا در بارگذاری cache: {str(e)}")

        # Generate new embeddings
        st.info("🔄 در حال تولید embeddings برای مواد قانونی...")
        progress_bar = st.progress(0)

        embeddings_list = []
        for i, text in enumerate(self.article_texts):
            embedding = self.client.get_embedding(text)
            if embedding:
                embeddings_list.append(embedding)
            else:
                # Fallback: zero vector if embedding fails
                embeddings_list.append([0.0] * self.settings.EMBEDDING_DIMENSION)

            progress_bar.progress((i + 1) / len(self.article_texts))

        embeddings = np.array(embeddings_list)

        # Cache for future use
        try:
            self.embeddings_cache.parent.mkdir(parents=True, exist_ok=True)
            with open(self.embeddings_cache, 'wb') as f:
                pickle.dump(embeddings_list, f)
            st.success("✅ embeddings ذخیره شدند")
        except Exception as e:
            st.warning(f"⚠️ خطا در ذخیره cache: {str(e)}")

        return embeddings

    def _build_faiss_index(self) -> faiss.Index:
        """
        Build FAISS index for fast similarity search.

        FAISS (Facebook AI Similarity Search) provides efficient
        nearest neighbor search in high-dimensional spaces.
        """
        dimension = self.settings.EMBEDDING_DIMENSION
        index = faiss.IndexFlatL2(dimension)  # L2 distance
        index.add(self.embeddings.astype('float32'))
        return index

    def retrieve_relevant_articles(
        self,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        use_hybrid: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve most relevant articles for a query using RAG.

        Args:
            query: User query (e.g., case description)
            top_k: Number of articles to retrieve
            similarity_threshold: Minimum similarity score (0-1)
            use_hybrid: Use both semantic and keyword matching

        Returns:
            List of articles with relevance scores
        """
        top_k = top_k or self.settings.TOP_K_ARTICLES
        similarity_threshold = similarity_threshold or self.settings.SIMILARITY_THRESHOLD

        # Generate query embedding
        query_embedding = self.client.get_embedding(query)
        if not query_embedding:
            st.error("❌ خطا در تولید embedding برای query")
            return []

        query_vector = np.array([query_embedding]).astype('float32')

        # FAISS search
        distances, indices = self.index.search(query_vector, top_k)

        # Convert distances to similarity scores (cosine similarity)
        # FAISS returns L2 distances, convert to similarity
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            article = self.articles[idx].copy()

            # Calculate cosine similarity
            similarity = 1 / (1 + distance)  # Simple conversion

            # Keyword matching bonus (hybrid approach)
            if use_hybrid:
                keyword_score = self._keyword_match_score(query, article)
                # Combine semantic and keyword scores
                final_score = 0.7 * similarity + 0.3 * keyword_score
            else:
                final_score = similarity

            article['relevance_score'] = float(final_score)
            article['similarity'] = float(similarity)

            # Only include if above threshold
            if final_score >= similarity_threshold:
                results.append(article)

        # Sort by relevance score
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
