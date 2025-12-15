#academic-advisor-backend/app/services/nlp_service.py
import logging
from typing import Dict, Any, List, Optional
import spacy
import asyncio
from collections import defaultdict, Counter
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class NLPService:
    def __init__(self):
        self.nlp = None
        self._load_model()
    
    def _load_model(self):
        """Load NLP model with enhanced capabilities"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("SpaCy model loaded successfully")
        except OSError:
            logger.warning("SpaCy model not found, using basic NLP")
            self.nlp = None
    
    async def analyze_cv_comprehensive(self, text: str) -> Dict[str, Any]:
        """
        Perform comprehensive CV analysis using NLP
        """
        if not text.strip():
            return {"error": "Empty text provided"}
        
        try:
            if self.nlp:
                return await self._analyze_cv_with_spacy(text)
            else:
                return await self._analyze_cv_basic(text)
        except Exception as e:
            logger.error(f"CV NLP analysis error: {e}")
            return {"error": str(e)}
    
    async def _analyze_cv_with_spacy(self, text: str) -> Dict[str, Any]:
        """
        Advanced CV analysis with SpaCy
        """
        doc = self.nlp(text[:1000000])  # Limit text length
        
        # Extract entities
        entities = await self._extract_cv_entities(doc)
        
        # Extract education information
        education_info = await self._extract_education(doc, text)
        
        # Extract experience information
        experience_info = await self._extract_experience(doc, text)
        
        # Extract personal information
        personal_info = await self._extract_personal_info(doc, entities)
        
        # Analyze writing style and quality
        writing_analysis = await self._analyze_writing_style(doc, text)
        
        # Extract achievements and accomplishments
        achievements = await self._extract_achievements(doc, text)
        
        return {
            "entities": entities,
            "education": education_info,
            "experience": experience_info,
            "personal_info": personal_info,
            "writing_analysis": writing_analysis,
            "achievements": achievements,
            "document_metrics": {
                "sentence_count": len(list(doc.sents)),
                "word_count": len([token for token in doc if not token.is_space]),
                "character_count": len(text),
                "readability_score": await self._calculate_readability(text),
                "professional_tone_score": await self._assess_professional_tone(doc)
            },
            "analysis_method": "spacy_enhanced"
        }
    
    async def _extract_cv_entities(self, doc) -> Dict[str, List[Dict]]:
        """
        Extract entities from CV text
        """
        entities = defaultdict(list)
        
        for ent in doc.ents:
            entity_info = {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": 0.8  # Default confidence for SpaCy entities
            }
            
            # Categorize entities for CV context
            if ent.label_ in ["PERSON", "ORG"]:
                entities["organizations"].append(entity_info)
            elif ent.label_ in ["GPE", "LOC"]:
                entities["locations"].append(entity_info)
            elif ent.label_ == "DATE":
                entities["dates"].append(entity_info)
            elif ent.label_ in ["MONEY", "QUANTITY"]:
                entities["quantities"].append(entity_info)
            else:
                entities["other"].append(entity_info)
        
        return dict(entities)
    
    async def _extract_education(self, doc, text: str) -> Dict[str, Any]:
        """
        Extract education information from CV
        """
        education = []
        text_lower = text.lower()
        
        # Look for education section
        education_sections = re.finditer(
            r'(?:education|academic background|qualifications)[:\s]*([^\n]+(?:\n[^\n]+)*)',
            text, 
            re.IGNORECASE
        )
        
        for section_match in education_sections:
            section_text = section_match.group(1)
            
            # Extract degrees
            degree_patterns = [
                r'(?:master|m\.?s\.?|m\.?sc\.?).*?(?:in|of)\s+([^\n,;]+)',
                r'(?:bachelor|b\.?s\.?|b\.?a\.?).*?(?:in|of)\s+([^\n,;]+)',
                r'(?:phd|ph\.?d\.?|doctoral).*?(?:in|of)\s+([^\n,;]+)',
                r'(?:associate|a\.?s\.?|a\.?a\.?).*?(?:in|of)\s+([^\n,;]+)'
            ]
            
            for pattern in degree_patterns:
                degree_matches = re.finditer(pattern, section_text, re.IGNORECASE)
                for match in degree_matches:
                    degree_field = match.group(1).strip()
                    education.append({
                        "degree": self._classify_degree(pattern),
                        "field": degree_field,
                        "institution": await self._extract_institution(section_text),
                        "year": await self._extract_year(section_text),
                        "confidence": 75
                    })
        
        # If no structured education found, look for education keywords
        if not education:
            education_keywords = ['university', 'college', 'institute', 'bachelor', 'master', 'phd', 'degree']
            for sent in doc.sents:
                sent_text = sent.text.lower()
                if any(keyword in sent_text for keyword in education_keywords):
                    education.append({
                        "degree": "unknown",
                        "field": await self._extract_field_from_sentence(sent.text),
                        "institution": await self._extract_institution(sent.text),
                        "year": await self._extract_year(sent.text),
                        "confidence": 50,
                        "context": sent.text[:100]
                    })
        
        return {
            "degrees": education,
            "highest_degree": await self._identify_highest_degree(education),
            "education_level": await self._assess_education_level(education)
        }
    
    async def _extract_experience(self, doc, text: str) -> Dict[str, Any]:
        """
        Extract work experience information
        """
        experience = []
        
        # Look for experience sections
        experience_sections = re.finditer(
            r'(?:experience|work history|employment)[:\s]*([^\n]+(?:\n[^\n]+)*)',
            text,
            re.IGNORECASE
        )
        
        for section_match in experience_sections:
            section_text = section_match.group(1)
            
            # Extract job entries (simplified pattern)
            job_pattern = r'([^\n]+?)\s*-\s*([^\n]+?)\s*-\s*([^\n]+?)(?=\n\n|\n[A-Z]|$)'
            job_matches = re.finditer(job_pattern, section_text, re.IGNORECASE)
            
            for match in job_matches:
                experience.append({
                    "title": match.group(1).strip(),
                    "company": match.group(2).strip(),
                    "duration": match.group(3).strip(),
                    "confidence": 70
                })
        
        # Calculate total experience
        total_experience = await self._calculate_total_experience(experience)
        
        return {
            "positions": experience,
            "total_experience_years": total_experience,
            "career_level": await self._assess_career_level(experience, total_experience)
        }
    
    async def _extract_personal_info(self, doc, entities: Dict) -> Dict[str, Any]:
        """
        Extract personal information
        """
        personal_info = {}
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, doc.text)
        if emails:
            personal_info["email"] = emails[0]
        
        # Extract phone numbers
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, doc.text)
        if phones:
            personal_info["phone"] = phones[0]
        
        # Extract locations
        if "locations" in entities:
            personal_info["locations"] = [loc["text"] for loc in entities["locations"][:3]]
        
        return personal_info
    
    async def _analyze_writing_style(self, doc, text: str) -> Dict[str, Any]:
        """
        Analyze writing style and quality
        """
        sentences = list(doc.sents)
        words = [token for token in doc if not token.is_space and token.is_alpha]
        
        # Calculate metrics
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        avg_word_length = sum(len(token.text) for token in words) / len(words) if words else 0
        
        # Assess vocabulary richness (type-token ratio)
        unique_words = set(token.text.lower() for token in words)
        ttr = len(unique_words) / len(words) if words else 0
        
        # Check for action verbs (important in CVs)
        action_verbs = ['managed', 'led', 'developed', 'implemented', 'created', 'designed', 
                       'optimized', 'improved', 'achieved', 'increased', 'reduced']
        action_verb_count = sum(1 for token in words if token.lemma_ in action_verbs and token.pos_ == "VERB")
        
        return {
            "avg_sentence_length": round(avg_sentence_length, 2),
            "avg_word_length": round(avg_word_length, 2),
            "vocabulary_richness": round(ttr, 3),
            "action_verb_count": action_verb_count,
            "action_verb_ratio": round(action_verb_count / len(words), 3) if words else 0,
            "writing_quality": await self._assess_writing_quality(doc, text)
        }
    
    async def _extract_achievements(self, doc, text: str) -> List[Dict[str, Any]]:
        """
        Extract achievements and accomplishments
        """
        achievements = []
        
        # Look for achievement indicators
        achievement_indicators = [
            r'increased.*?(?:by|to)\s+(\d+%?)',
            r'reduced.*?(?:by|to)\s+(\d+%?)',
            r'improved.*?(?:by|to)\s+(\d+%?)',
            r'achieved.*?(?:rate|score|metric)\s+of\s+(\d+%?)',
            r'saved.*?\$?(\d+)',
            r'generated.*?\$?(\d+)'
        ]
        
        for pattern in achievement_indicators:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                achievements.append({
                    "achievement": match.group(0),
                    "metric": match.group(1) if match.groups() else None,
                    "confidence": 65,
                    "type": self._classify_achievement_type(match.group(0))
                })
        
        return achievements
    
    async def _calculate_readability(self, text: str) -> float:
        """
        Calculate readability score (simplified Flesch Reading Ease)
        """
        sentences = re.split(r'[.!?]+', text)
        words = re.findall(r'\b\w+\b', text)
        syllables = sum(self._count_syllables(word) for word in words)
        
        if not sentences or not words:
            return 0
        
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = syllables / len(words)
        
        # Simplified Flesch Reading Ease
        readability = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        return max(0, min(100, readability))
    
    def _count_syllables(self, word: str) -> int:
        """
        Count syllables in a word (approximate)
        """
        word = word.lower()
        count = 0
        vowels = "aeiouy"
        
        if word[0] in vowels:
            count += 1
        
        for i in range(1, len(word)):
            if word[i] in vowels and word[i-1] not in vowels:
                count += 1
        
        if word.endswith('e'):
            count -= 1
        
        return max(1, count)
    
    async def _assess_professional_tone(self, doc) -> float:
        """
        Assess professional tone of the CV
        """
        professional_terms = ['managed', 'led', 'developed', 'implemented', 'achieved', 
                            'optimized', 'collaborated', 'presented', 'published']
        
        informal_terms = ['awesome', 'cool', 'stuff', 'things', 'guy', 'kind of', 'sort of']
        
        professional_count = sum(1 for token in doc if token.lemma_ in professional_terms)
        informal_count = sum(1 for token in doc if token.lemma_ in informal_terms)
        
        total_terms = len([token for token in doc if token.is_alpha])
        
        if total_terms == 0:
            return 50
        
        professional_score = (professional_count / total_terms) * 100
        informal_penalty = (informal_count / total_terms) * 50
        
        return max(0, min(100, professional_score - informal_penalty))
    
    # Helper methods
    def _classify_degree(self, pattern: str) -> str:
        """Classify degree type from pattern"""
        if 'master' in pattern:
            return "Master's"
        elif 'bachelor' in pattern:
            return "Bachelor's"
        elif 'phd' in pattern:
            return "PhD"
        elif 'associate' in pattern:
            return "Associate"
        else:
            return "Unknown"
    
    async def _extract_institution(self, text: str) -> str:
        """Extract institution name from text"""
        # Simple pattern matching for institutions
        institution_indicators = ['university', 'college', 'institute', 'school']
        words = text.split()
        
        for i, word in enumerate(words):
            if word.lower() in institution_indicators and i > 0:
                return ' '.join(words[max(0, i-2):i+2])
        
        return "Unknown"
    
    async def _extract_year(self, text: str) -> str:
        """Extract year from text"""
        year_pattern = r'\b(19|20)\d{2}\b'
        years = re.findall(year_pattern, text)
        return years[0] if years else "Unknown"
    
    async def _extract_field_from_sentence(self, sentence: str) -> str:
        """Extract field of study from sentence"""
        # Look for common field indicators
        field_indicators = ['computer science', 'engineering', 'mathematics', 'physics', 
                          'chemistry', 'biology', 'business', 'economics']
        
        for field in field_indicators:
            if field in sentence.lower():
                return field.title()
        
        return "Unknown"
    
    async def _identify_highest_degree(self, education: List[Dict]) -> str:
        """Identify highest degree"""
        degree_rank = {"PhD": 4, "Master's": 3, "Bachelor's": 2, "Associate": 1, "Unknown": 0}
        highest = max(education, key=lambda x: degree_rank.get(x.get("degree", "Unknown"), 0), default=None)
        return highest.get("degree", "Unknown") if highest else "Unknown"
    
    async def _assess_education_level(self, education: List[Dict]) -> str:
        """Assess overall education level"""
        highest_degree = await self._identify_highest_degree(education)
        
        if highest_degree == "PhD":
            return "doctoral"
        elif highest_degree == "Master's":
            return "masters"
        elif highest_degree == "Bachelor's":
            return "bachelors"
        elif highest_degree == "Associate":
            return "associate"
        else:
            return "unknown"
    
    async def _calculate_total_experience(self, experience: List[Dict]) -> float:
        """Calculate total years of experience"""
        # Simplified calculation - in production, you'd parse dates properly
        return min(len(experience) * 2.0, 30.0)  # Approximate 2 years per position
    
    async def _assess_career_level(self, experience: List[Dict], total_experience: float) -> str:
        """Assess career level based on experience"""
        if total_experience >= 10:
            return "senior"
        elif total_experience >= 5:
            return "mid-level"
        elif total_experience >= 2:
            return "junior"
        else:
            return "entry-level"
    
    def _classify_achievement_type(self, achievement: str) -> str:
        """Classify achievement type"""
        achievement_lower = achievement.lower()
        
        if any(word in achievement_lower for word in ['increased', 'improved', 'achieved']):
            return "performance"
        elif any(word in achievement_lower for word in ['reduced', 'saved', 'decreased']):
            return "efficiency"
        elif any(word in achievement_lower for word in ['developed', 'created', 'implemented']):
            return "innovation"
        else:
            return "general"
    
    async def _assess_writing_quality(self, doc, text: str) -> str:
        """Assess overall writing quality"""
        metrics = await self._analyze_writing_style(doc, text)
        
        if metrics["action_verb_ratio"] > 0.1 and metrics["vocabulary_richness"] > 0.6:
            return "excellent"
        elif metrics["action_verb_ratio"] > 0.05 and metrics["vocabulary_richness"] > 0.5:
            return "good"
        elif metrics["action_verb_ratio"] > 0.02:
            return "average"
        else:
            return "needs_improvement"
    
    async def _analyze_cv_basic(self, text: str) -> Dict[str, Any]:
        """
        Basic CV analysis without SpaCy
        """
        sentences = text.split('.')
        words = text.split()
        
        return {
            "document_metrics": {
                "sentence_count": len([s for s in sentences if s.strip()]),
                "word_count": len(words),
                "character_count": len(text),
                "avg_sentence_length": len(words) / len(sentences) if sentences else 0,
            },
            "analysis_method": "basic",
            "entities": {"organizations": [], "locations": [], "dates": [], "other": []},
            "education": {"degrees": [], "highest_degree": "unknown", "education_level": "unknown"},
            "experience": {"positions": [], "total_experience_years": 0, "career_level": "unknown"},
            "personal_info": {},
            "writing_analysis": {},
            "achievements": []
        }
    
    # Original method for backward compatibility
    async def analyze(self, text: str) -> Dict[str, Any]:
        """
        Original analyze method for backward compatibility
        """
        return await self.analyze_cv_comprehensive(text)