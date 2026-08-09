"""Milvus vector retriever for semantic search."""

from typing import Any

from loguru import logger

from app.core.config import get_settings
from app.core.infra.milvus_client import MilvusClientWrapper
from app.core.infra.llm_factory import LLMFactory
from app.core.models import RetrievalResult


class MilvusRetriever:
    """Milvus-based semantic retriever."""

    @classmethod
    async def search(
        cls,
        query: str,
        top_n: int | None = None,
        filters: dict[str, Any] | None = None
    ) -> list[RetrievalResult]:
        """
        Search resumes using semantic similarity.
        
        Args:
            query: Query text (JD or HyDE document)
            top_n: Number of results to return
            filters: Optional filters (e.g., min_years, min_degree)
            
        Returns:
            List of RetrievalResult
        """
        settings = get_settings()
        top_n = top_n or settings.retrieval.milvus_top_n
        
        # Embed the query
        query_embedding = await LLMFactory.embed_query(query)
        
        # Build search parameters
        search_params = {
            "metric_type": settings.milvus.metric_type,
            "params": {"ef": settings.milvus.hnsw_ef_search}
        }
        
        # Build filter expression
        expr = cls._build_filter_expr(filters)
        
        try:
            client = MilvusClientWrapper.get_client()
            
            # Perform search
            results = client.search(
                collection_name=settings.milvus.collection,
                data=[query_embedding],
                limit=top_n,
                output_fields=["resume_id", "doc_type", "section_name", "text"],
                search_params=search_params,
                filter=expr if expr else ""
            )
            
            # Process results
            retrieval_results = []
            seen_resume_ids = set()
            
            for hits in results:
                for hit in hits:
                    resume_id = hit["entity"]["resume_id"]
                    
                    # Deduplicate by resume_id (keep highest score)
                    if resume_id in seen_resume_ids:
                        continue
                    seen_resume_ids.add(resume_id)
                    
                    # Convert distance to similarity score (0-1)
                    distance = hit["distance"]
                    score = cls._distance_to_score(distance, settings.milvus.metric_type)
                    
                    retrieval_results.append(RetrievalResult(
                        resume_id=resume_id,
                        score=score,
                        source="milvus",
                        matched_sections=[hit["entity"].get("section_name", "")]
                    ))
            
            logger.info(f"Milvus search returned {len(retrieval_results)} unique resumes")
            return retrieval_results
            
        except Exception as e:
            logger.error(f"Milvus search failed: {e}")
            return []

    @classmethod
    async def search_with_hyde(
        cls,
        jd_text: str,
        hyde_doc: str,
        hyde_weight: float | None = None,
        top_n: int | None = None,
        filters: dict[str, Any] | None = None
    ) -> list[RetrievalResult]:
        """
        Search using weighted combination of JD and HyDE document embeddings.
        
        Args:
            jd_text: Original JD text
            hyde_doc: Generated hypothetical document
            hyde_weight: Weight for HyDE embedding (0-1), default from config
            top_n: Number of results
            filters: Optional filters
            
        Returns:
            List of RetrievalResult
        """
        settings = get_settings()
        hyde_weight = hyde_weight or settings.retrieval.hyde_weight
        top_n = top_n or settings.retrieval.milvus_top_n
        
        # Embed both queries
        jd_embedding = await LLMFactory.embed_query(jd_text)
        hyde_embedding = await LLMFactory.embed_query(hyde_doc)
        
        # Weighted combination
        combined_embedding = [
            jd_emb * (1 - hyde_weight) + hyde_emb * hyde_weight
            for jd_emb, hyde_emb in zip(jd_embedding, hyde_embedding)
        ]
        
        # Normalize
        norm = sum(x * x for x in combined_embedding) ** 0.5
        if norm > 0:
            combined_embedding = [x / norm for x in combined_embedding]
        
        # Build search parameters
        search_params = {
            "metric_type": settings.milvus.metric_type,
            "params": {"ef": settings.milvus.hnsw_ef_search}
        }
        
        # Build filter expression
        expr = cls._build_filter_expr(filters)
        
        try:
            client = MilvusClientWrapper.get_client()
            
            # Perform search
            results = client.search(
                collection_name=settings.milvus.collection,
                data=[combined_embedding],
                limit=top_n,
                output_fields=["resume_id", "doc_type", "section_name", "text"],
                search_params=search_params,
                filter=expr if expr else ""
            )
            
            # Process results
            retrieval_results = []
            seen_resume_ids = set()
            
            for hits in results:
                for hit in hits:
                    resume_id = hit["entity"]["resume_id"]
                    
                    if resume_id in seen_resume_ids:
                        continue
                    seen_resume_ids.add(resume_id)
                    
                    distance = hit["distance"]
                    score = cls._distance_to_score(distance, settings.milvus.metric_type)
                    
                    retrieval_results.append(RetrievalResult(
                        resume_id=resume_id,
                        score=score,
                        source="milvus",
                        matched_sections=[hit["entity"].get("section_name", "")]
                    ))
            
            logger.info(f"Milvus HyDE search returned {len(retrieval_results)} unique resumes")
            return retrieval_results
            
        except Exception as e:
            logger.error(f"Milvus HyDE search failed: {e}")
            return []

    @staticmethod
    def _build_filter_expr(filters: dict[str, Any] | None) -> str | None:
        """Build Milvus filter expression from filters dict."""
        if not filters:
            return None
        
        expr_parts = []
        
        # Note: Milvus filtering on resume metadata is limited
        # For complex filtering, we rely on ES or post-filtering
        # Here we just handle simple cases
        
        # Example: filter by doc_type
        if "doc_type" in filters:
            expr_parts.append(f'doc_type == "{filters["doc_type"]}"')
        
        return " and ".join(expr_parts) if expr_parts else None

    @staticmethod
    def _distance_to_score(distance: float, metric_type: str) -> float:
        """Convert distance to similarity score (0-1)."""
        if metric_type == "COSINE" or metric_type == "IP":
            # Cosine similarity and inner product are already in [0, 1] or [-1, 1]
            return max(0.0, min(1.0, (distance + 1) / 2))
        elif metric_type == "L2":
            # L2 distance: lower is better, convert to similarity
            return 1.0 / (1.0 + distance)
        else:
            return distance
