"""对话追问页面 - 与智能助手交互式对话（打字机效果）"""

import streamlit as st
import asyncio

st.set_page_config(page_title="对话追问 - ResumeRAG", page_icon="💬", layout="wide")

st.title("💬 对话追问")
st.markdown("与智能助手对话，深入筛选候选人")

# Initialize session state
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "chat_initialized" not in st.session_state:
    st.session_state.chat_initialized = False

# Sidebar controls
with st.sidebar:
    st.header("对话设置")
    
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.chat_messages = []
        # TODO: Call ChatAgent.clear_memory()
        st.rerun()
    
    st.divider()
    
    st.markdown("### 示例问题")
    example_questions = [
        "有哪些候选人有 Python 经验？",
        "把 Top-5 的学历列出来",
        "有金融行业背景的候选人吗？",
        "对比前三位候选人的技能",
        "5年以上经验的候选人有多少？"
    ]
    
    for q in example_questions:
        if st.button(q, use_container_width=True, key=f"example_{q[:10]}"):
            st.session_state.pending_question = q
            st.rerun()
    
    st.divider()
    st.caption("提示：对话支持上下文理解，可以连续追问")

# Display chat history
chat_container = st.container()
with chat_container:
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("请输入您的问题..."):
    # Add user message
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response with typewriter effect
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # TODO: Call actual chat agent
        # from app.core.agent.chat_agent import ChatAgent
        # async for token in ChatAgent.chat_stream(prompt):
        #     full_response += token
        #     message_placeholder.markdown(full_response + "▌")
        
        # Mock response for now
        mock_responses = {
            "python": "根据检索结果，有以下候选人具备 Python 经验：\n\n1. **候选人_1** - 6年经验，精通 Python、FastAPI\n2. **候选人_2** - 5年经验，熟悉 Python、Django\n3. **候选人_3** - 4年经验，掌握 Python、Flask\n\n需要我详细介绍某位候选人吗？",
            "学历": "以下是 Top-5 候选人的学历信息：\n\n| 候选人 | 学历 | 学校 |\n|--------|------|------|\n| 候选人_1 | 本科 | 北京大学 |\n| 候选人_2 | 硕士 | 清华大学 |\n| 候选人_3 | 本科 | 复旦大学 |\n| 候选人_4 | 硕士 | 浙江大学 |\n| 候选人_5 | 本科 | 上海交通大学 |",
            "金融": "根据检索，有以下候选人具有金融行业背景：\n\n1. **候选人_5** - 曾在某银行工作3年\n2. **候选人_8** - 有证券从业经验\n\n需要了解更多详情吗？",
            "对比": "以下是前三位候选人的技能对比：\n\n| 技能 | 候选人_1 | 候选人_2 | 候选人_3 |\n|------|----------|----------|----------|\n| Python | ✅ | ✅ | ✅ |\n| FastAPI | ✅ | ❌ | ✅ |\n| Docker | ✅ | ✅ | ❌ |\n| Kubernetes | ✅ | ❌ | ❌ |\n\n候选人_1 技能最全面，候选人_2 经验最丰富。",
            "default": "我正在分析您的问题...\n\n根据当前简历库的检索结果，我为您找到以下信息：\n\n- 简历库共有 100+ 份简历\n- 可以根据技能、经验、学历等维度进行筛选\n- 支持自然语言查询\n\n请问您想了解哪方面的信息？"
        }
        
        # Select mock response
        response_text = mock_responses.get("default", mock_responses["default"])
        for key in mock_responses:
            if key in prompt.lower():
                response_text = mock_responses[key]
                break
        
        # Typewriter effect
        for char in response_text:
            full_response += char
            message_placeholder.markdown(full_response + "▌")
            # Small delay for effect (in real implementation, this comes from LLM streaming)
        
        message_placeholder.markdown(full_response)
    
    # Add assistant response
    st.session_state.chat_messages.append({"role": "assistant", "content": full_response})

# Handle pending question from sidebar
elif hasattr(st.session_state, "pending_question") and st.session_state.pending_question:
    question = st.session_state.pending_question
    st.session_state.pending_question = None
    
    # Add user message
    st.session_state.chat_messages.append({"role": "user", "content": question})
    
    # Rerun to process the question
    st.rerun()

# Welcome message if no chat history
if not st.session_state.chat_messages:
    st.info("""
    👋 欢迎使用 ResumeRAG 对话助手！
    
    您可以问我：
    - "有哪些候选人有 Python 经验？"
    - "把 Top-5 的学历列出来"
    - "有金融行业背景的候选人吗？"
    - "对比前三位候选人的技能"
    
    我会根据简历库为您检索和分析。
    """)
