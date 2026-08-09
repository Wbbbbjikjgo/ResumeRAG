"""UI 共享工具：异步桥接、数据读取、状态检查。"""

import asyncio
import os
import sys
from typing import Any, Coroutine

import streamlit as st

# 确保项目根目录可导入（streamlit run app/ui/Home.py 场景）
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


# 复用同一个事件循环：asyncio.run() 每次创建新循环，
# 而 motor/aiohttp 单例客户端绑定首个循环，跨循环调用会静默失败导致服务显示离线
_LOOP = asyncio.new_event_loop()


def run_async(coro: Coroutine) -> Any:
    """在 Streamlit 同步环境中执行异步协程（复用持久事件循环）。"""
    return _LOOP.run_until_complete(coro)


@st.cache_data(ttl=30, show_spinner=False)
def get_stats() -> dict:
    """读取三库统计数据（30 秒缓存）。"""
    from app.core.config import get_settings
    from app.core.infra.mongo_client import MongoDBClient
    from app.core.infra.es_client import ElasticsearchClient
    from app.core.infra.milvus_client import MilvusClientWrapper

    settings = get_settings()
    stats = {"resumes": 0, "vectors": 0, "es_docs": 0, "services": {}}

    async def _collect() -> None:
        try:
            stats["resumes"] = await MongoDBClient.get_collection().count_documents({})
            stats["services"]["MongoDB"] = True
        except Exception:
            stats["services"]["MongoDB"] = False
        try:
            resp = await ElasticsearchClient.get_client().count(index=settings.elasticsearch.index)
            stats["es_docs"] = resp["count"]
            stats["services"]["Elasticsearch"] = True
        except Exception:
            stats["services"]["Elasticsearch"] = False
        try:
            client = MilvusClientWrapper.get_client()
            if client.has_collection(settings.milvus.collection):
                stats["vectors"] = client.get_collection_stats(settings.milvus.collection).get("row_count", 0)
            stats["services"]["Milvus"] = True
        except Exception:
            stats["services"]["Milvus"] = False

    run_async(_collect())
    return stats


@st.cache_data(ttl=30, show_spinner=False)
def get_resumes() -> list[dict]:
    """读取 MongoDB 中的简历列表（30 秒缓存）。"""
    from app.core.infra.mongo_client import MongoDBClient

    async def _fetch() -> list[dict]:
        cursor = MongoDBClient.get_collection().find(
            {}, {"full_text": 0}
        ).sort("upload_time", -1)
        return [doc async for doc in cursor]

    try:
        return run_async(_fetch())
    except Exception:
        return []


def highest_degree(education: list[dict]) -> str:
    """从教育经历取最高学历。"""
    order = ["大专", "本科", "硕士", "博士"]
    best, best_idx = "-", -1
    for edu in education or []:
        degree = edu.get("degree", "其他")
        if degree in order and order.index(degree) > best_idx:
            best, best_idx = degree, order.index(degree)
    return best


def refresh_data() -> None:
    """清除数据缓存（上传/入库后调用）。"""
    get_stats.clear()
    get_resumes.clear()
