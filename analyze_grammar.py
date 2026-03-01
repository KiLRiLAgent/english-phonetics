#!/usr/bin/env python3
"""Analyze grammar in lecture transcript using OpenAI"""

import sys
import os
import json
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def analyze_grammar(text):
    """Analyze grammar using OpenAI"""
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "You are an English grammar checker. Find grammatical errors, awkward phrasing, and suggest improvements. Return JSON format."
            },
            {
                "role": "user",
                "content": f"""Analyze this English text for grammar errors. Find:
1. Grammar mistakes (tense, agreement, etc.)
2. Awkward phrasing or unclear sentences
3. Missing punctuation or run-on sentences
4. Word choice issues

Return JSON array of errors:
{{
  "errors": [
    {{
      "text": "original text fragment",
      "type": "grammar|punctuation|clarity|word-choice",
      "issue": "description of the problem",
      "suggestion": "how to fix it"
    }}
  ],
  "summary": {{
    "total_errors": 0,
    "grammar": 0,
    "punctuation": 0,
    "clarity": 0,
    "word_choice": 0
  }}
}}

Text to analyze:
{text[:3000]}"""
            }
        ],
        "temperature": 0.3,
        "max_tokens": 2000
    }
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60
    )
    
    result = response.json()
    
    if 'error' in result:
        print(f"Error: {result['error']}")
        return None
    
    content = result['choices'][0]['message']['content']
    
    # Extract JSON
    try:
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
        
        data = json.loads(content)
        return data
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Response: {content}")
        return None

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python analyze_grammar.py <transcript_file>")
        sys.exit(1)
    
    transcript_file = sys.argv[1]
    
    with open(transcript_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f"Analyzing {len(text)} characters...")
    print(f"First 3000 chars will be analyzed\n")
    
    result = analyze_grammar(text)
    
    if result:
        # Save results
        output_file = Path(transcript_file).with_suffix('.grammar.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Analysis saved to: {output_file}")
        print(f"\n📊 Summary:")
        summary = result.get('summary', {})
        print(f"  Total errors: {summary.get('total_errors', 0)}")
        print(f"  Grammar: {summary.get('grammar', 0)}")
        print(f"  Punctuation: {summary.get('punctuation', 0)}")
        print(f"  Clarity: {summary.get('clarity', 0)}")
        print(f"  Word choice: {summary.get('word_choice', 0)}")
        
        print(f"\n🔍 Sample errors:")
        for i, err in enumerate(result.get('errors', [])[:5], 1):
            print(f"\n  {i}. [{err['type']}] {err['text']}")
            print(f"     Issue: {err['issue']}")
            print(f"     Fix: {err['suggestion']}")
