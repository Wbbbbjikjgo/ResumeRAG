"""Elasticsearch retriever for keyword-based search."""

from typing import Any

from loguru import logger

from app.core.config import get_settings
from app.core.infra.es_client import ElasticsearchClient
from app.core.models import RetrievalResult, JDQuery


class ESRetriever:
    """Elasticsearch-based keyword retriever."""

    @classmethod
    async def search(
        cls,
        jd_query: JDQuery,
        top_n: int | None = None
    ) -> list[RetrievalResult]:
        """
        Search resumes using keyword matching.
        
        Args:
            jd_query: Parsed JD query
            top_n: Number of results to return
            
        Returns:
            List of RetrievalResult
        """
        settings = get_settings()
        top_n = top_n or settings.retrieval.es_top_n
        
        # Build ES query
        query_body = cls._build_query(jd_query)
        
        try:
            client = ElasticsearchClient.get_client()
            
            # Perform search
            response = await client.search(
                index=settings.elasticsearch.index,
                body=query_body,
                size=top_n
            )
            
            # Process results
            retrieval_results = []
            hits = response.get("hits", {}).get("hits", [])
            
            for hit in hits:
                source = hit["_source"]
                resume_id = source.get("resume_id")
                
                if not resume_id:
                    continue
                
                # BM25 score
                score = hit["_score"]
                
                # Normalize score (rough approximation)
                normalized_score = min(1.0, score / 10.0)
                
                retrieval_results.append(RetrievalResult(
                    resume_id=resume_id,
                    score=normalized_score,
                    source="elasticsearch",
                    matched_sections=[]  # ES doesn't track sections
                ))
            
            logger.info(f"ES search returned {len(retrieval_results)} resumes")
            return retrieval_results
            
        except Exception as e:
            logger.error(f"ES search failed: {e}")
            return []

    @classmethod
    def _build_query(cls, jd_query: JDQuery) -> dict:
        """Build Elasticsearch query from JD query."""
        must_clauses = []
        should_clauses = []
        filter_clauses = []
        
        # Must: hard skills (required)
        if jd_query.must_skills:
            must_clauses.append({
                "terms": {
                    "skills": jd_query.must_skills
                }
            })
            
            # Also search in full_text for skills mentioned but not in skills field
            must_clauses.append({
                "bool": {
                    "should": [
                        {"match": {"full_text": skill}} for skill in jd_query.must_skills
                    ],
                    "minimum_should_match": 1
                }
            })
        
        # Should: nice-to-have skills (boost score)
        if jd_query.nice_skills:
            for skill in jd_query.nice_skills:
                should_clauses.append({
                    "term": {"skills": {"value": skill, "boost": 2.0}}
                })
                should_clauses.append({
                    "match": {"full_text": {"query": skill, "boost": 1.0}}
                })
        
        # Should: expanded keywords
        if jd_query.keywords:
            for keyword in jd_query.keywords[:10]:  # Limit to top 10
                should_clauses.append({
                    "match": {"full_text": {"query": keyword, "boost": 0.5}}
                })
        
        # Filter: minimum years of experience
        if jd_query.min_years is not None:
            filter_clauses.append({
                "range": {
                    "years_of_experience": {"gte": int(jd_query.min_years)}
                }
            })
        
        # Filter: minimum degree
        if jd_query.min_degree:
            degree_hierarchy = ["大专", "本科", "硕士", "博士"]
            try:
                min_idx = degree_hierarchy.index(jd_query.min_degree)
                allowed_degrees = degree_hierarchy[min_idx:]
                filter_clauses.append({
                    "terms": {"degree": allowed_degrees}
                })
            except ValueError:
                pass
        
        # Build final query
        query_body = {
            "query": {
                "bool": {
                    "must": must_clauses if must_clauses else [{"match_all": {}}],
                    "should": should_clauses,
                    "filter": filter_clauses,
                    "minimum_should_match": 0
                }
            },
            "sort": ["_score"]
        }
        
        return query_body

    @classmethod
    async def simple_search(
        cls,
        query_text: str,
        top_n: int = 20
    ) -> list[RetrievalResult]:
        """
        Simple text search without JD parsing.
        
        Args:
            query_text: Raw query text
            top_n: Number of results
            
        Returns:
            List of RetrievalResult
        """
        settings = get_settings()
        
        query_body = {
            "query": {
                "multi_match": {
                    "query": query_text,
                    "fields": ["full_text^1", "skills^3", "name^2"],
                    "type": "best_fields"
                }
            },
            "size": top_n
        }
        
        try:
            client = ElasticsearchClient.get_client()
            
            response = await client.search(
                index=settings.elasticsearch.index,
                body=query_body
            )
            
            retrieval_results = []
            hits = response.get("hits", {}).get("hits", [])
            
            for hit in hits:
                source = hit["_source"]
                resume_id = source.get("resume_id")
                
                if not resume_id:
                    continue
                
                score = hit["_score"]
                normalized_score = min(1.0, score / 10.0)
                
                retrieval_results.append(RetrievalResult(
                    resume_id=resume_id,
                    score=normalized_score,
                    source="elasticsearch"
                ))
            
            logger.info(f"ES simple search returned {len(retrieval_results)} resumes")
            return retrieval_results
            
        except Exception as e:
            logger.error(f"ES simple search failed: {e}")
            return []
