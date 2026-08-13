"""简历管理：上传解析入库 + 简历库浏览。"""

import streamlit as st

from common import get_resumes, get_stats, highest_degree, refresh_data, run_async, inject_css

inject_css()

st.title("简历管理")
st.caption("上传简历自动解析入库（MongoDB 全文 + Milvus 向量 + Elasticsearch 索引），并浏览简历库")

tab_upload, tab_library = st.tabs([
    ":material/upload_file: 上传简历",
    ":material/folder: 简历库",
])

# ---------- 上传 ----------
with tab_upload:
    uploaded_files = st.file_uploader(
        "选择简历文件（支持批量）",
        type=["pdf", "docx", "doc", "html", "htm", "png", "jpg", "jpeg", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files and st.button("开始解析并入库", type="primary", icon=":material/play_arrow:"):
        from app.core.parsing.pipeline import ParsingPipeline

        results = []
        progress = st.progress(0.0)
        for i, f in enumerate(uploaded_files):
            with st.status(f"解析中：{f.name}", expanded=False):
                try:
                    result = run_async(ParsingPipeline.ingest_resume(f.getvalue(), f.name, f.type))
                    results.append(result)
                    st.write(result.message)
                except Exception as e:  # noqa: BLE001
                    st.error(f"{f.name} 解析失败：{e}")
            progress.progress((i + 1) / len(uploaded_files))
        progress.empty()

        ok = [r for r in results if r.status == "success"]
        partial = [r for r in results if r.status == "partial"]
        if ok:
            st.success(f"成功入库 {len(ok)} 份简历", icon=":material/check_circle:")
        if partial:
            st.warning(f"{len(partial)} 份解析成功但部分入库失败：{', '.join(r.filename for r in partial)}",
                       icon=":material/warning:")
        refresh_data()

    st.caption("解析流程：文本加载 → 章节切分 → LLM 结构化抽取 → 三库写入")

# ---------- 简历库 ----------
with tab_library:
    resumes = get_resumes()

    if not resumes:
        st.info("简历库为空。可在「上传简历」页签上传，或运行 `python scripts/seed_data.py` 导入示例数据。",
                icon=":material/info:")
    else:
        stats = get_stats()
        m1, m2 = st.columns([1, 4])
        m1.metric("简历总数", f"{stats['resumes']} 份")

        st.dataframe(
            [
                {
                    "姓名": r.get("name") or "未知",
                    "技能": ", ".join((r.get("skills") or [])[:8]),
                    "学历": highest_degree(r.get("education")),
                    "经验(年)": r.get("years_of_experience") or "-",
                    "联系方式": r.get("phone") or r.get("email") or "-",
                }
                for r in resumes
            ],
            column_config={
                "姓名": st.column_config.TextColumn(width="small"),
                "技能": st.column_config.TextColumn(width="large"),
                "学历": st.column_config.TextColumn(width="small"),
                "经验(年)": st.column_config.NumberColumn(format="%.1f", width="small"),
                "联系方式": st.column_config.TextColumn(width="medium"),
            },
            hide_index=True,
        )

        st.markdown("##### 简历详情")
        for r in resumes:
            name = r.get("name") or "未知"
            with st.expander(f"{name} · {', '.join((r.get('skills') or [])[:5])}"):
                left, right = st.columns([1, 1])
                with left:
                    edu_lines = "\n".join(
                        f"- {e.get('school')} · {e.get('major')} · {e.get('degree')}（{e.get('start')}~{e.get('end')}）"
                        for e in (r.get("education") or [])
                    ) or "- 无"
                    st.markdown(
                        f"**联系方式**：{r.get('phone') or '-'} / {r.get('email') or '-'}\n\n"
                        f"**工作年限**：{r.get('years_of_experience') or '-'} 年\n\n"
                        f"**教育经历**：\n{edu_lines}"
                    )
                with right:
                    st.markdown("**工作经历**")
                    for exp in r.get("experience") or []:
                        period = f"{exp.get('start')} ~ {exp.get('end') or '至今'}"
                        st.markdown(f"- **{exp.get('company')}** · {exp.get('title')}（{period}）")
                if r.get("summary"):
                    st.markdown(f"**摘要**：{r['summary']}")
