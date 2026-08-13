"""Reranker module for fine-grained result refinement."""

import asyncio
from typing import Any

from loguru import logger

from app.core.config import get_settings
from app.core.infra.llm_factory import LLMFactory
from app.core.models import RetrievalResult


class Reranker:
    """Rerank retrieval results using cross-encoder or LLM."""

    @classmethod
    async def rerank(
        cls,
        query: str,
        results: list[RetrievalResult],
        documents: dict[str, str],
        top_k: int | None = None
    ) -> list[RetrievalResult]:
        """
        Rerank results using cross-encoder model.
        
        Args:
            query: Query text (JD or HyDE document)
            results: Initial retrieval results
            documents: Map of resume_id to full text
            top_k: Number of results to return after reranking
            
        Returns:
            Reranked list of RetrievalResult
        """
        settings = get_settings()
        
        if not settings.reranker.enabled:
            logger.info("Reranker disabled, returning original results")
            return results[:top_k]
        
        top_k = top_k or settings.reranker.top_k
        
        # Get documents for reranking
        query_doc_pairs = []
        valid_results = []
        
        for result in results:
            doc_text = documents.get(result.resume_id, "")
            if doc_text:
                query_doc_pairs.append((query, doc_text))
                valid_results.append(result)
        
        if not query_doc_pairs:
            logger.warning("No documents available for reranking")
            return results[:top_k]
        
        try:
            # Use cross-encoder reranker
            queries = [pair[0] for pair in query_doc_pairs]
            docs = [pair[1] for pair in query_doc_pairs]
            
            # Run reranker in thread pool (blocking operation)
            scores = await asyncio.to_thread(
                LLMFactory.rerank,
                query,
                docs
            )
            
            # Update result scores
            reranked_results = []
            for result, score in zip(valid_results, scores):
                reranked_results.append(RetrievalResult(
                    resume_id=result.resume_id,
                    score=float(score),
                    source="reranked",
                    matched_sections=result.matched_sections
                ))
            
            # Sort by rerank score
            reranked_results.sort(key=lambda x: x.score, reverse=True)
            
            logger.info(f"Reranked {len(reranked_results)} results, top score: {reranked_results[0].score:.4f}")
            return reranked_results[:top_k]
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}, returning original results")
            return results[:top_k]

    @classmethod
    async def llm_rerank(
        cls,
        query: str,
        results: list[RetrievalResult],
        documents: dict[str, str],
        top_k: int | None = None
    ) -> list[RetrievalResult]:
        """
        Rerank using LLM pairwise comparison (expensive but accurate).
        
        Args:
            query: Query text
            results: Initial results
            documents: Map of resume_id to full text
            top_k: Number of results to return
            
        Returns:
            Reranked results
        """
        settings = get_settings()
        top_k = top_k or settings.reranker.top_k
        
        if len(results) <= top_k:
            return results
        
        try:
            from langchain_core.prompts import ChatPromptTemplate
            
            rerank_prompt = ChatPromptTemplate.from_messages([
                ("system", """你是一个专业的简历评估专家。请根据岗位需求对候选人简历进行排序。

                岗位需求：{query}

                请对以下候选人按匹配度从高到低排序，返回 resume_id 列表（用逗号分隔）。

                候选人列表：
                {candidates}

                只返回 resume_id 列表，不要其他文字。"""),
                                ("human", "请排序以上候选人。")
                            ])
            
            # Build candidates text
            candidates_text = []
            for i, result in enumerate(results[:20], 1):  # Limit to top 20 for LLM
                doc_text = documents.get(result.resume_id, "")[:500]  # Truncate
                candidates_text.append(f"{i}. resume_id: {result.resume_id}\n摘要: {doc_text}")
            
            candidates_str = "\n\n".join(candidates_text)
            
            llm = LLMFactory.get_llm(streaming=False)
            response = await llm.ainvoke([
                ("system", rerank_prompt.format(query=query[:500], candidates=candidates_str)),
                ("human", "请排序以上候选人。")
            ])
            
            # Parse response
            response_text = response.content if hasattr(response, "content") else str(response)
            ordered_ids = [id.strip() for id in response_text.replace("\n", ",").split(",") if id.strip()]
            
            # Reorder results
            id_to_result = {r.resume_id: r for r in results}
            reranked = []
            for resume_id in ordered_ids:
                if resume_id in id_to_result:
                    reranked.append(id_to_result[resume_id])
            
            # Add any missing results at the end
            seen_ids = set(r.resume_id for r in reranked)
            for result in results:
                if result.resume_id not in seen_ids:
                    reranked.append(result)
            
            logger.info(f"LLM reranked {len(reranked)} results")
            return reranked[:top_k]
            
        except Exception as e:
            logger.error(f"LLM reranking failed: {e}")
            return results[:top_k]
