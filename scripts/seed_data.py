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
    ("李佳_数据分析师.txt", """李佳
电话：13911110009
邮箱：lijia@example.com

求职意向：数据分析师（业务分析方向）

教育背景
2015.09 - 2019.06  上海财经大学  统计学  本科

工作经历
2021.05 - 至今  美团  数据分析师
负责外卖业务经营分析，搭建 GMV 漏斗与用户增长指标体系，用 SQL、Python 处理亿级数据；输出周/月度经营报告支撑管理层决策。

2019.07 - 2021.04  唯品会  数据运营
负责用户行为分析与活动复盘，使用 Excel、Tableau 制作可视化报表，参与 A/B 测试实验设计与效果评估。

技能清单
SQL、Python、Excel、Tableau、Power BI、统计分析、A/B测试、用户增长、数据可视化、指标体系
"""),
    ("陈明_网络安全.txt", """陈明
电话：13911110010
邮箱：chenming@example.com

求职意向：网络安全工程师

教育背景
2013.09 - 2017.06  北京航空航天大学  信息安全  本科

工作经历
2019.03 - 至今  奇安信  安全工程师
负责企业安全运营，建设 SIEM 安全事件监控体系，主导攻防演练红蓝对抗，处理渗透测试与漏洞应急响应。

2017.07 - 2019.02  绿盟科技  渗透测试工程师
参与 Web 应用与内网渗透测试，编写漏洞报告与修复建议，熟悉 OWASP Top 10 与常见攻击手法。

技能清单
渗透测试、漏洞挖掘、WAF、IDS/IPS、应急响应、安全审计、Python、Linux、BurpSuite、等保测评
"""),
    ("黄伟_Android开发.txt", """黄伟
电话：13911110011
邮箱：huangwei@example.com

求职意向：Android 客户端开发工程师

教育背景
2014.09 - 2018.06  哈尔滨工业大学  计算机科学与技术  本科

工作经历
2020.04 - 至今  快手  Android 开发工程师
负责短视频 App 播放器与性能优化，使用 Kotlin、Jetpack Compose 重构核心页面，启动耗时降低 35%。

2018.07 - 2020.03  魅族  Android 开发工程师
负责系统应用开发，使用 Java、Kotlin 维护通讯录与桌面应用，优化内存占用与耗电。

技能清单
Kotlin、Java、Jetpack、MVVM、组件化、性能优化、Retrofit、OkHttp、Git、NDK
"""),
    ("林芳_UI设计师.txt", """林芳
电话：13911110012
邮箱：linfang@example.com

求职意向：UI / UX 设计师

教育背景
2015.09 - 2019.06  中国美术学院  视觉传达设计  本科

工作经历
2021.02 - 至今  网易  高级 UI 设计师
负责游戏与电商产品界面设计，主导设计系统建设，输出组件规范与视觉稿，推动设计落地一致性。

2019.07 - 2021.01  携程  视觉设计师
负责移动端界面设计与运营活动视觉，使用 Figma、Sketch 完成高保真原型与切图交付。

技能清单
Figma、Sketch、Photoshop、Illustrator、设计系统、交互设计、原型设计、视觉设计、动效设计、用户研究
"""),
    ("张涛_数据库DBA.txt", """张涛
电话：13911110013
邮箱：zhangtao@example.com

求职意向：数据库管理员（DBA）

教育背景
2011.09 - 2015.06  中山大学  软件工程  本科

工作经历
2018.06 - 至今  招商银行  数据库管理员
负责核心系统 MySQL、Oracle 数据库运维，主导主从复制、读写分离与容灾备份体系建设，优化慢查询提升性能。

2015.07 - 2018.05  中国电信  数据库工程师
负责业务数据库日常监控与维护，编写自动化运维脚本，参与数据库迁移与版本升级。

技能清单
MySQL、Oracle、Redis、数据库优化、主从复制、备份恢复、高可用、Linux、Shell、Python
"""),
    ("徐静_人力资源.txt", """徐静
电话：13911110014
邮箱：xujing@example.com

求职意向：人力资源 HRBP

教育背景
2012.09 - 2016.06  中国人民大学  人力资源管理  本科

工作经历
2019.08 - 至今  字节跳动  HRBP
负责技术团队人才招聘与组织发展，搭建人才梯队，主导绩效管理与员工关系，支撑业务快速扩张。

2016.07 - 2019.07  联想  HR 专员
负责招聘全流程与培训组织，维护招聘渠道，完成年度校招与社招目标。

技能清单
招聘、绩效管理、员工关系、组织发展、人才盘点、薪酬福利、劳动法、HRIS、沟通协调、数据分析
"""),
    ("高翔_嵌入式开发.txt", """高翔
电话：13911110015
邮箱：gaoxiang@example.com

求职意向：嵌入式软件开发工程师

教育背景
2013.09 - 2017.06  西安交通大学  电子信息工程  本科

工作经历
2020.02 - 至今  大疆  嵌入式开发工程师
负责无人机飞控系统固件开发，使用 C/C++ 与 RTOS，优化传感器数据融合算法，保障飞行稳定性。

2017.07 - 2020.01  华为  嵌入式软件工程师
负责通信设备板卡驱动开发，使用 Linux 内核与 UART/I2C/SPI 总线，参与硬件调试与功耗优化。

技能清单
C、C++、RTOS、Linux、ARM、单片机、I2C、SPI、UART、FreeRTOS
"""),
    ("罗成_音视频开发.txt", """罗成
电话：13911110016
邮箱：luocheng@example.com

求职意向：音视频开发工程师

教育背景
2012.09 - 2016.06  电子科技大学  通信工程  本科

工作经历
2019.05 - 至今  腾讯  音视频开发工程师
负责直播与实时音视频 SDK 开发，使用 WebRTC、FFmpeg 优化编解码与传输链路，抗弱网丢包率降低 30%。

2016.07 - 2019.04  科大讯飞  音频算法工程师
负责语音编解码与降噪算法开发，使用 C/C++ 优化 DSP 处理，参与声学前端模块设计。

技能清单
WebRTC、FFmpeg、H.264、H.265、C/C++、音视频编解码、流媒体、RTP/RTMP、OpenGL、性能优化
"""),
    ("韩雪_财务.txt", """韩雪
电话：13911110017
邮箱：hanxue@example.com

求职意向：财务分析师

教育背景
2013.09 - 2017.06  中央财经大学  会计学  本科

工作经历
2020.03 - 至今  阿里  财务分析师
负责业务线财务预算与经营分析，搭建财务预测模型，出具月度管理报表，支持业务经营决策。

2017.07 - 2020.02  普华永道  审计员
参与上市公司年报审计，执行实质性测试与内控测试，出具审计报告。

技能清单
财务分析、预算管理、成本控制、财务报表、CPA、Excel、财务建模、用友、金蝶、税务筹划
"""),
    ("何强_项目经理.txt", """何强
电话：13911110018
邮箱：heqiang@example.com

求职意向：项目经理（PM）

教育背景
2010.09 - 2014.06  同济大学  工程管理  本科

工作经历
2019.09 - 至今  华为  项目经理
负责政企项目交付管理，统筹需求、进度、成本与风险，主导 20+ 人团队完成大型系统集成项目按期交付。

2014.07 - 2019.08  中兴  项目专员
负责项目计划编制与进度跟踪，协调跨部门资源，组织项目评审与验收。

技能清单
项目管理、PMP、敏捷开发、Scrum、需求管理、风险管理、成本控制、沟通协调、计划制定、JIRA
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
