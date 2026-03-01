#!/usr/bin/env python3
"""Simple web server for viewing lecture transcriptions"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from pathlib import Path
from urllib.parse import unquote
import json
import mimetypes

PORT = 8899
BASE_DIR = Path(__file__).parent
TRANSCRIPTIONS_DIR = BASE_DIR / "transcriptions"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.serve_file("view_lecture.html", "text/html")
        
        elif self.path == "/transcribe.log":
            self.serve_file("transcribe.log", "text/plain")
        
        elif self.path == "/api/transcriptions":
            # List available transcription files
            files = []
            if TRANSCRIPTIONS_DIR.exists():
                files = [f.name for f in TRANSCRIPTIONS_DIR.glob("*.json")]
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(files).encode())
        
        elif self.path.startswith("/api/transcript/"):
            # Serve specific transcript JSON
            filename = self.path.split("/")[-1]
            file_path = TRANSCRIPTIONS_DIR / filename
            
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
            else:
                self.send_error(404, "File not found")
        
        elif self.path == "/api/grammar":
            # Serve latest grammar analysis
            grammar_files = list(TRANSCRIPTIONS_DIR.glob("*.grammar.json"))
            
            if grammar_files:
                latest = max(grammar_files, key=lambda p: p.stat().st_mtime)
                with open(latest, 'r') as f:
                    data = json.load(f)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
            else:
                self.send_error(404, "No grammar analysis found")
        
        elif self.path == "/api/grammar-linked":
            # Serve latest linked grammar analysis
            # Priority: indexed > filtered > words > linked
            grammar_files = list(TRANSCRIPTIONS_DIR.glob("*.grammar.full.words.filtered_indexed.json"))
            
            if not grammar_files:
                grammar_files = list(TRANSCRIPTIONS_DIR.glob("*.grammar.full.words.indexed.json"))
            
            if not grammar_files:
                grammar_files = list(TRANSCRIPTIONS_DIR.glob("*.grammar.full.words.filtered.json"))
            
            if not grammar_files:
                grammar_files = list(TRANSCRIPTIONS_DIR.glob("*.grammar.full.words.json"))
            
            if not grammar_files:
                grammar_files = list(TRANSCRIPTIONS_DIR.glob("*.grammar.linked.json"))
            
            if grammar_files:
                latest = max(grammar_files, key=lambda p: p.stat().st_mtime)
                with open(latest, 'r') as f:
                    data = json.load(f)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
            else:
                self.send_error(404, "No linked grammar analysis found")
        
        elif self.path.startswith("/audio/"):
            # Serve audio file with Range support for seeking
            audio_file = TRANSCRIPTIONS_DIR / unquote(self.path.split("/")[-1])
            
            if not audio_file.exists():
                self.send_error(404, "Audio file not found")
                return
            
            file_size = audio_file.stat().st_size
            
            # Check for Range header
            range_header = self.headers.get('Range')
            
            if range_header:
                # Parse range header: bytes=start-end
                try:
                    byte_range = range_header.split('=')[1]
                    start, end = byte_range.split('-')
                    start = int(start) if start else 0
                    end = int(end) if end else file_size - 1
                    
                    # Validate range
                    if start >= file_size or end >= file_size or start > end:
                        self.send_error(416, "Requested Range Not Satisfiable")
                        return
                    
                    length = end - start + 1
                    
                    # Send partial content
                    self.send_response(206)
                    self.send_header("Content-Type", "audio/mpeg")
                    self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                    self.send_header("Content-Length", str(length))
                    self.send_header("Accept-Ranges", "bytes")
                    self.end_headers()
                    
                    with open(audio_file, 'rb') as f:
                        f.seek(start)
                        self.wfile.write(f.read(length))
                except Exception as e:
                    print(f"Range request error: {e}")
                    self.send_error(400, "Bad Range Request")
            else:
                # Send full file
                self.send_response(200)
                self.send_header("Content-Type", "audio/mpeg")
                self.send_header("Content-Length", str(file_size))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                
                with open(audio_file, 'rb') as f:
                    self.wfile.write(f.read())
        
        elif self.path == "/api/grammar-full-linked":
            # Serve latest full grammar analysis
            # Priority: .filtered.json > .words.json > .smart.json
            grammar_files = list(TRANSCRIPTIONS_DIR.glob("*.grammar.full.words.filtered.json"))
            
            if not grammar_files:
                grammar_files = list(TRANSCRIPTIONS_DIR.glob("*.grammar.full.words.json"))
            
            if grammar_files:
                latest = max(grammar_files, key=lambda p: p.stat().st_mtime)
                with open(latest, 'r') as f:
                    data = json.load(f)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
            else:
                # Fallback to smart version
                grammar_files = list(TRANSCRIPTIONS_DIR.glob("*.grammar.full.smart.json"))
                if grammar_files:
                    latest = max(grammar_files, key=lambda p: p.stat().st_mtime)
                    with open(latest, 'r') as f:
                        data = json.load(f)
                    
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
                else:
                    # Fallback to partial analysis
                    grammar_files = list(TRANSCRIPTIONS_DIR.glob("*.grammar.linked.json"))
                    if grammar_files:
                        latest = max(grammar_files, key=lambda p: p.stat().st_mtime)
                        with open(latest, 'r') as f:
                            data = json.load(f)
                        
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
                    else:
                        self.send_error(404, "No full grammar analysis found")
        
        elif self.path == "/api/grammar-rules":
            # Serve grammar rules
            rules_file = BASE_DIR / "grammar_rules.json"
            
            if rules_file.exists():
                with open(rules_file, 'r') as f:
                    data = json.load(f)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
            else:
                self.send_error(404, "Grammar rules not found")
        
        elif self.path == "/grammar":
            self.serve_file("grammar_viewer_v3.html", "text/html")
        
        elif self.path == "/transcript":
            self.serve_file("transcript_viewer.html", "text/html")
        
        elif self.path == "/test-sync":
            self.serve_file("test_sync.html", "text/html")
        
        elif self.path == "/debug-offset":
            self.serve_file("debug_offset.html", "text/html")
        
        elif self.path == "/transcript-sentences":
            self.serve_file("transcript_sentences.html", "text/html")
        
        elif self.path == "/api/transcript-segments":
            # Serve segments (sentences)
            # Priority: short_segments > words
            words_files = list(TRANSCRIPTIONS_DIR.glob("lecture_audio_short_segments.json"))
            
            if not words_files:
                words_files = list(TRANSCRIPTIONS_DIR.glob("lecture_audio_words.json"))
            
            if not words_files:
                words_files = list(TRANSCRIPTIONS_DIR.glob("*_words.json"))
            
            if words_files:
                latest = max(words_files, key=lambda p: p.stat().st_mtime)
                with open(latest, 'r') as f:
                    data = json.load(f)
                
                # Extract segments
                segments = []
                for seg in data.get('segments', []):
                    segments.append({
                        'start': seg['start'],
                        'end': seg['end'],
                        'text': seg['text'].strip()
                    })
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(segments, ensure_ascii=False).encode())
            else:
                self.send_error(404, "No segment data found")
        
        elif self.path == "/api/audio-file":
            # Return the name of the available audio file
            audio_files = list(TRANSCRIPTIONS_DIR.glob("*.mp3"))
            if audio_files:
                latest = max(audio_files, key=lambda p: p.stat().st_mtime)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"filename": latest.name}).encode())
            else:
                self.send_error(404, "No audio file found")

        elif self.path == "/api/diarization":
            # Serve latest diarization data
            diar_files = list(TRANSCRIPTIONS_DIR.glob("*_diarization.json"))
            if diar_files:
                latest = max(diar_files, key=lambda p: p.stat().st_mtime)
                with open(latest, 'r') as f:
                    data = json.load(f)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
            else:
                self.send_error(404, "No diarization data found")

        elif self.path == "/api/transcript-words":
            # Serve latest word-level transcript, with speaker labels if available
            # Check for diarization data first (has words_with_speakers)
            diar_files = list(TRANSCRIPTIONS_DIR.glob("*_diarization.json"))
            if diar_files:
                latest_diar = max(diar_files, key=lambda p: p.stat().st_mtime)
                with open(latest_diar, 'r') as f:
                    diar_data = json.load(f)
                words = diar_data.get('words_with_speakers', [])
                if words:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(words, ensure_ascii=False).encode())
                    return

            # Fallback: plain words without speakers
            words_files = list(TRANSCRIPTIONS_DIR.glob("*_words_flat.json"))

            if not words_files:
                words_files = list(TRANSCRIPTIONS_DIR.glob("*_words.json"))

            if words_files:
                latest = max(words_files, key=lambda p: p.stat().st_mtime)
                with open(latest, 'r') as f:
                    data = json.load(f)

                # Extract words array
                if isinstance(data, list):
                    words = data
                elif isinstance(data, dict):
                    if 'words' in data:
                        words = data['words']
                    elif 'segments' in data:
                        words = []
                        for segment in data['segments']:
                            for word_data in segment.get('words', []):
                                words.append({
                                    'word': word_data['word'],
                                    'start': word_data['start'],
                                    'end': word_data['end']
                                })
                    else:
                        words = []
                else:
                    words = []

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(words, ensure_ascii=False).encode())
            else:
                self.send_error(404, "No word-level transcript found")
        
        else:
            self.send_error(404, "Not found")
    
    def serve_file(self, filename, content_type):
        file_path = BASE_DIR / filename
        
        if not file_path.exists():
            self.send_error(404, f"File not found: {filename}")
            return
        
        with open(file_path, 'rb') as f:
            content = f.read()
        
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content)
    
    def log_message(self, format, *args):
        # Suppress log messages
        pass

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

if __name__ == '__main__':
    TRANSCRIPTIONS_DIR.mkdir(exist_ok=True)

    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"✅ Lecture viewer running on http://localhost:{PORT}")
    print(f"   Transcriptions folder: {TRANSCRIPTIONS_DIR}")
    print(f"   Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
