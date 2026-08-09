"""对话追问：与智能招聘助手对话，基于简历库检索回答。"""

import streamlit as st

from common import run_async

st.title("对话追问")
st.caption("用自然语言筛选与对比候选人，助手会自动调用语义检索 / 关键词检索 / 条件筛选工具")

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

EXAMPLES = [
    "有哪些候选人熟悉 Java 和 Spring？",
    "5 年以上经验的候选人有哪些？",
    "对比一下候选人的学历和技能",
    "推荐适合后端开发岗位的人选",
]

with st.sidebar:
    if st.button("清空对话", icon=":material/delete_sweep:", width="stretch"):
        from app.core.agent.chat_agent import ChatAgent

        ChatAgent.clear_memory()
        st.session_state.chat_messages = []
        st.rerun()

    st.markdown("**示例问题**")
    for q in EXAMPLES:
        if st.button(q, key=f"eg_{q}", width="stretch"):
            st.session_state.pending_question = q
            st.rerun()

# 历史消息
for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 首次进入的欢迎语
if not st.session_state.chat_messages:
    st.info(
        "你可以直接提问，例如：「有哪些 5 年以上经验的 Java 候选人？」助手会检索简历库后回答。",
        icon=":material/chat:",
    )


def ask(question: str) -> None:
    """向 ChatAgent 提问并渲染回答。"""
    from app.core.agent.chat_agent import ChatAgent

    st.session_state.chat_messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("正在检索简历库…"):
            answer = run_async(ChatAgent.chat(question))
        st.markdown(answer)
    st.session_state.chat_messages.append({"role": "assistant", "content": answer})


if prompt := st.chat_input("请输入问题…"):
    ask(prompt)
elif st.session_state.get("pending_question"):
    question = st.session_state.pop("pending_question")
    ask(question)
