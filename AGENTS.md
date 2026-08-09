# AGENTS.md — AI Agent 行为规范与项目约定

> 本文件供 AI Agent（包括我）在操作此项目时阅读，确保行为一致、高效、不浪费 token。

---

## 1. 项目速览

- **项目名**：ResumeRAG — 基于人力资源场景的 RAG 简历推荐系统
- **核心流程**：JD 解析 → 多路召回（Milvus + ES）→ RRF 融合 → Reranker 精排 → 推荐理由生成 → 对话式追问
- **技术栈**：Python 3.11+ / LangChain / Milvus / Elasticsearch(ik) / MongoDB / Streamlit / BGE-M3 / bge-reranker-v2-m3
- **部署**：Docker Compose（Milvus + ES + MongoDB + App）
- **详细技术方案**：见 `技术方案.md`

---

## 2. Git 提交规范（核心规则）

### 2.1 每完成一个功能/修复/重构，必须立即 git commit

**绝对禁止**：攒一堆改动后一次性提交。
**正确做法**：每完成一个可独立运行、可独立验证的最小功能单元，立即 `git add` + `git commit`。

### 2.2 Commit Message 格式（Conventional Commits）

```
<type>(<scope>): <subject>

[可选 body]
```

#### Type 类型

| type | 含义 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(parsing): 添加 PDF 格式路由与 pdfplumber 解析` |
| `fix` | 修复 bug | `fix(retrieval): 修复 RRF 融合时空列表除零错误` |
| `refactor` | 重构（不改变功能） | `refactor(infra): 抽取三库客户端到 infra 目录` |
| `docs` | 文档变更 | `docs: 更新技术方案中的模块划分` |
| `style` | 代码格式（不影响逻辑） | `style: 统一 import 排序和空行` |
| `test` | 测试相关 | `test(parsing): 添加 PDF 解析单元测试` |
| `chore` | 构建/工具/依赖 | `chore: 添加 python-docx 到 requirements.txt` |
| `perf` | 性能优化 | `perf(retrieval): 双路召回改为 asyncio.gather 并发` |
| `ci` | CI/CD 变更 | `ci: 添加 docker-compose 构建配置` |

#### Scope 范围（对应项目模块）

| scope | 对应模块 |
|-------|----------|
| `parsing` | 简历解析流水线（loader/ocr/splitter/extractor） |
| `retrieval` | 检索链路（jd_parser/milvus/es/fusion/reranker） |
| `generation` | 推荐理由生成（explainer/prompts） |
| `agent` | 对话智能代理（tools/chat_agent） |
| `ui` | Streamlit 前端页面 |
| `infra` | 基础设施客户端（mongo/milvus/es/llm_factory） |
| `config` | 配置管理 |
| `deploy` | Docker/部署相关 |

### 2.3 Subject 写作规则

- 用中文，简明扼要，不超过 50 字
- 使用动词开头：添加、修复、重构、优化、移除、更新
- 不加句号

### 2.4 提交时机清单

按技术方案 T1–T7 迭代，每个迭代内的提交节奏：

| 阶段 | 提交粒度示例 |
|------|---------------|
| T1 环境搭建 | `chore(deploy): 添加 docker-compose 基础编排` → `feat(infra): MongoDB 客户端封装` → `feat(infra): Milvus 客户端封装` → `feat(infra): ES 客户端封装` → `feat(config): pydantic-settings 配置框架` |
| T2 解析流水线 | `feat(parsing): 格式路由与 PDF 解析` → `feat(parsing): PaddleOCR 扫描件识别` → `feat(parsing): Word/HTML 解析` → `feat(parsing): LLM 结构化抽取 Resume Schema` → `feat(parsing): 段落分块` → `feat(infra): 三库入库管道` → `feat(ui): 简历管理页面` |
| T3 单路检索 | `feat(retrieval): BGE-M3 Embedding 工厂` → `feat(retrieval): Milvus ANN 检索` → `feat(retrieval): JD 结构化解析` → `feat(ui): 智能推荐页面骨架` |
| T4 混合检索 | `feat(retrieval): ES 关键词召回` → `feat(retrieval): RRF 融合策略` → `feat(retrieval): bge-reranker 精排` → `feat(retrieval): 硬性条件前置过滤` |
| T5 推荐理由 | `feat(generation): 推荐理由 Prompt 与生成` → `feat(ui): 推荐结果卡片与高亮` → `feat(ui): Plotly 雷达图对比` |
| T6 对话代理 | `feat(agent): 检索工具封装` → `feat(agent): AgentExecutor + Memory` → `feat(ui): 对话追问页（打字机效果）` |
| T7 管理运维 | `feat(ui): 管理配置页` → `feat(config): 热更新支持` → `perf: 全链路耗时埋点` → `chore(deploy): 完整 Docker 部署` |

### 2.5 提交前检查

- [ ] 代码能正常运行（不提交跑不起来的半成品，除非标记 `WIP`）
- [ ] 无遗留的 `print("debug")` / `# TODO: remove`
- [ ] 新增依赖已更新 `requirements.txt`
- [ ] 不提交 `.env`、密钥、大文件（`data/` 下简历文件用 `.gitignore` 排除）

---

## 3. Token 节省规则（防止 AI 变笨/浪费）

### 3.1 上下文控制

- **不要一次性读取整个项目**：按模块逐个读取，只读当前任务相关的文件
- **大文件用行号范围读取**：`Read` 时指定 `start_line` / `end_line`，不要读全文
- **搜索结果只看前 3–5 条**：不要反复搜索同一关键词
- **不要重复读取已读过的文件**：如果需要回顾，在脑中回忆而非重新读取

### 3.2 搜索纪律

- 先 `SearchCodebase`（语义搜索）再 `Grep`（精确匹配），不要反过来
- 一次搜索用准关键词，不要连续发 5 个相似搜索
- 找到目标后立即停止搜索，开始编码
- 不要用搜索"确认"已经确定的事情

### 3.3 编码纪律

- **一次写完**：一个文件的修改用一次 `SearchReplace` 搞定，不要拆成 3 次
- **不要生成冗余代码**：不写没人调用的函数、不加没人看的注释
- **不要过度抽象**：当前只需要一个实现时，不要写"可扩展的"基类/接口
- **Prompt 模板集中管理**：所有 Prompt 放 `app/core/generation/prompts.py`，不要散落在各文件
- **错误处理只写必要的**：不要为每个函数都加 try/except，只在边界和 IO 处处理

### 3.4 回复纪律

- **不要复述用户的问题**：直接给方案/代码
- **不要列出"我将要做的事"清单然后一件件解释**：直接做
- **代码注释用中文**，简短即可，不要写"作文式"注释
- **不要生成示例数据/测试数据**除非明确要求

### 3.5 文件操作纪律

- 不要创建 `README.md`、`CHANGELOG.md`、`notes.md` 等文档，除非用户明确要求
- 不要创建临时文件（如 `test_xxx.py`）来"试试看"
- 编辑文件前确认路径存在，不要盲猜路径

---

## 4. 代码风格约定

### 4.1 Python

- Python 3.11+，使用新语法特性（`match`、`X | None`、`list[str]` 等）
- 类型注解：所有函数签名必须有类型注解
- 异步：IO 密集操作（Milvus/ES/Mongo/LLM 调用）使用 `async/await`
- 数据模型：统一用 Pydantic v2 `BaseModel`
- 配置：`pydantic-settings`，从 `config/config.yaml` + 环境变量加载
- 日志：`loguru`，不用 `logging` 标准库
- 导入顺序：标准库 → 第三方 → 本项目，各组之间空一行

### 4.2 命名

| 类型 | 风格 | 示例 |
|------|------|------|
| 文件/模块 | snake_case | `milvus_retriever.py` |
| 类 | PascalCase | `MilvusRetriever` |
| 函数/方法 | snake_case | `search_resumes` |
| 常量 | UPPER_SNAKE | `DEFAULT_TOP_K = 10` |
| 环境变量 | UPPER_SNAKE | `MILVUS_HOST` |

### 4.3 目录结构

严格按 `技术方案.md` 第 3.1 节的目录结构创建，不要随意新建目录或移动文件。

---

## 5. 架构约束

- **LLM 统一接口**：所有 LLM 调用通过 `llm_factory.py` 获取实例，不要在业务代码直接 `import openai`
- **三库客户端单例**：MongoDB/Milvus/ES 客户端全局单例，不要每次 new
- **检索链路可插拔**：每路召回实现统一接口 `BaseRetriever`，方便增减召回源
- **Prompt 与代码分离**：Prompt 模板字符串集中在 `prompts.py`，业务代码只引用不内联
- **配置驱动**：召回数、Top-K、RRF k、Rerank 开关、模型端点等全部走配置，不要硬编码

---

## 6. 常见陷阱（避免踩坑）

| 陷阱 | 正确做法 |
|------|----------|
| LangChain `create_extraction_chain` 已废弃 | 用 `with_structured_output` + Pydantic Schema |
| Milvus 连接失败不报错 | 启动时做健康检查，失败立即抛出 |
| ES ik 分词器未安装 | Docker 镜像用 `elasticsearch:7.17.x-analysis-ik` 或自建含 ik 的镜像 |
| BGE-M3 稀疏向量与稠密向量混淆 | 明确指定 `output_type`，默认只用稠密向量 |
| Streamlit `st.write_stream` 需要 generator | LLM 调用用 `.stream()` 返回 generator |
| MongoDB 大文档写入慢 | 简历 `full_text` 超过 16MB 时截断并告警（正常简历不会超） |
| 向量维度不匹配 | Milvus 集合维度必须与 Embedding 模型输出维度一致（BGE-M3 = 1024） |

---

## 7. .gitignore 必要项

```gitignore
# 环境
.env
.venv/
__pycache__/
*.pyc

# 数据
data/resumes/
*.pdf
*.docx

# IDE
.vscode/
.idea/

# 日志
logs/
*.log

# 模型缓存
models_cache/
```

---

## 8. 工作流程总结

```
接到任务 → 理解需求 → 读相关文件 → 编码 → 本地验证 → git add + commit（feat/fix/...）→ 报告完成
```

**核心原则**：小步快跑、每步提交、不浪费 token、不过度设计。
