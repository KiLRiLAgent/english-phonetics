#!/usr/bin/env python3
"""
GECToR: Grammatical Error Correction using Transformers
ML-based error detection as fallback for LanguageTool misses.

Model: grammarly/coedit-large (CoEdIT)
- Trained on CoNLL-2014, BEA-2019
- Can fix grammar, spelling, fluency
- ~800MB model size
"""

import os
from typing import List, Dict, Optional
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch


class GECToRChecker:
    """
    GECToR checker using CoEdIT model from Grammarly.
    Detects and corrects grammatical errors using ML.
    """
    
    def __init__(self, model_name: str = "grammarly/coedit-large"):
        """
        Initialize GECToR checker.
        
        Args:
            model_name: HuggingFace model name (default: grammarly/coedit-large)
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = "cpu"  # Use GPU if available
        
        if torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"  # Apple Silicon
        
        print(f"GECToR: Using device: {self.device}")
    
    def load_model(self):
        """Load model (lazy loading to save startup time)."""
        if self.model is None:
            print(f"Loading GECToR model: {self.model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            print("✅ GECToR model loaded")
    
    def correct(self, text: str) -> str:
        """
        Correct grammatical errors in text.
        
        Args:
            text: Input text
        
        Returns:
            Corrected text
        """
        self.load_model()
        
        # CoEdIT uses specific prompt format
        prompt = f"Fix grammar: {text}"
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=256,
                num_beams=4,
                early_stopping=True
            )
        
        corrected = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return corrected
    
    def find_errors(self, text: str) -> List[Dict]:
        """
        Find errors by comparing original with corrected text.
        
        Args:
            text: Input text
        
        Returns:
            List of error dicts
        """
        corrected = self.correct(text)
        
        # If no changes, no errors
        if text.strip() == corrected.strip():
            return []
        
        # Simple word-level diff
        original_words = text.split()
        corrected_words = corrected.split()
        
        errors = []
        
        # Find differences
        for i, (orig, corr) in enumerate(zip(original_words, corrected_words)):
            if orig != corr:
                errors.append({
                    'position': i,
                    'original': orig,
                    'corrected': corr,
                    'type': 'ML_CORRECTION',
                    'message': f"ML model suggests: '{orig}' → '{corr}'",
                    'rule_id': 'GECTOR_ML',
                    'category': 'GRAMMAR',
                    'replacements': [corr]
                })
        
        # Handle length mismatch (insertions/deletions)
        if len(original_words) != len(corrected_words):
            errors.append({
                'position': 0,
                'original': text,
                'corrected': corrected,
                'type': 'ML_FULL_CORRECTION',
                'message': f"ML model suggests corrections",
                'rule_id': 'GECTOR_ML_FULL',
                'category': 'GRAMMAR',
                'replacements': [corrected]
            })
        
        return errors
    
    def check_if_missed(self, text: str, known_errors: List[Dict]) -> List[Dict]:
        """
        Check if GECToR finds errors that LanguageTool missed.
        
        Args:
            text: Original text
            known_errors: Errors already found by LanguageTool
        
        Returns:
            Additional errors found by GECToR
        """
        corrected = self.correct(text)
        
        # If GECToR made changes, there might be missed errors
        if text.strip() != corrected.strip():
            # Get all GECToR errors
            ml_errors = self.find_errors(text)
            
            # Filter out errors already found by LanguageTool
            known_texts = {err.get('matched_text', err.get('incorrect_text', '')) 
                          for err in known_errors}
            
            new_errors = []
            for ml_err in ml_errors:
                if ml_err['original'] not in known_texts:
                    new_errors.append(ml_err)
            
            return new_errors
        
        return []


# Test
if __name__ == "__main__":
    checker = GECToRChecker()
    
    test_sentences = [
        "Yesterday I go to school",           # LanguageTool misses this
        "She don't like apples",              # LanguageTool catches this
        "I have went to the store",           # LanguageTool catches
        "I'm good in math",                   # LanguageTool catches
        "Between you and I",                  # LanguageTool catches
    ]
    
    print("Testing GECToR on common errors:\n")
    
    for text in test_sentences:
        print(f"Original:  {text}")
        corrected = checker.correct(text)
        print(f"Corrected: {corrected}")
        
        if text != corrected:
            print("✅ GECToR found error!")
        else:
            print("⚠️  No changes")
        
        print()
