"""Resume parsing pipeline orchestrator."""

import uuid
from datetime import datetime

from loguru import logger

from app.core.config import get_settings
from app.core.models import Resume, ResumeDocument, IngestResult
from app.core.parsing.loader import DocumentLoader
from app.core.parsing.ocr import OCREngine
from app.core.parsing.splitter import ResumeSplitter
from app.core.parsing.extractor import ResumeExtractor
from app.core.storage.ingest_service import IngestService


class ParsingPipeline:
    """Orchestrate the resume parsing process."""

    @classmethod
    async def parse_resume(
        cls,
        file_content: bytes,
        filename: str,
        content_type: str | None = None,
        use_ocr: bool | None = None
    ) -> tuple[ResumeDocument, list[dict]]:
        """
        Parse a resume file and return structured document + sections.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            content_type: MIME content type
            use_ocr: Force OCR on/off, None = auto-detect
            
        Returns:
            Tuple of (ResumeDocument, sections list)
        """
        settings = get_settings()
        resume_id = str(uuid.uuid4())
        
        logger.info(f"Starting parsing pipeline for: {filename}")
        
        # Step 1: Load document
        load_result = await DocumentLoader.load(file_content, filename, content_type)
        text = load_result["text"]
        metadata = load_result["metadata"]
        
        # Step 2: OCR if needed
        needs_ocr = metadata.get("needs_ocr", False)
        if use_ocr is None:
            use_ocr = settings.parsing.ocr_enabled and needs_ocr
        
        if use_ocr and (not text or len(text) < 100):
            logger.info(f"Running OCR on {filename}")
            if load_result["format"] == "image":
                text = await OCREngine.recognize(file_content)
            elif load_result["format"] == "pdf":
                text = await OCREngine.recognize_pdf_pages(file_content)
            
            metadata["ocr_applied"] = True
            metadata["ocr_engine"] = settings.parsing.ocr_engine
        else:
            metadata["ocr_applied"] = False
        
        # Truncate if too long
        max_length = settings.parsing.max_text_length
        if len(text) > max_length:
            text = text[:max_length]
            metadata["truncated"] = True
        else:
            metadata["truncated"] = False
        
        # Step 3: Split into sections
        sections = ResumeSplitter.split(text)
        
        # Step 4: Extract structured data
        resume = await ResumeExtractor.extract(text)
        
        # Step 5: Build document
        doc = ResumeDocument(
            resume_id=resume_id,
            name=resume.name,
            phone=resume.phone,
            email=resume.email,
            education=resume.education,
            experience=resume.experience,
            skills=resume.skills,
            years_of_experience=resume.years_of_experience,
            summary=resume.summary,
            full_text=text,
            parsed_metadata={
                **metadata,
                "parser": "pipeline_v1",
                "sections_count": len(sections),
                "parse_time": datetime.now().isoformat()
            },
            upload_time=datetime.now()
        )
        
        logger.info(f"Parsing complete: {filename} → {resume_id} (name: {doc.name})")
        
        return doc, sections

    @classmethod
    async def ingest_resume(
        cls,
        file_content: bytes,
        filename: str,
        content_type: str | None = None
    ) -> IngestResult:
        """
        Parse and ingest a resume into the system.
        
        This method handles the full pipeline including database storage.
        Currently returns parse result only; database storage will be added later.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            content_type: MIME content type
            
        Returns:
            IngestResult with status and parsed fields
        """
        resume_id = str(uuid.uuid4())
        
        try:
            doc, sections = await cls.parse_resume(file_content, filename, content_type)
            
            # 入库：MongoDB / Milvus / Elasticsearch
            store_status = await IngestService.store(doc, sections)
            
            failed_stores = [k for k, ok in store_status.items() if not ok]
            if failed_stores:
                return IngestResult(
                    resume_id=doc.resume_id,
                    filename=filename,
                    status="partial",
                    message=f"解析成功，但入库失败: {', '.join(failed_stores)}",
                    parsed_fields={
                        "name": doc.name,
                        "phone": doc.phone,
                        "email": doc.email,
                        "skills_count": len(doc.skills),
                        "years_of_experience": doc.years_of_experience,
                        "sections_count": len(sections)
                    }
                )
            
            return IngestResult(
                resume_id=doc.resume_id,
                filename=filename,
                status="success",
                message=f"Successfully parsed resume: {doc.name or 'Unknown'}",
                parsed_fields={
                    "name": doc.name,
                    "phone": doc.phone,
                    "email": doc.email,
                    "skills_count": len(doc.skills),
                    "years_of_experience": doc.years_of_experience,
                    "sections_count": len(sections)
                }
            )
            
        except Exception as e:
            logger.error(f"Ingestion failed for {filename}: {e}")
            return IngestResult(
                resume_id=resume_id,
                filename=filename,
                status="failed",
                message=f"Parsing failed: {str(e)}",
                parsed_fields={}
            )

    @classmethod
    async def batch_ingest(
        cls,
        files: list[tuple[bytes, str, str | None]]
    ) -> list[IngestResult]:
        """
        Batch ingest multiple resumes.
        
        Args:
            files: List of (file_content, filename, content_type) tuples
            
        Returns:
            List of IngestResult
        """
        results = []
        for file_content, filename, content_type in files:
            result = await cls.ingest_resume(file_content, filename, content_type)
            results.append(result)
        
        success_count = sum(1 for r in results if r.status == "success")
        logger.info(f"Batch ingestion complete: {success_count}/{len(results)} successful")
        
        return results
