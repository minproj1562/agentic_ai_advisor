# academic-advisor/academic-advisor-backend/app/services/cv_parser_v2.py
"""
AI-Powered CV Parser V6 - Handles ALL CV formats including tables, columns, mixed layouts

Features:
- Smart PDF extraction that handles multi-column and table layouts
- AI-powered parsing using OpenAI GPT
- Enhanced rule-based fallback
- Robust validation and cleaning

Version: 6.0
"""

import re
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
import pdfplumber
import io
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# ==================== Optional Dependencies ====================

OPENAI_AVAILABLE = False
openai_client = None

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
    logger.info("✅ OpenAI package available")
except ImportError:
    logger.warning("⚠️ OpenAI not installed. Run: pip install openai")

SPACY_AVAILABLE = False
nlp = None

try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
        SPACY_AVAILABLE = True
    except OSError:
        pass
except ImportError:
    pass


# ==================== CV Extraction Prompt ====================

CV_EXTRACTION_PROMPT = '''You are an expert CV/Resume parser. Extract information from this CV and return ONLY a valid JSON object.

CRITICAL INSTRUCTIONS:
1. Extract the ACTUAL data from the CV, not placeholder text
2. For experience years: Calculate from dates (e.g., "2018-Present" in 2025 = 7 years) OR extract directly if stated (e.g., "8 years of experience")
3. For research_areas: Extract TOPICS only (e.g., "Machine Learning", "NLP"), NOT sentences starting with verbs like "Developed..."
4. For teaching: Extract course/subject NAMES (e.g., "Artificial Intelligence", "Data Structures")
5. For current position: Use the MOST RECENT job title (e.g., "Assistant Professor", not dates or fragments)
6. If data is missing, use null or empty array, NOT placeholder text

Return this exact JSON structure:
{
    "personal_info": {
        "name": "Full name",
        "email": "email@domain.com",
        "phone": "phone number",
        "linkedin": "linkedin URL or null",
        "location": "city, country or null"
    },
    "education": [
        {
            "degree": "Ph.D./M.Tech/B.Tech etc",
            "field": "Field of study",
            "institution": "University name",
            "year": 2015,
            "details": "Any honors/thesis/GPA"
        }
    ],
    "experience": [
        {
            "title": "Job Title (e.g., Assistant Professor)",
            "organization": "Organization name",
            "start_year": 2018,
            "end_year": "Present or 2023",
            "is_current": true,
            "duration_years": 7,
            "responsibilities": ["key responsibility 1", "key responsibility 2"]
        }
    ],
    "total_experience_years": 8,
    "current_position": {
        "title": "Current job title",
        "organization": "Current organization"
    },
    "research_areas": ["Topic 1", "Topic 2", "Topic 3"],
    "skills": {
        "technical": ["Python", "TensorFlow", "etc"],
        "domains": ["AI/ML", "Data Science", "etc"]
    },
    "teaching": {
        "subjects": ["Subject 1", "Subject 2"],
        "courses_taught": ["Course 1", "Course 2"]
    },
    "publications_count": 0,
    "awards": ["Award 1", "Award 2"],
    "professional_summary": "1-2 sentence summary"
}

CV TEXT:
'''


# ==================== Smart PDF Extractor ====================

class SmartPDFExtractor:
    """
    Intelligent PDF text extraction that handles various layouts
    """
    
    @staticmethod
    async def extract(content: bytes) -> Tuple[str, str]:
        """
        Extract text using multiple strategies and return the best result
        Returns: (best_text, extraction_method)
        """
        strategies = []
        
        # Strategy 1: Default extraction
        try:
            text1 = await SmartPDFExtractor._extract_default(content)
            if text1:
                strategies.append(('default', text1, SmartPDFExtractor._score_text(text1)))
        except Exception as e:
            logger.warning(f"Default extraction failed: {e}")
        
        # Strategy 2: Extract with layout preservation
        try:
            text2 = await SmartPDFExtractor._extract_with_layout(content)
            if text2:
                strategies.append(('layout', text2, SmartPDFExtractor._score_text(text2)))
        except Exception as e:
            logger.warning(f"Layout extraction failed: {e}")
        
        # Strategy 3: Extract tables separately
        try:
            text3 = await SmartPDFExtractor._extract_with_tables(content)
            if text3:
                strategies.append(('tables', text3, SmartPDFExtractor._score_text(text3)))
        except Exception as e:
            logger.warning(f"Table extraction failed: {e}")
        
        # Choose best strategy based on score
        if not strategies:
            raise ValueError("Could not extract text from PDF using any strategy")
        
        # Sort by score and get best
        strategies.sort(key=lambda x: x[2], reverse=True)
        best = strategies[0]
        
        logger.info(f"📄 Using extraction strategy: {best[0]} (score: {best[2]})")
        return best[1], best[0]
    
    @staticmethod
    async def _extract_default(content: bytes) -> str:
        """Standard text extraction"""
        text_parts = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        return '\n'.join(text_parts)
    
    @staticmethod
    async def _extract_with_layout(content: bytes) -> str:
        """Extract with layout settings for multi-column"""
        text_parts = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                # Try to detect columns by analyzing character positions
                chars = page.chars
                if chars:
                    # Find the middle of the page
                    page_width = page.width
                    mid_x = page_width / 2
                    
                    # Check if there are significant chars on both sides
                    left_chars = [c for c in chars if c['x0'] < mid_x - 20]
                    right_chars = [c for c in chars if c['x0'] > mid_x + 20]
                    
                    if left_chars and right_chars:
                        # Likely two columns - extract left then right
                        left_bbox = (0, 0, mid_x - 10, page.height)
                        right_bbox = (mid_x + 10, 0, page_width, page.height)
                        
                        left_text = page.within_bbox(left_bbox).extract_text() or ''
                        right_text = page.within_bbox(right_bbox).extract_text() or ''
                        
                        text_parts.append(left_text)
                        text_parts.append(right_text)
                    else:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                else:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
        
        return '\n\n'.join(text_parts)
    
    @staticmethod
    async def _extract_with_tables(content: bytes) -> str:
        """Extract text and tables separately"""
        text_parts = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                # Extract regular text
                text = page.extract_text()
                if text:
                    text_parts.append(text)
                
                # Extract tables
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        if table:
                            for row in table:
                                if row:
                                    clean_row = ' | '.join(str(cell).strip() if cell else '' for cell in row)
                                    if clean_row.strip():
                                        text_parts.append(clean_row)
        
        return '\n'.join(text_parts)
    
    @staticmethod
    def _score_text(text: str) -> int:
        """Score extracted text quality"""
        score = 0
        
        # Length bonus
        score += min(len(text) // 100, 50)
        
        # Has email
        if re.search(r'\b[\w.-]+@[\w.-]+\.\w+\b', text):
            score += 20
        
        # Has phone
        if re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text):
            score += 10
        
        # Has years
        if re.search(r'\b(19|20)\d{2}\b', text):
            score += 15
        
        # Has common CV keywords
        keywords = ['experience', 'education', 'skills', 'professor', 'university', 'degree']
        for kw in keywords:
            if kw.lower() in text.lower():
                score += 5
        
        # Penalty for too many line breaks (indicates extraction issues)
        line_count = text.count('\n')
        if line_count > len(text) / 20:
            score -= 20
        
        return score


# ==================== AI Parser ====================

class AIParser:
    """AI-powered CV parser using OpenAI GPT"""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo-0125"  # Latest model with better JSON
    
    async def parse(self, text: str, filename: str) -> Dict[str, Any]:
        """Parse CV using OpenAI GPT"""
        try:
            # Truncate if needed
            max_chars = 12000
            if len(text) > max_chars:
                text = text[:max_chars] + "\n[...truncated...]"
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a CV parsing expert. Extract structured data from CVs. Return ONLY valid JSON, no markdown code blocks, no explanations."
                    },
                    {
                        "role": "user",
                        "content": CV_EXTRACTION_PROMPT + text
                    }
                ],
                temperature=0.1,
                max_tokens=3000,
                response_format={"type": "json_object"}  # Force JSON response
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean response
            content = re.sub(r'^```(?:json)?\n?', '', content)
            content = re.sub(r'\n?```$', '', content)
            
            parsed = json.loads(content)
            
            # Validate and clean
            parsed = self._validate_and_clean(parsed)
            
            logger.info(f"✅ AI parsing successful for {filename}")
            return {"success": True, "data": parsed, "method": "ai_gpt"}
            
        except Exception as e:
            logger.error(f"❌ AI parsing error: {e}")
            return {"success": False, "error": str(e)}
    
    def _validate_and_clean(self, data: Dict) -> Dict:
        """Validate and clean parsed data"""
        
        # Ensure required fields exist
        if 'personal_info' not in data:
            data['personal_info'] = {}
        
        if 'education' not in data:
            data['education'] = []
        elif not isinstance(data['education'], list):
            data['education'] = []
        
        if 'experience' not in data:
            data['experience'] = []
        elif not isinstance(data['experience'], list):
            data['experience'] = []
        
        # Clean current_position
        if 'current_position' in data:
            cp = data['current_position']
            if isinstance(cp, dict):
                title = cp.get('title', '')
                # Remove date fragments from title
                if title:
                    title = re.sub(r'\b\d{4}\b.*$', '', title).strip()
                    title = re.sub(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\b.*$', '', title, flags=re.IGNORECASE).strip()
                    title = title.rstrip(' -|')
                    cp['title'] = title
        
        # Calculate experience if not present
        if not data.get('total_experience_years'):
            data['total_experience_years'] = self._calc_experience(data.get('experience', []))
        
        # Ensure research_areas is a list of strings
        if 'research_areas' in data:
            areas = data['research_areas']
            if isinstance(areas, list):
                # Filter out action phrases
                clean_areas = []
                for area in areas:
                    if isinstance(area, str):
                        area = area.strip()
                        # Skip if starts with action verb
                        if not any(area.lower().startswith(v) for v in 
                                  ['developed', 'conducted', 'led', 'managed', 'created', 'designed', 'implemented']):
                            clean_areas.append(area)
                data['research_areas'] = clean_areas
        
        return data
    
    def _calc_experience(self, experience: List) -> int:
        """Calculate total experience from experience list"""
        total = 0
        current_year = datetime.now().year
        
        for exp in experience:
            if not isinstance(exp, dict):
                continue
            
            # Try duration_years first
            if exp.get('duration_years'):
                try:
                    total += int(exp['duration_years'])
                    continue
                except:
                    pass
            
            # Calculate from dates
            start = exp.get('start_year')
            end = exp.get('end_year')
            
            if start:
                try:
                    start_year = int(start) if isinstance(start, (int, str)) and str(start).isdigit() else None
                    if start_year:
                        if end in ['Present', 'present', 'Current', 'current', None] or exp.get('is_current'):
                            end_year = current_year
                        else:
                            end_year = int(end) if str(end).isdigit() else current_year
                        
                        years = end_year - start_year
                        if 0 < years < 50:
                            total += years
                except:
                    pass
        
        return total


# ==================== Enhanced Rule-Based Parser ====================

class RuleBasedParser:
    """Enhanced rule-based CV parser for when AI is unavailable"""
    
    def __init__(self):
        self.nlp = nlp if SPACY_AVAILABLE else None
    
    async def parse(self, text: str, filename: str) -> Dict[str, Any]:
        """Parse CV using pattern matching"""
        try:
            data = {
                'personal_info': self._extract_personal_info(text),
                'education': self._extract_education(text),
                'experience': self._extract_experience(text),
                'current_position': {},
                'total_experience_years': 0,
                'research_areas': self._extract_research_areas(text),
                'skills': self._extract_skills(text),
                'teaching': self._extract_teaching(text),
                'publications_count': 0,
                'awards': [],
                'professional_summary': self._extract_summary(text)
            }
            
            # Set current position from experience
            if data['experience']:
                for exp in data['experience']:
                    if exp.get('is_current'):
                        data['current_position'] = {
                            'title': exp.get('title', ''),
                            'organization': exp.get('organization', '')
                        }
                        break
                if not data['current_position'] and data['experience']:
                    data['current_position'] = {
                        'title': data['experience'][0].get('title', ''),
                        'organization': data['experience'][0].get('organization', '')
                    }
            
            # Calculate experience
            data['total_experience_years'] = self._calc_total_experience(text, data['experience'])
            
            return {"success": True, "data": data, "method": "rule_based"}
            
        except Exception as e:
            logger.error(f"Rule-based parsing error: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_personal_info(self, text: str) -> Dict:
        """Extract personal information"""
        info = {}
        
        # Name - first significant line
        lines = text.split('\n')
        for line in lines[:15]:
            line = line.strip()
            if line and 3 < len(line) < 50:
                # Check if looks like a name
                if not any(c.isdigit() for c in line):
                    if not any(skip in line.lower() for skip in ['curriculum', 'vitae', 'resume', 'cv', '@', 'http', 'phone', 'email', 'address']):
                        # Check for typical name pattern (2-4 capitalized words)
                        words = line.split()
                        if 1 <= len(words) <= 5:
                            if sum(1 for w in words if w[0].isupper()) >= len(words) * 0.5:
                                info['name'] = line
                                break
        
        # Email
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if emails:
            info['email'] = emails[0]
        
        # Phone - improved pattern
        phone_patterns = [
            r'\+?91[-\s]?\d{5}[-\s]?\d{5}',  # Indian format
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',   # (123) 456-7890
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # 123-456-7890
        ]
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                info['phone'] = matches[0]
                break
        
        # LinkedIn
        linkedin = re.search(r'linkedin\.com/in/[\w-]+', text, re.IGNORECASE)
        if linkedin:
            info['linkedin'] = linkedin.group()
        
        return info
    
    def _extract_education(self, text: str) -> List[Dict]:
        """Extract education information"""
        education = []
        
        # Degree patterns with capturing groups
        degree_patterns = [
            (r'Ph\.?D\.?\s*(?:in\s+)?([A-Za-z\s]+?)(?:\s+from|\s+at|\s*,|\s*\d|$)', 'Ph.D.', 4),
            (r'M\.?Tech\.?\s*(?:in\s+)?([A-Za-z\s]+?)(?:\s+from|\s+at|\s*,|\s*\d|$)', 'M.Tech', 3),
            (r'M\.?S\.?c?\.?\s*(?:in\s+)?([A-Za-z\s]+?)(?:\s+from|\s+at|\s*,|\s*\d|$)', 'M.Sc.', 3),
            (r'M\.?B\.?A\.?', 'MBA', 3),
            (r'B\.?Tech\.?\s*(?:in\s+)?([A-Za-z\s]+?)(?:\s+from|\s+at|\s*,|\s*\d|$)', 'B.Tech', 2),
            (r'B\.?S\.?c?\.?\s*(?:in\s+)?([A-Za-z\s]+?)(?:\s+from|\s+at|\s*,|\s*\d|$)', 'B.Sc.', 2),
        ]
        
        text_lower = text.lower()
        
        for pattern, degree_name, rank in degree_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # Find context around the degree mention
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    context_start = max(0, match.start() - 100)
                    context_end = min(len(text), match.end() + 200)
                    context = text[context_start:context_end]
                    
                    # Extract field
                    field = ""
                    if match.groups():
                        field = match.group(1).strip() if match.group(1) else ""
                        # Clean field
                        field = re.sub(r'\s+', ' ', field).strip()
                        if len(field) > 50:
                            field = field[:50]
                    
                    # Extract institution
                    institution = ""
                    inst_patterns = [
                        r'((?:University|Institute|College|School|NIT|IIT|VIT)[^,\n]{0,50})',
                        r'([A-Z][a-zA-Z\s]+(?:University|Institute|College))'
                    ]
                    for ip in inst_patterns:
                        inst_match = re.search(ip, context)
                        if inst_match:
                            institution = inst_match.group(1).strip()
                            break
                    
                    # Extract year
                    year = None
                    years = re.findall(r'(20\d{2}|19\d{2})', context)
                    if years:
                        year = int(years[-1])
                    
                    edu_entry = {
                        'degree': degree_name,
                        'field': field,
                        'institution': institution,
                        'year': year,
                        'rank': rank
                    }
                    
                    # Avoid duplicates
                    if not any(e.get('degree') == degree_name and e.get('institution') == institution for e in education):
                        education.append(edu_entry)
        
        # Sort by rank
        education.sort(key=lambda x: x.get('rank', 0), reverse=True)
        
        # Remove rank from output
        for edu in education:
            edu.pop('rank', None)
        
        return education
    
    def _extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience"""
        experience = []
        
        # Common job titles
        title_patterns = [
            r'(Assistant\s+Professor[^,\n]*)',
            r'(Associate\s+Professor[^,\n]*)',
            r'(Professor[^,\n]*)',
            r'(Lecturer[^,\n]*)',
            r'(Research\s+(?:Assistant|Associate|Fellow)[^,\n]*)',
            r'(Software\s+(?:Developer|Engineer)[^,\n]*)',
            r'(Senior\s+(?:Developer|Engineer|Consultant)[^,\n]*)',
            r'((?:AI|ML)\s+(?:Engineer|Consultant)[^,\n]*)',
            r'(Data\s+(?:Scientist|Engineer)[^,\n]*)',
        ]
        
        # Date patterns
        date_pattern = r'(\d{4})\s*[-–—]\s*(Present|Current|\d{4})'
        
        for pattern in title_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                title = match.group(1).strip()
                
                # Clean title
                title = re.sub(r'\s*\([^)]*\)', '', title)  # Remove parenthetical
                title = re.sub(r'\s*[-–—].*$', '', title)  # Remove trailing dash content
                title = title.strip()
                
                if len(title) < 5 or len(title) > 60:
                    continue
                
                # Look for dates nearby
                context_start = max(0, match.start() - 50)
                context_end = min(len(text), match.end() + 150)
                context = text[context_start:context_end]
                
                date_match = re.search(date_pattern, context)
                start_year = None
                end_year = None
                is_current = False
                
                if date_match:
                    start_year = int(date_match.group(1))
                    end = date_match.group(2)
                    if end in ['Present', 'Current']:
                        end_year = 'Present'
                        is_current = True
                    else:
                        end_year = int(end)
                
                # Look for organization
                org = ""
                org_patterns = [
                    r'(?:at|from)\s+([A-Z][A-Za-z\s]+(?:University|Institute|College|Inc|Ltd|Corp|Company))',
                    r'([A-Z][A-Za-z\s]+(?:University|Institute|College))'
                ]
                for op in org_patterns:
                    org_match = re.search(op, context)
                    if org_match:
                        org = org_match.group(1).strip()
                        break
                
                exp_entry = {
                    'title': title,
                    'organization': org,
                    'start_year': start_year,
                    'end_year': end_year,
                    'is_current': is_current
                }
                
                # Avoid duplicates
                if not any(e.get('title') == title for e in experience):
                    experience.append(exp_entry)
        
        # Sort by current first, then by start_year
        experience.sort(key=lambda x: (not x.get('is_current', False), -(x.get('start_year') or 0)))
        
        return experience
    
    def _calc_total_experience(self, text: str, experience: List) -> int:
        """Calculate total experience - check both explicit mentions and dates"""
        total = 0
        
        # First, look for explicit "X years of experience" mentions
        explicit_patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            r'over\s+(\d+)\s*years?',
            r'(\d+)\s*years?\s+in\s+(?:academia|industry|teaching)',
        ]
        
        for pattern in explicit_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    years = int(match.group(1))
                    if 1 <= years <= 50:
                        return years
                except:
                    pass
        
        # Calculate from experience entries
        current_year = datetime.now().year
        for exp in experience:
            start = exp.get('start_year')
            end = exp.get('end_year')
            
            if start:
                try:
                    start_year = int(start)
                    if end == 'Present' or exp.get('is_current'):
                        end_year = current_year
                    elif isinstance(end, int):
                        end_year = end
                    elif isinstance(end, str) and end.isdigit():
                        end_year = int(end)
                    else:
                        continue
                    
                    years = end_year - start_year
                    if 0 < years < 50:
                        total += years
                except:
                    pass
        
        return total
    
    def _extract_research_areas(self, text: str) -> List[str]:
        """Extract research areas"""
        areas = []
        
        # Known research areas
        known_areas = [
            'machine learning', 'artificial intelligence', 'deep learning',
            'natural language processing', 'nlp', 'computer vision',
            'data science', 'data mining', 'big data', 'data analytics',
            'cloud computing', 'cybersecurity', 'ethical ai', 'ai ethics',
            'reinforcement learning', 'neural networks', 'robotics',
            'internet of things', 'iot', 'blockchain', 'distributed systems',
            'software engineering', 'information technology', 'it security',
            'image processing', 'speech recognition', 'autonomous systems',
            'multimodal learning', 'few-shot learning', 'transfer learning'
        ]
        
        text_lower = text.lower()
        
        for area in known_areas:
            if area in text_lower:
                # Capitalize properly
                display = area.upper() if area in ['nlp', 'ai', 'iot', 'it'] else area.title()
                if display not in areas:
                    areas.append(display)
        
        return areas[:10]
    
    def _extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extract skills"""
        skills = {'technical': [], 'domains': []}
        
        # Technical skills
        tech_skills = ['python', 'java', 'javascript', 'c++', 'sql', 'r', 'matlab',
                      'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy',
                      'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'git']
        
        text_lower = text.lower()
        
        for skill in tech_skills:
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                display = skill.upper() if skill in ['sql', 'r', 'aws', 'gcp', 'git'] else skill.title()
                if skill == 'c++':
                    display = 'C++'
                skills['technical'].append(display)
        
        return skills
    
    def _extract_teaching(self, text: str) -> Dict[str, List[str]]:
        """Extract teaching information"""
        teaching = {'subjects': [], 'courses_taught': []}
        
        # Look for course mentions
        patterns = [
            r'(?:teaching|taught|courses? in)\s+([^,\.\n]+(?:,\s*[^,\.\n]+)*)',
            r'(?:subjects?|courses?):\s*([^,\.\n]+(?:,\s*[^,\.\n]+)*)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                courses_text = match.group(1)
                # Split on common separators
                courses = re.split(r'\s+and\s+|\s*,\s*|\s*&\s*', courses_text)
                for course in courses:
                    course = course.strip()
                    if 2 < len(course) < 50:
                        # Expand abbreviations
                        expansions = {
                            'AI': 'Artificial Intelligence',
                            'ML': 'Machine Learning',
                            'NLP': 'Natural Language Processing',
                            'AI/ML': 'AI and Machine Learning'
                        }
                        course = expansions.get(course.upper(), course)
                        if course not in teaching['subjects']:
                            teaching['subjects'].append(course)
        
        return teaching
    
    def _extract_summary(self, text: str) -> str:
        """Extract professional summary"""
        # Look for summary section
        patterns = [
            r'(?:professional\s+)?summary[:\s]+([^\n]+(?:\n[^\n]+){0,2})',
            r'(?:objective|profile)[:\s]+([^\n]+(?:\n[^\n]+){0,2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                summary = match.group(1).strip()
                # Clean up
                summary = re.sub(r'\s+', ' ', summary)
                if len(summary) > 300:
                    summary = summary[:300] + '...'
                return summary
        
        return ""


# ==================== Main Parser ====================

class AcademicCVParser:
    """Main CV Parser orchestrating AI and rule-based parsing"""
    
    def __init__(self):
        self.ai_parser = None
        self.rule_parser = RuleBasedParser()
        self._init_ai_parser()
    
    def _init_ai_parser(self):
        """Initialize AI parser"""
        try:
            from app.config import settings
            if OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
                self.ai_parser = AIParser(settings.OPENAI_API_KEY)
                logger.info("✅ AI Parser initialized")
            else:
                logger.warning("⚠️ AI Parser not available")
        except Exception as e:
            logger.error(f"AI parser init error: {e}")
    
    async def parse(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Main parsing method"""
        logger.info(f"📄 Parsing CV: {filename}")
        
        # Step 1: Smart text extraction
        text, extraction_method = await SmartPDFExtractor.extract(file_content)
        
        if not text or len(text.strip()) < 50:
            raise ValueError("Could not extract sufficient text from CV")
        
        logger.info(f"📝 Extracted {len(text)} chars using {extraction_method}")
        
        # Step 2: Try AI parsing
        parse_result = None
        if self.ai_parser:
            logger.info("🤖 Trying AI parsing...")
            ai_result = await self.ai_parser.parse(text, filename)
            if ai_result.get('success'):
                parse_result = ai_result
        
        # Step 3: Fallback to rule-based
        if not parse_result or not parse_result.get('success'):
            logger.info("📋 Using rule-based parsing...")
            parse_result = await self.rule_parser.parse(text, filename)
        
        # Step 4: Build result
        parsed_data = parse_result.get('data', {})
        suggested_profile = self._build_suggested_profile(parsed_data)
        quality_score = self._calculate_quality_score(parsed_data)
        
        return {
            'text': text,
            'personal_info': parsed_data.get('personal_info', {}),
            'education': parsed_data.get('education', []),
            'experience': parsed_data.get('experience', []),
            'research_interests': parsed_data.get('research_areas', []),
            'skills': parsed_data.get('skills', {}),
            'publications': parsed_data.get('publications', []),
            'teaching': parsed_data.get('teaching', {}),
            'total_experience_years': parsed_data.get('total_experience_years', 0),
            'suggested_profile': suggested_profile,
            'metadata': {
                'filename': filename,
                'parsed_at': datetime.utcnow().isoformat(),
                'parser_method': parse_result.get('method', 'unknown'),
                'extraction_method': extraction_method,
                'quality_score': quality_score,
                'parser_version': 'v6-ai-powered'
            },
            'word_count': len(text.split()),
            'quality_score': quality_score,
            'extraction_success': True
        }
    
    def _build_suggested_profile(self, data: Dict) -> Dict:
        """Build suggested profile structure"""
        education = data.get('education', [])
        highest = education[0] if education else {}
        
        experience = data.get('experience', [])
        current = data.get('current_position', {})
        if not current and experience:
            for exp in experience:
                if exp.get('is_current'):
                    current = {'title': exp.get('title', ''), 'organization': exp.get('organization', '')}
                    break
            if not current:
                current = {'title': experience[0].get('title', ''), 'organization': experience[0].get('organization', '')}
        
        research = data.get('research_areas', [])
        skills = data.get('skills', {})
        all_skills = []
        if isinstance(skills, dict):
            for v in skills.values():
                if isinstance(v, list):
                    all_skills.extend(v)
        
        teaching = data.get('teaching', {})
        all_subjects = []
        if isinstance(teaching, dict):
            for v in teaching.values():
                if isinstance(v, list):
                    all_subjects.extend(v)
        
        return {
            'personal_info': data.get('personal_info', {}),
            'academic_qualifications': {
                'highest_degree': highest.get('degree', 'Unknown'),
                'specialization': highest.get('field', ''),
                'university': highest.get('institution', ''),
                'graduation_year': highest.get('year'),
                'all_degrees': education
            },
            'current_position': {
                'designation': current.get('title', 'Faculty'),
                'institution': current.get('organization', ''),
                'department': '',
                'years_of_experience': data.get('total_experience_years', 0)
            },
            'research_expertise': {
                'primary_areas': research[:5],
                'secondary_interests': research[5:10],
                'keywords': all_skills[:20]
            },
            'teaching': {
                'current_subjects': list(set(all_subjects))[:10],
                'courses': teaching.get('courses_taught', [])
            },
            'publications': {
                'total_count': data.get('publications_count', 0),
                'notable_works': []
            },
            'skills': skills,
            'availability': {'office_location': '', 'office_hours': ''},
            'others': {'awards': data.get('awards', [])}
        }
    
    def _calculate_quality_score(self, data: Dict) -> float:
        """Calculate quality score"""
        score = 0
        
        pi = data.get('personal_info', {})
        if pi.get('name'): score += 15
        if pi.get('email'): score += 10
        
        if data.get('education'): score += 20
        if data.get('experience'): score += 20
        if data.get('research_areas'): score += 15
        if data.get('skills'): score += 10
        if data.get('teaching'): score += 10
        
        return min(100, score)


# ==================== Exports ====================

enhanced_cv_parser = AcademicCVParser()
cv_parser_v2 = enhanced_cv_parser
CVParserV2 = AcademicCVParser
EnhancedCVParser = AcademicCVParser

async def parse_cv_file(file_content: bytes, filename: str) -> Dict[str, Any]:
    return await enhanced_cv_parser.parse(file_content, filename)

__all__ = [
    'AcademicCVParser', 'EnhancedCVParser', 'enhanced_cv_parser',
    'cv_parser_v2', 'CVParserV2', 'parse_cv_file',
    'AIParser', 'RuleBasedParser', 'SmartPDFExtractor'
]