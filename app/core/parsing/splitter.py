"""Resume text splitter for semantic section splitting."""

import re
from typing import TypedDict

from loguru import logger


class ResumeSection(TypedDict):
    """Resume section with name and content."""
    section_name: str
    content: str


class ResumeSplitter:
    """Split resume text into semantic sections."""

    # Common section headers in Chinese resumes
    SECTION_PATTERNS = [
        # Basic info
        (r"(?:^|\n)\s*(?:基本信息|个人信息|个人资料|Basic\s+Info|Personal\s+Info)\s*(?:\n|$)", "基本信息"),
        # Education
        (r"(?:^|\n)\s*(?:教育(?:经历|背景)|学历|Education(?:al)?(?:\s+Background)?)\s*(?:\n|$)", "教育经历"),
        # Work experience
        (r"(?:^|\n)\s*(?:工作(?:经历|经验)|实习(?:经历|经验)|Work\s+(?:Experience|History))\s*(?:\n|$)", "工作经历"),
        # Project experience
        (r"(?:^|\n)\s*(?:项目(?:经历|经验)|Project\s+(?:Experience|History))\s*(?:\n|$)", "项目经历"),
        # Skills
        (r"(?:^|\n)\s*(?:技能|专业技能|技术栈|Skills|Technical\s+Skills)\s*(?:\n|$)", "技能"),
        # Certificates
        (r"(?:^|\n)\s*(?:证书|资格证书|Certifications?|Certificates?)\s*(?:\n|$)", "证书"),
        # Awards
        (r"(?:^|\n)\s*(?:荣誉|获奖|奖项|Awards?|Honors?)\s*(?:\n|$)", "荣誉"),
        # Self evaluation
        (r"(?:^|\n)\s*(?:自我评价|个人总结|Self[-\s]?(?:Evaluation|Summary))\s*(?:\n|$)", "自我评价"),
        # Objective
        (r"(?:^|\n)\s*(?:求职意向|职业目标|Objective|Career\s+Objective)\s*(?:\n|$)", "求职意向"),
    ]

    @classmethod
    def split(cls, text: str) -> list[ResumeSection]:
        """
        Split resume text into sections.
        
        Args:
            text: Full resume text
            
        Returns:
            List of sections with name and content
        """
        if not text or not text.strip():
            return []
        
        # Find all section boundaries
        boundaries = []
        for pattern, section_name in cls.SECTION_PATTERNS:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                boundaries.append({
                    "start": match.start(),
                    "end": match.end(),
                    "name": section_name
                })
        
        # Sort by position
        boundaries.sort(key=lambda x: x["start"])
        
        # Extract sections
        sections = []
        for i, boundary in enumerate(boundaries):
            start = boundary["end"]
            end = boundaries[i + 1]["start"] if i + 1 < len(boundaries) else len(text)
            
            content = text[start:end].strip()
            if content:
                sections.append({
                    "section_name": boundary["name"],
                    "content": content
                })
        
        # If no sections found, treat as single section
        if not sections:
            logger.warning("No section boundaries found, treating as single section")
            sections = [{
                "section_name": "全文",
                "content": text.strip()
            }]
        
        # Extract header (text before first section)
        if boundaries and boundaries[0]["start"] > 0:
            header = text[:boundaries[0]["start"]].strip()
            if header and len(header) > 20:  # Only if substantial
                sections.insert(0, {
                    "section_name": "头部",
                    "content": header
                })
        
        logger.info(f"Split resume into {len(sections)} sections")
        return sections

    @classmethod
    def get_full_text(cls, sections: list[ResumeSection]) -> str:
        """Combine sections back into full text."""
        return "\n\n".join(f"【{s['section_name']}】\n{s['content']}" for s in sections)

    @classmethod
    def get_section_by_name(cls, sections: list[ResumeSection], name: str) -> ResumeSection | None:
        """Get section by name."""
        for section in sections:
            if section["section_name"] == name:
                return section
        return None

    @classmethod
    def estimate_years_of_experience(cls, text: str) -> float | None:
        """
        Estimate years of experience from resume text.
        
        Returns:
            Estimated years or None if not found
        """
        # Look for explicit mentions
        patterns = [
            r"(\d+(?:\.\d+)?)\s*[年年]\s*(?:以上\s*)?(?:工作|相关)?(?:经验|经历)",
            r"(?:工作|相关)?(?:经验|经历)\s*(?:为|达|有)?\s*(\d+(?:\.\d+)?)\s*年",
            r"(\d+)\+?\s*years?\s*(?:of\s+)?experience",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        # Estimate from work history dates
        work_dates = re.findall(r"(\d{4})[.\-/年](\d{1,2})?(?:月)?\s*[-–~至到]\s*(\d{4})[.\-/年]?(\d{1,2})?(?:月)?", text)
        if work_dates:
            total_months = 0
            for start_year, start_month, end_year, end_month in work_dates:
                try:
                    start = int(start_year) * 12 + (int(start_month) if start_month else 1)
                    end = int(end_year) * 12 + (int(end_month) if end_month else 12)
                    total_months += max(0, end - start)
                except ValueError:
                    continue
            
            if total_months > 0:
                return round(total_months / 12, 1)
        
        return None

    @classmethod
    def extract_skills(cls, text: str) -> list[str]:
        """
        Extract skills from resume text using keyword matching.
        
        Returns:
            List of extracted skills
        """
        # Common tech skills
        tech_skills = [
            "Python", "Java", "JavaScript", "TypeScript", "Go", "Golang", "Rust", "C\\+\\+", "C#",
            "React", "Vue", "Angular", "Node\\.js", "Django", "Flask", "FastAPI", "Spring",
            "MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
            "Docker", "Kubernetes", "AWS", "Azure", "GCP",
            "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
            "PyTorch", "TensorFlow", "LangChain",
            "SQL", "NoSQL", "REST API", "GraphQL", "Microservices",
        ]
        
        # Common soft skills
        soft_skills = [
            "团队管理", "项目管理", "沟通协调", "领导力", "问题解决",
            "Team Leadership", "Project Management", "Communication",
        ]
        
        all_skills = tech_skills + soft_skills
        found_skills = set()
        
        for skill in all_skills:
            pattern = rf"\b{skill}\b"
            if re.search(pattern, text, re.IGNORECASE):
                # Normalize skill name
                normalized = skill.replace("\\+", "+").replace("\\.", ".")
                found_skills.add(normalized)
        
        return list(found_skills)
