#academic-advisor-backend/app/services/skill_extractor.py
import json
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from fuzzywuzzy import fuzz
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import spacy
from collections import defaultdict, Counter
import asyncio

logger = logging.getLogger(__name__)

class SkillExtractor:
    def __init__(self):
        # Load skill database
        self.skill_database = self.load_skill_database()
        
        # Load pre-trained model if available
        try:
            self.model = joblib.load('app/ml/models/skill_classifier.pkl')
            self.vectorizer = joblib.load('app/ml/models/tfidf_vectorizer.pkl')
        except:
            self.model = None
            self.vectorizer = None
        
        # Load NLP model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("SpaCy model not found, installing...")
            try:
                import os
                os.system("python -m spacy download en_core_web_sm")
                self.nlp = spacy.load("en_core_web_sm")
            except:
                self.nlp = None
                logger.error("Failed to load SpaCy model")
        
        # Enhanced skill categories with research areas
        self.categories = {
            'programming': ['python', 'java', 'javascript', 'c++', 'ruby', 'go', 'rust', 'scala', 'kotlin'],
            'web': ['react', 'angular', 'vue', 'django', 'flask', 'node.js', 'express', 'spring', 'laravel'],
            'data_science': ['pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'spark', 'hadoop', 'tableau'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible', 'jenkins'],
            'database': ['mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'cassandra', 'oracle'],
            'research_methods': ['qualitative analysis', 'quantitative analysis', 'mixed methods', 'case study', 
                               'survey research', 'experimental design', 'literature review', 'ethnography'],
            'academic_skills': ['research design', 'data analysis', 'statistical analysis', 'academic writing',
                              'peer review', 'grant writing', 'research ethics', 'publication'],
            'soft_skills': ['leadership', 'communication', 'teamwork', 'problem-solving', 'critical thinking',
                          'time management', 'adaptability', 'creativity']
        }
        
        # Research area taxonomy
        self.research_taxonomy = {
            'computer_science': {
                'artificial_intelligence': ['machine learning', 'deep learning', 'natural language processing', 
                                          'computer vision', 'robotics', 'expert systems'],
                'systems': ['operating systems', 'distributed systems', 'cloud computing', 'networking', 
                          'cybersecurity', 'database systems'],
                'theory': ['algorithms', 'data structures', 'computational theory', 'cryptography'],
                'software_engineering': ['software development', 'agile methodology', 'devops', 'testing']
            },
            'engineering': {
                'electrical': ['circuit design', 'signal processing', 'power systems', 'control systems'],
                'mechanical': ['thermodynamics', 'fluid mechanics', 'materials science', 'robotics'],
                'civil': ['structural engineering', 'transportation', 'environmental engineering'],
                'chemical': ['process engineering', 'biotechnology', 'materials science']
            },
            'sciences': {
                'physics': ['quantum mechanics', 'astrophysics', 'condensed matter', 'particle physics'],
                'chemistry': ['organic chemistry', 'inorganic chemistry', 'physical chemistry', 'analytical chemistry'],
                'biology': ['molecular biology', 'genetics', 'ecology', 'microbiology'],
                'mathematics': ['algebra', 'calculus', 'statistics', 'number theory']
            },
            'social_sciences': {
                'psychology': ['cognitive psychology', 'clinical psychology', 'social psychology', 'developmental'],
                'economics': ['microeconomics', 'macroeconomics', 'econometrics', 'development economics'],
                'sociology': ['social theory', 'demography', 'criminology', 'political sociology']
            }
        }
    
    def load_skill_database(self) -> Dict[str, Any]:
        """
        Load comprehensive skill database with research capabilities
        """
        return {
            'technical_skills': {
                'Python': {'aliases': ['python3', 'py'], 'category': 'programming', 'importance': 10, 'research_relevance': 8},
                'Machine Learning': {'aliases': ['ml', 'machine-learning'], 'category': 'data_science', 'importance': 9, 'research_relevance': 10},
                'Deep Learning': {'aliases': ['dl', 'neural networks'], 'category': 'data_science', 'importance': 9, 'research_relevance': 10},
                'Natural Language Processing': {'aliases': ['nlp'], 'category': 'data_science', 'importance': 8, 'research_relevance': 9},
                'Data Analysis': {'aliases': ['data analytics'], 'category': 'data_science', 'importance': 8, 'research_relevance': 9},
                'Statistical Analysis': {'aliases': ['statistics'], 'category': 'academic_skills', 'importance': 7, 'research_relevance': 9},
                'Research Design': {'aliases': ['experimental design'], 'category': 'research_methods', 'importance': 8, 'research_relevance': 10},
                'Academic Writing': {'aliases': ['scientific writing'], 'category': 'academic_skills', 'importance': 7, 'research_relevance': 9},
                'TensorFlow': {'aliases': ['tensor flow'], 'category': 'data_science', 'importance': 8, 'research_relevance': 8},
                'PyTorch': {'aliases': ['pytorch'], 'category': 'data_science', 'importance': 8, 'research_relevance': 8},
                'R Programming': {'aliases': ['r', 'r language'], 'category': 'programming', 'importance': 7, 'research_relevance': 9},
                'MATLAB': {'aliases': ['matlab'], 'category': 'programming', 'importance': 6, 'research_relevance': 8},
                # Add more skills...
            },
            'soft_skills': {
                'Research Leadership': {'aliases': ['research management'], 'importance': 8, 'research_relevance': 9},
                'Scientific Communication': {'aliases': ['academic communication'], 'importance': 9, 'research_relevance': 9},
                'Collaboration': {'aliases': ['research collaboration'], 'importance': 8, 'research_relevance': 8},
                'Critical Thinking': {'aliases': ['analytical thinking'], 'importance': 9, 'research_relevance': 9},
                'Problem Solving': {'aliases': ['research problem solving'], 'importance': 8, 'research_relevance': 9},
            },
            'research_domains': {
                'Artificial Intelligence': {'aliases': ['AI'], 'field': 'computer_science', 'subfield': 'artificial_intelligence'},
                'Machine Learning': {'aliases': ['ML'], 'field': 'computer_science', 'subfield': 'artificial_intelligence'},
                'Computer Vision': {'aliases': ['CV'], 'field': 'computer_science', 'subfield': 'artificial_intelligence'},
                'Data Science': {'aliases': ['data analytics'], 'field': 'computer_science', 'subfield': 'artificial_intelligence'},
                'Cybersecurity': {'aliases': ['security'], 'field': 'computer_science', 'subfield': 'systems'},
                'Cloud Computing': {'aliases': ['distributed systems'], 'field': 'computer_science', 'subfield': 'systems'},
                'Bioinformatics': {'aliases': ['computational biology'], 'field': 'sciences', 'subfield': 'biology'},
                'Renewable Energy': {'aliases': ['sustainable energy'], 'field': 'engineering', 'subfield': 'electrical'},
            }
        }
    
    async def extract_comprehensive(self, text: str) -> Dict[str, Any]:
        """
        Extract comprehensive skills and research areas from text
        """
        # Extract basic skills
        basic_skills = await self.extract(text)
        
        # Extract research areas
        research_areas = await self.extract_research_areas(text)
        
        # Extract expertise levels
        expertise_levels = await self.assess_expertise_levels(text, basic_skills)
        
        # Extract research themes
        research_themes = await self.identify_research_themes(text)
        
        # Calculate overall research profile
        research_profile = await self.create_research_profile(
            basic_skills, research_areas, expertise_levels, research_themes
        )
        
        return {
            "skills": basic_skills,
            "research_areas": research_areas,
            "expertise_levels": expertise_levels,
            "research_themes": research_themes,
            "research_profile": research_profile,
            "extraction_metadata": {
                "skill_count": len(basic_skills),
                "research_area_count": len(research_areas),
                "extraction_methods": ["rule_based", "pattern_matching", "nlp_enhanced"]
            }
        }
    
    async def extract_research_areas(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract research areas from text using multiple methods
        """
        extracted_areas = []
        text_lower = text.lower()
        
        # Method 1: Direct matching with research domains
        for domain, domain_info in self.skill_database['research_domains'].items():
            if self.find_concept_in_text(domain, text_lower):
                extracted_areas.append({
                    'name': domain,
                    'field': domain_info['field'],
                    'subfield': domain_info['subfield'],
                    'confidence': 85,
                    'type': 'primary_domain',
                    'matched_text': domain
                })
                continue
            
            # Check aliases
            for alias in domain_info.get('aliases', []):
                if self.find_concept_in_text(alias, text_lower):
                    extracted_areas.append({
                        'name': domain,
                        'field': domain_info['field'],
                        'subfield': domain_info['subfield'],
                        'confidence': 80,
                        'type': 'primary_domain',
                        'matched_text': alias
                    })
                    break
        
        # Method 2: Pattern-based extraction from education and research sections
        pattern_areas = await self.extract_research_patterns(text)
        extracted_areas.extend(pattern_areas)
        
        # Method 3: NLP-based extraction using entity recognition
        if self.nlp:
            nlp_areas = await self.extract_research_nlp(text)
            extracted_areas.extend(nlp_areas)
        
        # Deduplicate and rank
        unique_areas = self.deduplicate_research_areas(extracted_areas)
        ranked_areas = await self.rank_research_areas(unique_areas, text)
        
        return ranked_areas
    
    async def extract_research_patterns(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract research areas using pattern matching
        """
        areas = []
        
        # Patterns for research focus statements
        focus_patterns = [
            r'research\s+(?:focus|interest|area)[:\s]*([^\n\.]+)',
            r'focus\s+(?:on|in)\s+([^\n\.]+)',
            r'specializ(?:ation|ed)\s+in\s+([^\n\.]+)',
            r'primary\s+(?:research|study)\s+area[:\s]*([^\n\.]+)',
            r'field\s+of\s+(?:study|research)[:\s]*([^\n\.]+)'
        ]
        
        for pattern in focus_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                focus_text = match.group(1).strip()
                # Extract potential research areas from focus text
                potential_areas = self.identify_potential_areas(focus_text)
                areas.extend(potential_areas)
        
        # Extract from education sections
        education_pattern = r'(?:education|academic background)[:\s]*([^\n]+(?:\n[^\n]+)*)'
        education_matches = re.finditer(education_pattern, text, re.IGNORECASE)
        
        for match in education_matches:
            education_text = match.group(1)
            # Look for majors, degrees, specializations
            degree_patterns = [
                r'(?:major|degree|specialization)\s+(?:in|:)\s*([^\n,;]+)',
                r'(?:master|bachelor|phd|doctoral).*?(?:in|of)\s+([^\n,;]+)'
            ]
            
            for degree_pattern in degree_patterns:
                degree_matches = re.finditer(degree_pattern, education_text, re.IGNORECASE)
                for degree_match in degree_matches:
                    degree_area = degree_match.group(1).strip()
                    potential_areas = self.identify_potential_areas(degree_area)
                    areas.extend(potential_areas)
        
        return areas
    
    async def extract_research_nlp(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract research areas using NLP entity recognition
        """
        areas = []
        
        try:
            doc = self.nlp(text[:1000000])  # Limit text length
            
            # Extract noun phrases that might indicate research areas
            for chunk in doc.noun_chunks:
                chunk_text = chunk.text.lower().strip()
                if len(chunk_text) > 3 and len(chunk_text) < 50:
                    # Check if this noun phrase relates to research
                    if self.is_research_related(chunk_text):
                        potential_areas = self.identify_potential_areas(chunk_text)
                        areas.extend(potential_areas)
            
            # Extract entities that might be research domains
            for ent in doc.ents:
                if ent.label_ in ["ORG", "PRODUCT", "EVENT"]:
                    ent_text = ent.text.lower()
                    if self.is_research_related(ent_text):
                        potential_areas = self.identify_potential_areas(ent_text)
                        areas.extend(potential_areas)
                        
        except Exception as e:
            logger.error(f"NLP research extraction failed: {e}")
        
        return areas
    
    def identify_potential_areas(self, text: str) -> List[Dict[str, Any]]:
        """
        Identify potential research areas from text snippet
        """
        potential_areas = []
        text_lower = text.lower()
        
        # Check against research taxonomy
        for field, subfields in self.research_taxonomy.items():
            for subfield, areas in subfields.items():
                for area in areas:
                    if area in text_lower:
                        potential_areas.append({
                            'name': area.title(),
                            'field': field,
                            'subfield': subfield,
                            'confidence': 75,
                            'type': 'taxonomy_matched',
                            'matched_text': text
                        })
        
        # Check against research domains
        for domain, domain_info in self.skill_database['research_domains'].items():
            domain_lower = domain.lower()
            if domain_lower in text_lower:
                potential_areas.append({
                    'name': domain,
                    'field': domain_info['field'],
                    'subfield': domain_info['subfield'],
                    'confidence': 85,
                    'type': 'domain_matched',
                    'matched_text': text
                })
        
        return potential_areas
    
    def is_research_related(self, text: str) -> bool:
        """
        Check if text is likely related to research
        """
        research_indicators = [
            'research', 'study', 'analysis', 'investigation', 'experiment',
            'thesis', 'dissertation', 'publication', 'paper', 'journal',
            'conference', 'academic', 'scientific', 'methodology', 'hypothesis'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in research_indicators)
    
    async def assess_expertise_levels(self, text: str, skills: List[Dict]) -> Dict[str, Any]:
        """
        Assess expertise levels for skills and research areas
        """
        expertise_levels = {}
        text_lower = text.lower()
        
        for skill in skills:
            skill_name = skill['name'].lower()
            expertise_score = await self.calculate_expertise_score(skill_name, text_lower)
            
            expertise_levels[skill['name']] = {
                'score': expertise_score,
                'level': self.map_expertise_level(expertise_score),
                'confidence': skill.get('confidence', 50),
                'evidence': await self.extract_expertise_evidence(skill_name, text)
            }
        
        return expertise_levels
    
    async def calculate_expertise_score(self, skill: str, text: str) -> float:
        """
        Calculate expertise score for a skill (0-100)
        """
        score = 50  # Base score
        
        # Frequency of mention
        frequency = text.count(skill)
        score += min(frequency * 5, 20)
        
        # Proficiency indicators
        proficiency_terms = {
            'expert': 20, 'advanced': 15, 'proficient': 10, 'experienced': 10,
            'skilled': 8, 'familiar': 5, 'knowledgeable': 5, 'competent': 8
        }
        
        for term, boost in proficiency_terms.items():
            if f"{term} {skill}" in text or f"{skill} {term}" in text:
                score += boost
                break
        
        # Context indicators
        context_boosters = {
            'led': 10, 'managed': 8, 'developed': 7, 'implemented': 6,
            'designed': 8, 'architected': 10, 'optimized': 7, 'created': 6
        }
        
        for context, boost in context_boosters.items():
            if f"{context} {skill}" in text:
                score += boost
        
        # Duration indicators
        duration_pattern = r'(\d+)\s*(?:year|yr)s?.*?' + re.escape(skill)
        duration_match = re.search(duration_pattern, text)
        if duration_match:
            years = int(duration_match.group(1))
            score += min(years * 5, 25)
        
        return min(score, 100)
    
    def map_expertise_level(self, score: float) -> str:
        """
        Map expertise score to level
        """
        if score >= 80:
            return "expert"
        elif score >= 60:
            return "advanced"
        elif score >= 40:
            return "intermediate"
        else:
            return "beginner"
    
    async def extract_expertise_evidence(self, skill: str, text: str) -> List[str]:
        """
        Extract evidence supporting expertise assessment
        """
        evidence = []
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            if skill.lower() in sentence.lower():
                # Look for evidence patterns
                evidence_patterns = [
                    r'(\d+)\s*years.*?' + re.escape(skill),
                    r'(?:led|managed|developed).*?' + re.escape(skill),
                    r'(?:expert|advanced|proficient).*?' + re.escape(skill),
                    r'(?:published|presented).*?' + re.escape(skill)
                ]
                
                for pattern in evidence_patterns:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        evidence.append(sentence.strip())
                        break
        
        return evidence[:3]  # Return top 3 evidence pieces
    
    async def identify_research_themes(self, text: str) -> List[Dict[str, Any]]:
        """
        Identify broader research themes and interests
        """
        themes = []
        text_lower = text.lower()
        
        # Look for thematic patterns
        theme_indicators = {
            'interdisciplinary': ['interdisciplinary', 'cross-disciplinary', 'multidisciplinary'],
            'applied_research': ['applied research', 'real-world applications', 'industry applications'],
            'theoretical': ['theoretical', 'fundamental research', 'basic research'],
            'experimental': ['experimental', 'lab work', 'field work'],
            'computational': ['computational', 'simulation', 'modeling'],
            'qualitative': ['qualitative', 'case study', 'ethnographic'],
            'quantitative': ['quantitative', 'statistical', 'metrics']
        }
        
        for theme, indicators in theme_indicators.items():
            theme_score = sum(1 for indicator in indicators if indicator in text_lower)
            if theme_score > 0:
                themes.append({
                    'theme': theme,
                    'score': theme_score * 10,
                    'indicators': [ind for ind in indicators if ind in text_lower]
                })
        
        # Sort by score
        themes.sort(key=lambda x: x['score'], reverse=True)
        return themes
    
    async def create_research_profile(self, skills: List[Dict], research_areas: List[Dict], 
                                   expertise_levels: Dict, research_themes: List[Dict]) -> Dict[str, Any]:
        """
        Create comprehensive research profile
        """
        # Calculate overall research score
        research_score = await self.calculate_research_score(skills, research_areas, expertise_levels)
        
        # Identify primary research domains
        primary_domains = [area for area in research_areas if area.get('type') == 'primary_domain'][:3]
        
        # Extract technical competencies
        technical_competencies = [
            skill for skill in skills 
            if skill.get('category') in ['data_science', 'programming', 'research_methods']
        ]
        
        # Create research maturity assessment
        maturity = await self.assess_research_maturity(skills, research_areas, expertise_levels)
        
        return {
            "overall_score": research_score,
            "primary_domains": primary_domains,
            "technical_competencies": technical_competencies[:5],
            "research_themes": research_themes,
            "maturity_level": maturity,
            "skill_distribution": self.analyze_skill_distribution(skills),
            "research_focus": await self.identify_research_focus(research_areas, expertise_levels)
        }
    
    async def calculate_research_score(self, skills: List[Dict], research_areas: List[Dict], 
                                    expertise_levels: Dict) -> float:
        """
        Calculate overall research capability score
        """
        if not skills and not research_areas:
            return 0
        
        # Skill-based score
        research_skills = [s for s in skills if s.get('research_relevance', 0) > 5]
        skill_score = sum(s.get('research_relevance', 0) for s in research_skills) / len(research_skills) if research_skills else 0
        
        # Research area score
        area_score = len(research_areas) * 5
        
        # Expertise score
        expertise_scores = [exp.get('score', 0) for exp in expertise_levels.values()]
        expertise_score = sum(expertise_scores) / len(expertise_scores) if expertise_scores else 0
        
        # Combined score (weighted)
        total_score = (skill_score * 0.4) + (area_score * 0.3) + (expertise_score * 0.3)
        return min(total_score, 100)
    
    async def assess_research_maturity(self, skills: List[Dict], research_areas: List[Dict], 
                                     expertise_levels: Dict) -> str:
        """
        Assess research maturity level
        """
        research_skill_count = len([s for s in skills if s.get('research_relevance', 0) > 5])
        advanced_skills = len([exp for exp in expertise_levels.values() if exp.get('score', 0) >= 70])
        
        if research_skill_count >= 5 and advanced_skills >= 3 and len(research_areas) >= 2:
            return "established"
        elif research_skill_count >= 3 and advanced_skills >= 1 and len(research_areas) >= 1:
            return "developing"
        else:
            return "emerging"
    
    def analyze_skill_distribution(self, skills: List[Dict]) -> Dict[str, int]:
        """
        Analyze distribution of skills across categories
        """
        distribution = defaultdict(int)
        for skill in skills:
            category = skill.get('category', 'other')
            distribution[category] += 1
        return dict(distribution)
    
    async def identify_research_focus(self, research_areas: List[Dict], expertise_levels: Dict) -> str:
        """
        Identify primary research focus
        """
        if not research_areas:
            return "general"
        
        # Group by field
        field_counts = Counter(area.get('field', 'unknown') for area in research_areas)
        primary_field = field_counts.most_common(1)[0][0] if field_counts else "general"
        
        return primary_field
    
    def deduplicate_research_areas(self, areas: List[Dict]) -> List[Dict]:
        """
        Deduplicate research areas using fuzzy matching
        """
        unique_areas = {}
        
        for area in areas:
            area_name = area['name'].lower()
            found_duplicate = False
            
            for existing_name in unique_areas.keys():
                if fuzz.ratio(area_name, existing_name) > 85:
                    # Merge with existing area
                    existing = unique_areas[existing_name]
                    existing['confidence'] = max(existing['confidence'], area['confidence'])
                    if 'sources' not in existing:
                        existing['sources'] = []
                    existing['sources'].append(area.get('type', 'unknown'))
                    found_duplicate = True
                    break
            
            if not found_duplicate:
                unique_areas[area_name] = area
                unique_areas[area_name]['sources'] = [area.get('type', 'unknown')]
        
        return list(unique_areas.values())
    
    async def rank_research_areas(self, areas: List[Dict], text: str) -> List[Dict]:
        """
        Rank research areas by relevance and confidence
        """
        for area in areas:
            # Calculate relevance score
            relevance_score = area.get('confidence', 50)
            
            # Boost score based on frequency
            frequency = text.lower().count(area['name'].lower())
            relevance_score += min(frequency * 5, 20)
            
            # Boost for primary domains
            if area.get('type') == 'primary_domain':
                relevance_score += 10
            
            area['relevance_score'] = relevance_score
        
        # Sort by relevance score
        areas.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return areas
    
    def find_concept_in_text(self, concept: str, text: str) -> bool:
        """
        Find concept in text with word boundaries and variations
        """
        # Create pattern with word boundaries
        pattern = r'\b' + re.escape(concept.lower()) + r'\b'
        return bool(re.search(pattern, text))
    
    # Keep existing methods for backward compatibility
    async def extract(self, text: str) -> List[Dict[str, Any]]:
        """
        Original extract method for backward compatibility
        """
        # Use rule-based extraction from original implementation
        rule_based_skills = await self.extract_rule_based(text)
        
        # Use pattern matching from original implementation
        pattern_skills = await self.extract_pattern_based(text)
        
        # Combine and deduplicate
        all_skills = self.combine_skills(rule_based_skills, pattern_skills)
        
        # Calculate confidence scores
        skills_with_confidence = await self.calculate_confidence(all_skills, text)
        
        # Rank skills
        ranked_skills = self.rank_skills(skills_with_confidence)
        
        return ranked_skills
    
    async def extract_rule_based(self, text: str) -> List[Dict[str, Any]]:
        """
        Original rule-based extraction
        """
        extracted_skills = []
        text_lower = text.lower()
        
        for category, skills_dict in [
            ('technical', self.skill_database['technical_skills']),
            ('soft', self.skill_database['soft_skills'])
        ]:
            for skill_name, skill_info in skills_dict.items():
                if self.find_skill_in_text(skill_name, text_lower):
                    extracted_skills.append({
                        'name': skill_name,
                        'category': skill_info.get('category', category),
                        'type': category,
                        'research_relevance': skill_info.get('research_relevance', 0),
                        'matched_text': skill_name
                    })
                    continue
                
                for alias in skill_info.get('aliases', []):
                    if self.find_skill_in_text(alias, text_lower):
                        extracted_skills.append({
                            'name': skill_name,
                            'category': skill_info.get('category', category),
                            'type': category,
                            'research_relevance': skill_info.get('research_relevance', 0),
                            'matched_text': alias
                        })
                        break
        
        return extracted_skills
    
    def find_skill_in_text(self, skill: str, text: str) -> bool:
        """
        Original skill finding method
        """
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        return bool(re.search(pattern, text))
    
    async def extract_pattern_based(self, text: str) -> List[Dict[str, Any]]:
        """
        Original pattern-based extraction
        """
        skills = []
        
        skills_section_pattern = r'(?:skills|expertise|competencies|technologies)[:\s]*([^\n]+(?:\n[^\n]+)*)'
        matches = re.finditer(skills_section_pattern, text, re.IGNORECASE)
        
        for match in matches:
            skills_text = match.group(1)
            skill_items = re.split(r'[,;|•·\n]', skills_text)
            
            for item in skill_items:
                item = item.strip()
                if 2 < len(item) < 50:
                    skills.append({
                        'name': item,
                        'type': 'pattern_extracted',
                        'context': match.group(0)[:100]
                    })
        
        return skills
    
    def combine_skills(self, *skill_lists) -> List[Dict[str, Any]]:
        """
        Original skill combination method
        """
        combined = {}
        
        for skill_list in skill_lists:
            for skill in skill_list:
                skill_key = skill['name'].lower()
                
                found = False
                for existing_key in combined.keys():
                    if fuzz.ratio(skill_key, existing_key) > 85:
                        if 'sources' not in combined[existing_key]:
                            combined[existing_key]['sources'] = []
                        combined[existing_key]['sources'].append(skill.get('type', 'unknown'))
                        found = True
                        break
                
                if not found:
                    combined[skill_key] = skill
                    combined[skill_key]['sources'] = [skill.get('type', 'unknown')]
        
        return list(combined.values())
    
    async def calculate_confidence(self, skills: List[Dict], text: str) -> List[Dict]:
        """
        Original confidence calculation
        """
        text_lower = text.lower()
        
        for skill in skills:
            confidence = 60
            
            skill_lower = skill['name'].lower()
            frequency = text_lower.count(skill_lower)
            confidence += min(frequency * 5, 20)
            
            if 'sources' in skill:
                confidence += len(skill['sources']) * 10
            
            proficiency_terms = ['expert', 'advanced', 'proficient', 'experienced', 'skilled']
            for term in proficiency_terms:
                if f"{term} {skill_lower}" in text_lower or f"{skill_lower} {term}" in text_lower:
                    confidence += 15
                    break
            
            if re.search(rf'skills.*{re.escape(skill_lower)}', text_lower, re.DOTALL):
                confidence += 10
            
            skill['confidence'] = min(confidence, 95)
        
        return skills
    
    def rank_skills(self, skills: List[Dict]) -> List[Dict]:
        """
        Original skill ranking method
        """
        for skill in skills:
            importance = skill.get('confidence', 50)
            
            if skill.get('category') in ['programming', 'web', 'data_science', 'ai']:
                importance *= 1.2
            
            if skill['name'] in self.skill_database.get('technical_skills', {}):
                db_importance = self.skill_database['technical_skills'][skill['name']].get('importance', 5)
                importance += db_importance * 5
            
            skill['importance_score'] = importance
        
        skills.sort(key=lambda x: x.get('importance_score', 0), reverse=True)
        return skills
    
    def preprocess_text(self, text: str) -> str:
        """
        Original text preprocessing
        """
        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9\s+#]', ' ', text)
        text = ' '.join(text.split())
        return text