#!/usr/bin/env python3
"""
MVP English Speaking Practice Tool
Focus: Grammar + Fluency + Basic Pronunciation

Architecture:
- Whisper: Speech-to-text + WER
- LanguageTool: Grammar checking
- Gentle: Word timing + alignment
- Simple scoring: Word accuracy + Grammar + Fluency
"""

import os
import json
import whisper
import numpy as np
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import language_tool_python
from cambridge_grammar_rules import get_grammar_explanation


class EnglishPracticeAnalyzer:
    """
    Analyze spoken English for:
    1. Grammar correctness
    2. Fluency (WPM, pauses)
    3. Pronunciation (word accuracy)
    """
    
    def __init__(self):
        """Initialize analyzer with Whisper + LanguageTool."""
        print("Loading Whisper model...")
        self.whisper_model = whisper.load_model(os.getenv("WHISPER_MODEL", "base"))
        print("✅ Whisper loaded")
        
        print("Loading LanguageTool...")
        self.grammar_tool = language_tool_python.LanguageTool('en-US')
        print("✅ LanguageTool loaded")
    
    def analyze(self, audio_path: str, reference_text: str = None) -> Dict:
        """
        Full analysis pipeline.
        
        Args:
            audio_path: Path to audio file
            reference_text: Optional reference text (for reading practice)
        
        Returns:
            {
                "transcript": "what I said",
                "grammar": {
                    "errors": [...],
                    "score": 85,
                    "total_errors": 2
                },
                "fluency": {
                    "wpm": 120,
                    "duration": 5.5,
                    "avg_pause": 0.3
                },
                "pronunciation": {
                    "wer": 0.05,  # Word Error Rate
                    "word_accuracy": 95,
                    "mispronounced_words": [...]
                },
                "overall_score": 88
            }
        """
        # 1. Transcribe with Whisper
        result = self.whisper_model.transcribe(str(audio_path), language='en')
        transcript = result['text'].strip()
        segments = result.get('segments', [])
        
        # 2. Grammar analysis
        grammar_result = self._analyze_grammar(transcript)
        
        # 3. Fluency metrics
        fluency_result = self._analyze_fluency(segments, result)
        
        # 4. Pronunciation (if reference provided)
        if reference_text:
            pronunciation_result = self._analyze_pronunciation(
                transcript, 
                reference_text,
                segments
            )
        else:
            pronunciation_result = {
                "wer": 0,
                "word_accuracy": 100,
                "mispronounced_words": [],
                "note": "No reference text provided"
            }
        
        # 5. Overall score
        overall = self._calculate_overall_score(
            grammar_result,
            fluency_result,
            pronunciation_result
        )
        
        return {
            "transcript": transcript,
            "reference": reference_text,
            "grammar": grammar_result,
            "fluency": fluency_result,
            "pronunciation": pronunciation_result,
            "overall_score": overall,
            "analyzed_at": datetime.now().isoformat()
        }
    
    def _analyze_grammar(self, text: str) -> Dict:
        """Analyze grammar errors using LanguageTool."""
        matches = self.grammar_tool.check(text)
        
        # Filter out punctuation/typography (irrelevant for speech)
        SKIP_CATEGORIES = {"PUNCTUATION", "TYPOGRAPHY", "CASING", "WHITESPACE"}
        relevant_matches = [m for m in matches if m.category not in SKIP_CATEGORIES]
        
        errors = []
        for match in relevant_matches:
            # Get Cambridge Grammar explanation
            cambridge = get_grammar_explanation(match.rule_id)
            
            errors.append({
                "message": match.message,
                "offset": match.offset,
                "length": match.error_length,
                "replacements": match.replacements[:3],
                "category": match.category,
                "rule": match.rule_id,
                "severity": "error" if "GRAMMAR" in match.category else "warning",
                "context": match.context,
                "incorrect_text": match.matched_text,
                # Cambridge Grammar info
                "cambridge": {
                    "title": cambridge["title"],
                    "explanation": cambridge["explanation"],
                    "examples": cambridge["examples"],
                    "unit": cambridge["cambridge_unit"],
                    "book": cambridge["book"],
                    "level": cambridge["difficulty"]
                }
            })
        
        # Grammar score (0-100)
        # Penalize based on error count and severity
        error_penalty = len([e for e in errors if e['severity'] == 'error']) * 10
        warning_penalty = len([e for e in errors if e['severity'] == 'warning']) * 5
        
        score = max(0, 100 - error_penalty - warning_penalty)
        
        return {
            "score": score,
            "total_errors": len(errors),
            "errors": errors,
            "categories": {cat: len([e for e in errors if e['category'] == cat]) 
                          for cat in set(e['category'] for e in errors)}
        }
    
    def _analyze_fluency(self, segments: List, whisper_result: Dict) -> Dict:
        """Calculate fluency metrics."""
        if not segments:
            return {
                "wpm": 0,
                "duration": 0,
                "avg_pause": 0,
                "pause_count": 0
            }
        
        # Duration
        duration = segments[-1]['end'] - segments[0]['start']
        
        # Word count
        words = whisper_result['text'].split()
        word_count = len(words)
        
        # WPM (words per minute)
        wpm = (word_count / duration * 60) if duration > 0 else 0
        
        # Pauses (gaps between segments)
        pauses = []
        for i in range(len(segments) - 1):
            gap = segments[i+1]['start'] - segments[i]['end']
            if gap > 0.1:  # Pause > 100ms
                pauses.append(gap)
        
        avg_pause = np.mean(pauses) if pauses else 0
        
        return {
            "wpm": round(wpm, 1),
            "duration": round(duration, 2),
            "word_count": word_count,
            "avg_pause": round(avg_pause, 2),
            "pause_count": len(pauses),
            "pauses": [round(p, 2) for p in pauses]
        }
    
    def _analyze_pronunciation(self, transcript: str, reference: str, segments: List) -> Dict:
        """
        Compare transcript with reference text.
        Calculate WER (Word Error Rate).
        """
        # Normalize texts
        trans_words = transcript.lower().split()
        ref_words = reference.lower().split()
        
        # Simple WER calculation (Levenshtein distance at word level)
        wer = self._calculate_wer(ref_words, trans_words)
        
        # Find mispronounced words (words in reference but not in transcript)
        mispronounced = []
        trans_set = set(trans_words)
        
        for i, word in enumerate(ref_words):
            if word not in trans_set:
                mispronounced.append({
                    "word": word,
                    "position": i,
                    "context": ' '.join(ref_words[max(0, i-2):min(len(ref_words), i+3)])
                })
        
        word_accuracy = max(0, 100 - wer * 100)
        
        return {
            "wer": round(wer, 3),
            "word_accuracy": round(word_accuracy, 1),
            "mispronounced_words": mispronounced,
            "transcript_words": len(trans_words),
            "reference_words": len(ref_words)
        }
    
    def _calculate_wer(self, reference: List[str], hypothesis: List[str]) -> float:
        """Calculate Word Error Rate using Levenshtein distance."""
        # Dynamic programming for edit distance
        d = np.zeros((len(reference) + 1, len(hypothesis) + 1))
        
        for i in range(len(reference) + 1):
            d[i][0] = i
        for j in range(len(hypothesis) + 1):
            d[0][j] = j
        
        for i in range(1, len(reference) + 1):
            for j in range(1, len(hypothesis) + 1):
                if reference[i-1] == hypothesis[j-1]:
                    d[i][j] = d[i-1][j-1]
                else:
                    substitution = d[i-1][j-1] + 1
                    insertion = d[i][j-1] + 1
                    deletion = d[i-1][j] + 1
                    d[i][j] = min(substitution, insertion, deletion)
        
        wer = d[len(reference)][len(hypothesis)] / len(reference) if reference else 0
        return wer
    
    def _calculate_overall_score(self, grammar: Dict, fluency: Dict, pronunciation: Dict) -> int:
        """
        Calculate overall score (0-100).
        
        Weights:
        - Grammar: 40%
        - Pronunciation: 35%
        - Fluency: 25%
        """
        grammar_score = grammar['score']
        pronunciation_score = pronunciation['word_accuracy']
        
        # Fluency score based on WPM
        # Optimal: 120-150 WPM for clear speech
        wpm = fluency['wpm']
        if 120 <= wpm <= 150:
            fluency_score = 100
        elif 100 <= wpm < 120 or 150 < wpm <= 180:
            fluency_score = 80
        elif 80 <= wpm < 100 or 180 < wpm <= 200:
            fluency_score = 60
        else:
            fluency_score = 40
        
        overall = (
            grammar_score * 0.4 +
            pronunciation_score * 0.35 +
            fluency_score * 0.25
        )
        
        return round(overall)


def format_report(result: Dict) -> str:
    """Format analysis result as human-readable report."""
    report = []
    report.append("=" * 60)
    report.append("ENGLISH SPEAKING PRACTICE ANALYSIS")
    report.append("=" * 60)
    report.append("")
    
    # Overall
    report.append(f"📊 Overall Score: {result['overall_score']}/100")
    report.append("")
    
    # Transcript
    report.append(f"📝 You said: \"{result['transcript']}\"")
    if result['reference']:
        report.append(f"📖 Reference: \"{result['reference']}\"")
    report.append("")
    
    # Grammar
    grammar = result['grammar']
    report.append(f"📚 GRAMMAR: {grammar['score']}/100")
    if grammar['total_errors'] == 0:
        report.append("   ✅ No grammar errors detected!")
    else:
        report.append(f"   ❌ {grammar['total_errors']} error(s) found:")
        for i, err in enumerate(grammar['errors'][:5], 1):  # Show max 5
            report.append(f"\n   {i}. {err['severity'].upper()}: {err['message']}")
            report.append(f"      Incorrect: '{err['incorrect_text']}'")
            if err['replacements']:
                report.append(f"      ✏️  Correct: {', '.join(err['replacements'])}")
            
            # Cambridge Grammar explanation
            cambridge = err.get('cambridge', {})
            if cambridge:
                report.append(f"\n      📖 {cambridge.get('title', '')}")
                report.append(f"      💡 {cambridge.get('explanation', '')}")
                if cambridge.get('examples'):
                    report.append(f"      Examples: {cambridge['examples'][0]}")
                report.append(f"      📕 {cambridge.get('book', '')} - {cambridge.get('unit', '')}")
                report.append(f"      🎯 Level: {cambridge.get('level', '')}")
    report.append("")
    
    # Fluency
    fluency = result['fluency']
    report.append(f"🎤 FLUENCY:")
    report.append(f"   Speed: {fluency['wpm']} WPM (words per minute)")
    report.append(f"   Duration: {fluency['duration']}s")
    report.append(f"   Pauses: {fluency['pause_count']} (avg {fluency['avg_pause']}s)")
    report.append("")
    
    # Pronunciation
    pronunciation = result['pronunciation']
    report.append(f"🗣️  PRONUNCIATION: {pronunciation['word_accuracy']}/100")
    report.append(f"   Word Error Rate: {pronunciation['wer']*100:.1f}%")
    if pronunciation['mispronounced_words']:
        report.append(f"   ❌ Mispronounced words:")
        for word in pronunciation['mispronounced_words'][:5]:
            report.append(f"      - '{word['word']}'")
    else:
        report.append("   ✅ All words recognized correctly!")
    
    report.append("")
    report.append("=" * 60)
    
    return "\n".join(report)


if __name__ == "__main__":
    # Test
    analyzer = EnglishPracticeAnalyzer()
    
    # Test with your voice recordings
    test_audio = "test_data/kirill_normal.wav"
    reference = "Don't you tell me what to do"
    
    if Path(test_audio).exists():
        print(f"\nAnalyzing: {test_audio}\n")
        result = analyzer.analyze(test_audio, reference)
        print(format_report(result))
        
        # Save JSON
        output_file = "test_data/analysis_result.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n📁 Full result saved to: {output_file}")
    else:
        print(f"Test file not found: {test_audio}")
