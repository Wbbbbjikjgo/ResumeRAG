"""Pydantic data models for ResumeRAG."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class EducationItem(BaseModel):
    """Education experience item."""
    school: str
    major: str
    degree: Literal["大专", "本科", "硕士", "博士", "其他"]
    start: str
    end: str


class ExperienceItem(BaseModel):
    """Work experience item."""
    company: str
    title: str
    start: str
    end: str
    description: str


class Resume(BaseModel):
    """Parsed resume structure."""
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    education: list[EducationItem] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    years_of_experience: float | None = None
    summary: str | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "张三",
                "phone": "13800138000",
                "email": "zhangsan@example.com",
                "education": [
                    {
                        "school": "北京大学",
                        "major": "计算机科学",
                        "degree": "本科",
                        "start": "2014",
                        "end": "2018"
                    }
                ],
                "experience": [
                    {
                        "company": "某科技公司",
                        "title": "Python开发工程师",
                        "start": "2018-07",
                        "end": "2022-06",
                        "description": "负责后端开发..."
                    }
                ],
                "skills": ["Python", "FastAPI", "Docker"],
                "years_of_experience": 4.0,
                "summary": "4年Python开发经验..."
            }
        }


class ResumeDocument(BaseModel):
    """Full resume document stored in MongoDB."""
    resume_id: str
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    education: list[EducationItem] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    years_of_experience: float | None = None
    summary: str | None = None
    full_text: str = ""
    parsed_metadata: dict = Field(default_factory=dict)
    upload_time: datetime = Field(default_factory=datetime.now)


class JDQuery(BaseModel):
    """Structured JD query parsed by LLM."""
    must_skills: list[str] = Field(default_factory=list, description="硬性技能要求")
    nice_skills: list[str] = Field(default_factory=list, description="加分技能")
    min_years: float | None = None
    min_degree: str | None = None
    keywords: list[str] = Field(default_factory=list, description="扩展查询词（同义词/近义词）")
    intent_summary: str = ""


class RetrievalResult(BaseModel):
    """Single retrieval result."""
    resume_id: str
    score: float
    source: Literal["milvus", "elasticsearch", "fusion"]
    matched_sections: list[str] = Field(default_factory=list)


class RecommendResult(BaseModel):
    """Recommendation result with explanation."""
    resume_id: str
    resume: Resume | None = None
    match_score: float = Field(description="匹配度分数 0-100")
    rerank_score: float = 0.0
    rrf_score: float = 0.0
    match_items: list[str] = Field(default_factory=list, description="匹配项")
    improvement_items: list[str] = Field(default_factory=list, description="待提高项")
    summary: str = ""
    highlighted_skills: list[str] = Field(default_factory=list)


class RadarData(BaseModel):
    """Radar chart data for comparison."""
    resume_id: str
    name: str
    dimensions: dict[str, float] = Field(default_factory=dict)
    # 示例: {"技能匹配": 85, "经验年限": 70, "学历": 90, "项目相关度": 75, "行业背景": 60}


class ChatMessage(BaseModel):
    """Chat message for conversation."""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class IngestResult(BaseModel):
    """Result of resume ingestion."""
    resume_id: str
    filename: str
    status: Literal["success", "failed", "partial"]
    message: str = ""
    parsed_fields: dict = Field(default_factory=dict)
