"""ResumeRAG 端到端测试脚本（DeepSeek + Milvus + MongoDB + ES）。

测试流程：
1. 数据库连通性检查（MongoDB / Elasticsearch / Milvus）
2. DeepSeek LLM 调用：JD 结构化解析 + HyDE 生成
3. 简历解析 + 三库入库全流程
4. 混合检索（Milvus 语义 + ES 关键词 + RRF + 精排）
5. 推荐理由生成
"""

import asyncio
import sys
import traceback
from datetime import datetime

RESULTS: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, ok, detail))
    mark = "PASS" if ok else "FAIL"
    print(f"\n[{mark}] {name} {('- ' + detail) if detail else ''}")


SAMPLE_RESUMES = [
    ("张三_后端开发.txt", """张三
电话：13800000001
邮箱：zhangsan@example.com

求职意向：Java 后端开发工程师

教育背景
2012.09 - 2016.06  北京大学  计算机科学与技术  本科

工作经历
2016.07 - 2020.08  美团  后端开发工程师
- 负责订单中心微服务开发，使用 Java、Spring Boot、Spring Cloud
- 主导 MySQL 分库分表改造，QPS 提升 3 倍
- 使用 Redis 实现分布式缓存与限流

2020.09 - 至今  字节跳动  高级后端开发工程师
- 负责推荐系统后端架构，日均请求量 5 亿次
- 设计 Kafka 消息队列削峰方案，系统可用性达 99.99%
- 推动 Docker、Kubernetes 容器化部署落地

专业技能
Java、Spring Boot、Spring Cloud、MySQL、Redis、Kafka、Docker、Kubernetes、微服务架构、高并发系统设计
"""),
    ("李四_算法工程师.txt", """李四
电话：13800000002
邮箱：lisi@example.com

求职意向：机器学习算法工程师

教育背景
2015.09 - 2019.06  清华大学  软件工程  本科
2019.09 - 2022.06  清华大学  计算机科学与技术  硕士

工作经历
2022.07 - 至今  阿里巴巴  算法工程师
- 负责搜索推荐排序模型，使用深度学习（PyTorch、TensorFlow）
- 优化 CTR 预估模型，AUC 从 0.72 提升至 0.79
- 熟悉 NLP 技术，参与大语言模型微调与 RAG 检索增强生成项目
- 使用 Python 构建数据处理与特征工程流水线

专业技能
Python、PyTorch、TensorFlow、机器学习、深度学习、NLP、推荐系统、大语言模型、RAG、特征工程
"""),
    ("王五_前端开发.txt", """王五
电话：13800000003
邮箱：wangwu@example.com

求职意向：Web 前端开发工程师

教育背景
2014.09 - 2018.06  武汉大学  信息管理与信息系统  大专

工作经历
2018.07 - 2021.05  小米  前端开发工程师
- 负责商城 PC 端与 H5 页面开发，使用 JavaScript、Vue.js
- 使用 Webpack 优化构建流程，首屏加载提速 40%

2021.06 - 至今  京东  高级前端开发工程师
- 负责中后台系统开发，使用 React、TypeScript
- 搭建组件库与前端监控体系

专业技能
JavaScript、TypeScript、Vue、React、HTML、CSS、Webpack、Node.js
"""),
]

JD_TEXT = """招聘岗位：资深 Java 后端开发工程师

岗位职责：
1. 负责公司核心业务系统的后端设计与开发
2. 参与高并发、高可用微服务架构设计与优化

任职要求：
1. 本科及以上学历，计算机相关专业
2. 5年以上 Java 开发经验
3. 精通 Java、Spring Boot、Spring Cloud，熟悉微服务架构
4. 熟练使用 MySQL、Redis，具备分库分表与缓存设计经验
5. 熟悉 Docker、Kubernetes 容器化部署者优先
6. 有 Kafka 等消息中间件使用经验者优先
"""


async def test_infra() -> bool:
    """数据库连通性检查。"""
    ok_all = True
    # MongoDB
    try:
        from app.core.infra.mongo_client import MongoDBClient
        client = MongoDBClient.get_client()
        await client.admin.command("ping")
        record("MongoDB 连接", True)
    except Exception as e:
        record("MongoDB 连接", False, str(e)); ok_all = False
    # Elasticsearch
    try:
        from app.core.infra.es_client import ElasticsearchClient
        es = ElasticsearchClient.get_client()
        info = await es.info()
        record("Elasticsearch 连接", True, f"version={info['version']['number']}")
    except Exception as e:
        record("Elasticsearch 连接", False, str(e)); ok_all = False
    # Milvus
    try:
        from app.core.infra.milvus_client import MilvusClientWrapper
        ok = await MilvusClientWrapper.health_check()
        record("Milvus 连接", bool(ok))
        ok_all = ok_all and bool(ok)
    except Exception as e:
        record("Milvus 连接", False, str(e)); ok_all = False
    return ok_all


async def test_llm() -> bool:
    """DeepSeek LLM 调用：JD 解析 + HyDE。"""
    from app.core.retrieval.jd_parser import JDParser

    jd_query = await JDParser.parse(JD_TEXT)
    ok = bool(jd_query.must_skills)
    record(
        "LLM JD解析", ok,
        f"must_skills={jd_query.must_skills}, min_years={jd_query.min_years}, min_degree={jd_query.min_degree}"
    )
    if not ok:
        return False

    hyde_doc = await JDParser.generate_hyde_document(jd_query)
    record("LLM HyDE生成", bool(hyde_doc), f"{len(hyde_doc)} chars")
    return bool(hyde_doc)


async def test_ingest() -> bool:
    """简历解析 + 三库入库。"""
    from app.core.parsing.pipeline import ParsingPipeline

    ok_all = True
    for filename, content in SAMPLE_RESUMES:
        result = await ParsingPipeline.ingest_resume(content.encode("utf-8"), filename, "text/plain")
        record(
            f"入库: {filename}",
            result.status == "success",
            f"status={result.status}, {result.message}, fields={result.parsed_fields}"
        )
        ok_all = ok_all and result.status == "success"
    return ok_all


async def test_retrieval() -> bool:
    """混合检索 + 推荐理由生成。"""
    from app.core.retrieval.hybrid_pipeline import HybridRetrievalPipeline
    from app.core.generation.explainer import Explainer
    from app.core.models import Resume
    from app.core.infra.mongo_client import MongoDBClient

    jd_query, results = await HybridRetrievalPipeline.retrieve(JD_TEXT, top_k=3)
    ok = len(results) > 0
    record("混合检索", ok, f"返回 {len(results)} 条结果")
    for i, r in enumerate(results, 1):
        print(f"    #{i} resume_id={r.resume_id[:8]}... score={r.score:.4f} source={r.source}")
    if not ok:
        return False

    # 推荐理由：取第一名简历生成解释
    top = results[0]
    collection = MongoDBClient.get_collection()
    mongo_doc = await collection.find_one({"resume_id": top.resume_id})
    if not mongo_doc:
        record("推荐理由生成", False, "MongoDB 中未找到 TOP1 简历")
        return False

    resume = Resume(**{k: mongo_doc.get(k) for k in Resume.model_fields.keys() if k in mongo_doc})
    explanation = await Explainer.explain(jd_query, resume, top.score)
    ok2 = bool(explanation.get("summary"))
    record("推荐理由生成", ok2, f"match={explanation.get('match_items')}, summary={explanation.get('summary')}")
    return ok2


async def main() -> int:
    print(f"===== ResumeRAG E2E 测试 开始 @ {datetime.now():%H:%M:%S} =====")

    steps = [
        ("基础设施连通", test_infra),
        ("DeepSeek LLM 调用", test_llm),
        ("简历解析+入库", test_ingest),
        ("混合检索+推荐理由", test_retrieval),
    ]

    for name, fn in steps:
        print(f"\n>>> 阶段: {name}")
        try:
            ok = await fn()
            if not ok:
                print(f"!!! 阶段未全部通过: {name}，继续执行后续阶段")
        except Exception:
            traceback.print_exc()
            record(name, False, "阶段抛出异常")

    print("\n===== 测试汇总 =====")
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    for name, ok, detail in RESULTS:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"总计: {passed}/{len(RESULTS)} 通过")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
