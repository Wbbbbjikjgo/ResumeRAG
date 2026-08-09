"""Result fusion strategies for combining multiple retrieval sources."""

from collections import defaultdict

from loguru import logger

from app.core.config import get_settings
from app.core.models import RetrievalResult


class ResultFusion:
    """Fuse results from multiple retrieval sources."""

    @classmethod
    def rrf_fusion(
        cls,
        result_lists: list[list[RetrievalResult]],
        k: int | None = None,
        top_n: int | None = None
    ) -> list[RetrievalResult]:
        """
        Reciprocal Rank Fusion (RRF) for combining ranked lists.
        
        RRF score = Σ 1 / (k + rank_i)
        
        Args:
            result_lists: List of result lists from different sources
            k: RRF constant (default 60)
            top_n: Number of results to return after fusion
            
        Returns:
            Fused and re-ranked list of RetrievalResult
        """
        settings = get_settings()
        k = k or settings.retrieval.rrf_k
        
        # Track scores and sources for each resume_id
        resume_scores: dict[str, float] = defaultdict(float)
        resume_sources: dict[str, list[str]] = defaultdict(list)
        resume_sections: dict[str, list[str]] = defaultdict(list)
        
        # Process each result list
        for result_list in result_lists:
            for rank, result in enumerate(result_list, start=1):
                resume_id = result.resume_id
                
                # RRF score contribution
                rrf_score = 1.0 / (k + rank)
                resume_scores[resume_id] += rrf_score
                
                # Track source
                if result.source not in resume_sources[resume_id]:
                    resume_sources[resume_id].append(result.source)
                
                # Track matched sections
                resume_sections[resume_id].extend(result.matched_sections)
        
        # Sort by fused score
        sorted_resume_ids = sorted(
            resume_scores.keys(),
            key=lambda x: resume_scores[x],
            reverse=True
        )
        
        # Build fused results
        fused_results = []
        for resume_id in sorted_resume_ids[:top_n]:
            fused_results.append(RetrievalResult(
                resume_id=resume_id,
                score=resume_scores[resume_id],
                source="fusion",
                matched_sections=list(set(resume_sections[resume_id]))
            ))
        
        logger.info(f"RRF fusion: {len(result_lists)} sources → {len(fused_results)} results")
        return fused_results

    @classmethod
    def weighted_fusion(
        cls,
        result_lists: list[list[RetrievalResult]],
        weights: list[float] | None = None,
        top_n: int | None = None
    ) -> list[RetrievalResult]:
        """
        Weighted score fusion for combining results.
        
        Args:
            result_lists: List of result lists from different sources
            weights: Weight for each source (default equal weights)
            top_n: Number of results to return
            
        Returns:
            Fused and re-ranked list of RetrievalResult
        """
        if not result_lists:
            return []
        
        n_sources = len(result_lists)
        if weights is None:
            weights = [1.0 / n_sources] * n_sources
        elif len(weights) != n_sources:
            raise ValueError(f"Weights length ({len(weights)}) must match sources ({n_sources})")
        
        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        # Track scores for each resume_id
        resume_scores: dict[str, float] = defaultdict(float)
        resume_sources: dict[str, list[str]] = defaultdict(list)
        resume_sections: dict[str, list[str]] = defaultdict(list)
        
        # Process each result list with its weight
        for result_list, weight in zip(result_lists, weights):
            for result in result_list:
                resume_id = result.resume_id
                resume_scores[resume_id] += result.score * weight
                
                if result.source not in resume_sources[resume_id]:
                    resume_sources[resume_id].append(result.source)
                
                resume_sections[resume_id].extend(result.matched_sections)
        
        # Sort by weighted score
        sorted_resume_ids = sorted(
            resume_scores.keys(),
            key=lambda x: resume_scores[x],
            reverse=True
        )
        
        # Build fused results
        fused_results = []
        for resume_id in sorted_resume_ids[:top_n]:
            fused_results.append(RetrievalResult(
                resume_id=resume_id,
                score=resume_scores[resume_id],
                source="fusion",
                matched_sections=list(set(resume_sections[resume_id]))
            ))
        
        logger.info(f"Weighted fusion: {n_sources} sources → {len(fused_results)} results")
        return fused_results

    @classmethod
    def deduplicate(
        cls,
        results: list[RetrievalResult],
        keep_highest_score: bool = True
    ) -> list[RetrievalResult]:
        """
        Deduplicate results by resume_id.
        
        Args:
            results: List of results (may contain duplicates)
            keep_highest_score: If True, keep the entry with highest score
            
        Returns:
            Deduplicated list
        """
        seen: dict[str, RetrievalResult] = {}
        
        for result in results:
            if result.resume_id not in seen:
                seen[result.resume_id] = result
            elif keep_highest_score and result.score > seen[result.resume_id].score:
                seen[result.resume_id] = result
        
        # Preserve original order
        deduplicated = []
        seen_ids = set()
        for result in results:
            if result.resume_id not in seen_ids:
                deduplicated.append(seen[result.resume_id])
                seen_ids.add(result.resume_id)
        
        return deduplicated
