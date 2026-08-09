"""ResumeRAG - 智能简历推荐系统首页"""

import streamlit as st

st.set_page_config(
    page_title="ResumeRAG - 智能简历推荐系统",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("🎯 ResumeRAG")
st.markdown("### 基于 RAG 的智能简历推荐系统")

st.markdown("""
---

欢迎使用 **ResumeRAG** —— 一个基于检索增强生成（RAG）技术的智能简历推荐系统。

### 核心功能

| 功能 | 描述 |
|------|------|
| 📄 **简历管理** | 上传、解析、存储多格式简历（PDF/Word/HTML/图片） |
| 🔍 **智能推荐** | 输入岗位描述（JD），自动推荐 Top-K 匹配候选人 |
| 💬 **对话追问** | 对推荐结果进行自然语言追问，深入筛选 |
| 📊 **可解释推荐** | 为每位候选人生成匹配理由和对比分析 |

### 快速开始

1. **上传简历** → 进入「简历管理」页面，批量上传候选人简历
2. **输入 JD** → 进入「智能推荐」页面，粘贴岗位描述
3. **查看推荐** → 系统自动检索并推荐最佳候选人
4. **追问筛选** → 进入「对话追问」页面，进一步筛选

### 技术架构

- **检索引擎**：Milvus（语义向量）+ Elasticsearch（关键词）
- **融合策略**：RRF（Reciprocal Rank Fusion）
- **精排模型**：BGE-Reranker-v2-m3
- **Embedding**：BGE-M3（多语言，1024维）
- **LLM**：支持 OpenAI GPT-4 / Qwen / ChatGLM

---

*使用左侧导航栏选择功能页面*
""")

# Sidebar info
with st.sidebar:
    st.header("系统状态")
    
    # TODO: Connect to actual backend
    st.metric("简历库总数", "0", help="已解析入库的简历数量")
    st.metric("今日推荐", "0", help="今日生成的推荐次数")
    
    st.divider()
    
    st.header("配置信息")
    st.json({
        "Embedding": "BGE-M3",
        "Reranker": "bge-reranker-v2-m3",
        "Milvus": "localhost:19530",
        "Elasticsearch": "localhost:9200",
        "MongoDB": "localhost:27017"
    })
    
    st.divider()
    st.caption("ResumeRAG v1.0 | Powered by LangChain + RAG")
