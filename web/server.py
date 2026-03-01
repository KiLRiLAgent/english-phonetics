#!/usr/bin/env python3
"""
Pronunciation Analyzer — Web Server
Records audio from browser, analyzes with Whisper, returns colored transcript.
"""

import os
import sys
import json
import re
import tempfile
import warnings
from pathlib import Path
from datetime import datetime

warnings.filterwarnings("ignore")

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
# cgi removed (deprecated in 3.13+)

PORT = 8780
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Whisper now loaded inside MVP analyzer
import numpy as np

# Load MVP analyzer
print("Loading MVP English Practice Analyzer...")
sys.path.insert(0, str(Path(__file__).parent.parent))
from analyzer_mvp import EnglishPracticeAnalyzer
ANALYZER = EnglishPracticeAnalyzer()
print("✅ MVP Analyzer ready!")

# Grammar checking now handled by MVP analyzer


def analyze_audio(audio_path: str, reference: str = None) -> dict:
    """Full analysis pipeline using MVP analyzer."""
    # Use default reference if not provided
    if not reference:
        reference = "don't you tell me what to do"
    
    # Use MVP analyzer
    try:
        result = ANALYZER.analyze(audio_path, reference)
    except Exception as e:
        return {"error": str(e)}
    
    # Convert MVP result to web UI format
    transcript = result['transcript']
    grammar = result['grammar']
    fluency = result['fluency']
    pronunciation = result['pronunciation']
    
    # Convert to word-level data for UI
    # Simple approach: split transcript and mark mispronounced words
    words_list = transcript.split()
    mispronounced_set = set(w['word'] for w in pronunciation.get('mispronounced_words', []))
    
    scored_words = []
    for i, word in enumerate(words_list):
        # Determine color based on mispronunciation
        if word.lower() in mispronounced_set:
            color = 'red'
            score = 40
        else:
            color = 'green'
            score = 90
        
        scored_words.append({
            'word': word,
            'score': score,
            'color': color,
            'level': 'excellent' if color == 'green' else 'poor',
            'confidence': 0.95 if color == 'green' else 0.6
        })
    
    return {
        "transcript": transcript,
        "reference": reference,
        "words": scored_words,
        "overall_score": result['overall_score'],
        "total_words": len(scored_words),
        "green": sum(1 for w in scored_words if w["color"] == "green"),
        "yellow": 0,
        "orange": 0,
        "red": sum(1 for w in scored_words if w["color"] == "red"),
        "grammar_errors": grammar['errors'],
        "grammar_score": grammar['score'],
        "fluency": fluency,
        "pronunciation": pronunciation,
        "analyzed_at": result['analyzed_at'],
    }


def get_html():
    """Read HTML fresh each time (dev mode)"""
    html_path = Path(__file__).parent / "index.html"
    if html_path.exists():
        return html_path.read_text()
    return "index.html not found"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()
            self.wfile.write(get_html().encode())
        elif parsed.path.startswith("/uploads/"):
            fpath = UPLOAD_DIR / Path(parsed.path).name
            if fpath.exists():
                self.send_response(200)
                self.send_header("Content-Type", "audio/webm")
                self.send_header("Content-Length", str(fpath.stat().st_size))
                self.end_headers()
                with open(fpath, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404)
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/analyze":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            # Save uploaded audio
            filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm"
            filepath = UPLOAD_DIR / filename
            with open(filepath, "wb") as f:
                f.write(body)

            # Analyze
            try:
                result = analyze_audio(str(filepath))
                result["audio_url"] = f"/uploads/{filename}"
                resp = json.dumps(result, ensure_ascii=False)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(resp.encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass


def main():
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"🎤 Pronunciation Analyzer at http://127.0.0.1:{PORT}")
    server.serve_forever()

if __name__ == "__main__":
    main()
