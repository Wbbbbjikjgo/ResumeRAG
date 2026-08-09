"""简历管理页面 - 上传、解析、查看简历"""

import streamlit as st
import asyncio
from datetime import datetime

st.set_page_config(page_title="简历管理 - ResumeRAG", page_icon="📄", layout="wide")

st.title("📄 简历管理")
st.markdown("上传、解析和管理候选人简历")

# Initialize session state
if "parsed_resumes" not in st.session_state:
    st.session_state.parsed_resumes = []

# File upload section
st.header("上传简历")

uploaded_files = st.file_uploader(
    "选择简历文件（支持 PDF、Word、HTML、图片）",
    type=["pdf", "docx", "doc", "html", "htm", "png", "jpg", "jpeg"],
    accept_multiple_files=True,
    help="支持批量上传，系统会自动解析简历内容"
)

# Upload and parse button
if uploaded_files and st.button("🚀 开始解析", type="primary"):
    progress_bar = st.progress(0)
    status_container = st.container()
    
    with status_container:
        results = []
        total = len(uploaded_files)
        
        for i, uploaded_file in enumerate(uploaded_files):
            progress_bar.progress((i + 1) / total)
            
            with st.spinner(f"正在解析: {uploaded_file.name}"):
                try:
                    # Read file content
                    file_content = uploaded_file.getvalue()
                    
                    # TODO: Call actual parsing pipeline
                    # from app.core.parsing.pipeline import ParsingPipeline
                    # result = await ParsingPipeline.ingest_resume(
                    #     file_content,
                    #     uploaded_file.name,
                    #     uploaded_file.type
                    # )
                    
                    # Mock result for now
                    result = {
                        "filename": uploaded_file.name,
                        "status": "success",
                        "name": f"候选人_{i+1}",
                        "skills": ["Python", "FastAPI", "Docker"],
                        "years": 3.5,
                        "message": "解析成功"
                    }
                    
                    results.append(result)
                    st.session_state.parsed_resumes.append(result)
                    
                except Exception as e:
                    st.error(f"解析失败 {uploaded_file.name}: {str(e)}")
        
        progress_bar.progress(1.0)
        
        # Show results
        st.success(f"✅ 成功解析 {len([r for r in results if r['status'] == 'success'])} / {total} 份简历")

# Display parsed resumes
st.divider()
st.header("已解析简历")

if st.session_state.parsed_resumes:
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("简历总数", len(st.session_state.parsed_resumes))
    with col2:
        st.metric("今日上传", len([r for r in st.session_state.parsed_resumes if r.get("upload_date") == datetime.now().date()]))
    with col3:
        avg_skills = sum(len(r.get("skills", [])) for r in st.session_state.parsed_resumes) / len(st.session_state.parsed_resumes) if st.session_state.parsed_resumes else 0
        st.metric("平均技能数", f"{avg_skills:.1f}")
    
    st.divider()
    
    # Resume list
    for i, resume in enumerate(st.session_state.parsed_resumes):
        with st.expander(f"📋 {resume.get('name', 'Unknown')} - {resume.get('filename', '')}", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**文件名**: {resume.get('filename', 'N/A')}")
                st.markdown(f"**状态**: {resume.get('status', 'unknown')}")
                st.markdown(f"**技能**: {', '.join(resume.get('skills', []))}")
                if resume.get('years'):
                    st.markdown(f"**经验年限**: {resume.get('years')}年")
            
            with col2:
                if st.button("🗑️ 删除", key=f"delete_{i}"):
                    st.session_state.parsed_resumes.pop(i)
                    st.rerun()
else:
    st.info("暂无已解析简历，请上传简历文件")

# Sidebar info
with st.sidebar:
    st.header("解析说明")
    st.markdown("""
    ### 支持的格式
    - **PDF**: 文本型 PDF 自动提取，扫描件使用 OCR
    - **Word**: .docx 格式
    - **HTML**: 网页格式简历
    - **图片**: PNG/JPG，使用 PaddleOCR 识别
    
    ### 解析内容
    - 基本信息（姓名、联系方式）
    - 教育背景
    - 工作经历
    - 技能清单
    - 项目经验
    """)
    
    st.divider()
    st.caption("提示：解析后的简历会自动入库，用于后续的智能推荐")
