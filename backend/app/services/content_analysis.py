import re
import nltk
from textblob import TextBlob
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

class ContentAnalyzer:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.reliable_keywords = [
            'research', 'study', 'data', 'evidence', 'analysis', 'report',
            'scientific', 'peer-reviewed', 'journal', 'publication', 'source',
            'citation', 'reference', 'methodology', 'results', 'conclusion',
            'statistics', 'survey', 'experiment', 'clinical', 'academic'
        ]
        
        self.unreliable_patterns = [
            r'\b(fake|hoax|scam|clickbait|unbelievable|shocking|miracle)\b',
            r'\b(\d+%\s*(off|discount|sale))\b',
            r'\b(urgent|act now|limited time|don\'t miss)\b',
            r'\b(conspiracy|theory|cover-up|secret)\b',
            r'\b(\w+!\s*){3,}',  # Multiple exclamation marks
        ]
    
    def analyze_content(self, content: str, author_reliability: float = 0.0) -> Dict:
        """Analyze content and return reliability score with breakdown"""
        
        # Basic content metrics
        word_count = len(content.split())
        sentence_count = len(sent_tokenize(content))
        
        # Sentiment analysis - DETERMINISTIC by rounding to 2 decimal places
        blob = TextBlob(content)
        sentiment_polarity = round(blob.sentiment.polarity, 2)  # FIX: Reduce precision variance
        sentiment_subjectivity = round(blob.sentiment.subjectivity, 2)  # FIX: Reduce precision variance
        
        # Readability score (simplified Flesch-Kincaid)
        avg_sentence_length = word_count / max(sentence_count, 1)
        syllable_count = sum(self._count_syllables(word) for word in content.split())
        avg_syllables_per_word = syllable_count / max(word_count, 1)
        readability_score = round(206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word), 2)  # FIX: Round for determinism
        
        # Keyword analysis
        reliable_keyword_score = self._analyze_reliable_keywords(content)
        unreliable_pattern_score = self._analyze_unreliable_patterns(content)
        
        # Structure analysis
        structure_score = self._analyze_structure(content)
        
        # Fact-checking indicators
        fact_check_score = self._analyze_fact_checking_indicators(content)
        
        # Calculate overall reliability score
        content_score = self._calculate_content_score(
            reliable_keyword_score,
            unreliable_pattern_score,
            structure_score,
            fact_check_score,
            sentiment_polarity,
            sentiment_subjectivity,
            readability_score
        )
        
        # Combine with author reliability
        final_score = (content_score * 0.7) + (author_reliability * 0.3)
        
        return {
            "reliability_score": round(max(0, min(100, final_score)), 2),  # FIX: Round for determinism
            "content_score": content_score,
            "author_reliability": author_reliability,
            "breakdown": {
                "reliable_keywords": round(reliable_keyword_score, 2),  # FIX: Round for determinism
                "unreliable_patterns": round(unreliable_pattern_score, 2),  # FIX: Round for determinism
                "structure": round(structure_score, 2),  # FIX: Round for determinism
                "fact_checking": round(fact_check_score, 2),  # FIX: Round for determinism
                "sentiment_polarity": sentiment_polarity,
                "sentiment_subjectivity": sentiment_subjectivity,
                "readability": readability_score,
                "word_count": word_count,
                "sentence_count": sentence_count
            },
            "recommendations": self._generate_recommendations(content_score, reliable_keyword_score, unreliable_pattern_score)
        }
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word"""
        word = word.lower()
        vowels = "aeiouy"
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            if char in vowels:
                if not prev_was_vowel:
                    syllable_count += 1
                prev_was_vowel = True
            else:
                prev_was_vowel = False
        
        if word.endswith("e"):
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def _analyze_reliable_keywords(self, content: str) -> float:
        """Analyze presence of reliable content keywords"""
        content_lower = content.lower()
        keyword_matches = sum(1 for keyword in self.reliable_keywords if keyword in content_lower)
        return min(100, (keyword_matches / len(self.reliable_keywords)) * 100)
    
    def _analyze_unreliable_patterns(self, content: str) -> float:
        """Analyze presence of unreliable content patterns"""
        score = 100
        for pattern in self.unreliable_patterns:
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            score -= matches * 20  # Each match reduces reliability
        return max(0, score)
    
    def _analyze_structure(self, content: str) -> float:
        """Analyze content structure for reliability indicators"""
        score = 50  # Base score
        
        # Check for proper capitalization
        if content and content[0].isupper():
            score += 10
        
        # Check for proper punctuation
        sentences = sent_tokenize(content)
        if len(sentences) > 1:
            score += 10
        
        # Check for paragraph structure
        paragraphs = content.split('\n\n')
        if len(paragraphs) > 1:
            score += 10
        
        # Check for citations/references
        if any(char in content for char in ['[', ']', '(', ')']):
            score += 10
        
        # Check for length (not too short, not too long)
        word_count = len(content.split())
        if 100 <= word_count <= 1000:
            score += 10
        elif 50 <= word_count < 100:
            score += 5
        
        return min(100, score)
    
    def _analyze_fact_checking_indicators(self, content: str) -> float:
        """Analyze indicators of fact-checking and verification"""
        score = 50  # Base score
        
        # Check for numbers and statistics
        if re.search(r'\b\d+(?:\.\d+)?%\b', content):
            score += 15
        
        # Check for dates
        if re.search(r'\b\d{4}\b', content):
            score += 10
        
        # Check for sources/references
        if any(word in content.lower() for word in ['according to', 'source', 'report', 'study']):
            score += 15
        
        # Check for balanced perspective
        if any(word in content.lower() for word in ['however', 'although', 'despite', 'nevertheless']):
            score += 10
        
        return min(100, score)
    
    def _calculate_content_score(self, reliable_keywords: float, unreliable_patterns: float,
                               structure: float, fact_checking: float, sentiment_polarity: float,
                               sentiment_subjectivity: float, readability: float) -> float:
        """Calculate overall content reliability score"""
        
        # Weight different factors
        weights = {
            'reliable_keywords': 0.2,
            'unreliable_patterns': 0.25,
            'structure': 0.15,
            'fact_checking': 0.2,
            'sentiment': 0.1,
            'readability': 0.1
        }
        
        # Sentiment score (moderate sentiment is better) - DETERMINISTIC
        sentiment_score = 100 - ((abs(sentiment_polarity) * 50) + (sentiment_subjectivity * 25))
        sentiment_score = max(0, min(100, round(sentiment_score, 2)))  # FIX: Clamp and round
        
        # Readability score (normalize to 0-100)
        readability_score = max(0, min(100, readability))
        
        # Calculate weighted average
        final_score = (
            reliable_keywords * weights['reliable_keywords'] +
            unreliable_patterns * weights['unreliable_patterns'] +
            structure * weights['structure'] +
            fact_checking * weights['fact_checking'] +
            sentiment_score * weights['sentiment'] +
            readability_score * weights['readability']
        )
        
        return round(final_score, 2)  # FIX: Round for determinism
    
    def _generate_recommendations(self, content_score: float, reliable_keywords: float, unreliable_patterns: float) -> List[str]:
        """Generate recommendations to improve content reliability"""
        recommendations = []
        
        if content_score < 60:
            recommendations.append("Consider adding more evidence and sources to support your claims")
        
        if reliable_keywords < 30:
            recommendations.append("Include more research-based content and references to studies")
        
        if unreliable_patterns < 70:
            recommendations.append("Avoid sensational language and clickbait phrases")
        
        if content_score < 50:
            recommendations.append("Provide more detailed analysis and balanced perspective")
        
        if not recommendations:
            recommendations.append("Content appears reliable and well-structured")
        
        return recommendations
