"""Hybrid retrieval pipeline orchestrating multiple retrieval sources."""

import asyncio
from typing import Any

from loguru import logger

from app.core.config import get_settings
from app.core.models import JDQuery, RetrievalResult, RecommendResult
from app.core.retrieval.jd_parser import JDParser
from app.core.retrieval.milvus_retriever import MilvusRetriever
from app.core.retrieval.es_retriever import ESRetriever
from app.core.retrieval.fusion import ResultFusion
from app.core.retrieval.reranker import Reranker
from app.core.infra.llm_factory import LLMFactory


class HybridRetrievalPipeline:
    """Orchestrate the full hybrid retrieval process."""

    @classmethod
    async def retrieve(
        cls,
        jd_text: str,
        top_k: int | None = None,
        use_hyde: bool = True,
        use_rerank: bool = True,
        filters: dict[str, Any] | None = None
    ) -> tuple[JDQuery, list[RetrievalResult]]:
        """
        Execute full hybrid retrieval pipeline.
        
        Pipeline:
        1. Parse JD → structured query
        2. Generate HyDE document (optional)
        3. Parallel retrieval: Milvus (semantic) + ES (keyword)
        4. RRF fusion
        5. Reranking (optional)
        
        Args:
            jd_text: Raw job description text
            top_k: Number of final results
            use_hyde: Whether to use HyDE technique
            use_rerank: Whether to apply reranking
            filters: Optional filters (min_years, min_degree, etc.)
            
        Returns:
            Tuple of (JDQuery, list of RetrievalResult)
        """
        settings = get_settings()
        top_k = top_k or settings.retrieval.final_top_k
        
        logger.info(f"Starting hybrid retrieval for JD: {jd_text[:100]}...")
        
        # Step 1: Parse JD
        jd_query = await JDParser.parse(jd_text)
        logger.info(f"JD parsed: {len(jd_query.must_skills)} must skills, {len(jd_query.nice_skills)} nice skills")
        
        # Step 2: Generate HyDE document
        hyde_doc = None
        if use_hyde:
            hyde_doc = await JDParser.generate_hyde_document(jd_query)
        
        # Step 3: Parallel retrieval
        milvus_task = cls._milvus_search(jd_text, hyde_doc, filters)
        es_task = ESRetriever.search(jd_query)
        
        milvus_results, es_results = await asyncio.gather(
            milvus_task,
            es_task,
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(milvus_results, Exception):
            logger.error(f"Milvus retrieval failed: {milvus_results}")
            milvus_results = []
        if isinstance(es_results, Exception):
            logger.error(f"ES retrieval failed: {es_results}")
            es_results = []
        
        logger.info(f"Retrieved: Milvus={len(milvus_results)}, ES={len(es_results)}")
        
        # Step 4: Fusion
        fused_results = ResultFusion.rrf_fusion(
            [milvus_results, es_results],
            top_n=top_k * 3  # Keep more for reranking
        )
        
        logger.info(f"Fused to {len(fused_results)} results")
        
        # Step 5: Reranking (if enabled and we have results)
        if use_rerank and fused_results and settings.reranker.enabled:
            documents = await cls._fetch_documents([r.resume_id for r in fused_results])
            if documents:
                if LLMFactory.get_reranker() is not None:
                    fused_results = await Reranker.rerank(
                        query=hyde_doc or jd_text,
                        results=fused_results,
                        documents=documents,
                        top_k=top_k
                    )
                else:
                    # Cross-Encoder 不可用时降级为 LLM 精排
                    fused_results = await Reranker.llm_rerank(
                        query=jd_text,
                        results=fused_results,
                        documents=documents,
                        top_k=top_k
                    )
        
        # Final truncation
        final_results = fused_results[:top_k]
        
        logger.info(f"Final results: {len(final_results)}")
        return jd_query, final_results

    @staticmethod
    async def _fetch_documents(resume_ids: list[str]) -> dict[str, str]:
        """Fetch resume texts from MongoDB for reranking."""
        try:
            from app.core.infra.mongo_client import MongoDBClient
            collection = MongoDBClient.get_collection()
            cursor = collection.find(
                {"resume_id": {"$in": resume_ids}},
                {"resume_id": 1, "full_text": 1, "summary": 1}
            )
            documents = {}
            async for doc in cursor:
                text = doc.get("summary") or doc.get("full_text", "")
                if text:
                    documents[doc["resume_id"]] = text[:1500]
            return documents
        except Exception as e:
            logger.error(f"Fetch documents failed: {e}")
            return {}

    @classmethod
    async def _milvus_search(
        cls,
        jd_text: str,
        hyde_doc: str | None,
        filters: dict[str, Any] | None
    ) -> list[RetrievalResult]:
        """Execute Milvus search with or without HyDE."""
        settings = get_settings()
        
        if hyde_doc:
            return await MilvusRetriever.search_with_hyde(
                jd_text=jd_text,
                hyde_doc=hyde_doc,
                hyde_weight=settings.retrieval.hyde_weight,
                top_n=settings.retrieval.milvus_top_n,
                filters=filters
            )
        else:
            return await MilvusRetriever.search(
                query=jd_text,
                top_n=settings.retrieval.milvus_top_n,
                filters=filters
            )

    @classmethod
    async def retrieve_simple(
        cls,
        query_text: str,
        top_k: int = 10
    ) -> list[RetrievalResult]:
        """
        Simple retrieval without JD parsing (for conversational search).
        
        Args:
            query_text: Raw query text
            top_k: Number of results
            
        Returns:
            List of RetrievalResult
        """
        # Parallel retrieval
        milvus_task = MilvusRetriever.search(query_text, top_n=top_k * 2)
        es_task = ESRetriever.simple_search(query_text, top_n=top_k * 2)
        
        milvus_results, es_results = await asyncio.gather(
            milvus_task,
            es_task,
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(milvus_results, Exception):
            milvus_results = []
        if isinstance(es_results, Exception):
            es_results = []
        
        # Fusion
        fused = ResultFusion.rrf_fusion(
            [milvus_results, es_results],
            top_n=top_k
        )
        
        return fused
