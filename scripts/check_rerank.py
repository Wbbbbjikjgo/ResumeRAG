"""验证 LLM 精排降级路径（候选数 > top_k 时触发 llm_rerank）。"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.run_e2e_test import JD_TEXT
from app.core.retrieval.hybrid_pipeline import HybridRetrievalPipeline


async def main() -> None:
    jd, results = await HybridRetrievalPipeline.retrieve(JD_TEXT, top_k=2)
    print("RERANK PATH OK:", [(r.resume_id[:8], round(r.score, 4), r.source) for r in results])


if __name__ == "__main__":
    asyncio.run(main())
