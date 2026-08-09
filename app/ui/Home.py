"""ResumeRAG 首页：概览与入口。"""

import streamlit as st

from common import get_stats

st.set_page_config(
    page_title="ResumeRAG",
    page_icon=":material/search:",
    layout="wide",
)

st.title("ResumeRAG")
st.caption("基于 RAG 的智能简历推荐系统 · Milvus 语义检索 + Elasticsearch 关键词检索 + DeepSeek 大模型")

# 数据概览
stats = get_stats()

m1, m2, m3 = st.columns(3)
m1.metric("简历库", f"{stats['resumes']} 份")
m2.metric("向量切片", f"{stats['vectors']} 条")
m3.metric("索引文档", f"{stats['es_docs']} 条")

# 服务状态
svc = stats["services"]
st.markdown(
    f"MongoDB :{'green' if svc.get('MongoDB') else 'red'}-badge[{'正常' if svc.get('MongoDB') else '离线'}] "
    f"Elasticsearch :{'green' if svc.get('Elasticsearch') else 'red'}-badge[{'正常' if svc.get('Elasticsearch') else '离线'}] "
    f"Milvus :{'green' if svc.get('Milvus') else 'red'}-badge[{'正常' if svc.get('Milvus') else '离线'}]"
)

st.header("功能入口", divider=True)

c1, c2, c3 = st.columns(3)

with c1, st.container(border=True):
    st.markdown(":material/upload_file: **简历管理**")
    st.markdown("上传并解析简历（PDF / Word / HTML / 图片），自动抽取结构化信息并入库。")
    st.page_link("pages/1_简历管理.py", label="进入", icon=":material/arrow_forward:")

with c2, st.container(border=True):
    st.markdown(":material/search: **智能推荐**")
    st.markdown("粘贴岗位描述（JD），双路召回 + RRF 融合 + 精排，输出 Top-K 候选人与推荐理由。")
    st.page_link("pages/2_智能推荐.py", label="进入", icon=":material/arrow_forward:")

with c3, st.container(border=True):
    st.markdown(":material/chat: **对话追问**")
    st.markdown("用自然语言追问与筛选候选人，例如“有哪些 5 年以上经验的 Java 候选人”。")
    st.page_link("pages/3_对话追问.py", label="进入", icon=":material/arrow_forward:")

# 快速开始
st.header("使用流程", divider=True)
st.markdown(
    """
1. **入库简历**：在「简历管理」上传候选人简历
2. **输入 JD**：在「智能推荐」粘贴岗位描述
3. **查看结果**：系统返回按匹配度排序的候选人及推荐理由
4. **继续追问**：在「对话追问」中按条件进一步筛选
"""
)

if stats["resumes"] == 0:
    st.info("简历库为空，请先在「简历管理」上传简历，或运行 `python scripts/seed_data.py` 导入示例数据。",
            icon=":material/info:")

with st.sidebar:
    st.markdown(":material/settings: **检索配置**")
    st.caption("Milvus 语义召回 + ES 关键词召回 → RRF 融合 → 精排（FlagEmbedding 不可用时降级 LLM 精排）")
