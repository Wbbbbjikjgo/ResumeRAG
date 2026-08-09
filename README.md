# ResumeRAG - 基于人力资源场景的 RAG 简历推荐系统

基于 RAG（检索增强生成）技术的智能简历推荐系统，帮助 HR 快速筛选匹配度高的候选人。

## 核心功能

- **简历智能解析**：支持 PDF/Word/HTML/图片扫描件，自动提取结构化信息
- **JD 理解**：自然语言岗位描述 → 结构化查询条件 + HyDE 假设文档
- **混合检索**：Milvus 语义召回 + Elasticsearch 关键词召回 → RRF 融合 → Reranker 精排
- **可解释推荐**：为每位候选人生成匹配理由、匹配点/待提高项
- **对话式追问**：支持 HR 对推荐结果进行自然语言追问

## 技术栈

- **前端**：Streamlit
- **后端**：FastAPI + LangChain
- **向量库**：Milvus
- **全文检索**：Elasticsearch (ik 分词)
- **文档存储**：MongoDB
- **Embedding**：BGE-M3
- **Reranker**：bge-reranker-v2-m3
- **LLM**：OpenAI GPT-4 / Qwen / ChatGLM（可配置）

## 快速开始

### 1. 启动基础设施

```bash
docker-compose up -d mongodb milvus elasticsearch
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件：

```env
OPENAI_API_KEY=your-api-key
LLM_MODEL=gpt-4
```

### 4. 启动应用

```bash
streamlit run app/ui/Home.py
```

访问 http://localhost:8501

## 项目结构

```
ResumeRAG/
├── app/
│   ├── core/
│   │   ├── config.py          # 配置管理
│   │   ├── models.py          # 数据模型
│   │   ├── parsing/           # 简历解析
│   │   ├── retrieval/         # 检索链路
│   │   ├── generation/        # 推荐理由生成
│   │   ├── agent/             # 对话智能代理
│   │   └── infra/             # 基础设施客户端
│   └── ui/                    # Streamlit 前端
├── config/
│   └── config.yaml            # 配置文件
├── docker-compose.yml
└── requirements.txt
```

## 文档

- [技术方案](./技术方案.md)
- [AI Agent 规范](./AGENTS.md)

## License

MIT
