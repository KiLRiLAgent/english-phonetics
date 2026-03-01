#!/usr/bin/env python3
"""
AI Grammar Filter
Uses local LLM (Ollama) or API to filter false positives and verify grammar errors
"""

import json
import subprocess
import os
from typing import List, Dict, Optional
import requests

class AIGrammarFilter:
    """Filter grammar errors using AI (local Ollama or API)."""
    
    def __init__(self, model: str = "gpt-4o-mini", use_local: bool = False):
        """
        Initialize AI filter.
        
        Args:
            model: Model name (OpenAI: gpt-4o-mini, gpt-4o, or Ollama: qwen2.5:7b)
            use_local: Use local Ollama (True) or OpenAI API (False)
        """
        self.model = model
        self.use_local = use_local
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if AI service is available."""
        if not self.use_local:
            # OpenAI API: check if key exists
            if self.openai_api_key and len(self.openai_api_key) > 20:
                print(f"✅ OpenAI API ready (model: {self.model})")
                return True
            else:
                print("⚠️  OPENAI_API_KEY not found")
                return False
        
        # Local Ollama
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Check if model is downloaded
            return self.model in result.stdout
        except Exception as e:
            print(f"⚠️  Ollama not available: {e}")
            return False
    
    def filter_errors(self, errors: List[Dict], transcript: str) -> List[Dict]:
        """
        Filter false positives using AI.
        
        Args:
            errors: List of potential errors from LanguageTool
            transcript: Full transcript text
        
        Returns:
            Filtered list with only real errors
        """
        if not self.available or len(errors) == 0:
            return errors
        
        # Build prompt
        prompt = self._build_prompt(errors, transcript)
        
        # Get AI response
        try:
            if self.use_local:
                response = self._query_ollama(prompt)
            else:
                response = self._query_api(prompt)
            
            # Parse response
            filtered = self._parse_response(response, errors)
            
            print(f"🤖 AI filtered: {len(errors)} → {len(filtered)} errors")
            return filtered
        
        except Exception as e:
            print(f"⚠️  AI filter failed: {e}")
            return errors  # Return original on error
    
    def _build_prompt(self, errors: List[Dict], transcript: str) -> str:
        """Build prompt for AI."""
        # Format errors for AI review
        errors_text = "\n".join([
            f"{i+1}. \"{e['incorrect_text']}\" → \"{e.get('replacements', ['?'])[0]}\""
            f" ({e['category']}) - {e['message']}"
            for i, e in enumerate(errors)
        ])
        
        prompt = f"""You are a grammar checker for SPOKEN English transcripts.

Review these potential errors found by LanguageTool.
Filter out FALSE POSITIVES (not real errors).

IGNORE (false positives):
- Names and proper nouns (Matej, Glennie, RedRoll, etc.)
- Technical terms and jargon (subreddits, analytics, API, etc.)
- Punctuation issues (speech doesn't have punctuation)
- Capitalization (irrelevant in speech)
- Informal style (gonna, wanna - acceptable in speech)
- Transcription artifacts (Whisper mistakes)

KEEP (real errors):
- Subject-verb agreement ("client do" → "client does")
- Incorrect verb tenses
- Article mistakes (a/an/the)
- Real grammatical errors that affect meaning

Potential errors found:
{errors_text}

Transcript context (first 500 chars):
{transcript[:500]}...

Return ONLY the error numbers that are REAL grammatical errors (comma-separated).
Examples:
- "1,3,6" if errors 1, 3, 6 are real
- "none" if all are false positives
- "all" if all are real errors

Your answer (numbers only):"""
        
        return prompt
    
    def _query_ollama(self, prompt: str) -> str:
        """Query local Ollama model."""
        try:
            result = subprocess.run(
                ["ollama", "run", self.model, prompt],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            print("⚠️  Ollama query timeout")
            return ""
        except Exception as e:
            print(f"⚠️  Ollama error: {e}")
            return ""
    
    def _query_api(self, prompt: str) -> str:
        """Query OpenAI API."""
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a grammar checker for spoken English. Filter false positives."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 100
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                print(f"⚠️  OpenAI API error: {response.status_code}")
                return ""
                
        except Exception as e:
            print(f"⚠️  OpenAI query failed: {e}")
            return ""
    
    def _parse_response(self, response: str, original_errors: List[Dict]) -> List[Dict]:
        """Parse AI response and filter errors."""
        response = response.strip().lower()
        
        # Handle special cases
        if "none" in response:
            return []  # No real errors
        
        if "all" in response:
            return original_errors  # All are real
        
        # Parse error numbers
        try:
            # Extract numbers (1,3,6 → [1,3,6])
            import re
            numbers = re.findall(r'\d+', response)
            indices = [int(n) - 1 for n in numbers]  # Convert to 0-based
            
            # Filter errors by index
            filtered = [original_errors[i] for i in indices 
                       if 0 <= i < len(original_errors)]
            
            return filtered
        
        except Exception as e:
            print(f"⚠️  Failed to parse AI response: {e}")
            return original_errors  # Return all on parse error


def download_model(model: str = "qwen2.5:7b"):
    """Download Ollama model in background."""
    print(f"📥 Downloading {model}...")
    try:
        subprocess.Popen(
            ["ollama", "pull", model],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"✅ Download started in background")
    except Exception as e:
        print(f"❌ Failed to start download: {e}")


if __name__ == "__main__":
    # Test
    filter = AIGrammarFilter()
    
    if not filter.available:
        print("Model not available. Downloading...")
        download_model()
    else:
        print("✅ AI filter ready")
