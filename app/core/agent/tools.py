"""Agent tools for conversational retrieval."""

import json
import re

from langchain_core.tools import tool
from loguru import logger

from app.core.infra.mongo_client import MongoDBClient
from app.core.retrieval.milvus_retriever import MilvusRetriever
from app.core.retrieval.es_retriever import ESRetriever

_DEGREE_ORDER = ["大专", "本科", "硕士", "博士"]


def _parse_query_arg(query: str, top_k: int) -> tuple[str, int]:
    """兼容 Agent 将整个 JSON 传入 query 参数的情况。"""
    if query.strip().startswith("{"):
        try:
            data = json.loads(query)
            query = str(data.get("query", ""))
            top_k = int(data.get("top_k") or top_k)
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    return query, top_k


def _highest_degree(education: list[dict]) -> str:
    """从教育经历取最高学历。"""
    best, best_idx = "", -1
    for edu in education or []:
        degree = edu.get("degree", "")
        if degree in _DEGREE_ORDER and _DEGREE_ORDER.index(degree) > best_idx:
            best, best_idx = degree, _DEGREE_ORDER.index(degree)
    return best


async def _format_candidates(resume_ids: list[str], with_score: dict[str, float] | None = None) -> str:
    """从 MongoDB 查询简历并格式化为候选人摘要文本。"""
    if not resume_ids:
        return "未找到相关简历。"

    docs = await MongoDBClient.get_collection().find(
        {"resume_id": {"$in": resume_ids}},
        {"full_text": 0}
    ).to_list(length=len(resume_ids))
    by_id = {d.get("resume_id"): d for d in docs}

    parts = [f"共 {len(by_id)} 位候选人：\n"]
    for i, rid in enumerate(resume_ids, 1):
        d = by_id.get(rid)
        if not d:
            continue
        skills = ", ".join((d.get("skills") or [])[:10]) or "未提取"
        degree = d.get("degree") or _highest_degree(d.get("education") or []) or "-"
        line = (
            f"{i}. {d.get('name', '未知')}（{degree}，"
            f"{d.get('years_of_experience') or '-'} 年经验，resume_id: {rid}）"
            f"\n   技能: {skills}"
        )
        if d.get("summary"):
            line += f"\n   摘要: {d['summary'][:120]}"
        if with_score and rid in with_score:
            line += f"\n   匹配分: {with_score[rid]:.3f}"
        parts.append(line)
    return "\n".join(parts)


@tool
async def semantic_search(query: str, top_k: int = 5) -> str:
    """
    语义检索工具：根据自然语言描述在简历库中进行语义相似度检索，返回候选人详情。

    Args:
        query: 查询文本（自然语言，如"熟悉 Java 和 Spring 的后端开发"）
        top_k: 返回结果数量

    Returns:
        候选人详情列表
    """
    query, top_k = _parse_query_arg(query, top_k)
    logger.info(f"Semantic search: {query[:50]}...")
    results = await MilvusRetriever.search(query, top_n=top_k)
    if not results:
        return "未找到相关简历。"
    scores = {r.resume_id: r.score for r in results}
    return await _format_candidates([r.resume_id for r in results], scores)


@tool
async def keyword_search(query: str, top_k: int = 5) -> str:
    """
    关键词检索工具：根据关键词在简历库中进行全文检索，返回候选人详情。

    Args:
        query: 查询关键词（如"Java Redis 微服务"）
        top_k: 返回结果数量

    Returns:
        候选人详情列表
    """
    query, top_k = _parse_query_arg(query, top_k)
    logger.info(f"Keyword search: {query[:50]}...")
    results = await ESRetriever.simple_search(query, top_n=top_k)
    if not results:
        return "未找到相关简历。"
    scores = {r.resume_id: r.score for r in results}
    return await _format_candidates([r.resume_id for r in results], scores)


@tool
async def filter_search(skills: str = "", min_years: int = 0, degree: str = "") -> str:
    """
    条件筛选工具：根据技能、工作年限、学历等硬性条件筛选简历库。

    Args:
        skills: 要求的技能（逗号分隔，如"Java,Spring"），为空则不限
        min_years: 最低工作年限（0 表示不限）
        degree: 最低学历（大专/本科/硕士/博士），为空则不限

    Returns:
        符合条件的候选人详情列表
    """
    logger.info(f"Filter search: skills={skills}, years={min_years}, degree={degree}")

    # 兼容 Agent 将整个 JSON 传入第一个参数的情况
    if skills.strip().startswith("{"):
        try:
            data = json.loads(skills)
            raw_skills = data.get("skills", "")
            skills = raw_skills if isinstance(raw_skills, str) else ",".join(raw_skills)
            min_years = int(data.get("min_years") or min_years)
            degree = data.get("degree") or degree
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    mongo_filter: dict = {}
    if skills:
        skill_list = [s.strip() for s in skills.replace("，", ",").split(",") if s.strip()]
        # 正则包含匹配（忽略大小写，"Spring" 可命中 "Spring Boot"）
        mongo_filter["$and"] = [
            {"skills": {"$regex": re.escape(s), "$options": "i"}} for s in skill_list
        ]
    if min_years > 0:
        mongo_filter["years_of_experience"] = {"$gte": min_years}

    docs = await MongoDBClient.get_collection().find(
        mongo_filter, {"full_text": 0}
    ).sort("years_of_experience", -1).to_list(length=50)

    # 学历在应用层过滤（MongoDB 未存 degree 字段，从教育经历计算）
    if degree and degree in _DEGREE_ORDER:
        allowed = set(_DEGREE_ORDER[_DEGREE_ORDER.index(degree):])
        docs = [d for d in docs if _highest_degree(d.get("education") or []) in allowed]

    if not docs:
        return "未找到符合筛选条件的候选人。"
    return await _format_candidates([d["resume_id"] for d in docs][:10])


@tool
async def compare_candidates(resume_ids: str) -> str:
    """
    对比多个候选人的学历、技能、经验等关键信息。

    Args:
        resume_ids: 候选人 resume_id 列表（逗号分隔）

    Returns:
        候选人对比详情
    """
    ids = [i.strip() for i in resume_ids.split(",") if i.strip()]
    logger.info(f"Comparing candidates: {len(ids)} 位")
    if not ids:
        return "未提供有效的候选人 ID。"
    return "候选人对比：\n" + await _format_candidates(ids)


# Tool registry for agent
TOOL_REGISTRY = [
    semantic_search,
    keyword_search,
    filter_search,
    compare_candidates,
]
