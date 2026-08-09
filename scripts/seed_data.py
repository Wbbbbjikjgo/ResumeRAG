"""导入示例简历数据（清空三库后写入，用于 UI 测试）。"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SAMPLE_RESUMES = [
    ("陈志强_Java后端.txt", """陈志强
电话：13911110001
邮箱：chenzhiqiang@example.com

求职意向：资深 Java 后端开发工程师

教育背景
2008.09 - 2012.06  华中科技大学  软件工程  本科

工作经历
2018.03 - 至今  美团  高级Java开发工程师
负责订单中心核心系统开发，主导微服务化改造，QPS 从 2万提升至 10万；设计分库分表方案支撑亿级订单数据。

2014.07 - 2018.02  用友网络  Java开发工程师
参与企业级 ERP 系统后端开发，使用 Spring Cloud 构建服务集群，负责 MySQL 性能优化与 Redis 缓存设计。

2012.07 - 2014.06  中软国际  软件开发工程师
参与银行核心系统维护，使用 Java、Oracle 开发交易模块。

技能清单
Java、Spring Boot、Spring Cloud、MySQL、Redis、Kafka、分库分表、微服务架构、Docker、Kubernetes
"""),
    ("刘婷_前端开发.txt", """刘婷
电话：13911110002
邮箱：liuting@example.com

求职意向：高级前端开发工程师

教育背景
2012.09 - 2016.06  电子科技大学  数字媒体技术  本科

工作经历
2020.05 - 至今  字节跳动  高级前端开发工程师
负责抖音电商中台前端架构，主导微前端改造，搭建组件库与设计系统，首屏性能优化 40%。

2016.07 - 2020.04  网易  前端开发工程师
负责云音乐 Web 端迭代开发，使用 React、TypeScript 重构核心页面，搭建前端监控体系。

技能清单
JavaScript、TypeScript、React、Vue、Webpack、微前端、Node.js、性能优化、HTML5、CSS3
"""),
    ("王建国_算法工程师.txt", """王建国
电话：13911110003
邮箱：wangjianguo@example.com

求职意向：资深算法工程师（推荐/搜索方向）

教育背景
2013.09 - 2016.06  中国科学院大学  计算机应用技术  硕士
2009.09 - 2013.06  武汉大学  计算机科学与技术  本科

工作经历
2019.04 - 至今  阿里巴巴  高级算法工程师
负责淘宝首页推荐系统精排模型迭代，设计多目标排序模型 DeepFM/DIN，CTR 提升 12%；主导召回层向量化改造。

2016.07 - 2019.03  百度  算法工程师
参与搜索排序模型优化，负责 query 理解与语义匹配模型，使用 TensorFlow 训练大规模排序模型。

技能清单
Python、推荐系统、TensorFlow、PyTorch、NLP、召回排序、特征工程、深度学习、Spark、向量检索
"""),
    ("赵敏_测试开发.txt", """赵敏
电话：13911110004
邮箱：zhaomin@example.com

求职意向：测试开发工程师

教育背景
2014.09 - 2018.06  西安电子科技大学  软件工程  本科

工作经历
2021.02 - 至今  京东  测试开发工程师
负责交易系统自动化测试平台建设，使用 Python、Pytest 搭建接口自动化框架，覆盖率提升至 85%；开发精准测试工具。

2018.07 - 2021.01  小米  软件测试工程师
负责 MIUI 系统应用功能测试与性能测试，搭建 App 自动化 UI 测试体系。

技能清单
Python、Pytest、自动化测试、接口测试、性能测试、JMeter、Selenium、持续集成、Jenkins、SQL
"""),
    ("孙浩_Go后端.txt", """孙浩
电话：13911110005
邮箱：sunhao@example.com

求职意向：Go 后端开发工程师

教育背景
2015.09 - 2019.06  东南大学  计算机科学与技术  本科

工作经历
2021.06 - 至今  哔哩哔哩  Go 开发工程师
负责弹幕系统后端开发，使用 Go 与 Kafka 构建高并发消息链路，日均处理消息 50 亿条；参与服务容器化与 K8s 迁移。

2019.07 - 2021.05  七牛云  后端开发工程师
参与对象存储网关开发，使用 Go 实现高并发文件上传下载服务，优化网关吞吐性能。

技能清单
Go、Gin、Kafka、Redis、MySQL、gRPC、Kubernetes、Docker、微服务、高并发系统
"""),
    ("周雪_产品经理.txt", """周雪
电话：13911110006
邮箱：zhouxue@example.com

求职意向：高级产品经理（B端/SaaS方向）

教育背景
2011.09 - 2015.06  南京大学  信息管理与信息系统  本科

工作经历
2019.09 - 至今  钉钉  高级产品经理
负责协同办公文档产品线，主导多人实时协作功能设计，用户留存率提升 18%；搭建产品数据指标体系。

2015.07 - 2019.08  金蝶软件  产品经理
负责企业财务 SaaS 产品规划与迭代，完成从需求调研到上线的全流程管理。

技能清单
产品规划、需求分析、原型设计、Axure、数据分析、SQL、B端产品、SaaS、项目管理、用户研究
"""),
    ("吴磊_数据工程师.txt", """吴磊
电话：13911110007
邮箱：wulei@example.com

求职意向：大数据开发工程师

教育背景
2012.09 - 2015.06  北京邮电大学  软件工程  硕士

工作经历
2018.01 - 至今  滴滴出行  大数据开发工程师
负责实时数仓建设，使用 Flink、Kafka 构建实时计算链路；主导离线数仓分层设计与 Hive/Spark 性能优化。

2015.07 - 2017.12  网易有道  数据开发工程师
负责用户行为数据管道开发，使用 Hadoop 生态组件完成数据采集与 ETL。

技能清单
Flink、Spark、Kafka、Hive、Hadoop、数据仓库、ETL、SQL、Python、实时计算
"""),
    ("郑丽_运维开发.txt", """郑丽
电话：13911110008
邮箱：zhengli@example.com

求职意向：DevOps / SRE 工程师

教育背景
2013.09 - 2017.06  大连理工大学  网络工程  本科

工作经历
2020.03 - 至今  蚂蚁集团  SRE工程师
负责支付链路稳定性保障，建设监控告警与容量规划体系；主导 Kubernetes 集群运维与 CI/CD 流水线建设。

2017.07 - 2020.02  华为云  运维工程师
负责云平台基础组件运维，编写自动化运维脚本，参与故障演练与应急预案建设。

技能清单
Kubernetes、Docker、Prometheus、Grafana、CI/CD、Linux、Shell、Python、Jenkins、稳定性建设
"""),
]


async def main() -> None:
    from app.core.config import get_settings
    from app.core.infra.mongo_client import MongoDBClient
    from app.core.infra.es_client import ElasticsearchClient
    from app.core.infra.milvus_client import MilvusClientWrapper
    from app.core.parsing.pipeline import ParsingPipeline

    settings = get_settings()
    print("清理旧数据...")
    await MongoDBClient.get_client().drop_database(settings.mongodb.database)
    try:
        es = ElasticsearchClient.get_client()
        if await es.indices.exists(index=settings.elasticsearch.index):
            await es.indices.delete(index=settings.elasticsearch.index)
    except Exception as e:
        print(f"[WARN] ES 清理失败: {e}")
    try:
        client = MilvusClientWrapper.get_client()
        if client.has_collection(settings.milvus.collection):
            client.drop_collection(settings.milvus.collection)
    except Exception as e:
        print(f"[WARN] Milvus 清理失败: {e}")

    print(f"导入 {len(SAMPLE_RESUMES)} 份示例简历...")
    for filename, content in SAMPLE_RESUMES:
        result = await ParsingPipeline.ingest_resume(content.encode("utf-8"), filename, "text/plain")
        mark = "OK  " if result.status == "success" else "FAIL"
        print(f"[{mark}] {filename} -> {result.status} | {result.message}")

    count = await MongoDBClient.get_collection().count_documents({})
    print(f"完成，MongoDB 现有 {count} 份简历")


if __name__ == "__main__":
    asyncio.run(main())
