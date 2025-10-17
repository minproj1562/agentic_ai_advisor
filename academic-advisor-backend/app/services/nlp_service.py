# app/services/nlp_service.py
import spacy
import nltk
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
from typing import Dict, List, Any
import re
from collections import Counter
import numpy as np

class NLPService:
    def __init__(self):
        # Load spaCy model
        self.nlp = spacy.load("en_core_web_sm")
        
        # Load transformers models
        self.ner_pipeline = pipeline(
            "ner",
            model="dslim/bert-base-NER",
            aggregation_strategy="simple"
        )
        
        self.summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn"
        )
        
        # Download NLTK data
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
        
    async def analyze(self, text: str) -> Dict[str, Any]:
        """
        Comprehensive NLP analysis of CV text
        """
        doc = self.nlp(text)
        
        # Extract entities
        entities = await self.extract_entities(text)
        
        # Extract key phrases
        key_phrases = await self.extract_key_phrases(doc)
        
        # Sentiment analysis
        sentiment = await self.analyze_sentiment(text)
        
        # Generate summary
        summary = await self.generate_summary(text)
        
        # Extract contact information
        contact_info = await self.extract_contact_info(text)
        
        # Extract dates and timeline
        timeline = await self.extract_timeline(doc)
        
        return {
            "entities": entities,
            "key_phrases": key_phrases,
            "sentiment": sentiment,
            "summary": summary,
            "contact_info": contact_info,
            "timeline": timeline,
            "statistics": {
                "word_count": len(doc),
                "sentence_count": len(list(doc.sents)),
                "avg_word_length": np.mean([len(token.text) for token in doc])
            }
        }
    
    async def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities using BERT NER
        """
        entities = self.ner_pipeline(text)
        
        # Group entities by type
        grouped = {}
        for entity in entities:
            entity_type = entity['entity_group']
            if entity_type not in grouped:
                grouped[entity_type] = []
            grouped[entity_type].append(entity['word'])
        
        return grouped
    
    async def extract_key_phrases(self, doc) -> List[str]:
        """
        Extract key phrases using statistical methods
        """
        # Extract noun phrases
        noun_phrases = [chunk.text for chunk in doc.noun_chunks]
        
        # Extract important bigrams and trigrams
        from nltk.collocations import BigramAssocMeasures, BigramCollocationFinder
        from nltk.collocations import TrigramAssocMeasures, TrigramCollocationFinder
        
        words = [token.text.lower() for token in doc if not token.is_stop and token.is_alpha]
        
        # Bigrams
        bigram_finder = BigramCollocationFinder.from_words(words)
        bigrams = bigram_finder.nbest(BigramAssocMeasures.likelihood_ratio, 10)
        
        # Trigrams
        trigram_finder = TrigramCollocationFinder.from_words(words)
        trigrams = trigram_finder.nbest(TrigramAssocMeasures.likelihood_ratio, 5)
        
        key_phrases = noun_phrases[:10]
        key_phrases.extend([' '.join(bigram) for bigram in bigrams])
        key_phrases.extend([' '.join(trigram) for trigram in trigrams])
        
        return list(set(key_phrases))
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment and tone of the CV
        """
        from textblob import TextBlob
        
        blob = TextBlob(text)
        
        return {
            "polarity": blob.sentiment.polarity,
            "subjectivity": blob.sentiment.subjectivity,
            "tone": self.determine_tone(blob.sentiment.polarity)
        }
    
    def determine_tone(self, polarity: float) -> str:
        """
        Determine tone based on polarity
        """
        if polarity > 0.5:
            return "very_positive"
        elif polarity > 0.1:
            return "positive"
        elif polarity < -0.5:
            return "very_negative"
        elif polarity < -0.1:
            return "negative"
        else:
            return "neutral"
    
    async def generate_summary(self, text: str) -> str:
        """
        Generate a summary of the CV
        """
        # Limit text length for summarization
        max_length = 1024
        if len(text) > max_length:
            text = text[:max_length]
        
        try:
            summary = self.summarizer(
                text,
                max_length=150,
                min_length=50,
                do_sample=False
            )
            return summary[0]['summary_text']
        except:
            # Fallback to simple extractive summarization
            sentences = text.split('.')[:3]
            return '. '.join(sentences)
    
    async def extract_contact_info(self, text: str) -> Dict[str, str]:
        """
        Extract contact information using regex
        """
        contact = {}
        
        # Email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact['email'] = emails[0]
        
        # Phone
        phone_pattern = r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}'
        phones = re.findall(phone_pattern, text)
        if phones:
            contact['phone'] = phones[0]
        
        # LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin = re.findall(linkedin_pattern, text)
        if linkedin:
            contact['linkedin'] = f"https://{linkedin[0]}"
        
        # GitHub
        github_pattern = r'github\.com/[\w-]+'
        github = re.findall(github_pattern, text)
        if github:
            contact['github'] = f"https://{github[0]}"
        
        return contact
    
    async def extract_timeline(self, doc) -> List[Dict[str, Any]]:
        """
        Extract dates and create timeline
        """
        timeline = []
        
        # Date patterns
        date_patterns = [
            r'\b(19|20)\d{2}\b',  # Years
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',  # Month Year
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # MM/DD/YYYY
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, doc.text)
            for match in matches:
                timeline.append({
                    "date": match.group(),
                    "position": match.start(),
                    "context": doc.text[max(0, match.start()-50):min(len(doc.text), match.end()+50)]
                })
        
        # Sort by position in document
        timeline.sort(key=lambda x: x['position'])
        
        return timeline