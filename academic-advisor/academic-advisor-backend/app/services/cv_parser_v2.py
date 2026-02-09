# academic-advisor/academic-advisor-backend/app/services/cv_parser_v2.py
"""
AI-Powered CV Parser V8 - With Free AI Alternatives
Supports: OpenAI, Groq (FREE), Google Gemini, and Enhanced Rule-Based Fallback

Version: 8.0
"""

import re
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
import pdfplumber
import io
from datetime import datetime
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

# ==================== Configuration ====================

# Try to import AI clients
OPENAI_AVAILABLE = False
GROQ_AVAILABLE = False

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    pass

# Groq uses OpenAI-compatible API
try:
    import httpx
    GROQ_AVAILABLE = True
except ImportError:
    pass


# ==================== Constants ====================

VALID_DEGREES = {
    'phd': 'Ph.D.', 'ph.d': 'Ph.D.', 'ph.d.': 'Ph.D.', 'doctor': 'Ph.D.', 'doctorate': 'Ph.D.',
    'mtech': 'M.Tech', 'm.tech': 'M.Tech', 'm.tech.': 'M.Tech',
    'msc': 'M.Sc.', 'm.sc': 'M.Sc.', 'm.sc.': 'M.Sc.', 'ms': 'M.S.', 'm.s': 'M.S.',
    'master': "Master's", 'masters': "Master's", 'mba': 'MBA',
    'me': 'M.E.', 'm.e': 'M.E.', 'mca': 'MCA',
    'btech': 'B.Tech', 'b.tech': 'B.Tech', 'b.tech.': 'B.Tech',
    'bsc': 'B.Sc.', 'b.sc': 'B.Sc.', 'bs': 'B.S.', 'b.s': 'B.S.',
    'bachelor': "Bachelor's", 'bachelors': "Bachelor's",
    'be': 'B.E.', 'b.e': 'B.E.', 'bca': 'BCA', 'ba': 'B.A.',
}

DEGREE_RANKS = {
    'Ph.D.': 5, "Master's": 4, 'M.Tech': 4, 'M.S.': 4, 'M.Sc.': 4, 'MBA': 4, 'M.E.': 4,
    "Bachelor's": 3, 'B.Tech': 3, 'B.S.': 3, 'B.Sc.': 3, 'B.E.': 3, 'BCA': 3,
}

ACADEMIC_TITLES = [
    'professor', 'associate professor', 'assistant professor', 'asst professor',
    'lecturer', 'senior lecturer', 'reader', 'fellow', 'research fellow',
    'postdoctoral', 'postdoc', 'instructor', 'adjunct', 'visiting professor',
    'dean', 'head of department', 'hod', 'director', 'principal',
    'researcher', 'research associate', 'research assistant', 'scientist',
]

INDUSTRY_TITLES = [
    'software engineer', 'software developer', 'senior developer', 'lead developer',
    'data scientist', 'data engineer', 'ml engineer', 'ai engineer', 'deep learning engineer',
    'technical lead', 'tech lead', 'team lead', 'project manager', 'engineering manager',
    'consultant', 'senior consultant', 'principal consultant', 'architect',
    'analyst', 'senior analyst', 'manager', 'senior manager', 'director', 'vp', 'cto',
]

RESEARCH_KEYWORDS = [
    'machine learning', 'artificial intelligence', 'deep learning', 'neural networks',
    'natural language processing', 'nlp', 'computer vision', 'image processing',
    'data science', 'data mining', 'data analytics', 'big data', 'data engineering',
    'cloud computing', 'distributed systems', 'parallel computing', 'edge computing',
    'cybersecurity', 'information security', 'network security', 'cryptography',
    'software engineering', 'software development', 'devops', 'mlops',
    'database', 'information retrieval', 'knowledge graphs',
    'robotics', 'automation', 'control systems', 'embedded systems',
    'internet of things', 'iot', 'blockchain', 'web development',
    'reinforcement learning', 'transfer learning', 'federated learning',
    'ethical ai', 'responsible ai', 'fairness in ml', 'explainable ai', 'xai',
    'autonomous systems', 'computer graphics', 'virtual reality', 'augmented reality',
    'bioinformatics', 'healthcare ai', 'medical imaging', 'recommendation systems',
    'speech recognition', 'signal processing', 'optimization', 'algorithms',
]

INSTITUTION_KEYWORDS = [
    'university', 'institute', 'college', 'school', 'academy',
    'iit', 'nit', 'iiit', 'bits', 'vit', 'srm', 'manipal',
    'mit', 'stanford', 'harvard', 'oxford', 'cambridge', 'berkeley', 'caltech',
    'carnegie mellon', 'georgia tech', 'princeton', 'cornell', 'yale',
]


# ==================== AI Prompt ====================

AI_EXTRACTION_PROMPT = '''Extract CV information and return ONLY valid JSON (no markdown).

RULES:
1. POSITION: Extract actual job title like "Assistant Professor", NOT dates or fragments
2. EDUCATION: Separate degree, field, institution, year
3. EXPERIENCE: Calculate from dates or explicit mentions like "8 years experience"
4. RESEARCH AREAS: Topic names only, NOT sentences with verbs like "Developed..."
5. TEACHING: Subject names like "Machine Learning", NOT "Teaching ML courses"

Return this JSON:
{
    "personal_info": {"name": "", "email": "", "phone": "", "linkedin": ""},
    "education": [{"degree": "", "field": "", "institution": "", "year": null}],
    "work_experience": [{"title": "", "organization": "", "start_year": null, "end_year": "", "is_current": false}],
    "current_position": {"title": "", "organization": ""},
    "total_experience_years": 0,
    "research_areas": [],
    "skills": {"programming": [], "tools": [], "domains": []},
    "teaching": {"subjects": []},
    "awards": []
}

CV TEXT:
'''


# ==================== PDF Extractor ====================

class SmartPDFExtractor:
    """Intelligent PDF text extraction"""
    
    @staticmethod
    async def extract(content: bytes) -> Tuple[str, Dict]:
        """Extract text using best strategy"""
        results = []
        
        # Try multiple strategies
        strategies = [
            ('standard', SmartPDFExtractor._extract_standard),
            ('layout', SmartPDFExtractor._extract_layout_aware),
            ('tables', SmartPDFExtractor._extract_with_tables),
        ]
        
        for name, func in strategies:
            try:
                text, meta = await func(content)
                if text and len(text.strip()) > 50:
                    score = SmartPDFExtractor._score(text)
                    results.append((name, text, score, meta))
            except Exception as e:
                logger.debug(f"{name} extraction failed: {e}")
        
        if not results:
            raise ValueError("Could not extract text from PDF")
        
        # Pick best
        results.sort(key=lambda x: x[2], reverse=True)
        best = results[0]
        logger.info(f"📄 Using {best[0]} extraction (score: {best[2]})")
        
        return best[1], {'method': best[0], 'score': best[2]}
    
    @staticmethod
    async def _extract_standard(content: bytes) -> Tuple[str, Dict]:
        parts = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    parts.append(text)
        return '\n\n'.join(parts), {}
    
    @staticmethod
    async def _extract_layout_aware(content: bytes) -> Tuple[str, Dict]:
        parts = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                chars = page.chars
                if chars and len(chars) > 100:
                    mid_x = page.width / 2
                    left = sum(1 for c in chars if c['x0'] < mid_x - 30)
                    right = sum(1 for c in chars if c['x0'] > mid_x + 30)
                    
                    if left > 50 and right > 50:
                        # Two columns
                        try:
                            left_text = page.within_bbox((0, 0, mid_x - 20, page.height)).extract_text() or ''
                            right_text = page.within_bbox((mid_x + 20, 0, page.width, page.height)).extract_text() or ''
                            
                            # Check which is main content (longer = main)
                            if len(right_text) > len(left_text) * 1.5:
                                parts.extend([right_text, "---", left_text])
                            else:
                                parts.extend([left_text, right_text])
                            continue
                        except:
                            pass
                
                text = page.extract_text()
                if text:
                    parts.append(text)
        
        return '\n\n'.join(parts), {'layout': 'multi-column'}
    
    @staticmethod
    async def _extract_with_tables(content: bytes) -> Tuple[str, Dict]:
        parts = []
        table_count = 0
        
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        table_count += 1
                        for row in table:
                            if row:
                                cells = [str(c).strip() for c in row if c]
                                if cells:
                                    parts.append(' | '.join(cells))
                
                text = page.extract_text()
                if text:
                    parts.append(text)
        
        return '\n'.join(parts), {'tables': table_count}
    
    @staticmethod
    def _score(text: str) -> int:
        if not text:
            return 0
        
        score = min(len(text) // 50, 30)
        
        if re.search(r'[\w.-]+@[\w.-]+\.\w+', text):
            score += 15
        if re.search(r'\d{10}|\d{3}[-.]?\d{3}[-.]?\d{4}', text):
            score += 10
        if re.search(r'\b(19|20)\d{2}\b', text):
            score += 10
        
        for kw in ['professor', 'university', 'education', 'experience', 'phd', 'master']:
            if kw in text.lower():
                score += 3
        
        return score


# ==================== Data Cleaner ====================

class DataCleaner:
    """Clean and validate extracted data"""
    
    @staticmethod
    def clean(data: Dict) -> Dict:
        if not isinstance(data, dict):
            return {}
        
        data['personal_info'] = DataCleaner._clean_personal(data.get('personal_info', {}))
        data['education'] = DataCleaner._clean_education(data.get('education', []))
        data['work_experience'] = DataCleaner._clean_experience(data.get('work_experience', []))
        data['current_position'] = DataCleaner._clean_position(
            data.get('current_position', {}),
            data.get('work_experience', [])
        )
        data['research_areas'] = DataCleaner._clean_research(data.get('research_areas', []))
        data['total_experience_years'] = DataCleaner._calc_experience(
            data.get('total_experience_years'),
            data.get('work_experience', [])
        )
        data['teaching'] = DataCleaner._clean_teaching(data.get('teaching', {}))
        
        return data
    
    @staticmethod
    def _clean_personal(info: Any) -> Dict:
        if not isinstance(info, dict):
            return {}
        
        result = {}
        
        name = str(info.get('name', '')).strip()
        if name:
            name = re.sub(r'^(Dr\.?|Prof\.?|Mr\.?|Ms\.?)\s*', '', name, flags=re.I)
            if 2 < len(name) < 60 and not any(c.isdigit() for c in name):
                result['name'] = name
        
        email = str(info.get('email', ''))
        match = re.search(r'[\w.-]+@[\w.-]+\.\w{2,}', email)
        if match:
            result['email'] = match.group()
        
        phone = str(info.get('phone', ''))
        phone_clean = re.sub(r'[^\d+\-\.\(\)\s]', '', phone)
        if len(re.sub(r'\D', '', phone_clean)) >= 10:
            result['phone'] = phone_clean.strip()
        
        return result
    
    @staticmethod
    def _clean_education(education: Any) -> List[Dict]:
        if not isinstance(education, list):
            return []
        
        cleaned = []
        seen = set()
        
        for edu in education:
            if not isinstance(edu, dict):
                continue
            
            degree = str(edu.get('degree', '')).strip()
            degree_key = degree.lower().replace('.', '').replace(' ', '')
            normalized = VALID_DEGREES.get(degree_key, degree if degree else None)
            
            if not normalized:
                continue
            
            entry = {'degree': normalized}
            
            field = str(edu.get('field', '')).strip()
            if field and len(field) < 80:
                field = re.sub(r'\s+(from|at|university|institute).*$', '', field, flags=re.I)
                entry['field'] = field.strip()
            
            institution = str(edu.get('institution', '')).strip()
            if institution and len(institution) < 120:
                entry['institution'] = institution
            
            year = edu.get('year')
            if year:
                try:
                    y = int(year)
                    if 1950 <= y <= datetime.now().year + 5:
                        entry['year'] = y
                except:
                    pass
            
            key = (normalized, entry.get('institution', ''))
            if key not in seen:
                seen.add(key)
                cleaned.append(entry)
        
        cleaned.sort(key=lambda x: DEGREE_RANKS.get(x.get('degree', ''), 0), reverse=True)
        return cleaned
    
    @staticmethod
    def _clean_experience(experience: Any) -> List[Dict]:
        if not isinstance(experience, list):
            return []
        
        cleaned = []
        
        for exp in experience:
            if not isinstance(exp, dict):
                continue
            
            title = DataCleaner._clean_title(str(exp.get('title', '')))
            if not title:
                continue
            
            entry = {'title': title}
            
            org = str(exp.get('organization', '')).strip()
            if org and len(org) < 120:
                entry['organization'] = org
            
            start = exp.get('start_year')
            if start:
                try:
                    entry['start_year'] = int(start)
                except:
                    pass
            
            end = exp.get('end_year')
            if end:
                if str(end).lower() in ['present', 'current', 'now']:
                    entry['end_year'] = 'Present'
                    entry['is_current'] = True
                else:
                    try:
                        entry['end_year'] = int(end)
                    except:
                        pass
            
            if exp.get('is_current'):
                entry['is_current'] = True
                entry['end_year'] = 'Present'
            
            cleaned.append(entry)
        
        cleaned.sort(key=lambda x: (not x.get('is_current', False), -(x.get('start_year', 0))))
        return cleaned
    
    @staticmethod
    def _clean_title(title: str) -> str:
        if not title:
            return ""
        
        # Remove dates and fragments
        title = re.sub(r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b', '', title, flags=re.I)
        title = re.sub(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b', '', title, flags=re.I)
        title = re.sub(r'\b\d{4}\b', '', title)
        title = re.sub(r'\b(present|current|ongoing)\b', '', title, flags=re.I)
        title = re.sub(r'[\s\-–—|:,\.]+$', '', title)
        title = re.sub(r'^[\s\-–—|:,\.]+', '', title)
        title = re.sub(r'\s+', ' ', title).strip()
        
        if len(title) < 4:
            return ""
        
        # Validate against known titles
        title_lower = title.lower()
        all_titles = ACADEMIC_TITLES + INDUSTRY_TITLES
        
        if any(t in title_lower for t in all_titles):
            return title
        
        # Common partial matches
        if any(kw in title_lower for kw in ['professor', 'engineer', 'developer', 'scientist', 'analyst', 'manager', 'consultant', 'researcher', 'lecturer']):
            return title
        
        return ""
    
    @staticmethod
    def _clean_position(position: Any, experience: List) -> Dict:
        result = {}
        
        if isinstance(position, dict):
            title = DataCleaner._clean_title(str(position.get('title', '')))
            if title:
                result['title'] = title
                result['organization'] = str(position.get('organization', '')).strip()
        
        if not result.get('title') and experience:
            for exp in experience:
                if exp.get('is_current'):
                    result = {'title': exp.get('title', ''), 'organization': exp.get('organization', '')}
                    break
            if not result.get('title'):
                result = {'title': experience[0].get('title', ''), 'organization': experience[0].get('organization', '')}
        
        return result
    
    @staticmethod
    def _clean_research(areas: Any) -> List[str]:
        if not isinstance(areas, list):
            return []
        
        cleaned = []
        seen = set()
        
        action_verbs = ['developed', 'conducted', 'led', 'managed', 'created', 'designed', 
                       'implemented', 'built', 'worked', 'collaborated', 'published', 
                       'presented', 'supervised', 'mentored', 'taught', 'engaged']
        
        for area in areas:
            if not isinstance(area, str):
                continue
            
            area = area.strip()
            if len(area) < 3 or len(area) > 80:
                continue
            
            area_lower = area.lower()
            if any(area_lower.startswith(v) for v in action_verbs):
                continue
            
            if re.search(r'\b(is|are|was|were|has|have|will|would)\b', area_lower):
                continue
            
            if area_lower not in seen:
                seen.add(area_lower)
                cleaned.append(area)
        
        return cleaned[:15]
    
    @staticmethod
    def _calc_experience(years: Any, experience: List) -> int:
        if years:
            try:
                y = int(years)
                if 0 < y < 60:
                    return y
            except:
                pass
        
        total = 0
        current_year = datetime.now().year
        
        for exp in experience:
            start = exp.get('start_year')
            if not start:
                continue
            
            try:
                start_int = int(start)
                end = exp.get('end_year')
                
                if exp.get('is_current') or end == 'Present':
                    end_int = current_year
                elif isinstance(end, int):
                    end_int = end
                else:
                    continue
                
                years_worked = end_int - start_int
                if 0 < years_worked < 50:
                    total += years_worked
            except:
                pass
        
        return total
    
    @staticmethod
    def _clean_teaching(teaching: Any) -> Dict:
        if not isinstance(teaching, dict):
            return {'subjects': []}
        
        subjects = []
        for key in ['subjects', 'courses', 'courses_taught']:
            items = teaching.get(key, [])
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, str) and 2 < len(item.strip()) < 80:
                        # Expand abbreviations
                        expansions = {
                            'AI': 'Artificial Intelligence', 'ML': 'Machine Learning',
                            'NLP': 'Natural Language Processing', 'DL': 'Deep Learning',
                            'DS': 'Data Structures', 'DBMS': 'Database Management',
                            'OS': 'Operating Systems', 'CN': 'Computer Networks'
                        }
                        item = expansions.get(item.strip().upper(), item.strip())
                        if item not in subjects:
                            subjects.append(item)
        
        return {'subjects': subjects}


# ==================== AI Parsers ====================

class GroqParser:
    """
    FREE AI parser using Groq API
    Get free API key at: https://console.groq.com/
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-8b-instant"  # Fast and free
    
    async def parse(self, text: str, filename: str) -> Dict[str, Any]:
        try:
            max_chars = 10000
            if len(text) > max_chars:
                text = text[:max_chars] + "\n[...truncated...]"
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are a CV parser. Return ONLY valid JSON."},
                            {"role": "user", "content": AI_EXTRACTION_PROMPT + text}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 2000
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"Groq API error: {response.status_code}")
                
                data = response.json()
                content = data['choices'][0]['message']['content'].strip()
                
                # Clean markdown
                content = re.sub(r'^```(?:json)?\n?', '', content)
                content = re.sub(r'\n?```$', '', content)
                
                parsed = json.loads(content)
                parsed = DataCleaner.clean(parsed)
                
                logger.info(f"✅ Groq parsing successful")
                return {"success": True, "data": parsed, "method": "groq_llama"}
                
        except Exception as e:
            logger.error(f"Groq parsing error: {e}")
            return {"success": False, "error": str(e)}


class OpenAIParser:
    """OpenAI GPT parser"""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo"
    
    async def parse(self, text: str, filename: str) -> Dict[str, Any]:
        try:
            max_chars = 12000
            if len(text) > max_chars:
                text = text[:max_chars] + "\n[...truncated...]"
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a CV parser. Return ONLY valid JSON."},
                    {"role": "user", "content": AI_EXTRACTION_PROMPT + text}
                ],
                temperature=0.1,
                max_tokens=2500,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            content = re.sub(r'^```(?:json)?\n?', '', content)
            content = re.sub(r'\n?```$', '', content)
            
            parsed = json.loads(content)
            parsed = DataCleaner.clean(parsed)
            
            logger.info(f"✅ OpenAI parsing successful")
            return {"success": True, "data": parsed, "method": "openai_gpt"}
            
        except Exception as e:
            logger.error(f"OpenAI parsing error: {e}")
            return {"success": False, "error": str(e)}


# ==================== Enhanced Rule-Based Parser ====================

class RuleParser:
    """Comprehensive rule-based parser"""
    
    async def parse(self, text: str, filename: str) -> Dict[str, Any]:
        try:
            data = {
                'personal_info': self._extract_personal(text),
                'education': self._extract_education(text),
                'work_experience': self._extract_experience(text),
                'current_position': {},
                'total_experience_years': 0,
                'research_areas': self._extract_research(text),
                'skills': self._extract_skills(text),
                'teaching': self._extract_teaching(text),
                'awards': []
            }
            
            # Set current position
            for exp in data['work_experience']:
                if exp.get('is_current'):
                    data['current_position'] = {
                        'title': exp.get('title', ''),
                        'organization': exp.get('organization', '')
                    }
                    break
            
            if not data['current_position'] and data['work_experience']:
                data['current_position'] = {
                    'title': data['work_experience'][0].get('title', ''),
                    'organization': data['work_experience'][0].get('organization', '')
                }
            
            # Calculate experience
            data['total_experience_years'] = self._calc_experience(text, data['work_experience'])
            
            # Clean
            data = DataCleaner.clean(data)
            
            logger.info(f"✅ Rule-based parsing successful")
            return {"success": True, "data": data, "method": "rule_based"}
            
        except Exception as e:
            logger.error(f"Rule parsing error: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_personal(self, text: str) -> Dict:
        info = {}
        lines = text.split('\n')
        
        # Name
        for line in lines[:20]:
            line = line.strip()
            if not line or len(line) > 60:
                continue
            
            skip = ['@', 'http', r'\d{10}', 'curriculum', 'vitae', 'resume', 'phone', 'email', 'linkedin']
            if any(re.search(s, line, re.I) for s in skip):
                continue
            
            words = line.split()
            if 1 <= len(words) <= 5:
                clean = [w for w in words if w.lower() not in ['dr', 'dr.', 'prof', 'prof.', 'mr', 'mr.', 'ms', 'ms.']]
                if clean and sum(1 for w in clean if w[0].isupper()) >= len(clean) * 0.5:
                    info['name'] = ' '.join(clean)
                    break
        
        # Email
        emails = re.findall(r'[\w.-]+@[\w.-]+\.\w{2,}', text)
        if emails:
            info['email'] = emails[0]
        
        # Phone
        patterns = [r'\+91[\s-]?\d{5}[\s-]?\d{5}', r'\+1[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}', 
                   r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', r'\d{5}[\s-]?\d{5}']
        for p in patterns:
            m = re.search(p, text)
            if m:
                info['phone'] = m.group()
                break
        
        return info
    
    def _extract_education(self, text: str) -> List[Dict]:
        education = []
        
        # Patterns for degree + field + institution + year
        patterns = [
            (r'Ph\.?D\.?\s*(?:in\s+)?([A-Za-z\s&]+?)(?:\s*[-–,]|\s+from\s+|\s+at\s+)([A-Za-z\s,]+?)(?:\s*[-–,]\s*)(\d{4})', 'Ph.D.'),
            (r'M\.?Tech\.?\s*(?:in\s+)?([A-Za-z\s&]+?)(?:\s*[-–,]|\s+from\s+)([A-Za-z\s,]+?)(?:\s*[-–,]\s*)(\d{4})', 'M.Tech'),
            (r'M\.?S\.?c?\.?\s*(?:in\s+)?([A-Za-z\s&]+?)(?:\s*[-–,]|\s+from\s+)([A-Za-z\s,]+?)(?:\s*[-–,]\s*)(\d{4})', 'M.Sc.'),
            (r'B\.?Tech\.?\s*(?:in\s+)?([A-Za-z\s&]+?)(?:\s*[-–,]|\s+from\s+)([A-Za-z\s,]+?)(?:\s*[-–,]\s*)(\d{4})', 'B.Tech'),
            (r'B\.?S\.?c?\.?\s*(?:in\s+)?([A-Za-z\s&]+?)(?:\s*[-–,]|\s+from\s+)([A-Za-z\s,]+?)(?:\s*[-–,]\s*)(\d{4})', 'B.Sc.'),
        ]
        
        for pattern, degree in patterns:
            for m in re.finditer(pattern, text, re.I):
                field = m.group(1).strip()[:60]
                institution = m.group(2).strip()[:100]
                year = int(m.group(3))
                
                if not any(e['degree'] == degree and e.get('year') == year for e in education):
                    education.append({
                        'degree': degree,
                        'field': re.sub(r'\s+(from|at).*$', '', field, flags=re.I),
                        'institution': institution,
                        'year': year
                    })
        
        # Fallback: simple degree detection
        if not education:
            simple = [
                (r'Ph\.?D\.?', 'Ph.D.'), (r'M\.?Tech', 'M.Tech'), (r'M\.?S\.?c?', 'M.Sc.'),
                (r'MBA', 'MBA'), (r'B\.?Tech', 'B.Tech'), (r'B\.?S\.?c?', 'B.Sc.')
            ]
            
            for pattern, degree in simple:
                if re.search(pattern, text, re.I) and not any(e['degree'] == degree for e in education):
                    # Find context
                    m = re.search(pattern, text, re.I)
                    ctx = text[max(0, m.start()-50):min(len(text), m.end()+150)]
                    
                    # Find institution
                    institution = ""
                    for kw in INSTITUTION_KEYWORDS:
                        im = re.search(rf'\b\w*{kw}\w*(?:\s+\w+)*', ctx, re.I)
                        if im:
                            institution = im.group()[:80]
                            break
                    
                    # Find year
                    years = re.findall(r'\b(20\d{2}|19\d{2})\b', ctx)
                    year = int(years[-1]) if years else None
                    
                    education.append({
                        'degree': degree,
                        'field': '',
                        'institution': institution,
                        'year': year
                    })
        
        education.sort(key=lambda x: DEGREE_RANKS.get(x.get('degree', ''), 0), reverse=True)
        return education
    
    def _extract_experience(self, text: str) -> List[Dict]:
        experience = []
        all_titles = ACADEMIC_TITLES + INDUSTRY_TITLES
        
        # Pattern: Title at/in Org, Date-Date
        for title_kw in all_titles:
            pattern = rf'\b({re.escape(title_kw)}[^,\n]{{0,40}}?)(?:\s*[-–|]|\s+at\s+|\s+in\s+)([A-Za-z][A-Za-z\s,\.]+?)(?:\s*[-–|]\s*)(\d{{4}})\s*[-–]\s*(Present|Current|\d{{4}})'
            
            for m in re.finditer(pattern, text, re.I):
                title = DataCleaner._clean_title(m.group(1))
                if not title:
                    continue
                
                org = re.sub(r'\s*[-–|,]\s*$', '', m.group(2)).strip()[:100]
                start = int(m.group(3))
                end = m.group(4)
                
                is_current = end.lower() in ['present', 'current']
                
                if not any(e.get('title') == title and e.get('start_year') == start for e in experience):
                    experience.append({
                        'title': title,
                        'organization': org,
                        'start_year': start,
                        'end_year': 'Present' if is_current else int(end),
                        'is_current': is_current
                    })
        
        experience.sort(key=lambda x: (not x.get('is_current', False), -(x.get('start_year', 0))))
        return experience
    
    def _calc_experience(self, text: str, experience: List) -> int:
        # Look for explicit mentions
        patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            r'over\s+(\d+)\s+years?',
            r'(\d+)\s+years?\s+(?:of\s+)?(?:teaching|research|industry)',
        ]
        
        for p in patterns:
            m = re.search(p, text, re.I)
            if m:
                try:
                    y = int(m.group(1))
                    if 1 <= y <= 50:
                        return y
                except:
                    pass
        
        # Calculate from experience
        total = 0
        current_year = datetime.now().year
        
        for exp in experience:
            start = exp.get('start_year')
            if not start:
                continue
            
            end = exp.get('end_year')
            if end == 'Present' or exp.get('is_current'):
                end_year = current_year
            elif isinstance(end, int):
                end_year = end
            else:
                continue
            
            years = end_year - start
            if 0 < years < 50:
                total += years
        
        return total
    
    def _extract_research(self, text: str) -> List[str]:
        areas = []
        text_lower = text.lower()
        
        for kw in RESEARCH_KEYWORDS:
            if kw in text_lower:
                formatted = kw.upper() if len(kw) <= 4 else kw.title()
                if formatted not in areas:
                    areas.append(formatted)
        
        return areas[:12]
    
    def _extract_skills(self, text: str) -> Dict:
        skills = {'programming': [], 'tools': [], 'domains': []}
        text_lower = text.lower()
        
        programming = ['python', 'java', 'javascript', 'c++', 'c#', 'r', 'sql', 'matlab', 'go', 'rust', 'kotlin', 'typescript']
        tools = ['tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy', 'docker', 'kubernetes', 'aws', 'azure', 'git', 'spark', 'hadoop']
        
        for s in programming:
            if re.search(r'\b' + re.escape(s) + r'\b', text_lower):
                skills['programming'].append('C++' if s == 'c++' else s.upper() if len(s) <= 3 else s.title())
        
        for s in tools:
            if re.search(r'\b' + re.escape(s) + r'\b', text_lower):
                skills['tools'].append(s.upper() if s in ['aws', 'gcp', 'git'] else s.title())
        
        return skills
    
    def _extract_teaching(self, text: str) -> Dict:
        subjects = []
        
        patterns = [
            r'(?:teaching|taught|courses?\s+in|subjects?:)\s*([^\.]+)',
        ]
        
        for p in patterns:
            for m in re.finditer(p, text, re.I):
                items = re.split(r'\s+and\s+|\s*,\s*|\s*&\s*', m.group(1))
                for item in items:
                    item = item.strip()
                    if 2 < len(item) < 60:
                        expansions = {'AI': 'Artificial Intelligence', 'ML': 'Machine Learning', 'NLP': 'Natural Language Processing'}
                        item = expansions.get(item.upper(), item)
                        if item not in subjects:
                            subjects.append(item)
        
        return {'subjects': subjects}


# ==================== Main Parser ====================

class AcademicCVParser:
    """Main parser with multiple AI backends and fallback"""
    
    def __init__(self):
        self.openai_parser = None
        self.groq_parser = None
        self.rule_parser = RuleParser()
        self._init_ai_parsers()
    
    def _init_ai_parsers(self):
        try:
            from app.config import settings
            
            # Try Groq first (FREE!)
            groq_key = getattr(settings, 'GROQ_API_KEY', None)
            if groq_key:
                self.groq_parser = GroqParser(groq_key)
                logger.info("✅ Groq parser initialized (FREE)")
            
            # Then OpenAI
            if OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
                self.openai_parser = OpenAIParser(settings.OPENAI_API_KEY)
                logger.info("✅ OpenAI parser initialized")
            
            if not self.groq_parser and not self.openai_parser:
                logger.warning("⚠️ No AI parsers available, using rule-based only")
                
        except Exception as e:
            logger.warning(f"AI parser init error: {e}")
    
    async def parse(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        logger.info(f"📄 Parsing CV: {filename}")
        
        # Extract text
        text, extraction_meta = await SmartPDFExtractor.extract(file_content)
        
        if not text or len(text.strip()) < 50:
            raise ValueError("Could not extract text from CV")
        
        logger.info(f"📝 Extracted {len(text)} chars")
        
        # Try parsers in order
        parse_result = None
        
        # 1. Try Groq (FREE)
        if self.groq_parser and not parse_result:
            logger.info("🤖 Trying Groq (free)...")
            result = await self.groq_parser.parse(text, filename)
            if result.get('success'):
                parse_result = result
        
        # 2. Try OpenAI
        if self.openai_parser and not parse_result:
            logger.info("🤖 Trying OpenAI...")
            result = await self.openai_parser.parse(text, filename)
            if result.get('success'):
                parse_result = result
        
        # 3. Fallback to rules
        if not parse_result or not parse_result.get('success'):
            logger.info("📋 Using rule-based parsing...")
            parse_result = await self.rule_parser.parse(text, filename)
        
        # Build result
        data = parse_result.get('data', {})
        suggested = self._build_suggested_profile(data)
        quality = self._calc_quality(data)
        
        return {
            'text': text,
            'personal_info': data.get('personal_info', {}),
            'education': data.get('education', []),
            'experience': data.get('work_experience', []),
            'research_interests': data.get('research_areas', []),
            'skills': data.get('skills', {}),
            'teaching': data.get('teaching', {}),
            'total_experience_years': data.get('total_experience_years', 0),
            'suggested_profile': suggested,
            'metadata': {
                'filename': filename,
                'parsed_at': datetime.utcnow().isoformat(),
                'parser_method': parse_result.get('method', 'unknown'),
                'extraction_method': extraction_meta.get('method', 'unknown'),
                'quality_score': quality,
                'parser_version': 'v8-multi-ai'
            },
            'word_count': len(text.split()),
            'quality_score': quality,
            'extraction_success': True
        }
    
    def _build_suggested_profile(self, data: Dict) -> Dict:
        education = data.get('education', [])
        highest = education[0] if education else {}
        
        experience = data.get('work_experience', [])
        current = data.get('current_position', {})
        
        if not current.get('title') and experience:
            for exp in experience:
                if exp.get('is_current'):
                    current = {'title': exp.get('title', ''), 'organization': exp.get('organization', '')}
                    break
            if not current.get('title') and experience:
                current = {'title': experience[0].get('title', ''), 'organization': experience[0].get('organization', '')}
        
        skills = data.get('skills', {})
        all_skills = []
        if isinstance(skills, dict):
            for v in skills.values():
                if isinstance(v, list):
                    all_skills.extend(v)
        
        teaching = data.get('teaching', {})
        subjects = teaching.get('subjects', []) if isinstance(teaching, dict) else []
        
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
                'primary_areas': data.get('research_areas', [])[:5],
                'secondary_interests': data.get('research_areas', [])[5:10],
                'keywords': all_skills[:20]
            },
            'teaching': {
                'current_subjects': list(set(subjects))[:10]
            },
            'publications': {'total_count': 0, 'notable_works': []},
            'skills': skills,
            'availability': {'office_location': '', 'office_hours': ''},
            'others': {'awards': data.get('awards', [])}
        }
    
    def _calc_quality(self, data: Dict) -> float:
        score = 0
        
        pi = data.get('personal_info', {})
        if pi.get('name'): score += 15
        if pi.get('email'): score += 10
        
        if data.get('education'): score += 20
        if data.get('work_experience'): score += 20
        
        current = data.get('current_position', {})
        if current.get('title') and len(current.get('title', '')) > 3:
            score += 15
        
        if data.get('research_areas'): score += 10
        if data.get('skills'): score += 5
        if data.get('teaching', {}).get('subjects'): score += 5
        
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
    'cv_parser_v2', 'CVParserV2', 'parse_cv_file'
]