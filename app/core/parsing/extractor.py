"""LLM-based structured extraction for resume parsing."""

import re
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from app.core.config import get_settings
from app.core.infra.llm_factory import LLMFactory
from app.core.models import Resume, EducationItem, ExperienceItem


class ResumeExtractor:
    """Extract structured resume data using LLM."""

    EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
        ("system", """你是一个专业的简历解析助手。请从以下简历文本中提取结构化信息。

要求：
1. 严格按照提供的 JSON Schema 输出
2. 如果某个字段在文本中找不到，使用 null 或空列表
3. 教育经历按时间倒序排列
4. 工作经历按时间倒序排列
5. 技能列表去重并规范化（如 "JS" → "JavaScript"）
6. 工作年限根据工作经历估算，如果无法估算则为 null
7. 生成一段 100 字以内的简历摘要

输出格式：严格 JSON，不要包含其他文字。"""),
        ("human", "请解析以下简历：\n\n{resume_text}")
    ])

    @classmethod
    async def extract(cls, resume_text: str) -> Resume:
        """
        Extract structured resume data from text.
        
        Args:
            resume_text: Full resume text
            
        Returns:
            Parsed Resume object
        """
        if not resume_text or len(resume_text.strip()) < 50:
            logger.warning("Resume text too short for extraction")
            return cls._fallback_extract(resume_text)
        
        try:
            # Use LLM with structured output
            llm = LLMFactory.get_llm()
            structured_llm = llm.with_structured_output(Resume)
            
            result = await structured_llm.ainvoke([
                ("system", """你是一个专业的简历解析助手。请从以下简历文本中提取结构化信息。

要求：
1. 严格按照提供的 Schema 输出
2. 如果某个字段在文本中找不到，使用 null 或空列表
3. 教育经历按时间倒序排列
4. 工作经历按时间倒序排列
5. 技能列表去重并规范化
6. 工作年限根据工作经历估算
7. 生成一段 100 字以内的简历摘要"""),
                ("human", f"请解析以下简历：\n\n{resume_text[:10000]}")  # Limit to 10k chars
            ])
            
            logger.info(f"LLM extraction successful: {result.name}")
            return result
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}, falling back to regex")
            return cls._fallback_extract(resume_text)

    @classmethod
    def _fallback_extract(cls, resume_text: str) -> Resume:
        """
        Fallback extraction using regex patterns.
        
        Used when LLM extraction fails.
        """
        if not resume_text:
            return Resume()
        
        # Extract name (usually at the beginning)
        name = cls._extract_name(resume_text)
        
        # Extract contact info
        phone = cls._extract_phone(resume_text)
        email = cls._extract_email(resume_text)
        
        # Extract skills
        from app.core.parsing.splitter import ResumeSplitter
        skills = ResumeSplitter.extract_skills(resume_text)
        
        # Estimate years of experience
        years = ResumeSplitter.estimate_years_of_experience(resume_text)
        
        # Generate basic summary
        summary = f"简历包含 {len(skills)} 项技能"
        if years:
            summary += f"，约 {years} 年工作经验"
        
        return Resume(
            name=name,
            phone=phone,
            email=email,
            education=[],  # Regex extraction of education is complex, skip
            experience=[],  # Regex extraction of experience is complex, skip
            skills=skills,
            years_of_experience=years,
            summary=summary
        )

    @staticmethod
    def _extract_name(text: str) -> str | None:
        """Extract name from resume text."""
        # Name is usually at the beginning, before contact info
        lines = text.strip().split("\n")
        for line in lines[:5]:
            line = line.strip()
            # Skip lines that look like headers or contact info
            if not line or len(line) > 20:
                continue
            if re.search(r"电话|邮箱|email|phone|@\d", line, re.IGNORECASE):
                continue
            # Chinese name pattern (2-4 characters)
            if re.match(r"^[\u4e00-\u9fa5]{2,4}$", line):
                return line
            # English name pattern
            if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$", line):
                return line
        return None

    @staticmethod
    def _extract_phone(text: str) -> str | None:
        """Extract phone number from resume text."""
        # Chinese mobile phone
        match = re.search(r"1[3-9]\d{9}", text)
        if match:
            return match.group(0)
        
        # International format
        match = re.search(r"\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}", text)
        if match:
            return match.group(0)
        
        return None

    @staticmethod
    def _extract_email(text: str) -> str | None:
        """Extract email from resume text."""
        match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        if match:
            return match.group(0)
        return None

    @classmethod
    async def extract_with_validation(cls, resume_text: str) -> tuple[Resume, dict[str, Any]]:
        """
        Extract resume data with validation against original text.
        
        Returns:
            Tuple of (Resume, validation_info)
        """
        resume = await cls.extract(resume_text)
        
        # Validate extracted data
        validation = {
            "name_found": resume.name and resume.name.lower() in resume_text.lower(),
            "phone_found": resume.phone and resume.phone in resume_text,
            "email_found": resume.email and resume.email.lower() in resume_text.lower(),
            "skills_count": len(resume.skills),
            "skills_found_in_text": sum(
                1 for skill in resume.skills 
                if skill.lower() in resume_text.lower()
            ),
            "confidence": 0.0
        }
        
        # Calculate confidence score
        checks = [
            validation["name_found"],
            validation["phone_found"] or validation["email_found"],
            validation["skills_count"] > 0,
            validation["skills_found_in_text"] / max(validation["skills_count"], 1) > 0.8
        ]
        validation["confidence"] = sum(checks) / len(checks)
        
        return resume, validation
