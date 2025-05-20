import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
import camelot
from PIL import Image
import io
import logging
from typing import List, Dict, Any
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFProcessor:
    def __init__(self):
        self.min_text_length = 50  # Minimum text length to avoid OCR
        
    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract text from PDF with OCR fallback"""
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
            
        doc = fitz.open(pdf_path)
        extracted_content = []
        
        for page_num in range(len(doc)):
            logger.info(f"Processing page {page_num + 1}/{len(doc)}")
            page = doc[page_num]
            
            # Try direct text extraction
            text = page.get_text()
            
            # If text is too short, use OCR
            if len(text.strip()) < self.min_text_length:
                logger.info(f"Using OCR for page {page_num + 1}")
                text = self._ocr_page(page)
            
            # Extract tables
            tables = self._extract_tables(str(pdf_path), page_num + 1)
            
            extracted_content.append({
                'page_num': page_num + 1,
                'text': text,
                'tables': tables
            })
        
        doc.close()
        print(f"[pdf_processor] Extracted {len(extracted_content)} pages from {pdf_path.name}")
        return extracted_content
    
    def _ocr_page(self, page) -> str:
        """OCR a single page"""
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.pil_tobytes(format="PNG")))
        text = pytesseract.image_to_string(img)
        return text
    
    def _extract_tables(self, pdf_path: str, page_num: int) -> List[str]:
        """Extract tables from a specific page"""
        try:
            tables = camelot.read_pdf(
                pdf_path, 
                pages=str(page_num), 
                flavor='stream',
                suppress_warnings=True
            )
            return [table.df.to_string() for table in tables]
        except Exception as e:
            logger.warning(f"Table extraction failed for page {page_num}: {e}")
            return []


# Example usage
if __name__ == "__main__":
    processor = PDFProcessor()
    content = processor.extract_text_from_pdf("data/pdfs/sample_budget.pdf")
    print(f"Extracted {len(content)} pages")