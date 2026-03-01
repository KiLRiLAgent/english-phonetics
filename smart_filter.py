#!/usr/bin/env python3
"""
Smart Grammar Error Filter
Filters false positives using Named Entity Recognition (NER)
"""

import re
from typing import List, Dict, Set

class SmartGrammarFilter:
    """Filter false positives using NER and heuristics."""
    
    def __init__(self):
        """Initialize filter with NER model."""
        self.nlp = None
        self._load_ner()
    
    def _load_ner(self):
        """Lazy load spaCy NER model."""
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            print("✅ NER model loaded (spaCy)")
        except (ImportError, OSError, Exception) as e:
            print(f"⚠️  NER model not available, using heuristics only")
            self.nlp = None
    
    def extract_entities(self, text: str) -> Set[str]:
        """
        Extract named entities from text.
        
        Returns:
            Set of entity texts (PERSON, ORG, PRODUCT, GPE)
        """
        if not self.nlp:
            return set()
        
        doc = self.nlp(text)
        entities = set()
        
        for ent in doc.ents:
            # Include: people, organizations, products, places
            if ent.label_ in {"PERSON", "ORG", "PRODUCT", "GPE", "NORP"}:
                # Add both original and lowercase
                entities.add(ent.text)
                entities.add(ent.text.lower())
        
        return entities
    
    def is_likely_proper_noun(self, word: str, context: str) -> bool:
        """
        Check if word is likely a proper noun (name/company).
        
        Uses heuristics:
        - Capitalized mid-sentence
        - Multiple capitals (camelCase)
        - Preceded by title (Mr., Dr., etc.)
        - Short and all caps (acronym)
        - Unusual letter combinations (foreign names)
        """
        # Capitalized and not at sentence start
        if word and word[0].isupper() and not self._is_sentence_start(word, context):
            # Exception: common words that should be lowercase
            common_lowercase = {"I", "A", "The", "And", "Or", "But", "In", "On", "At", "To", "For"}
            if word not in common_lowercase:
                return True
        
        # Multiple capitals (RedRoll, iPhone, etc.)
        if len([c for c in word if c.isupper()]) >= 2:
            return True
        
        # Preceded by title
        if re.search(r'\b(Mr|Mrs|Ms|Dr|Prof|Sir|Lady)\.?\s+' + re.escape(word), context, re.IGNORECASE):
            return True
        
        # Short all-caps (acronym/abbreviation)
        if len(word) <= 5 and word.isupper():
            return True
        
        # Foreign/unusual names (contains unusual letter combos)
        unusual_patterns = [
            r'[jqxz]{2}',  # Double j, q, x, z (Matej, etc.)
            r'[aeiouy]{3}',  # Triple vowel
            r'^[A-Z][a-z]+[A-Z]',  # CamelCase
        ]
        for pattern in unusual_patterns:
            if re.search(pattern, word):
                return True
        
        return False
    
    def _is_sentence_start(self, word: str, context: str) -> bool:
        """Check if word is at sentence start."""
        # Find word position in context
        idx = context.find(word)
        if idx == -1:
            return False
        
        # Check what's before
        before = context[:idx].strip()
        
        # Empty or ends with sentence terminator
        return not before or before[-1] in '.!?'
    
    def filter_errors(self, errors: List[Dict], text: str) -> List[Dict]:
        """
        Filter false positives from grammar errors.
        
        Args:
            errors: List of grammar errors from LanguageTool
            text: Full transcript text
        
        Returns:
            Filtered list without false positives
        """
        # Extract named entities from full text
        entities = self.extract_entities(text)
        
        filtered = []
        
        for error in errors:
            # Get error details
            category = error.get('category', '')
            incorrect = error.get('incorrect_text', '')
            context = error.get('context', '')
            
            # Skip if TYPOS and word is a named entity
            if category == 'TYPOS':
                # Check if it's in NER entities
                if incorrect in entities or incorrect.lower() in entities:
                    continue  # Skip: likely a name/company
                
                # Check if it's a proper noun by heuristics
                if self.is_likely_proper_noun(incorrect, context):
                    continue  # Skip: likely a name/company
            
            # Keep error
            filtered.append(error)
        
        return filtered
