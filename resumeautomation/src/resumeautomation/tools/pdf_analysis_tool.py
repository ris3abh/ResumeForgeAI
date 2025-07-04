from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
import os
import json
import fitz  # PyMuPDF
import pdfplumber
from PIL import Image
import cv2
import numpy as np
import easyocr

class PDFAnalysisInput(BaseModel):
    """Input schema for PDF Analysis Tool."""
    pdf_path: str = Field(..., description="Path to the PDF file to analyze")
    analysis_type: str = Field(default="full", description="Type of analysis: 'full', 'page_count', 'text_only', 'layout_only'")
    ocr_enabled: bool = Field(default=True, description="Whether to use OCR for text extraction")

class PDFAnalysisTool(BaseTool):
    name: str = "PDF Analysis Tool"
    description: str = (
        "Analyze PDF files to extract text, count pages, analyze layout, and verify formatting. "
        "Can perform OCR on image-based PDFs and provide detailed structure analysis."
    )
    args_schema: Type[BaseModel] = PDFAnalysisInput

    def __init__(self):
        super().__init__()
        self.ocr_reader = None

    def _run(self, pdf_path: str, analysis_type: str = "full", ocr_enabled: bool = True) -> str:
        """Analyze PDF file based on specified analysis type."""
        try:
            if not os.path.exists(pdf_path):
                return json.dumps({"status": "error", "message": f"PDF file not found: {pdf_path}"})
            
            analysis_result = {
                "status": "success",
                "file_path": pdf_path,
                "file_size": os.path.getsize(pdf_path)
            }
            
            if analysis_type in ["full", "page_count"]:
                analysis_result.update(self._analyze_page_count(pdf_path))
            
            if analysis_type in ["full", "text_only"]:
                analysis_result.update(self._extract_text(pdf_path, ocr_enabled))
            
            if analysis_type in ["full", "layout_only"]:
                analysis_result.update(self._analyze_layout(pdf_path))
            
            if analysis_type == "full":
                analysis_result.update(self._check_formatting_issues(analysis_result))
            
            return json.dumps(analysis_result, indent=2)
            
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def _analyze_page_count(self, pdf_path: str) -> dict:
        """Analyze PDF page count and basic properties."""
        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            
            pages_info = []
            for page_num in range(page_count):
                page = doc[page_num]
                page_info = {
                    "page_number": page_num + 1,
                    "width": page.rect.width,
                    "height": page.rect.height,
                    "rotation": page.rotation
                }
                pages_info.append(page_info)
            
            doc.close()
            
            return {
                "page_count": page_count,
                "is_single_page": page_count == 1,
                "pages_info": pages_info
            }
            
        except Exception as e:
            return {"page_analysis_error": str(e)}

    def _extract_text(self, pdf_path: str, ocr_enabled: bool = True) -> dict:
        """Extract text from PDF using multiple methods."""
        try:
            # Method 1: PyMuPDF text extraction
            doc = fitz.open(pdf_path)
            pymupdf_text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                pymupdf_text += page.get_text() + "\n"
            
            doc.close()
            
            # Method 2: pdfplumber text extraction
            pdfplumber_text = ""
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            pdfplumber_text += page_text + "\n"
            except Exception as e:
                pdfplumber_text = f"pdfplumber extraction failed: {str(e)}"
            
            # Method 3: OCR if enabled and little text found
            ocr_text = ""
            if ocr_enabled and len(pymupdf_text.strip()) < 100:
                try:
                    ocr_text = self._extract_text_ocr(pdf_path)
                except Exception as e:
                    ocr_text = f"OCR extraction failed: {str(e)}"
            
            # Choose best text extraction
            best_text = pymupdf_text
            if len(pdfplumber_text) > len(best_text):
                best_text = pdfplumber_text
            if len(ocr_text) > len(best_text):
                best_text = ocr_text
            
            return {
                "text_content": best_text,
                "text_length": len(best_text),
                "pymupdf_length": len(pymupdf_text),
                "pdfplumber_length": len(pdfplumber_text),
                "ocr_length": len(ocr_text),
                "extraction_method": "pymupdf" if best_text == pymupdf_text else "pdfplumber" if best_text == pdfplumber_text else "ocr",
                "word_count": len(best_text.split()),
                "line_count": len(best_text.split('\n'))
            }
            
        except Exception as e:
            return {"text_extraction_error": str(e)}

    def _extract_text_ocr(self, pdf_path: str) -> str:
        """Extract text using OCR from PDF."""
        try:
            if self.ocr_reader is None:
                self.ocr_reader = easyocr.Reader(['en'])
            
            # Convert PDF to images
            doc = fitz.open(pdf_path)
            ocr_text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Convert page to image
                mat = fitz.Matrix(2, 2)  # Zoom factor for better OCR
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Convert to numpy array for OCR
                nparr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                # Perform OCR
                results = self.ocr_reader.readtext(img)
                
                # Extract text from results
                page_text = ""
                for (bbox, text, confidence) in results:
                    if confidence > 0.5:  # Only include high-confidence text
                        page_text += text + " "
                
                ocr_text += page_text + "\n"
            
            doc.close()
            return ocr_text
            
        except Exception as e:
            return f"OCR processing failed: {str(e)}"

    def _analyze_layout(self, pdf_path: str) -> dict:
        """Analyze PDF layout and structure."""
        try:
            layout_info = {
                "tables": [],
                "text_blocks": [],
                "images": [],
                "fonts": {},
                "spacing_analysis": {}
            }
            
            # Use pdfplumber for detailed layout analysis
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Analyze tables
                    tables = page.find_tables()
                    if tables:
                        layout_info["tables"].extend([{
                            "page": page_num + 1,
                            "bbox": table.bbox,
                            "rows": len(table.extract())
                        } for table in tables])
                    
                    # Analyze text characteristics
                    chars = page.chars
                    if chars:
                        # Font analysis
                        fonts = {}
                        for char in chars:
                            font_name = char.get('fontname', 'Unknown')
                            font_size = char.get('size', 0)
                            font_key = f"{font_name}_{font_size}"
                            fonts[font_key] = fonts.get(font_key, 0) + 1
            return layout_info
        except Exception as e:
            return {"layout_analysis_error": str(e)}