"""智能推荐：JD 输入 → 混合检索 → 候选人排序 → 推荐理由。"""

import streamlit as st

from common import highest_degree, run_async

st.title("智能推荐")
st.caption("粘贴岗位描述（JD），系统解析需求后执行双路召回 + RRF 融合 + 精排，返回最匹配候选人")

DEFAULT_JD = """招聘岗位：资深 Java 后端开发工程师

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

# ---------- JD 输入 ----------
with st.form("jd_form"):
    jd_text = st.text_area("岗位描述（JD）", value=DEFAULT_JD, height=220, label_visibility="collapsed")
    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
    top_k = c1.number_input("推荐人数", 1, 20, 5)
    use_hyde = c2.toggle("HyDE 增强", value=True, help="先生成假设候选人文档再做语义检索")
    use_rerank = c3.toggle("精排", value=True, help="Cross-Encoder 不可用时自动降级为 LLM 精排")
    submitted = c4.form_submit_button("开始推荐", type="primary", icon=":material/search:")

# ---------- 执行检索 ----------
if submitted and jd_text.strip():
    from app.core.retrieval.hybrid_pipeline import HybridRetrievalPipeline

    with st.status("正在执行混合检索…", expanded=True) as status:
        st.write("1/4 解析岗位需求")
        jd_query, results = run_async(
            HybridRetrievalPipeline.retrieve(
                jd_text=jd_text, top_k=int(top_k), use_hyde=use_hyde, use_rerank=use_rerank
            )
        )
        st.write("2/4 双路召回 + RRF 融合完成")
        status.update(label=f"检索完成，找到 {len(results)} 位候选人", state="complete")

    st.session_state["jd_query"] = jd_query
    st.session_state["results"] = results
    st.session_state["explanations"] = {}

# ---------- 展示结果 ----------
jd_query = st.session_state.get("jd_query")
results = st.session_state.get("results") or []

if jd_query is not None:
    with st.container(border=True):
        st.markdown(":material/description: **岗位需求解析**")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**必备技能**")
            st.markdown(" ".join(f":blue-badge[{s}]" for s in jd_query.must_skills) or "-")
        with c2:
            st.markdown("**加分技能**")
            st.markdown(" ".join(f":gray-badge[{s}]" for s in jd_query.nice_skills) or "-")
        req = []
        if jd_query.min_years:
            req.append(f"经验 ≥ {jd_query.min_years:g} 年")
        if jd_query.min_degree:
            req.append(f"学历 ≥ {jd_query.min_degree}")
        if req:
            st.caption(" · ".join(req))

if results:
    st.header("推荐结果", divider=True)

    from app.core.infra.mongo_client import MongoDBClient

    # 批量取候选人信息
    async def _fetch(ids: list[str]) -> dict:
        cursor = MongoDBClient.get_collection().find({"resume_id": {"$in": ids}}, {"full_text": 0})
        return {d["resume_id"]: d async for d in cursor}

    resume_map = run_async(_fetch([r.resume_id for r in results]))

    for rank, r in enumerate(results, 1):
        doc = resume_map.get(r.resume_id, {})
        name = doc.get("name") or r.resume_id[:8]
        degree = highest_degree(doc.get("education"))
        years = doc.get("years_of_experience")

        with st.container(border=True):
            head_l, head_r = st.columns([4, 1])
            with head_l:
                st.markdown(f"**#{rank} {name}** · {degree} · {f'{years:g} 年经验' if years else '经验未知'}")
                skills = doc.get("skills") or []
                if skills:
                    st.markdown(" ".join(f":gray-badge[{s}]" for s in skills[:10]))
            with head_r:
                st.metric("匹配分", f"{r.score:.3f}", help="RRF 融合得分（越大越好）")

            if doc.get("summary"):
                st.caption(doc["summary"])

            if st.button("生成推荐理由", key=f"explain_{r.resume_id}", icon=":material/lightbulb:"):
                from app.core.generation.explainer import Explainer
                from app.core.models import Resume

                resume_obj = Resume(
                    **{k: doc.get(k) for k in Resume.model_fields if k in doc}
                )
                with st.spinner("LLM 正在分析匹配度…"):
                    explanation = run_async(Explainer.explain(jd_query, resume_obj, r.score))
                st.session_state["explanations"][r.resume_id] = explanation

            if r.resume_id in st.session_state.get("explanations", {}):
                exp = st.session_state["explanations"][r.resume_id]
                with st.container(border=False):
                    st.markdown("**匹配点**")
                    for item in exp.get("match_items", []):
                        st.markdown(f"- :green[✓] {item}")
                    for item in exp.get("improvement_items", []):
                        st.markdown(f"- :orange[△] {item}")
                    if exp.get("summary"):
                        st.info(exp["summary"], icon=":material/summarize:")
else:
    if jd_query is not None:
        st.warning("未检索到匹配候选人，请检查简历库是否已入库数据。", icon=":material/search_off:")

with st.sidebar:
    st.markdown(":material/route: **推荐流程**")
    st.caption("JD 解析 → HyDE 假设文档 → Milvus 语义召回 + ES 关键词召回 → RRF 融合 → 精排 → LLM 推荐理由")
