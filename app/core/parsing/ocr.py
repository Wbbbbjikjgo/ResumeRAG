"""OCR module for scanned document recognition."""

import io
from typing import Any

from loguru import logger

from app.core.config import get_settings


class OCREngine:
    """OCR engine abstraction for PaddleOCR and Tesseract."""

    _paddle_ocr_instance: Any = None

    @classmethod
    async def recognize(cls, image_content: bytes, engine: str | None = None) -> str:
        """
        Recognize text from image.
        
        Args:
            image_content: Image bytes
            engine: OCR engine to use (paddleocr/tesseract), defaults to config
            
        Returns:
            Recognized text
        """
        settings = get_settings()
        engine = engine or settings.parsing.ocr_engine
        
        if engine == "paddleocr":
            return await cls._recognize_paddle(image_content)
        elif engine == "tesseract":
            return await cls._recognize_tesseract(image_content)
        else:
            logger.warning(f"Unknown OCR engine: {engine}, falling back to paddleocr")
            return await cls._recognize_paddle(image_content)

    @classmethod
    async def _recognize_paddle(cls, image_content: bytes) -> str:
        """Recognize text using PaddleOCR."""
        try:
            from paddleocr import PaddleOCR
            from PIL import Image
            import numpy as np
            
            # Initialize PaddleOCR (lazy loading)
            if cls._paddle_ocr_instance is None:
                logger.info("Initializing PaddleOCR...")
                cls._paddle_ocr_instance = PaddleOCR(
                    use_angle_cls=True,
                    lang="ch",  # Chinese + English
                    show_log=False
                )
            
            # Convert bytes to numpy array
            image = Image.open(io.BytesIO(image_content))
            img_array = np.array(image)
            
            # Run OCR
            result = cls._paddle_ocr_instance.ocr(img_array, cls=True)
            
            # Extract text
            text_parts = []
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) >= 2:
                        text_parts.append(line[1][0])
            
            text = "\n".join(text_parts)
            logger.info(f"PaddleOCR recognized {len(text)} characters")
            
            return text
            
        except ImportError:
            logger.error("PaddleOCR not installed, falling back to Tesseract")
            return await cls._recognize_tesseract(image_content)
        except Exception as e:
            logger.error(f"PaddleOCR failed: {e}")
            return ""

    @classmethod
    async def _recognize_tesseract(cls, image_content: bytes) -> str:
        """Recognize text using Tesseract."""
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(io.BytesIO(image_content))
            
            # Use Chinese + English
            text = pytesseract.image_to_string(image, lang="chi_sim+eng")
            
            logger.info(f"Tesseract recognized {len(text)} characters")
            return text
            
        except ImportError:
            logger.error("Tesseract not installed")
            return ""
        except Exception as e:
            logger.error(f"Tesseract failed: {e}")
            return ""

    @classmethod
    async def recognize_pdf_pages(cls, pdf_content: bytes, page_indices: list[int] | None = None) -> str:
        """
        Recognize text from specific PDF pages using OCR.
        
        Args:
            pdf_content: PDF bytes
            page_indices: List of page indices to OCR (0-based), None means all pages
            
        Returns:
            Recognized text from all specified pages
        """
        import pdfplumber
        from PIL import Image
        
        text_parts = []
        
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            pages = page_indices if page_indices is not None else range(len(pdf.pages))
            
            for page_idx in pages:
                if page_idx >= len(pdf.pages):
                    continue
                
                page = pdf.pages[page_idx]
                
                # Convert page to image
                img = page.to_image(resolution=300)
                img_bytes = io.BytesIO()
                img.original.save(img_bytes, format="PNG")
                img_bytes.seek(0)
                
                # OCR the image
                page_text = await cls.recognize(img_bytes.getvalue())
                if page_text:
                    text_parts.append(f"--- Page {page_idx + 1} ---\n{page_text}")
        
        return "\n\n".join(text_parts)
