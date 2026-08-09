"""Recommendation explanation generator."""

from typing import Any

from loguru import logger

from app.core.infra.llm_factory import LLMFactory
from app.core.models import JDQuery, Resume, RecommendResult
from app.core.generation.prompts import EXPLAIN_PROMPT


class Explainer:
    """Generate recommendation explanations."""

    @classmethod
    async def explain(
        cls,
        jd_query: JDQuery,
        resume: Resume,
        match_score: float
    ) -> dict[str, Any]:
        """
        Generate explanation for a recommendation.
        
        Args:
            jd_query: Parsed JD query
            resume: Parsed resume
            match_score: Pre-computed match score
            
        Returns:
            Dict with match_items, improvement_items, summary, highlighted_skills
        """
        try:
            # Build experience summary
            experience_summary = ""
            if resume.experience:
                exp_parts = []
                for exp in resume.experience[:3]:  # Top 3 experiences
                    exp_parts.append(f"{exp.company} - {exp.title} ({exp.start}~{exp.end})")
                experience_summary = "; ".join(exp_parts)
            
            # Build degree info
            degree = None
            if resume.education:
                degree = resume.education[0].degree
            
            # Generate explanation using LLM（非流式，避免 DeepSeek 流式+JSON 阻塞）
            llm = LLMFactory.get_llm(streaming=False)
            
            response = await llm.ainvoke([
                ("system", """你是一个专业的招聘顾问。请根据岗位需求和候选人简历，生成匹配度分析。

要求：
1. match_items: 候选人与岗位匹配的点（技能、经验、学历等）
2. improvement_items: 候选人可能不足的地方
3. summary: 100字以内的综合评语
4. highlighted_skills: 候选人具备的核心技能列表

输出格式：严格 JSON。"""),
                ("human", f"""岗位需求：
{jd_query.intent_summary}

核心要求：
- 必须技能：{', '.join(jd_query.must_skills) if jd_query.must_skills else '无特定要求'}
- 加分技能：{', '.join(jd_query.nice_skills) if jd_query.nice_skills else '无'}
- 经验要求：{jd_query.min_years or '不限'}年
- 学历要求：{jd_query.min_degree or '不限'}

候选人简历：
姓名：{resume.name or '未知'}
技能：{', '.join(resume.skills) if resume.skills else '未提取到'}
经验年限：{resume.years_of_experience or '未知'}
学历：{degree or '未知'}
工作经历摘要：{experience_summary or '无'}

请分析该候选人与岗位的匹配度。""")
            ])
            
            # Parse response
            response_text = response.content if hasattr(response, "content") else str(response)
            
            # Try to extract JSON from response
            import json
            import re
            
            # Look for JSON block
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    return {
                        "match_items": result.get("match_items", []),
                        "improvement_items": result.get("improvement_items", []),
                        "summary": result.get("summary", ""),
                        "highlighted_skills": result.get("highlighted_skills", [])
                    }
                except json.JSONDecodeError:
                    pass
            
            # Fallback: generate basic explanation
            return cls._fallback_explain(jd_query, resume, match_score)
            
        except Exception as e:
            logger.error(f"Explanation generation failed: {e}")
            return cls._fallback_explain(jd_query, resume, match_score)

    @classmethod
    def _fallback_explain(
        cls,
        jd_query: JDQuery,
        resume: Resume,
        match_score: float
    ) -> dict[str, Any]:
        """Generate basic explanation without LLM."""
        match_items = []
        improvement_items = []
        highlighted_skills = []
        
        # Check skill matches
        jd_skills = set(jd_query.must_skills + jd_query.nice_skills)
        resume_skills = set(resume.skills)
        
        matched_skills = jd_skills & resume_skills
        missing_skills = jd_skills - resume_skills
        
        if matched_skills:
            match_items.append(f"具备核心技能：{', '.join(list(matched_skills)[:5])}")
            highlighted_skills = list(matched_skills)
        
        if missing_skills:
            improvement_items.append(f"缺少技能：{', '.join(list(missing_skills)[:3])}")
        
        # Check experience
        if jd_query.min_years and resume.years_of_experience:
            if resume.years_of_experience >= jd_query.min_years:
                match_items.append(f"经验年限符合要求（{resume.years_of_experience}年）")
            else:
                improvement_items.append(f"经验年限不足（要求{jd_query.min_years}年，实际{resume.years_of_experience}年）")
        
        # Check degree
        if jd_query.min_degree and resume.education:
            degree_hierarchy = ["大专", "本科", "硕士", "博士"]
            try:
                required_idx = degree_hierarchy.index(jd_query.min_degree)
                actual_idx = degree_hierarchy.index(resume.education[0].degree)
                if actual_idx >= required_idx:
                    match_items.append(f"学历符合要求（{resume.education[0].degree}）")
                else:
                    improvement_items.append(f"学历低于要求（要求{jd_query.min_degree}，实际{resume.education[0].degree}）")
            except ValueError:
                pass
        
        # Generate summary
        summary = f"匹配度 {match_score:.0f}分。"
        if match_items:
            summary += match_items[0] + "。"
        
        return {
            "match_items": match_items,
            "improvement_items": improvement_items,
            "summary": summary,
            "highlighted_skills": highlighted_skills
        }

    @classmethod
    async def batch_explain(
        cls,
        jd_query: JDQuery,
        resumes: list[tuple[Resume, float]]
    ) -> list[dict[str, Any]]:
        """
        Generate explanations for multiple resumes.
        
        Args:
            jd_query: Parsed JD query
            resumes: List of (Resume, match_score) tuples
            
        Returns:
            List of explanation dicts
        """
        explanations = []
        for resume, score in resumes:
            explanation = await cls.explain(jd_query, resume, score)
            explanations.append(explanation)
        
        return explanations
