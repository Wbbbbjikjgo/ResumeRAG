"""Agent tools for conversational retrieval."""

from typing import Any

from langchain_core.tools import tool
from loguru import logger

from app.core.retrieval.hybrid_pipeline import HybridRetrievalPipeline
from app.core.retrieval.milvus_retriever import MilvusRetriever
from app.core.retrieval.es_retriever import ESRetriever


@tool
async def semantic_search(query: str, top_k: int = 10) -> str:
    """
    语义检索工具：根据查询文本在简历库中进行语义相似度检索。
    
    Args:
        query: 查询文本（自然语言）
        top_k: 返回结果数量
    
    Returns:
        检索结果摘要
    """
    logger.info(f"Semantic search: {query[:50]}...")
    
    results = await MilvusRetriever.search(query, top_n=top_k)
    
    if not results:
        return "未找到相关简历。"
    
    # Format results
    output_parts = [f"找到 {len(results)} 份相关简历：\n"]
    for i, result in enumerate(results[:top_k], 1):
        output_parts.append(f"{i}. resume_id: {result.resume_id}, 相似度: {result.score:.3f}")
    
    return "\n".join(output_parts)


@tool
async def keyword_search(query: str, top_k: int = 10) -> str:
    """
    关键词检索工具：根据关键词在简历库中进行全文检索。
    
    Args:
        query: 查询关键词
        top_k: 返回结果数量
    
    Returns:
        检索结果摘要
    """
    logger.info(f"Keyword search: {query[:50]}...")
    
    results = await ESRetriever.simple_search(query, top_n=top_k)
    
    if not results:
        return "未找到相关简历。"
    
    # Format results
    output_parts = [f"找到 {len(results)} 份相关简历：\n"]
    for i, result in enumerate(results[:top_k], 1):
        output_parts.append(f"{i}. resume_id: {result.resume_id}, 相关度: {result.score:.3f}")
    
    return "\n".join(output_parts)


@tool
async def filter_search(
    skills: str = "",
    min_years: int = 0,
    degree: str = ""
) -> str:
    """
    条件筛选工具：根据技能、年限、学历等条件筛选简历。
    
    Args:
        skills: 要求的技能（逗号分隔）
        min_years: 最低工作年限
        degree: 最低学历（大专/本科/硕士/博士）
    
    Returns:
        筛选结果摘要
    """
    logger.info(f"Filter search: skills={skills}, years={min_years}, degree={degree}")
    
    # Build query from filters
    query_parts = []
    if skills:
        query_parts.append(f"技能包含 {skills}")
    if min_years > 0:
        query_parts.append(f"经验 {min_years} 年以上")
    if degree:
        query_parts.append(f"学历 {degree} 及以上")
    
    query = " AND ".join(query_parts) if query_parts else "所有候选人"
    
    # TODO: Implement actual filtering against MongoDB
    # For now, return placeholder
    return f"条件筛选: {query}\n（数据库连接待实现，当前返回模拟数据）"


@tool
def get_current_candidates() -> str:
    """
    获取当前推荐上下文中的候选人列表。
    
    Returns:
        当前候选人列表
    """
    # TODO: Get from session state or context
    return "当前推荐上下文中的候选人列表（待实现）"


@tool
async def compare_candidates(resume_ids: str) -> str:
    """
    对比多个候选人的技能和经验。
    
    Args:
        resume_ids: 候选人 ID 列表（逗号分隔）
    
    Returns:
        对比结果
    """
    ids = [id.strip() for id in resume_ids.split(",")]
    logger.info(f"Comparing candidates: {ids}")
    
    # TODO: Fetch actual resume data and compare
    return f"对比 {len(ids)} 位候选人：\n" + "\n".join(f"- {id}" for id in ids)


# Tool registry for agent
TOOL_REGISTRY = [
    semantic_search,
    keyword_search,
    filter_search,
    get_current_candidates,
    compare_candidates
]
