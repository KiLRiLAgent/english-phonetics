#!/usr/bin/env python3
"""
Custom grammar rules for detecting common ESL mistakes
that LanguageTool misses.

Educational explanations included for better learning.
"""

import re
from typing import List, Dict, Tuple


# Educational explanations for custom rules
CUSTOM_RULE_EXPLANATIONS = {
    "CUSTOM_PAST_MARKER_TENSE": {
        "title": "Past Time Markers + Past Tense",
        "explanation": (
            "When you use past time expressions (yesterday, last week, ago, etc.), "
            "you MUST use the past tense form of the verb. This shows that the action "
            "happened in the past and is finished.\n\n"
            "Present tense (go, play, eat) = actions happening NOW or regularly.\n"
            "Past tense (went, played, ate) = actions that FINISHED in the past."
        ),
        "examples": [
            "✅ Yesterday I went to school (action finished yesterday)",
            "✅ Last week I played football",
            "✅ Two days ago I ate pizza",
            "❌ Yesterday I go to school (WRONG: 'go' is present, not past)",
            "❌ Last week I play football (WRONG: need 'played')",
            "❌ Two days ago I eat pizza (WRONG: need 'ate')"
        ],
        "cambridge_unit": "Unit 11-12 (Past Simple)",
        "book": "English Grammar in Use (Intermediate)",
        "difficulty": "Elementary",
        "common_markers": [
            "yesterday", "last week/month/year", "X days/weeks ago",
            "in 2020", "when I was young", "this morning (if it's afternoon now)"
        ],
        "tip": "💡 Tip: If you can answer 'WHEN did this happen?' with a specific past time → use past tense!"
    },
    
    "CUSTOM_PAST_CONTINUOUS": {
        "title": "Past Time Markers + Past Continuous (was/were -ing)",
        "explanation": (
            "When describing an action that was in progress at a specific time in the past, "
            "use the past continuous: was/were + verb-ing.\n\n"
            "Present continuous (am/is/are + -ing) = happening NOW.\n"
            "Past continuous (was/were + -ing) = was happening THEN."
        ),
        "examples": [
            "✅ Yesterday I was going to school when it rained",
            "✅ Last night I was watching TV",
            "✅ At 8pm I was eating dinner",
            "❌ Yesterday I am going to school (WRONG: 'am going' is present)",
            "❌ Last night I is watching TV (WRONG: need 'was watching')",
            "❌ At 8pm I are eating dinner (WRONG: need 'was eating')"
        ],
        "cambridge_unit": "Unit 13-14 (Past Continuous)",
        "book": "English Grammar in Use (Intermediate)",
        "difficulty": "Pre-Intermediate",
        "tip": "💡 Tip: Use past continuous when the action was NOT finished at that moment (was in progress)."
    }
}

class CustomGrammarChecker:
    """
    Detect grammar errors that LanguageTool misses.
    Focus on ESL common mistakes.
    """
    
    def __init__(self):
        # Past time markers
        self.past_markers = [
            'yesterday', 'ago', 'last week', 'last month', 'last year',
            'last night', 'last time', 'in 2023', 'in 2024',
        ]
        
        # Present tense verbs (non-3rd person)
        self.present_verbs = [
            'go', 'come', 'do', 'make', 'take', 'give', 'get', 'see',
            'know', 'think', 'feel', 'want', 'need', 'like', 'love',
            'hate', 'have', 'use', 'work', 'play', 'study',
        ]
        
        # Present continuous pattern
        self.present_continuous = r'\b(am|is|are)\s+\w+ing\b'
        
    def check(self, text: str) -> List[Dict]:
        """
        Check text for custom grammar errors.
        
        Returns:
            List of error dictionaries similar to LanguageTool format
        """
        errors = []
        text_lower = text.lower()
        
        # Rule 1: Past time marker + present tense
        for marker in self.past_markers:
            if marker in text_lower:
                # Check for present tense verbs after this marker
                errors.extend(self._check_past_marker_tense(text, marker))
        
        return errors
    
    def _check_past_marker_tense(self, text: str, marker: str) -> List[Dict]:
        """
        Check if present tense is used after a past time marker.
        
        Example: "Yesterday I go to school" should be "went"
        """
        errors = []
        text_lower = text.lower()
        
        # Find marker position
        marker_pos = text_lower.find(marker)
        if marker_pos == -1:
            return errors
        
        # Look for present tense verbs after the marker
        # Pattern: [marker] ... I/we/you/they [verb]
        # Pattern: [marker] ... he/she/it [verb]s
        
        # Check for "I/we/you/they + present tense verb"
        for verb in self.present_verbs:
            # Pattern: marker ... I go
            pattern = rf'\b{marker}\b[^.!?]*\b(I|we|you|they)\s+{verb}\b'
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            
            for match in matches:
                verb_pos = match.end() - len(verb)
                errors.append({
                    'offset': verb_pos,
                    'length': len(verb),
                    'message': f'Use past tense "{verb} → {self._get_past_tense(verb)}" after "{marker}"',
                    'replacements': [self._get_past_tense(verb)],
                    'rule_id': 'CUSTOM_PAST_MARKER_TENSE',
                    'category': 'GRAMMAR',
                    'matched_text': verb,
                    'context': match.group(0),
                    'error_length': len(verb),
                    'explanation': CUSTOM_RULE_EXPLANATIONS['CUSTOM_PAST_MARKER_TENSE']
                })
        
        # Check for "am/is/are + verb+ing" after past marker
        pattern = rf'\b{marker}\b[^.!?]*\b(am|is|are)\s+(\w+ing)\b'
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        
        for match in matches:
            continuous_verb = match.group(2)
            verb_pos = match.start(1)
            errors.append({
                'offset': verb_pos,
                'length': len(match.group(1)) + 1 + len(continuous_verb),
                'message': f'Use past continuous "was/were {continuous_verb}" after "{marker}"',
                'replacements': [f"was {continuous_verb}", f"were {continuous_verb}"],
                'rule_id': 'CUSTOM_PAST_CONTINUOUS',
                'category': 'GRAMMAR',
                'matched_text': f"{match.group(1)} {continuous_verb}",
                'context': match.group(0),
                'error_length': len(match.group(1)) + 1 + len(continuous_verb),
                'explanation': CUSTOM_RULE_EXPLANATIONS['CUSTOM_PAST_CONTINUOUS']
            })
        
        return errors
    
    def _get_past_tense(self, verb: str) -> str:
        """Get past tense form of common verbs."""
        # Irregular verbs
        irregular = {
            'go': 'went',
            'come': 'came',
            'do': 'did',
            'make': 'made',
            'take': 'took',
            'give': 'gave',
            'get': 'got',
            'see': 'saw',
            'know': 'knew',
            'think': 'thought',
            'feel': 'felt',
            'have': 'had',
        }
        
        if verb in irregular:
            return irregular[verb]
        
        # Regular verbs: add -ed
        return verb + 'ed'


# Test
if __name__ == '__main__':
    checker = CustomGrammarChecker()
    
    tests = [
        "Yesterday I go to school.",
        "Last week I am going to the store.",
        "I go to school yesterday.",
        "She don't like apples.",  # Not covered by this rule
    ]
    
    for text in tests:
        errors = checker.check(text)
        print(f"\n{text}")
        print(f"  Custom errors: {len(errors)}")
        for err in errors:
            print(f"    - [{err['rule_id']}] {err['message']}")
            print(f"      Matched: '{err['matched_text']}'")
            print(f"      Suggestions: {err['replacements']}")
