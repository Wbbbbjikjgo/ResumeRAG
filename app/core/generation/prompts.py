"""Prompt templates for generation module."""

from langchain_core.prompts import ChatPromptTemplate


# Recommendation explanation prompt
EXPLAIN_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个专业的招聘顾问。请根据岗位需求和候选人简历，生成匹配度分析。

要求：
1. match_items: 候选人与岗位匹配的点（技能、经验、学历等）
2. improvement_items: 候选人可能不足的地方
3. summary: 100字以内的综合评语
4. highlighted_skills: 候选人具备的核心技能列表

输出格式：严格 JSON，不要包含其他文字。"""),
    ("human", """岗位需求：
{jd_summary}

核心要求：
- 必须技能：{must_skills}
- 加分技能：{nice_skills}
- 经验要求：{min_years}年
- 学历要求：{min_degree}

候选人简历：
姓名：{name}
技能：{skills}
经验年限：{years}
学历：{degree}
工作经历摘要：{experience_summary}

请分析该候选人与岗位的匹配度。""")
])


# Resume summary generation prompt
SUMMARIZE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "你是一个专业的简历摘要撰写助手。请用简洁的语言概括候选人的核心优势（100字以内）。"),
    ("human", "请为以下简历生成摘要：\n\n{resume_text}")
])


# Chat response prompt
CHAT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是 ResumeRAG 智能招聘助手。基于检索到的简历信息回答 HR 的问题。

要求：
1. 回答要准确、简洁
2. 如果信息不足，明确说明
3. 支持对比分析、筛选建议等
4. 使用中文回答"""),
    ("human", "{question}")
])


# JD analysis prompt (for display)
JD_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """请分析以下岗位需求，生成清晰的结构化摘要，便于 HR 确认。

输出格式：
## 岗位摘要
[100字以内的岗位概述]

## 核心要求
- 必须技能：[列表]
- 加分技能：[列表]
- 经验要求：[X年以上/不限]
- 学历要求：[最低学历/不限]

## 扩展关键词
[用于检索的同义词/相关术语]"""),
    ("human", "岗位描述：\n\n{jd_text}")
])
