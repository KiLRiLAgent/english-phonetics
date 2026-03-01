#!/usr/bin/env python3
"""
Azure Pronunciation Assessment integration.

Free Tier: 5 hours/month (300+ requests with 15-sec audio)
Pay-as-you-go: ~$1 per 1000 requests

Docs: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-pronunciation-assessment
"""

import os
import json
import azure.cognitiveservices.speech as speechsdk
from pathlib import Path
from typing import Dict, List


class AzureScorer:
    """
    Pronunciation assessment using Azure Speech Service.
    
    Provides:
    - Word-level pronunciation scores (0-100)
    - Phoneme-level scores with expected vs actual
    - Specific error detection (omissions, substitutions, insertions)
    - Fluency and prosody scores
    """
    
    def __init__(self, subscription_key: str = None, region: str = None):
        """
        Initialize scorer with Azure credentials.
        
        Args:
            subscription_key: Azure Speech subscription key
            region: Azure region (e.g., 'eastus', 'westeurope')
        """
        self.subscription_key = subscription_key or os.getenv("AZURE_SPEECH_KEY")
        self.region = region or os.getenv("AZURE_SPEECH_REGION", "eastus")
        
        if not self.subscription_key:
            raise ValueError(
                "Azure Speech subscription key required.\n"
                "Set AZURE_SPEECH_KEY env var or pass subscription_key parameter.\n"
                "Get free key at: https://portal.azure.com (5 hours/month free)"
            )
        
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.subscription_key,
            region=self.region
        )
    
    def score_pronunciation(self, audio_path: str, reference_text: str) -> Dict:
        """
        Score pronunciation of audio against reference text.
        
        Args:
            audio_path: Path to audio file (WAV format recommended)
            reference_text: Expected text
        
        Returns:
            {
                "overall_score": 85.5,
                "words": [
                    {
                        "word": "hello",
                        "score": 90,
                        "start": 0.5,
                        "end": 0.9,
                        "accuracy_score": 92,
                        "error_type": None,  # or "Omission", "Insertion", "Mispronunciation"
                        "phonemes": [
                            {
                                "phone": "h",
                                "expected_ipa": "h",
                                "actual_ipa": "h",
                                "score": 95
                            },
                            ...
                        ],
                        "issues": []
                    },
                    ...
                ],
                "fluency": {
                    "fluency_score": 85,
                    "prosody_score": 80,
                    "completeness_score": 100
                }
            }
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Configure pronunciation assessment
        pronunciation_config = speechsdk.PronunciationAssessmentConfig(
            reference_text=reference_text,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
            enable_miscue=True
        )
        
        # Enable prosody (intonation) evaluation
        pronunciation_config.enable_prosody_assessment()
        
        # Create audio config from file
        audio_config = speechsdk.AudioConfig(filename=str(audio_path))
        
        # Create speech recognizer
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )
        
        # Apply pronunciation assessment config
        pronunciation_config.apply_to(speech_recognizer)
        
        # Perform recognition
        result = speech_recognizer.recognize_once()
        
        # Check result
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            pronunciation_result = speechsdk.PronunciationAssessmentResult(result)
            return self._parse_result(pronunciation_result, result)
        
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return {
                "error": "No speech detected in audio",
                "overall_score": 0,
                "words": [],
                "fluency": {}
            }
        
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            error_msg = f"Recognition canceled: {cancellation.reason}"
            if cancellation.reason == speechsdk.CancellationReason.Error:
                error_msg += f" - {cancellation.error_details}"
            
            return {
                "error": error_msg,
                "overall_score": 0,
                "words": [],
                "fluency": {}
            }
        
        else:
            return {
                "error": f"Unexpected result: {result.reason}",
                "overall_score": 0,
                "words": [],
                "fluency": {}
            }
    
    def _parse_result(self, pronunciation_result, speech_result) -> Dict:
        """Parse Azure pronunciation result into our standard format."""
        
        # Get JSON details
        json_result = json.loads(speech_result.properties.get(
            speechsdk.PropertyId.SpeechServiceResponse_JsonResult
        ))
        
        # Overall scores
        overall_score = pronunciation_result.pronunciation_score
        accuracy_score = pronunciation_result.accuracy_score
        fluency_score = pronunciation_result.fluency_score
        completeness_score = pronunciation_result.completeness_score
        prosody_score = pronunciation_result.prosody_score if hasattr(pronunciation_result, 'prosody_score') else None
        
        # Parse word-level details
        words = []
        nb_result = json_result.get('NBest', [{}])[0]
        word_details = nb_result.get('Words', [])
        
        for word_data in word_details:
            word_text = word_data.get('Word', '')
            word_score = word_data.get('PronunciationAssessment', {}).get('AccuracyScore', 0)
            error_type = word_data.get('PronunciationAssessment', {}).get('ErrorType', 'None')
            
            # Timing (in 100-nanosecond units)
            offset_ticks = word_data.get('Offset', 0)
            duration_ticks = word_data.get('Duration', 0)
            start_time = offset_ticks / 10_000_000  # Convert to seconds
            end_time = (offset_ticks + duration_ticks) / 10_000_000
            
            # Parse phoneme-level scores
            phonemes = []
            phoneme_details = word_data.get('Phonemes', [])
            
            for phone_data in phoneme_details:
                phone = phone_data.get('Phoneme', '')
                phone_score = phone_data.get('PronunciationAssessment', {}).get('AccuracyScore', 0)
                
                phonemes.append({
                    'phone': phone,
                    'expected_ipa': phone,  # Azure uses IPA-like notation
                    'actual_ipa': phone,  # Azure doesn't expose what was actually said
                    'score': phone_score
                })
            
            # Detect issues
            issues = []
            if error_type == 'Mispronunciation':
                issues.append('mispronunciation')
            elif error_type == 'Omission':
                issues.append('word omitted')
            elif error_type == 'Insertion':
                issues.append('unexpected word')
            
            # Find low-scoring phonemes
            for phone in phonemes:
                if phone['score'] < 60:
                    issues.append(f"poor /{phone['phone']}/ ({phone['score']:.0f}%)")
            
            # Color coding
            if word_score >= 75:
                color = 'green'
            elif word_score >= 50:
                color = 'yellow'
            else:
                color = 'red'
            
            words.append({
                'word': word_text,
                'score': round(word_score, 1),
                'color': color,
                'start': round(start_time, 2),
                'end': round(end_time, 2),
                'accuracy_score': word_score,
                'error_type': error_type,
                'phonemes': phonemes,
                'issues': issues,
                'aligned': error_type != 'Omission'
            })
        
        # Fluency metrics
        fluency = {
            'fluency_score': round(fluency_score, 1),
            'completeness_score': round(completeness_score, 1),
            'accuracy_score': round(accuracy_score, 1)
        }
        
        if prosody_score is not None:
            fluency['prosody_score'] = round(prosody_score, 1)
        
        return {
            'overall_score': round(overall_score, 1),
            'words': words,
            'total_words': len(words),
            'aligned_words': len([w for w in words if w['aligned']]),
            'fluency': fluency,
            'alignment_method': 'azure',
            'recognized_text': speech_result.text,
            'azure_raw': json_result
        }


def get_scorer() -> AzureScorer:
    """Get singleton scorer instance."""
    global _scorer
    if '_scorer' not in globals():
        _scorer = AzureScorer()
    return _scorer


if __name__ == "__main__":
    # Test
    import sys
    
    if not os.getenv("AZURE_SPEECH_KEY"):
        print("❌ AZURE_SPEECH_KEY not set!")
        print("\nGet free key at: https://portal.azure.com")
        print("Free tier: 5 hours/month")
        print("\nThen: export AZURE_SPEECH_KEY='your_key_here'")
        print("      export AZURE_SPEECH_REGION='eastus'  # or your region")
        sys.exit(1)
    
    scorer = get_scorer()
    
    # Test on Russian accent audio
    test_audio = "test_data/russian_accent/russian1.mp3"
    test_text = "Please call Stella."
    
    if Path(test_audio).exists():
        print(f"Testing: {test_audio}")
        print(f"Reference: {test_text}\n")
        
        result = scorer.score_pronunciation(test_audio, test_text)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"Overall score: {result['overall_score']}/100")
            print(f"Recognized text: \"{result['recognized_text']}\"\n")
            
            for word in result['words']:
                emoji = {'green': '🟢', 'yellow': '🟡', 'red': '🔴'}.get(word['color'], '⚪')
                print(f"{emoji} {word['word']:15s} {word['score']:5.1f}/100")
                if word['error_type'] != 'None':
                    print(f"   Error type: {word['error_type']}")
                if word['issues']:
                    print(f"   Issues: {', '.join(word['issues'])}")
            
            print(f"\nFluency:")
            for key, val in result['fluency'].items():
                print(f"  {key}: {val}/100")
    else:
        print(f"Test file not found: {test_audio}")
