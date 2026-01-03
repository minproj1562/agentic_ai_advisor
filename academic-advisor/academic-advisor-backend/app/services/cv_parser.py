#academic-advisor-backend/app/services/cv_parser.py
import io
import re
import logging
from typing import Dict, Any, List, Optional
from PyPDF2 import PdfReader
import docx2txt
from PIL import Image
import asyncio

# Configure logging
logger = logging.getLogger(__name__)

class CVParser:
    def __init__(self):
        self.section_headers = [
            'education', 'experience', 'skills', 'projects',
            'certifications', 'publications', 'summary', 'objective',
            'work experience', 'professional experience', 'employment',
            'academic background', 'technical skills', 'achievements',
            'work history', 'professional background', 'employment history',
            'academic qualifications', 'educational background'
        ]
        
        # Try to import optional dependencies
        self.has_pymupdf = False
        self.has_tesseract = False
        
        try:
            import fitz
            self.fitz = fitz
            self.has_pymupdf = True
            logger.info("PyMuPDF (fitz) available for PDF parsing")
        except ImportError:
            logger.warning("PyMuPDF not available, using fallback PDF parsing")
        
        try:
            import pytesseract
            self.pytesseract = pytesseract
            self.has_tesseract = True
            logger.info("Tesseract available for OCR")
        except ImportError:
            logger.warning("Tesseract not available, OCR disabled")
    
    async def parse(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Parse CV from various formats with comprehensive error handling
        """
        try:
            file_extension = filename.split('.')[-1].lower()
            
            if file_extension == 'pdf':
                return await self.parse_pdf_advanced(file_content)
            elif file_extension in ['doc', 'docx']:
                return await self.parse_docx(file_content)
            elif file_extension in ['txt']:
                return await self.parse_text(file_content)
            elif file_extension in ['jpg', 'jpeg', 'png']:
                return await self.parse_image(file_content)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
                
        except Exception as e:
            logger.error(f"Error parsing CV file {filename}: {str(e)}")
            raise
    
    async def parse_pdf_advanced(self, content: bytes) -> Dict[str, Any]:
        """
        Advanced PDF parsing with multiple fallback methods
        """
        text = ""
        metadata = {}
        extraction_methods = []
        
        # Method 1: Try PyMuPDF first (most accurate)
        if self.has_pymupdf:
            try:
                pdf_text, pdf_metadata = await self._parse_with_pymupdf(content)
                text = pdf_text
                metadata.update(pdf_metadata)
                extraction_methods.append("pymupdf")
                logger.info("Successfully extracted text using PyMuPDF")
            except Exception as e:
                logger.warning(f"PyMuPDF extraction failed: {e}")
        
        # Method 2: Fallback to PyPDF2 if PyMuPDF failed or didn't extract much text
        if not text or len(text.strip()) < 100:
            try:
                pdf_text, pdf_metadata = await self._parse_with_pypdf2(content)
                if len(pdf_text) > len(text):
                    text = pdf_text
                    metadata.update(pdf_metadata)
                extraction_methods.append("pypdf2")
                logger.info("Successfully extracted text using PyPDF2")
            except Exception as e:
                logger.warning(f"PyPDF2 extraction failed: {e}")
        
        # Method 3: If still no text, try OCR (for scanned PDFs)
        if self.has_tesseract and (not text or len(text.strip()) < 50):
            try:
                ocr_text = await self._parse_with_ocr(content)
                if ocr_text and len(ocr_text) > len(text):
                    text = ocr_text
                    extraction_methods.append("ocr")
                    logger.info("Successfully extracted text using OCR")
            except Exception as e:
                logger.warning(f"OCR extraction failed: {e}")
        
        # Process extracted text
        sections = self.extract_sections(text)
        entities = await self.extract_entities(text)
        
        return {
            "text": text,
            "sections": sections,
            "entities": entities,
            "metadata": metadata,
            "extraction_methods": extraction_methods,
            "length": len(text),
            "word_count": len(text.split()),
            "character_count": len(text.replace(" ", "")),
            "extraction_success": len(text.strip()) > 0
        }
    
    async def _parse_with_pymupdf(self, content: bytes) -> tuple[str, Dict[str, Any]]:
        """Parse PDF using PyMuPDF"""
        text = ""
        metadata = {}
        
        try:
            pdf_document = self.fitz.open(stream=content, filetype="pdf")
            metadata['pages'] = pdf_document.page_count
            metadata['encrypted'] = pdf_document.is_encrypted
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                page_text = page.get_text()
                text += page_text + "\n"
                
                # Extract images and run OCR if text is minimal (scanned PDF)
                if len(page_text.strip()) < 50 and self.has_tesseract:
                    image_list = page.get_images()
                    for img_index, img in enumerate(image_list):
                        try:
                            xref = img[0]
                            pix = self.fitz.Pixmap(pdf_document, xref)
                            if pix.n - pix.alpha < 4:  # GRAY or RGB
                                img_data = pix.tobytes("png")
                                ocr_text = await self._ocr_image(img_data)
                                text += ocr_text + "\n"
                            pix = None
                        except Exception as e:
                            logger.warning(f"OCR on page image failed: {e}")
                            continue
            
            # Extract document metadata
            doc_metadata = pdf_document.metadata
            if doc_metadata:
                metadata.update({
                    'title': doc_metadata.get('title', ''),
                    'author': doc_metadata.get('author', ''),
                    'subject': doc_metadata.get('subject', ''),
                    'keywords': doc_metadata.get('keywords', ''),
                    'creator': doc_metadata.get('creator', ''),
                    'producer': doc_metadata.get('producer', ''),
                    'creation_date': doc_metadata.get('creationDate', ''),
                    'modification_date': doc_metadata.get('modDate', '')
                })
            
            pdf_document.close()
            
        except Exception as e:
            logger.error(f"PyMuPDF parsing error: {e}")
            raise
        
        return text, metadata
    
    async def _parse_with_pypdf2(self, content: bytes) -> tuple[str, Dict[str, Any]]:
        """Parse PDF using PyPDF2 as fallback"""
        text = ""
        metadata = {}
        
        try:
            pdf = PdfReader(io.BytesIO(content))
            metadata['pages'] = len(pdf.pages)
            metadata['encrypted'] = pdf.is_encrypted
            
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            # Extract metadata
            if pdf.metadata:
                meta = pdf.metadata
                metadata.update({
                    'title': getattr(meta, 'title', ''),
                    'author': getattr(meta, 'author', ''),
                    'subject': getattr(meta, 'subject', ''),
                    'creator': getattr(meta, 'creator', ''),
                    'producer': getattr(meta, 'producer', ''),
                })
                
        except Exception as e:
            logger.error(f"PyPDF2 parsing error: {e}")
            raise
        
        return text, metadata
    
    async def _parse_with_ocr(self, content: bytes) -> str:
        """Extract text using OCR for scanned PDFs"""
        text = ""
        
        if not self.has_pymupdf or not self.has_tesseract:
            return text
        
        try:
            pdf_document = self.fitz.open(stream=content, filetype="pdf")
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                
                # Convert page to image
                pix = page.get_pixmap(matrix=self.fitz.Matrix(2, 2))  # Higher resolution
                img_data = pix.tobytes("png")
                
                # Perform OCR
                page_text = await self._ocr_image(img_data)
                text += page_text + "\n"
                
                pix = None
            
            pdf_document.close()
            
        except Exception as e:
            logger.error(f"OCR parsing error: {e}")
        
        return text
    
    async def _ocr_image(self, image_data: bytes) -> str:
        """Perform OCR on image data"""
        try:
            image = Image.open(io.BytesIO(image_data))
            text = self.pytesseract.image_to_string(image)
            return text
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return ""
    
    async def parse_docx(self, content: bytes) -> Dict[str, Any]:
        """Parse DOCX files"""
        try:
            text = docx2txt.process(io.BytesIO(content))
            sections = self.extract_sections(text)
            entities = await self.extract_entities(text)
            
            return {
                "text": text,
                "sections": sections,
                "entities": entities,
                "metadata": {"format": "docx"},
                "length": len(text),
                "word_count": len(text.split()),
                "character_count": len(text.replace(" ", "")),
                "extraction_success": True
            }
        except Exception as e:
            logger.error(f"DOCX parsing error: {e}")
            raise
    
    async def parse_text(self, content: bytes) -> Dict[str, Any]:
        """Parse plain text files"""
        try:
            text = content.decode('utf-8', errors='ignore')
            sections = self.extract_sections(text)
            entities = await self.extract_entities(text)
            
            return {
                "text": text,
                "sections": sections,
                "entities": entities,
                "metadata": {"format": "text"},
                "length": len(text),
                "word_count": len(text.split()),
                "character_count": len(text.replace(" ", "")),
                "extraction_success": True
            }
        except Exception as e:
            logger.error(f"Text parsing error: {e}")
            raise
    
    async def parse_image(self, content: bytes) -> Dict[str, Any]:
        """Parse image files using OCR"""
        if not self.has_tesseract:
            raise ValueError("Tesseract OCR not available for image parsing")
        
        try:
            text = await self._ocr_image(content)
            sections = self.extract_sections(text)
            entities = await self.extract_entities(text)
            
            return {
                "text": text,
                "sections": sections,
                "entities": entities,
                "metadata": {"format": "image", "ocr_used": True},
                "length": len(text),
                "word_count": len(text.split()),
                "character_count": len(text.replace(" ", "")),
                "extraction_success": len(text.strip()) > 0
            }
        except Exception as e:
            logger.error(f"Image parsing error: {e}")
            raise
    
    def extract_sections(self, text: str) -> Dict[str, str]:
        """
        Extract structured sections from CV text using advanced pattern matching
        """
        sections = {}
        lines = text.split('\n')
        current_section = 'personal_info'
        section_content = []
        
        # Enhanced header patterns
        header_patterns = [
            (re.compile(r'^\s*(education|educational background|academic background|academic qualifications)\s*:?\s*$', re.IGNORECASE), 'education'),
            (re.compile(r'^\s*(experience|work experience|professional experience|employment history|work history)\s*:?\s*$', re.IGNORECASE), 'experience'),
            (re.compile(r'^\s*(skills|technical skills|key skills|competencies)\s*:?\s*$', re.IGNORECASE), 'skills'),
            (re.compile(r'^\s*(projects|personal projects|academic projects)\s*:?\s*$', re.IGNORECASE), 'projects'),
            (re.compile(r'^\s*(certifications|certificates|licenses)\s*:?\s*$', re.IGNORECASE), 'certifications'),
            (re.compile(r'^\s*(publications|papers|research papers)\s*:?\s*$', re.IGNORECASE), 'publications'),
            (re.compile(r'^\s*(summary|professional summary|career objective|objective)\s*:?\s*$', re.IGNORECASE), 'summary'),
            (re.compile(r'^\s*(achievements|awards|honors)\s*:?\s*$', re.IGNORECASE), 'achievements'),
            (re.compile(r'^\s*(languages|language skills)\s*:?\s*$', re.IGNORECASE), 'languages'),
            (re.compile(r'^\s*(interests|hobbies|personal interests)\s*:?\s*$', re.IGNORECASE), 'interests'),
        ]
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
                
            # Check if line matches any section header pattern
            found_header = False
            for pattern, section_name in header_patterns:
                if pattern.match(line_stripped):
                    # Save current section
                    if section_content:
                        sections[current_section] = '\n'.join(section_content).strip()
                    
                    # Start new section
                    current_section = section_name
                    section_content = []
                    found_header = True
                    break
            
            if not found_header:
                section_content.append(line_stripped)
        
        # Save the final section
        if section_content:
            sections[current_section] = '\n'.join(section_content).strip()
        
        return sections
    
    async def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract key entities from CV text (email, phone, education, etc.)
        """
        entities = {
            'emails': [],
            'phones': [],
            'urls': [],
            'education_keywords': [],
            'skill_keywords': [],
            'companies': [],
            'job_titles': []
        }
        
        # Email extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities['emails'] = re.findall(email_pattern, text)
        
        # Phone number extraction (international format)
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        entities['phones'] = re.findall(phone_pattern, text)
        
        # URL extraction
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*\??[/\w\.-=&%]*'
        entities['urls'] = re.findall(url_pattern, text)
        
        # Education keywords
        education_terms = [
            'bachelor', 'master', 'phd', 'doctorate', 'mba', 'msc', 'bsc', 'ba', 'ma',
            'university', 'college', 'institute', 'school', 'faculty', 'degree',
            'diploma', 'certificate', 'graduated', 'alumni'
        ]
        entities['education_keywords'] = [term for term in education_terms if term in text.lower()]
        
        return entities
    
    def calculate_parsing_quality_score(self, parsed_data: Dict[str, Any]) -> float:
        """
        Calculate a quality score for the parsing result (0-100)
        """
        score = 0
        
        # Text length factor
        text_length = parsed_data.get('length', 0)
        if text_length > 1000:
            score += 30
        elif text_length > 500:
            score += 20
        elif text_length > 100:
            score += 10
        
        # Section coverage factor
        sections = parsed_data.get('sections', {})
        section_count = len(sections)
        if section_count >= 5:
            score += 30
        elif section_count >= 3:
            score += 20
        elif section_count >= 1:
            score += 10
        
        # Entity extraction factor
        entities = parsed_data.get('entities', {})
        entity_score = min(20, len(entities.get('emails', [])) * 5 + 
                          len(entities.get('phones', [])) * 3 +
                          len(entities.get('education_keywords', [])) * 2)
        score += entity_score
        
        # Extraction method bonus
        methods = parsed_data.get('extraction_methods', [])
        if 'pymupdf' in methods:
            score += 10
        if 'ocr' in methods and text_length > 100:
            score += 10
        
        return min(100, score)

# Singleton instance
cv_parser_instance = CVParser()