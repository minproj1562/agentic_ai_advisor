# app/services/skill_extractor.py
import json
import re
from typing import List, Dict, Any
from fuzzywuzzy import fuzz
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

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
        
        # Skill categories
        self.categories = {
            'programming': ['python', 'java', 'javascript', 'c++', 'ruby', 'go', 'rust'],
            'web': ['react', 'angular', 'vue', 'django', 'flask', 'node.js', 'express'],
            'data': ['pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'spark'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform'],
            'database': ['mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch'],
            'soft_skills': ['leadership', 'communication', 'teamwork', 'problem-solving']
        }
    
    def load_skill_database(self) -> Dict[str, Any]:
        """
        Load comprehensive skill database
        """
        # This would typically load from a database or file
        return {
            'technical_skills': {
                'Python': {'aliases': ['python3', 'py'], 'category': 'programming', 'importance': 10},
                'JavaScript': {'aliases': ['js', 'es6'], 'category': 'programming', 'importance': 9},
                'React': {'aliases': ['react.js', 'reactjs'], 'category': 'web', 'importance': 8},
                'Machine Learning': {'aliases': ['ml', 'machine-learning'], 'category': 'ai', 'importance': 9},
                'Docker': {'aliases': ['containerization'], 'category': 'devops', 'importance': 7},
                # Add more skills...
            },
            'soft_skills': {
                'Leadership': {'aliases': ['team lead', 'management'], 'importance': 8},
                'Communication': {'aliases': ['interpersonal'], 'importance': 9},
                # Add more soft skills...
            },
            'certifications': {
                'AWS Certified': {'aliases': ['aws certification'], 'importance': 8},
                'PMP': {'aliases': ['project management professional'], 'importance': 7},
                # Add more certifications...
            }
        }
    
    async def extract(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract skills from CV text using multiple methods
        """
        # Method 1: Rule-based extraction
        rule_based_skills = await self.extract_rule_based(text)
        
        # Method 2: ML-based extraction (if model available)
        ml_skills = await self.extract_ml_based(text) if self.model else []
        
        # Method 3: Pattern matching
        pattern_skills = await self.extract_pattern_based(text)
        
        # Combine and deduplicate
        all_skills = self.combine_skills(rule_based_skills, ml_skills, pattern_skills)
        
        # Calculate confidence scores
        skills_with_confidence = await self.calculate_confidence(all_skills, text)
        
        # Rank skills
        ranked_skills = self.rank_skills(skills_with_confidence)
        
        return ranked_skills
    
    async def extract_rule_based(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract skills using rule-based approach
        """
        extracted_skills = []
        text_lower = text.lower()
        
        for category, skills_dict in [
            ('technical', self.skill_database['technical_skills']),
            ('soft', self.skill_database['soft_skills'])
        ]:
            for skill_name, skill_info in skills_dict.items():
                # Check main skill name
                if self.find_skill_in_text(skill_name, text_lower):
                    extracted_skills.append({
                        'name': skill_name,
                        'category': skill_info.get('category', category),
                        'type': category,
                        'matched_text': skill_name
                    })
                    continue
                
                # Check aliases
                for alias in skill_info.get('aliases', []):
                    if self.find_skill_in_text(alias, text_lower):
                        extracted_skills.append({
                            'name': skill_name,
                            'category': skill_info.get('category', category),
                            'type': category,
                            'matched_text': alias
                        })
                        break
        
        return extracted_skills
    
    def find_skill_in_text(self, skill: str, text: str) -> bool:
        """
        Find skill in text with word boundaries
        """
        # Create pattern with word boundaries
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        return bool(re.search(pattern, text))
    
    async def extract_ml_based(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract skills using machine learning model
        """
        if not self.model or not self.vectorizer:
            return []
        
        # Preprocess text
        processed_text = self.preprocess_text(text)
        
        # Vectorize
        features = self.vectorizer.transform([processed_text])
        
        # Predict
        predictions = self.model.predict_proba(features)[0]
        
        # Get top skills
        skill_indices = np.where(predictions > 0.5)[0]
        
        skills = []
        for idx in skill_indices:
            skills.append({
                'name': self.model.classes_[idx],
                'confidence': float(predictions[idx]),
                'type': 'ml_predicted'
            })
        
        return skills
    
    async def extract_pattern_based(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract skills using regex patterns
        """
        skills = []
        
        # Pattern for skills section
        skills_section_pattern = r'(?:skills|expertise|competencies|technologies)[:\s]*([^\n]+(?:\n[^\n]+)*)'
        matches = re.finditer(skills_section_pattern, text, re.IGNORECASE)
        
        for match in matches:
            skills_text = match.group(1)
            # Split by common delimiters
            skill_items = re.split(r'[,;|•·\n]', skills_text)
            
            for item in skill_items:
                item = item.strip()
                if 2 < len(item) < 50:  # Reasonable skill name length
                    skills.append({
                        'name': item,
                        'type': 'pattern_extracted',
                        'context': match.group(0)[:100]
                    })
        
        return skills
    
    def combine_skills(self, *skill_lists) -> List[Dict[str, Any]]:
        """
        Combine and deduplicate skills from multiple sources
        """
        combined = {}
        
        for skill_list in skill_lists:
            for skill in skill_list:
                skill_key = skill['name'].lower()
                
                # Check for similar skills using fuzzy matching
                found = False
                for existing_key in combined.keys():
                    if fuzz.ratio(skill_key, existing_key) > 85:
                        # Merge information
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
        Calculate confidence scores for extracted skills
        """
        text_lower = text.lower()
        
        for skill in skills:
            confidence = 60  # Base confidence
            
            # Increase confidence based on frequency
            skill_lower = skill['name'].lower()
            frequency = text_lower.count(skill_lower)
            confidence += min(frequency * 5, 20)
            
            # Increase confidence if found in multiple sources
            if 'sources' in skill:
                confidence += len(skill['sources']) * 10
            
            # Check for proficiency indicators
            proficiency_terms = ['expert', 'advanced', 'proficient', 'experienced', 'skilled']
            for term in proficiency_terms:
                if f"{term} {skill_lower}" in text_lower or f"{skill_lower} {term}" in text_lower:
                    confidence += 15
                    break
            
            # Check if it's in a skills section
            if re.search(rf'skills.*{re.escape(skill_lower)}', text_lower, re.DOTALL):
                confidence += 10
            
            skill['confidence'] = min(confidence, 95)
        
        return skills
    
    def rank_skills(self, skills: List[Dict]) -> List[Dict]:
        """
        Rank skills by importance and confidence
        """
        for skill in skills:
            # Calculate importance score
            importance = skill.get('confidence', 50)
            
            # Boost technical skills
            if skill.get('category') in ['programming', 'web', 'data', 'ai']:
                importance *= 1.2
            
            # Boost if in skill database
            if skill['name'] in self.skill_database.get('technical_skills', {}):
                db_importance = self.skill_database['technical_skills'][skill['name']].get('importance', 5)
                importance += db_importance * 5
            
            skill['importance_score'] = importance
        
        # Sort by importance score
        skills.sort(key=lambda x: x.get('importance_score', 0), reverse=True)
        
        return skills
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text for ML model
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-zA-Z0-9\s+#]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text