# app/services/cv_parser.py
import io
import re
from typing import Dict, Any, List
from PyPDF2 import PdfReader
import docx2txt
import pytesseract
from PIL import Image
import fitz  # PyMuPDF

class CVParser:
    def __init__(self):
        self.section_headers = [
            'education', 'experience', 'skills', 'projects',
            'certifications', 'publications', 'summary', 'objective',
            'work experience', 'professional experience', 'employment',
            'academic background', 'technical skills', 'achievements'
        ]
    
    async def parse(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Parse CV from various formats
        """
        file_extension = filename.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            return await self.parse_pdf(file_content)
        elif file_extension in ['doc', 'docx']:
            return await self.parse_docx(file_content)
        elif file_extension in ['txt']:
            return await self.parse_text(file_content)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    async def parse_pdf(self, content: bytes) -> Dict[str, Any]:
        """
        Parse PDF with multiple methods for better extraction
        """
        text = ""
        metadata = {}
        
        # Method 1: PyPDF2
        try:
            pdf = PdfReader(io.BytesIO(content))
            metadata['pages'] = len(pdf.pages)
            
            for page in pdf.pages:
                text += page.extract_text() + "\n"
            
            # Extract metadata
            if pdf.metadata:
                metadata['title'] = pdf.metadata.get('/Title', '')
                metadata['author'] = pdf.metadata.get('/Author', '')
                metadata['subject'] = pdf.metadata.get('/Subject', '')
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")
        
        # Method 2: PyMuPDF for better text extraction
        try:
            pdf_document = fitz.open(stream=content, filetype="pdf")
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                text += page.get_text() + "\n"
                
                # Extract images and run OCR if needed
                image_list = page.get_images()
                if image_list and not text.strip():
                    # If no text extracted and images present, try OCR
                    for img_index, img in enumerate(image_list):
                        xref = img[0]
                        pix = fitz.Pixmap(pdf_document, xref)
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            img_data = pix.tobytes("png")
                            img = Image.open(io.BytesIO(img_data))
                            ocr_text = pytesseract.image_to_string(img)
                            text += ocr_text + "\n"
                        pix = None
            
            pdf_document.close()
        except Exception as e:
            print(f"PyMuPDF extraction failed: {e}")
        
        # Process extracted text
        sections = self.extract_sections(text)
        
        return {
            "text": text,
            "sections": sections,
            "metadata": metadata,
            "length": len(text),
            "word_count": len(text.split())
        }
    
    async def parse_docx(self, content: bytes) -> Dict[str, Any]:
        """
        Parse DOCX files
        """
        text = docx2txt.process(io.BytesIO(content))
        sections = self.extract_sections(text)
        
        return {
            "text": text,
            "sections": sections,
            "metadata": {},
            "length": len(text),
            "word_count": len(text.split())
        }
    
    async def parse_text(self, content: bytes) -> Dict[str, Any]:
        """
        Parse plain text files
        """
        text = content.decode('utf-8', errors='ignore')
        sections = self.extract_sections(text)
        
        return {
            "text": text,
            "sections": sections,
            "metadata": {},
            "length": len(text),
            "word_count": len(text.split())
        }
    
    def extract_sections(self, text: str) -> Dict[str, str]:
        """
        Extract sections from CV text
        """
        sections = {}
        lines = text.split('\n')
        current_section = 'header'
        section_content = []
        
        for line in lines:
            line_lower = line.strip().lower()
            
            # Check if line is a section header
            is_header = False
            for header in self.section_headers:
                if (line_lower.startswith(header) or 
                    line_lower.endswith(header) or
                    header == line_lower.replace(':', '').strip()):
                    
                    # Save previous section
                    if section_content:
                        sections[current_section] = '\n'.join(section_content)
                    
                    # Start new section
                    current_section = header.replace(' ', '_')
                    section_content = []
                    is_header = True
                    break
            
            if not is_header and line.strip():
                section_content.append(line)
        
        # Save last section
        if section_content:
            sections[current_section] = '\n'.join(section_content)
        
        return sections