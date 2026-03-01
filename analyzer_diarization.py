#!/usr/bin/env python3
"""
MVP English Speaking Practice Tool with Speaker Diarization
Focus: Grammar + Fluency + Pronunciation + Multi-speaker support

New features:
- Speaker diarization (pyannote.audio) - identify who speaks when
- Timestamps for each grammar error
- Summary + Top-3 errors + Timeline format
- Analyze only target speaker (ignore others)
"""

import os
import json
import whisper
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import language_tool_python
from cambridge_grammar_rules import get_grammar_explanation
from custom_grammar_rules import CustomGrammarChecker
from smart_filter import SmartGrammarFilter
from ai_grammar_filter import AIGrammarFilter
from dotenv import load_dotenv

# Optional: GECToR ML checker (lazy load)
try:
    from gector_checker import GECToRChecker
    GECTOR_AVAILABLE = True
except ImportError:
    GECTOR_AVAILABLE = False

# Load environment variables
load_dotenv()


class EnglishPracticeAnalyzerDiarization:
    """
    Analyze spoken English with speaker separation.
    
    Features:
    1. Grammar correctness
    2. Fluency (WPM, pauses)
    3. Pronunciation (word accuracy)
    4. Speaker diarization (who speaks when)
    5. Timestamps for all errors
    """
    
    def __init__(self):
        """Initialize analyzer with Whisper + LanguageTool + Pyannote."""
        print("Loading Whisper model...")
        self.whisper_model = whisper.load_model(os.getenv("WHISPER_MODEL", "base"))
        print("✅ Whisper loaded")
        
        print("Loading LanguageTool...")
        self.grammar_tool = language_tool_python.LanguageTool('en-US')
        self.custom_grammar = CustomGrammarChecker()
        self.smart_filter = SmartGrammarFilter()
        
        # AI filter (OpenAI API by default)
        use_ai = os.getenv("USE_AI_FILTER", "true").lower() == "true"
        ai_model = os.getenv("AI_MODEL", "gpt-4o-mini")  # gpt-4o-mini or gpt-4o
        self.ai_filter = AIGrammarFilter(model=ai_model, use_local=False) if use_ai else None
        
        print("✅ LanguageTool loaded")
        
        # Lazy load GECToR ML checker
        self.gector = None
        self.use_ml = os.getenv("USE_ML_CHECKER", "true").lower() == "true"
        
        if self.use_ml and GECTOR_AVAILABLE:
            print("GECToR ML checker: enabled (will load on first use)")
        elif self.use_ml and not GECTOR_AVAILABLE:
            print("⚠️  GECToR not available (install: pip install transformers torch)")
            self.use_ml = False
        
        # Lazy load diarization pipeline (requires HF token)
        self.diarization_pipeline = None
    
    def _load_diarization(self):
        """Load speaker diarization pipeline (lazy)."""
        if self.diarization_pipeline is not None:
            return
        
        print("Loading speaker diarization pipeline...")
        try:
            from pyannote.audio import Pipeline
            
            hf_token = os.getenv("HUGGINGFACE_TOKEN")
            if not hf_token:
                raise ValueError(
                    "HUGGINGFACE_TOKEN not found in .env!\n"
                    "See GET_HUGGINGFACE_TOKEN.md for instructions."
                )
            
            self.diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=hf_token
            )
            print("✅ Speaker diarization loaded")
        except Exception as e:
            print(f"⚠️  Speaker diarization failed: {e}")
            print("Continuing without speaker separation...")
            self.diarization_pipeline = None
    
    def analyze(
        self, 
        audio_path: str, 
        reference_text: str = None,
        target_speaker: int = None,
        enable_diarization: bool = True
    ) -> Dict:
        """
        Full analysis pipeline with speaker diarization.
        
        Args:
            audio_path: Path to audio file
            reference_text: Optional reference text (for reading practice)
            target_speaker: Speaker to analyze (0, 1, 2...). If None, analyze all.
            enable_diarization: Enable speaker separation
        
        Returns:
            {
                "transcript": "what I said",
                "speakers": {
                    "total": 2,
                    "segments": [
                        {"speaker": 0, "start": 0.5, "end": 5.2, "text": "..."},
                        {"speaker": 1, "start": 5.5, "end": 10.1, "text": "..."}
                    ]
                },
                "grammar": {
                    "errors": [
                        {
                            "timestamp": 3.2,
                            "message": "...",
                            "severity": "error",
                            ...
                        }
                    ],
                    "score": 85,
                    "total_errors": 2
                },
                "fluency": {...},
                "pronunciation": {...},
                "overall_score": 88,
                "summary": {
                    "duration": 15.5,
                    "speaking_time": 8.2,
                    "speaking_percentage": 53
                }
            }
        """
        # 1. Speaker diarization (if enabled)
        speaker_segments = []
        if enable_diarization:
            self._load_diarization()
            if self.diarization_pipeline:
                speaker_segments = self._diarize_speakers(audio_path)
        
        # 2. Transcribe with Whisper (with word-level timestamps)
        # Use initial_prompt for better proper noun recognition
        initial_prompt = (
            "This is a business meeting or presentation. "
            "Common names: Matt, Matej, Josh, Devin, Alex, Sarah, Mike, Tom. "
            "Common companies: Google, Reddit, Slack, Analytics."
        )
        
        result = self.whisper_model.transcribe(
            str(audio_path), 
            language='en',
            word_timestamps=True,
            condition_on_previous_text=True,  # For long audio files
            initial_prompt=initial_prompt  # Context for better name recognition
        )
        transcript = result['text'].strip()
        segments = result.get('segments', [])
        
        # 3. Map words to speakers
        if speaker_segments:
            segments_with_speakers = self._map_speakers_to_words(segments, speaker_segments)
        else:
            # No diarization - assume single speaker
            segments_with_speakers = segments
            for seg in segments_with_speakers:
                seg['speaker'] = 0
        
        # 4. Filter by target speaker (if specified)
        if target_speaker is not None:
            filtered_segments = [s for s in segments_with_speakers if s.get('speaker') == target_speaker]
            filtered_transcript = ' '.join(s['text'] for s in filtered_segments)
        else:
            filtered_segments = segments_with_speakers
            filtered_transcript = transcript
        
        # 5. Grammar analysis (with timestamps)
        grammar_result = self._analyze_grammar_with_timestamps(
            filtered_transcript, 
            filtered_segments
        )
        
        # 6. Fluency metrics
        fluency_result = self._analyze_fluency(filtered_segments, result)
        
        # 7. Pronunciation (if reference provided)
        if reference_text:
            pronunciation_result = self._analyze_pronunciation(
                filtered_transcript, 
                reference_text,
                filtered_segments
            )
        else:
            pronunciation_result = {
                "wer": 0,
                "word_accuracy": 100,
                "mispronounced_words": [],
                "note": "No reference text provided"
            }
        
        # 8. Overall score
        overall = self._calculate_overall_score(
            grammar_result,
            fluency_result,
            pronunciation_result
        )
        
        # 9. Summary stats
        total_duration = segments[-1]['end'] - segments[0]['start'] if segments else 0
        speaking_time = sum(s['end'] - s['start'] for s in filtered_segments)
        speaking_pct = (speaking_time / total_duration * 100) if total_duration > 0 else 100
        
        # 10. Top errors
        top_errors = self._get_top_errors(grammar_result['errors'])
        
        # 11. Multi-speaker breakdown (if no target speaker and multiple speakers)
        speaker_breakdown = None
        if target_speaker is None and speaker_segments:
            unique_speakers = set(s.get('speaker', 0) for s in segments_with_speakers)
            if len(unique_speakers) > 1:
                speaker_breakdown = self._analyze_per_speaker(
                    segments_with_speakers,
                    speaker_segments,
                    reference_text
                )
        
        result = {
            "transcript": filtered_transcript,
            "full_transcript": transcript,
            "reference": reference_text,
            "speakers": {
                "total": len(set(s.get('speaker', 0) for s in segments_with_speakers)),
                "segments": speaker_segments,
                "target_speaker": target_speaker
            },
            "grammar": grammar_result,
            "fluency": fluency_result,
            "pronunciation": pronunciation_result,
            "overall_score": overall,
            "summary": {
                "duration": round(total_duration, 1),
                "speaking_time": round(speaking_time, 1),
                "speaking_percentage": round(speaking_pct)
            },
            "top_errors": top_errors,
            "analyzed_at": datetime.now().isoformat()
        }
        
        # Add speaker breakdown if available
        if speaker_breakdown:
            result["speaker_breakdown"] = speaker_breakdown
        
        return result
    
    def _diarize_speakers(self, audio_path: str) -> List[Dict]:
        """
        Identify speakers in audio.
        
        Returns:
            [
                {"speaker": 0, "start": 0.5, "end": 5.2},
                {"speaker": 1, "start": 5.5, "end": 10.1},
                ...
            ]
        """
        if not self.diarization_pipeline:
            return []
        
        print("Running speaker diarization...")
        diarization = self.diarization_pipeline(audio_path)
        
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            # Extract speaker ID (e.g., "SPEAKER_00" -> 0)
            speaker_id = int(speaker.split('_')[-1]) if '_' in speaker else 0
            
            segments.append({
                "speaker": speaker_id,
                "start": round(turn.start, 2),
                "end": round(turn.end, 2)
            })
        
        print(f"✅ Found {len(set(s['speaker'] for s in segments))} speaker(s)")
        return segments
    
    def _map_speakers_to_words(self, whisper_segments: List, speaker_segments: List) -> List:
        """Map speaker labels to Whisper word segments."""
        for wseg in whisper_segments:
            # Find speaker for this time range
            mid_time = (wseg['start'] + wseg['end']) / 2
            
            for sseg in speaker_segments:
                if sseg['start'] <= mid_time <= sseg['end']:
                    wseg['speaker'] = sseg['speaker']
                    break
            else:
                wseg['speaker'] = 0  # Default to speaker 0
        
        return whisper_segments
    
    def _analyze_per_speaker(
        self, 
        segments_with_speakers: List, 
        speaker_segments: List,
        reference_text: str = None
    ) -> Dict:
        """
        Analyze each speaker separately for multi-speaker calls.
        
        Returns:
            {
                "speaker_0": {
                    "overall_score": 85,
                    "grammar": {...},
                    "fluency": {...},
                    "summary": {...},
                    "top_errors": [...]
                },
                "speaker_1": {...}
            }
        """
        print("Analyzing each speaker separately...")
        
        unique_speakers = sorted(set(s.get('speaker', 0) for s in segments_with_speakers))
        breakdown = {}
        
        for speaker_id in unique_speakers:
            print(f"  Analyzing Speaker {speaker_id}...")
            
            # Filter segments for this speaker
            speaker_segs = [s for s in segments_with_speakers if s.get('speaker') == speaker_id]
            
            if not speaker_segs:
                continue
            
            # Build transcript for this speaker
            speaker_transcript = ' '.join(s['text'] for s in speaker_segs)
            
            # Grammar analysis
            grammar_result = self._analyze_grammar_with_timestamps(
                speaker_transcript,
                speaker_segs
            )
            
            # Fluency analysis
            fluency_result = self._analyze_fluency(speaker_segs, {'segments': speaker_segs})
            
            # Pronunciation (no reference for multi-speaker)
            pronunciation_result = {
                "wer": 0,
                "word_accuracy": 100,
                "mispronounced_words": [],
                "note": "No reference text for multi-speaker analysis"
            }
            
            # Overall score
            overall = self._calculate_overall_score(
                grammar_result,
                fluency_result,
                pronunciation_result
            )
            
            # Summary stats
            speaking_time = sum(s['end'] - s['start'] for s in speaker_segs)
            total_duration = segments_with_speakers[-1]['end'] - segments_with_speakers[0]['start']
            speaking_pct = (speaking_time / total_duration * 100) if total_duration > 0 else 0
            
            # Top errors
            top_errors = self._get_top_errors(grammar_result['errors'])
            
            breakdown[f"speaker_{speaker_id}"] = {
                "speaker_id": speaker_id,
                "transcript": speaker_transcript,
                "overall_score": overall,
                "grammar": grammar_result,
                "fluency": fluency_result,
                "pronunciation": pronunciation_result,
                "summary": {
                    "speaking_time": round(speaking_time, 1),
                    "speaking_percentage": round(speaking_pct)
                },
                "top_errors": top_errors
            }
        
        print(f"✅ Analyzed {len(breakdown)} speaker(s)")
        return breakdown
    
    def _analyze_grammar_with_timestamps(self, text: str, segments: List) -> Dict:
        """Analyze grammar errors and map them to timestamps."""
        # Check with LanguageTool
        matches = self.grammar_tool.check(text)
        
        # Filter out punctuation/typography/style/typos
        SKIP_CATEGORIES = {
            "PUNCTUATION", "TYPOGRAPHY", "CASING", "WHITESPACE",
            "STYLE", "REPETITIONS_STYLE",  # Skip style suggestions (gonna, really good, etc.)
            "TYPOS"  # Skip spelling mistakes (names, technical terms, etc.)
        }
        relevant_matches = []
        
        for m in matches:
            # Skip punctuation/typography
            if m.category in SKIP_CATEGORIES:
                continue
            
            # Skip punctuation-related errors (Whisper artifacts)
            # These are not speech errors - they're transcription formatting
            punctuation_keywords = ['comma', 'period', 'punctuation', 'quotation', 'apostrophe', 
                                   'hyphen', 'dash', 'colon', 'semicolon', 'exclamation']
            if any(kw in m.message.lower() for kw in punctuation_keywords):
                continue
            
            # Skip capitalization errors in speech (not relevant for oral)
            if 'capital' in m.message.lower() or 'uppercase' in m.message.lower():
                continue
            
            # Filter false positives: likely proper nouns (names, company names)
            if m.category == "TYPOS":
                matched_text = m.matched_text
                
                # Skip if starts with capital letter (likely a name/company)
                if matched_text and matched_text[0].isupper():
                    # Exception: don't skip if at sentence start AND looks like common word
                    # (e.g., "gonna" at sentence start should still be flagged)
                    if m.offset == 0 or text[m.offset - 1:m.offset] == ". ":
                        # Check if it's a common informal word (not a name)
                        informal_words = {"gonna", "wanna", "gotta", "Gonna", "Wanna", "Gotta"}
                        if matched_text not in informal_words:
                            continue  # Skip proper noun
                    else:
                        continue  # Skip mid-sentence capitalized word (name/product)
            
            relevant_matches.append(m)
        
        # Add custom grammar rules (e.g., "Yesterday I go")
        custom_matches = self.custom_grammar.check(text)
        
        errors = []
        for match in relevant_matches:
            # Find timestamp for this error
            timestamp = self._find_timestamp_for_offset(match.offset, text, segments)
            
            # Get Cambridge Grammar explanation
            cambridge = get_grammar_explanation(match.rule_id)
            
            errors.append({
                "timestamp": timestamp,
                "message": match.message,
                "offset": match.offset,
                "length": match.error_length,
                "replacements": match.replacements[:3],
                "category": match.category,
                "rule": match.rule_id,
                "severity": "error" if "GRAMMAR" in match.category else "warning",
                "context": match.context,
                "incorrect_text": match.matched_text,
                "cambridge": {
                    "title": cambridge["title"],
                    "explanation": cambridge["explanation"],
                    "examples": cambridge["examples"],
                    "unit": cambridge["cambridge_unit"],
                    "book": cambridge["book"],
                    "level": cambridge["difficulty"]
                }
            })
        
        # Process custom grammar matches
        for match in custom_matches:
            # Find timestamp
            timestamp = self._find_timestamp_for_offset(match['offset'], text, segments)
            
            # Use explanation from custom rule (includes educational content)
            explanation = match.get('explanation', {})
            
            errors.append({
                "timestamp": timestamp,
                "message": match['message'],
                "offset": match['offset'],
                "length": match['length'],
                "replacements": match['replacements'],
                "category": match['category'],
                "rule": match['rule_id'],
                "severity": "error",
                "context": match['context'],
                "incorrect_text": match['matched_text'],
                "cambridge": {
                    "title": explanation.get("title", "Grammar Rule"),
                    "explanation": explanation.get("explanation", ""),
                    "examples": explanation.get("examples", []),
                    "unit": explanation.get("cambridge_unit", ""),
                    "book": explanation.get("book", ""),
                    "level": explanation.get("difficulty", "Unknown"),
                    "common_markers": explanation.get("common_markers", []),
                    "tip": explanation.get("tip", "")
                }
            })
        
        # ML fallback: check if GECToR finds missed errors
        if self.use_ml and len(errors) < 5:  # Only if few errors found
            ml_errors = self._check_ml_errors(text, errors, segments)
            errors.extend(ml_errors)
        
        # Smart filter: remove false positives (names, companies, etc.)
        errors = self.smart_filter.filter_errors(errors, text)
        
        # AI filter: final verification (optional)
        if self.ai_filter and self.ai_filter.available and len(errors) > 0:
            errors = self.ai_filter.filter_errors(errors, text)
        
        # Sort by timestamp
        errors.sort(key=lambda e: e['timestamp'] or 0)
        
        # Grammar score
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
    
    def _check_ml_errors(self, text: str, existing_errors: List, segments: List) -> List[Dict]:
        """
        Check for errors using ML (GECToR) as fallback.
        Only called if few errors found by LanguageTool.
        
        Args:
            text: Original text
            existing_errors: Errors already found
            segments: Whisper segments for timestamps
        
        Returns:
            Additional errors found by ML
        """
        if not self.use_ml or not GECTOR_AVAILABLE:
            return []
        
        # Lazy load GECToR
        if self.gector is None:
            try:
                print("Loading GECToR ML model...")
                self.gector = GECToRChecker()
                print("✅ GECToR loaded")
            except Exception as e:
                print(f"⚠️  Failed to load GECToR: {e}")
                self.use_ml = False
                return []
        
        try:
            # Get ML corrections
            corrected = self.gector.correct(text)
            
            # If no changes, no new errors
            if text.strip() == corrected.strip():
                return []
            
            print(f"  ML found difference:")
            print(f"    Original:  {text}")
            print(f"    Corrected: {corrected}")
            
            # Extract errors from diff
            # Simple approach: if text changed, mark as ML error
            ml_errors = []
            
            # Get existing error positions
            known_positions = {e['offset'] for e in existing_errors}
            
            # Word-level diff
            orig_words = text.split()
            corr_words = corrected.split()
            
            char_pos = 0
            for i, (orig, corr) in enumerate(zip(orig_words, corr_words)):
                if orig != corr and char_pos not in known_positions:
                    # Find timestamp
                    timestamp = self._find_timestamp_for_offset(char_pos, text, segments)
                    
                    ml_errors.append({
                        "timestamp": timestamp,
                        "message": f"ML model suggests: '{orig}' → '{corr}'",
                        "offset": char_pos,
                        "length": len(orig),
                        "replacements": [corr],
                        "category": "ML_GRAMMAR",
                        "rule": "GECTOR_ML",
                        "severity": "warning",  # ML = warning (less certain)
                        "context": text[max(0, char_pos-20):char_pos+len(orig)+20],
                        "incorrect_text": orig,
                        "cambridge": {
                            "title": "ML Grammar Suggestion",
                            "explanation": (
                                "This correction was suggested by an AI model (GECToR). "
                                "It may indicate a grammar error that rule-based checkers missed."
                            ),
                            "examples": [
                                f"Your text: {orig}",
                                f"ML suggests: {corr}"
                            ],
                            "unit": "Machine Learning Detection",
                            "book": "GECToR (Grammarly AI)",
                            "level": "Intermediate"
                        }
                    })
                
                char_pos += len(orig) + 1  # +1 for space
            
            if ml_errors:
                print(f"  → ML found {len(ml_errors)} additional error(s)")
            
            return ml_errors
        
        except Exception as e:
            print(f"⚠️  ML check failed: {e}")
            return []
    
    def _find_timestamp_for_offset(self, char_offset: int, text: str, segments: List) -> Optional[float]:
        """Find timestamp for a character offset in the text."""
        # Count words up to this offset
        text_before = text[:char_offset]
        words_before = len(text_before.split())
        
        # Find the segment containing this word
        word_count = 0
        for seg in segments:
            seg_words = len(seg['text'].split())
            if word_count + seg_words >= words_before:
                # This segment contains the error
                return round(seg['start'], 1)
            word_count += seg_words
        
        return None
    
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
        words = ' '.join(s['text'] for s in segments).split()
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
        """Compare transcript with reference text."""
        # Normalize texts
        trans_words = transcript.lower().split()
        ref_words = reference.lower().split()
        
        # Simple WER calculation
        wer = self._calculate_wer(ref_words, trans_words)
        
        # Find mispronounced words with timestamps
        mispronounced = []
        trans_set = set(trans_words)
        
        for i, word in enumerate(ref_words):
            if word not in trans_set:
                # Find approximate timestamp
                timestamp = None
                if i < len(segments):
                    timestamp = segments[i]['start']
                
                mispronounced.append({
                    "word": word,
                    "position": i,
                    "timestamp": timestamp,
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
        """Calculate overall score (0-100)."""
        grammar_score = grammar['score']
        pronunciation_score = pronunciation['word_accuracy']
        
        # Fluency score based on WPM
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
    
    def _get_top_errors(self, errors: List[Dict], top_n: int = 3) -> List[Dict]:
        """Get top N most critical errors."""
        # Sort by severity (errors first, then warnings)
        errors_only = [e for e in errors if e['severity'] == 'error']
        warnings_only = [e for e in errors if e['severity'] == 'warning']
        
        sorted_errors = errors_only + warnings_only
        
        # Group by rule to find most common errors
        error_counts = {}
        for err in sorted_errors:
            rule = err['rule']
            if rule not in error_counts:
                error_counts[rule] = []
            error_counts[rule].append(err)
        
        # Sort by frequency
        top_rules = sorted(error_counts.items(), key=lambda x: len(x[1]), reverse=True)[:top_n]
        
        top_errors = []
        for rule, examples in top_rules:
            # Take first example of this error type
            example = examples[0]
            top_errors.append({
                **example,
                "occurrences": len(examples),
                "all_examples": [
                    {
                        "timestamp": e['timestamp'],
                        "incorrect_text": e['incorrect_text'],
                        "context": e['context']
                    } 
                    for e in examples
                ]
            })
        
        return top_errors


def format_timestamp(seconds: Optional[float]) -> str:
    """Format seconds as MM:SS."""
    if seconds is None:
        return "??:??"
    
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def format_report_new(result: Dict) -> str:
    """Format analysis result with new Summary + Top-3 + Timeline format."""
    report = []
    
    # Header
    report.append("=" * 70)
    report.append("🎯 ENGLISH SPEAKING PRACTICE ANALYSIS")
    report.append("=" * 70)
    report.append("")
    
    # === SUMMARY ===
    summary = result['summary']
    grammar = result['grammar']
    pronunciation = result['pronunciation']
    
    report.append("📊 SUMMARY")
    report.append("-" * 70)
    report.append(f"Overall Score:      {result['overall_score']}/100")
    report.append(f"Duration:           {format_timestamp(summary['duration'])}")
    report.append(f"Your speaking time: {format_timestamp(summary['speaking_time'])} ({summary['speaking_percentage']}%)")
    report.append(f"Errors found:       {grammar['total_errors']} grammar, {len(pronunciation.get('mispronounced_words', []))} pronunciation")
    report.append("")
    
    # === TOP 3 CRITICAL ERRORS ===
    top_errors = result.get('top_errors', [])
    if top_errors:
        report.append("🔥 TOP 3 CRITICAL ERRORS")
        report.append("-" * 70)
        
        for i, err in enumerate(top_errors[:3], 1):
            cambridge = err.get('cambridge', {})
            
            report.append(f"\n{i}. {cambridge.get('title', err['category'])} (occurred {err['occurrences']} time(s))")
            
            # Show first example
            example = err['all_examples'][0] if err['all_examples'] else {}
            timestamp = format_timestamp(example.get('timestamp'))
            
            report.append(f"❌ {timestamp} \"{example.get('incorrect_text', '')}\"")
            if err['replacements']:
                report.append(f"✅ Should be: \"{err['replacements'][0]}\"")
            
            # Cambridge explanation
            if cambridge:
                report.append(f"📚 {cambridge.get('explanation', '')}")
                if cambridge.get('examples'):
                    report.append(f"   Example: {cambridge['examples'][0]}")
                report.append(f"   📕 {cambridge.get('book', '')} - {cambridge.get('unit', '')}")
            
            report.append("")
    
    # === ALL ERRORS (TIMELINE) ===
    all_errors = grammar.get('errors', [])
    if all_errors:
        report.append("📝 ALL ERRORS (TIMELINE)")
        report.append("-" * 70)
        
        for err in all_errors:
            timestamp = format_timestamp(err.get('timestamp'))
            error_type = "Grammar" if err['severity'] == 'error' else "Warning"
            
            report.append(f"{timestamp} | {error_type} | \"{err['incorrect_text']}\" → \"{err['replacements'][0] if err['replacements'] else '?'}\"")
        
        report.append("")
    
    # === RECOMMENDATIONS ===
    if top_errors:
        report.append("🎯 RECOMMENDATIONS")
        report.append("-" * 70)
        
        for err in top_errors[:3]:
            cambridge = err.get('cambridge', {})
            report.append(f"- Review {cambridge.get('title', err['category'])} ({err['occurrences']} errors)")
        
        report.append("")
    
    report.append("=" * 70)
    
    return "\n".join(report)


if __name__ == "__main__":
    # Test
    analyzer = EnglishPracticeAnalyzerDiarization()
    
    # Test with recording
    test_audio = "test_data/kirill_normal.wav"
    reference = "Don't you tell me what to do"
    
    if Path(test_audio).exists():
        print(f"\nAnalyzing: {test_audio}\n")
        result = analyzer.analyze(
            test_audio, 
            reference,
            enable_diarization=False  # Disable for single-speaker test
        )
        print(format_report_new(result))
        
        # Save JSON
        output_file = "test_data/analysis_result_diarization.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n📁 Full result saved to: {output_file}")
    else:
        print(f"Test file not found: {test_audio}")
