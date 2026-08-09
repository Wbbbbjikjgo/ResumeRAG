"""JD (Job Description) parser for structured query generation."""

import json
import re

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from app.core.models import JDQuery
from app.core.infra.llm_factory import LLMFactory


class JDParser:
    """Parse job descriptions into structured queries."""

    PARSE_PROMPT = ChatPromptTemplate.from_messages([
        ("system", """你是一个专业的岗位需求解析助手。请从以下岗位描述（JD）中提取结构化信息。

要求：
1. must_skills: 硬性技能要求（必须具备的技能）
2. nice_skills: 加分技能（有则更好）
3. min_years: 最低工作年限要求（数字，无要求则为 null）
4. min_degree: 最低学历要求（大专/本科/硕士/博士，无要求则为 null）
5. keywords: 扩展查询词（同义词、近义词、相关术语，用于提升召回率）
6. intent_summary: 100字以内的岗位需求摘要

输出格式：严格 JSON，不要包含其他文字。"""),
        ("human", "请解析以下岗位描述：\n\n{jd_text}")
    ])

    @classmethod
    async def parse(cls, jd_text: str) -> JDQuery:
        """
        Parse job description into structured query.
        
        Args:
            jd_text: Raw job description text
            
        Returns:
            JDQuery with structured fields
        """
        if not jd_text or len(jd_text.strip()) < 20:
            logger.warning("JD text too short for parsing")
            return cls._fallback_parse(jd_text)
        
        try:
            llm = LLMFactory.get_llm()

            result = await llm.ainvoke([
                ("system", """你是一个专业的岗位需求解析助手。请从以下岗位描述（JD）中提取结构化信息。

要求：
1. must_skills: 硬性技能要求（必须具备的技能）
2. nice_skills: 加分技能（有则更好）
3. min_years: 最低工作年限要求（数字，无要求则为 null）
4. min_degree: 最低学历要求（大专/本科/硕士/博士，无要求则为 null）
5. keywords: 扩展查询词（同义词、近义词、相关术语）
6. intent_summary: 100字以内的岗位需求摘要

输出格式：严格 JSON 对象，键为上述字段，不要包含其他文字或 markdown 标记。"""),
                ("human", f"请解析以下岗位描述：\n\n{jd_text[:5000]}")
            ], response_format={"type": "json_object"})

            response_text = result.content if hasattr(result, "content") else str(result)
            parsed = cls._extract_json(response_text)
            jd_query = JDQuery(**parsed)

            logger.info(f"JD parsed: {len(jd_query.must_skills)} must skills, {len(jd_query.nice_skills)} nice skills")
            return jd_query

        except Exception as e:
            logger.error(f"LLM JD parsing failed: {e}, falling back to regex")
            return cls._fallback_parse(jd_text)

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract a JSON object from LLM response text."""
        text = text.strip()
        # 去掉可能的 markdown 代码块标记
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                return json.loads(match.group())
            raise

    @classmethod
    def _fallback_parse(cls, jd_text: str) -> JDQuery:
        """
        Fallback JD parsing using regex patterns.
        
        Used when LLM parsing fails.
        """
        if not jd_text:
            return JDQuery()
        
        # Extract years requirement
        min_years = None
        years_match = re.search(r"(\d+)\s*[年y]+\s*(?:以上|经验|experience)", jd_text, re.IGNORECASE)
        if years_match:
            min_years = float(years_match.group(1))
        
        # Extract degree requirement
        min_degree = None
        degree_patterns = [
            (r"博士|PhD|Doctorate", "博士"),
            (r"硕士|Master|研究生", "硕士"),
            (r"本科|Bachelor|大学", "本科"),
            (r"大专|College|专科", "大专"),
        ]
        for pattern, degree in degree_patterns:
            if re.search(pattern, jd_text, re.IGNORECASE):
                min_degree = degree
                break
        
        # Extract skills (simple keyword matching)
        from app.core.parsing.splitter import ResumeSplitter
        all_skills = ResumeSplitter.extract_skills(jd_text)
        
        # Assume all extracted skills are must-have for fallback
        must_skills = all_skills[:10]  # Limit to top 10
        nice_skills = all_skills[10:20]
        
        # Generate keywords (synonyms)
        keywords = cls._generate_keywords(must_skills)
        
        # Generate summary
        intent_summary = f"岗位需要 {len(must_skills)} 项核心技能"
        if min_years:
            intent_summary += f"，{min_years}年以上经验"
        if min_degree:
            intent_summary += f"，{min_degree}及以上学历"
        
        return JDQuery(
            must_skills=must_skills,
            nice_skills=nice_skills,
            min_years=min_years,
            min_degree=min_degree,
            keywords=keywords,
            intent_summary=intent_summary
        )

    @staticmethod
    def _generate_keywords(skills: list[str]) -> list[str]:
        """Generate expanded keywords with synonyms."""
        synonym_map = {
            "Python": ["Python开发", "Python工程师", "Django", "Flask", "FastAPI"],
            "Java": ["Java开发", "Spring", "Spring Boot", "JVM"],
            "JavaScript": ["JS", "ES6", "TypeScript", "前端开发"],
            "React": ["React.js", "React Native", "前端框架"],
            "Vue": ["Vue.js", "Vuex", "前端框架"],
            "Machine Learning": ["ML", "机器学习", "深度学习", "AI"],
            "Docker": ["容器化", "Docker Compose", "Kubernetes"],
            "MySQL": ["关系型数据库", "SQL", "数据库"],
            "Redis": ["缓存", "NoSQL", "内存数据库"],
        }
        
        keywords = []
        for skill in skills:
            if skill in synonym_map:
                keywords.extend(synonym_map[skill])
            else:
                keywords.append(skill)
        
        return list(set(keywords))  # Deduplicate

    @classmethod
    async def generate_hyde_document(cls, jd_query: JDQuery) -> str:
        """
        Generate hypothetical document using HyDE technique.
        
        Creates an "ideal resume summary" that matches the JD,
        which can be used to improve semantic retrieval.
        
        Args:
            jd_query: Parsed JD query
            
        Returns:
            Hypothetical resume text
        """
        prompt = """基于以下岗位需求，生成一份理想候选人的简历摘要（300字以内）。

岗位需求：
- 核心技能：{must_skills}
- 加分技能：{nice_skills}
- 经验要求：{min_years}年
- 学历要求：{min_degree}
- 岗位摘要：{intent_summary}

请生成一份符合该岗位要求的候选人简历摘要，突出相关经验和技能。"""

        try:
            llm = LLMFactory.get_llm()
            
            result = await llm.ainvoke([
                ("system", "你是一个专业的简历撰写助手。请根据岗位需求生成一份理想候选人的简历摘要。"),
                ("human", prompt.format(
                    must_skills=", ".join(jd_query.must_skills) if jd_query.must_skills else "无特定要求",
                    nice_skills=", ".join(jd_query.nice_skills) if jd_query.nice_skills else "无",
                    min_years=jd_query.min_years or "无特定要求",
                    min_degree=jd_query.min_degree or "无特定要求",
                    intent_summary=jd_query.intent_summary
                ))
            ])
            
            hyde_doc = result.content if hasattr(result, "content") else str(result)
            logger.info(f"HyDE document generated: {len(hyde_doc)} chars")
            return hyde_doc
            
        except Exception as e:
            logger.error(f"HyDE generation failed: {e}")
            # Fallback: use intent summary
            return jd_query.intent_summary
