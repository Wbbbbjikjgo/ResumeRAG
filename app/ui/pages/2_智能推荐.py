"""智能推荐页面 - JD 输入与候选人推荐"""

import streamlit as st
import asyncio

st.set_page_config(page_title="智能推荐 - ResumeRAG", page_icon="🔍", layout="wide")

st.title("🔍 智能推荐")
st.markdown("输入岗位描述（JD），系统自动推荐最匹配的候选人")

# Initialize session state
if "recommendation_results" not in st.session_state:
    st.session_state.recommendation_results = None
if "jd_query" not in st.session_state:
    st.session_state.jd_query = None

# JD input section
st.header("岗位描述")

jd_text = st.text_area(
    "请输入岗位描述（JD）",
    height=200,
    placeholder="""例如：
我们正在寻找一位资深 Python 后端工程师，要求：
- 5年以上 Python 开发经验
- 熟悉 FastAPI、Django 等 Web 框架
- 有微服务架构经验
- 熟悉 Docker、Kubernetes
- 有大规模系统开发经验优先
- 本科及以上学历""",
    help="粘贴完整的岗位描述，系统会自动解析核心要求"
)

# Configuration options
col1, col2, col3 = st.columns(3)
with col1:
    top_k = st.slider("推荐人数", 5, 20, 10, help="返回前 K 个最匹配的候选人")
with col2:
    use_hyde = st.checkbox("启用 HyDE", value=True, help="使用假设文档增强检索")
with col3:
    use_rerank = st.checkbox("启用精排", value=True, help="使用 Cross-Encoder 精排")

# Search button
if st.button("🚀 开始推荐", type="primary", disabled=not jd_text):
    with st.spinner("正在解析岗位需求..."):
        # TODO: Call actual retrieval pipeline
        # from app.core.retrieval.hybrid_pipeline import HybridRetrievalPipeline
        # jd_query, results = await HybridRetrievalPipeline.retrieve(
        #     jd_text=jd_text,
        #     top_k=top_k,
        #     use_hyde=use_hyde,
        #     use_rerank=use_rerank
        # )
        
        # Mock results for now
        st.session_state.jd_query = {
            "must_skills": ["Python", "FastAPI", "Docker"],
            "nice_skills": ["Kubernetes", "微服务"],
            "min_years": 5,
            "min_degree": "本科",
            "intent_summary": "寻找资深 Python 后端工程师"
        }
        
        st.session_state.recommendation_results = [
            {
                "resume_id": f"resume_{i}",
                "name": f"候选人_{i+1}",
                "match_score": 95 - i * 5,
                "skills": ["Python", "FastAPI", "Docker", "Kubernetes"][:4-i%2],
                "years": 6 - i * 0.5,
                "degree": "本科" if i % 2 == 0 else "硕士",
                "match_items": ["核心技能匹配", "经验年限符合"],
                "improvement_items": ["可加强微服务经验"] if i > 2 else [],
                "summary": f"匹配度 {95 - i * 5}分，技能与经验均符合要求。"
            }
            for i in range(top_k)
        ]
        
        st.success(f"✅ 找到 {len(st.session_state.recommendation_results)} 位匹配候选人")

# Display results
if st.session_state.recommendation_results:
    st.divider()
    st.header("推荐结果")
    
    # Show JD analysis
    if st.session_state.jd_query:
        with st.expander("📋 岗位需求解析", expanded=True):
            jd = st.session_state.jd_query
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**核心技能**: {', '.join(jd['must_skills'])}")
                st.markdown(f"**经验要求**: {jd['min_years']}年以上")
            with col2:
                st.markdown(f"**加分技能**: {', '.join(jd['nice_skills'])}")
                st.markdown(f"**学历要求**: {jd['min_degree']}及以上")
    
    # Display candidate cards
    for i, result in enumerate(st.session_state.recommendation_results):
        with st.expander(
            f"#{i+1} {result['name']} - 匹配度 {result['match_score']}分",
            expanded=(i < 3)  # Expand top 3 by default
        ):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.metric("匹配度", f"{result['match_score']}分")
                st.metric("经验年限", f"{result['years']}年")
                st.metric("学历", result['degree'])
            
            with col2:
                st.markdown("**核心技能**")
                st.markdown(", ".join(result['skills']))
                
                if result.get('match_items'):
                    st.markdown("**✅ 匹配项**")
                    for item in result['match_items']:
                        st.markdown(f"- {item}")
                
                if result.get('improvement_items'):
                    st.markdown("**⚠️ 待提高**")
                    for item in result['improvement_items']:
                        st.markdown(f"- {item}")
            
            with col3:
                st.markdown("**综合评价**")
                st.info(result['summary'])
    
    # Comparison section
    st.divider()
    st.header("候选人对比")
    
    selected_candidates = st.multiselect(
        "选择要对比的候选人（2-4人）",
        options=[f"{r['name']} ({r['match_score']}分)" for r in st.session_state.recommendation_results],
        default=[f"{r['name']} ({r['match_score']}分)" for r in st.session_state.recommendation_results[:3]],
        max_selections=4
    )
    
    if len(selected_candidates) >= 2:
        # TODO: Generate radar chart
        st.info("📊 雷达图对比功能开发中...")
        
        # Simple comparison table
        comparison_data = []
        for name in selected_candidates:
            for r in st.session_state.recommendation_results:
                if f"{r['name']} ({r['match_score']}分)" == name:
                    comparison_data.append({
                        "候选人": r['name'],
                        "匹配度": r['match_score'],
                        "经验": f"{r['years']}年",
                        "学历": r['degree'],
                        "技能": ", ".join(r['skills'][:3])
                    })
        
        st.dataframe(comparison_data, use_container_width=True)

# Sidebar info
with st.sidebar:
    st.header("推荐说明")
    st.markdown("""
    ### 推荐流程
    1. **JD 解析** → 提取核心技能、经验要求
    2. **双路召回** → Milvus 语义 + ES 关键词
    3. **RRF 融合** → 合并两路结果
    4. **精排** → Cross-Encoder 精细打分
    5. **生成理由** → LLM 生成匹配分析
    
    ### 配置说明
    - **推荐人数**: 返回前 K 个候选人
    - **HyDE**: 生成假设文档提升召回
    - **精排**: 使用 Reranker 精细排序
    """)
    
    st.divider()
    st.caption("提示：推荐结果可导出或进一步追问筛选")
