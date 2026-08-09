"""Conversational chat agent for interactive retrieval."""

import asyncio
from typing import AsyncIterator, Any

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain.memory import ConversationBufferWindowMemory
from loguru import logger

from app.core.infra.llm_factory import LLMFactory
from app.core.agent.tools import TOOL_REGISTRY


class ChatAgent:
    """Conversational agent for interactive resume retrieval."""

    _agent_executor: AgentExecutor | None = None
    _memory: ConversationBufferWindowMemory | None = None

    @classmethod
    def _get_agent(cls) -> AgentExecutor:
        """Get or create agent executor."""
        if cls._agent_executor is None:
            llm = LLMFactory.get_llm()
            
            # Create memory
            cls._memory = ConversationBufferWindowMemory(
                memory_key="chat_history",
                return_messages=True,
                k=10  # Keep last 10 turns
            )
            
            # Create prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", """你是 ResumeRAG 智能招聘助手。你可以帮助 HR 进行以下操作：

1. **语义检索**：使用 semantic_search 工具根据自然语言查询简历
2. **关键词检索**：使用 keyword_search 工具根据关键词检索简历
3. **条件筛选**：使用 filter_search 工具按技能/年限/学历筛选
4. **对比候选人**：使用 compare_candidates 工具对比多个候选人

回答要求：
- 使用中文回答
- 回答要简洁、准确
- 如果需要检索，主动调用工具
- 如果信息不足，明确说明

可用工具：
{tools}

工具名称：{tool_names}

历史对话：{chat_history}"""),
                MessagesPlaceholder(variable_name="input"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            # Create agent
            agent = create_react_agent(
                llm=llm,
                tools=TOOL_REGISTRY,
                prompt=prompt
            )
            
            # Create executor
            cls._agent_executor = AgentExecutor(
                agent=agent,
                tools=TOOL_REGISTRY,
                memory=cls._memory,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5
            )
            
            logger.info("Chat agent initialized")
        
        return cls._agent_executor

    @classmethod
    async def chat(cls, question: str, session_id: str | None = None) -> str:
        """
        Chat with the agent (non-streaming).
        
        Args:
            question: User question
            session_id: Optional session ID for conversation isolation
            
        Returns:
            Agent response
        """
        logger.info(f"Chat question: {question[:50]}...")
        
        agent = cls._get_agent()
        
        try:
            result = await agent.ainvoke({
                "input": question
            })
            
            response = result.get("output", "抱歉，我无法回答这个问题。")
            logger.info(f"Chat response: {response[:50]}...")
            
            return response
            
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return f"抱歉，处理您的问题时出现错误：{str(e)}"

    @classmethod
    async def chat_stream(cls, question: str, session_id: str | None = None) -> AsyncIterator[str]:
        """
        Chat with the agent (streaming with typewriter effect).
        
        Args:
            question: User question
            session_id: Optional session ID
            
        Yields:
            Response tokens
        """
        logger.info(f"Chat stream question: {question[:50]}...")
        
        agent = cls._get_agent()
        
        try:
            async for event in agent.astream_events({
                "input": question
            }, version="v1"):
                kind = event.get("event")
                
                # Stream LLM tokens
                if kind == "on_chat_model_stream":
                    content = event.get("data", {}).get("chunk", {})
                    if hasattr(content, "content") and content.content:
                        yield content.content
                
                # Stream tool calls (for visibility)
                elif kind == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    yield f"\n*[调用工具: {tool_name}]*\n"
                    
        except Exception as e:
            logger.error(f"Chat stream failed: {e}")
            yield f"抱歉，处理您的问题时出现错误：{str(e)}"

    @classmethod
    def clear_memory(cls, session_id: str | None = None):
        """Clear conversation memory."""
        if cls._memory:
            cls._memory.clear()
            logger.info("Chat memory cleared")

    @classmethod
    def get_chat_history(cls) -> list[dict[str, str]]:
        """Get conversation history."""
        if not cls._memory:
            return []
        
        messages = cls._memory.chat_memory.messages
        return [
            {
                "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                "content": msg.content
            }
            for msg in messages
        ]
