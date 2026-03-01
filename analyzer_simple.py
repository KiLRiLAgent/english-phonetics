#!/usr/bin/env python3
"""
Simple English Practice Analyzer
Version 3.0 - Simplified Architecture

Components:
1. Whisper - Raw transcription (as spoken, no corrections)
2. OpenAI API - Grammar check
3. Beautiful UI - Timeline with errors
"""

import os
import json
import whisper
import requests
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class SimpleAnalyzer:
    """Simplified English analyzer: Whisper + OpenAI only."""
    
    def __init__(self, whisper_model: str = "large-v3-turbo"):
        """Initialize analyzer."""
        self.whisper_model_name = whisper_model
        self.openai_key = os.getenv("OPENAI_API_KEY")
        
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY not set in .env")
        
        print(f"📥 Loading Whisper model: {whisper_model}...")
        self.whisper_model = whisper.load_model(whisper_model)
        print("✅ Whisper ready")
    
    def analyze(self, audio_path: str) -> Dict:
        """
        Analyze audio file.
        
        Returns:
            {
                "transcript": str,
                "words": [{"word": str, "start": float, "end": float}, ...],
                "errors": [{"text": str, "message": str, "timestamp": float, "severity": str}, ...],
                "score": int  # 0-100
            }
        """
        print(f"\n🎤 Analyzing: {audio_path}")
        
        # 1. Transcribe with Whisper
        print("🔊 Transcribing...")
        result = self.whisper_model.transcribe(
            audio_path,
            language="en",
            word_timestamps=True,
            condition_on_previous_text=True,
            initial_prompt="Business meeting discussion about analytics, projects, clients."
        )
        
        transcript = result["text"].strip()
        
        # Extract word-level timestamps
        words = []
        for segment in result.get("segments", []):
            for word_data in segment.get("words", []):
                words.append({
                    "word": word_data["word"].strip(),
                    "start": word_data["start"],
                    "end": word_data["end"]
                })
        
        print(f"📝 Transcript ({len(transcript)} chars, {len(words)} words)")
        
        # 2. Check grammar with OpenAI
        print("🤖 Checking grammar with OpenAI...")
        errors = self._check_grammar(transcript, words)
        
        # 3. Calculate score
        # Simple formula: 100 - (errors * 10), minimum 0
        score = max(0, 100 - len(errors) * 10)
        
        print(f"✅ Analysis complete: {len(errors)} errors, score {score}/100")
        
        return {
            "transcript": transcript,
            "words": words,
            "errors": errors,
            "score": score,
            "analyzed_at": datetime.now().isoformat()
        }
    
    def _check_grammar(self, transcript: str, words: List[Dict]) -> List[Dict]:
        """Check grammar using OpenAI API."""
        
        # Build prompt
        prompt = f"""You are a grammar checker for SPOKEN English.

Analyze this transcript and find REAL grammatical errors.

IGNORE (not errors):
- Informal speech (gonna, wanna, yeah, etc.)
- Filler words (um, uh, like, etc.)
- Incomplete sentences (normal in speech)
- Names and proper nouns
- Punctuation (speech has no punctuation)
- Capitalization

FIND (real errors):
- Subject-verb agreement ("he don't" → "he doesn't")
- Verb tense mistakes
- Article errors (a/an/the)
- Pronoun errors
- Word order problems

Transcript:
{transcript}

Return a JSON array of errors. Each error:
{{
  "text": "incorrect phrase",
  "correction": "correct phrase",
  "message": "brief explanation",
  "severity": "minor|moderate|major"
}}

If no errors found, return empty array: []

JSON only (no markdown):"""

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are a grammar checker. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "response_format": {"type": "json_object"}
                },
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"⚠️  OpenAI error {response.status_code}: {response.text}")
                return []
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Parse JSON response
            data = json.loads(content)
            errors_list = data.get("errors", []) if isinstance(data, dict) else data
            
            # Add timestamps to errors
            errors_with_timestamps = []
            for error in errors_list:
                # Find timestamp of error phrase in transcript
                timestamp = self._find_timestamp(error['text'], words)
                errors_with_timestamps.append({
                    **error,
                    "timestamp": timestamp
                })
            
            return errors_with_timestamps
        
        except Exception as e:
            print(f"⚠️  Grammar check failed: {e}")
            return []
    
    def _find_timestamp(self, phrase: str, words: List[Dict]) -> float:
        """Find timestamp of a phrase in word list."""
        phrase_lower = phrase.lower()
        phrase_words = phrase_lower.split()
        
        # Search for matching sequence
        for i in range(len(words) - len(phrase_words) + 1):
            window = " ".join([w["word"].lower() for w in words[i:i+len(phrase_words)]])
            if phrase_lower in window or window in phrase_lower:
                return words[i]["start"]
        
        # Fallback: search for first word
        for word in words:
            if phrase_words[0] in word["word"].lower():
                return word["start"]
        
        return 0.0
    
    def save_result(self, result: Dict, output_path: str):
        """Save analysis result to JSON."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved to: {output_path}")


def format_timestamp(seconds: float) -> str:
    """Convert seconds to MM:SS format."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


if __name__ == "__main__":
    # Test
    analyzer = SimpleAnalyzer()
    
    # Test file
    audio_file = "test_data/test_business_long.mp3"
    
    if os.path.exists(audio_file):
        result = analyzer.analyze(audio_file)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 ANALYSIS SUMMARY")
        print("="*60)
        print(f"Score: {result['score']}/100")
        print(f"Errors: {len(result['errors'])}")
        print(f"\nTranscript ({len(result['transcript'])} chars):")
        print(result['transcript'][:200] + "..." if len(result['transcript']) > 200 else result['transcript'])
        
        if result['errors']:
            print(f"\n❌ Errors found:")
            for i, err in enumerate(result['errors'], 1):
                print(f"\n{i}. [{format_timestamp(err['timestamp'])}] \"{err['text']}\"")
                print(f"   → \"{err['correction']}\"")
                print(f"   {err['message']} ({err['severity']})")
        
        # Save
        analyzer.save_result(result, "test_data/simple_result.json")
    else:
        print(f"❌ Test file not found: {audio_file}")
