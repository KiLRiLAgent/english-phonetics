#!/usr/bin/env python3
"""
English Practice Backend Server
Microservice for speech analysis with speaker diarization

API:
  POST /analyze
    - file: audio file (WAV/MP3)
    - reference: optional reference text
    - enable_diarization: bool (default: true)
    - target_speaker: int (optional)
    
  GET /health
    - Check if server is running
"""

import os
import sys
import json
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from flask_cors import CORS
import tempfile
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from analyzer_diarization import EnglishPracticeAnalyzerDiarization, format_timestamp

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max
CORS(app)  # Enable CORS for web UI

# Results directory
RESULTS_DIR = Path.home() / ".english_practice" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Initialize analyzer (global, lazy load)
analyzer = None

def get_analyzer():
    """Lazy load analyzer."""
    global analyzer
    if analyzer is None:
        print("Loading analyzer...")
        analyzer = EnglishPracticeAnalyzerDiarization()
        print("✅ Analyzer ready")
    return analyzer


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'version': '2.0',
        'features': ['grammar', 'fluency', 'pronunciation', 'diarization', 'timestamps']
    })


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Analyze audio file.
    
    Form data:
        file: audio file (required)
        reference: reference text (optional)
        enable_diarization: "true" or "false" (default: "true")
        target_speaker: speaker index (optional, e.g., "0", "1")
    
    Returns:
        JSON with analysis results
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Get parameters
        reference = request.form.get('reference', None)
        enable_diarization = request.form.get('enable_diarization', 'true').lower() == 'true'
        target_speaker = request.form.get('target_speaker', None)
        
        if target_speaker is not None:
            try:
                target_speaker = int(target_speaker)
            except ValueError:
                return jsonify({'error': 'target_speaker must be an integer'}), 400
        
        # Save uploaded file to temp
        temp_dir = tempfile.mkdtemp()
        filename = secure_filename(file.filename)
        audio_path = os.path.join(temp_dir, filename)
        file.save(audio_path)
        
        print(f"Analyzing: {filename}")
        print(f"  Reference: {reference or 'None'}")
        print(f"  Diarization: {enable_diarization}")
        print(f"  Target speaker: {target_speaker if target_speaker is not None else 'All'}")
        
        # Analyze
        analyzer = get_analyzer()
        result = analyzer.analyze(
            audio_path,
            reference_text=reference,
            enable_diarization=enable_diarization,
            target_speaker=target_speaker
        )
        
        # Cleanup
        os.remove(audio_path)
        os.rmdir(temp_dir)
        
        print(f"✅ Analysis complete: {result['overall_score']}/100")
        
        # Save result to history
        saved_filename = save_result(result)
        result['saved_filename'] = saved_filename
        print(f"💾 Result saved: {saved_filename}")
        
        return jsonify(result)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/speakers', methods=['POST'])
def detect_speakers():
    """
    Detect speakers in audio (diarization only, no analysis).
    
    Form data:
        file: audio file (required)
    
    Returns:
        JSON with speaker segments
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Save to temp
        temp_dir = tempfile.mkdtemp()
        filename = secure_filename(file.filename)
        audio_path = os.path.join(temp_dir, filename)
        file.save(audio_path)
        
        print(f"Detecting speakers in: {filename}")
        
        # Run diarization only
        analyzer = get_analyzer()
        analyzer._load_diarization()
        
        if analyzer.diarization_pipeline is None:
            return jsonify({'error': 'Speaker diarization not available (missing HF token)'}), 500
        
        speaker_segments = analyzer._diarize_speakers(audio_path)
        
        # Cleanup
        os.remove(audio_path)
        os.rmdir(temp_dir)
        
        # Calculate speaker stats
        speaker_stats = {}
        for seg in speaker_segments:
            speaker_id = seg['speaker']
            duration = seg['end'] - seg['start']
            
            if speaker_id not in speaker_stats:
                speaker_stats[speaker_id] = {
                    'id': speaker_id,
                    'total_time': 0,
                    'segments_count': 0
                }
            
            speaker_stats[speaker_id]['total_time'] += duration
            speaker_stats[speaker_id]['segments_count'] += 1
        
        return jsonify({
            'speakers': {
                'total': len(speaker_stats),
                'segments': speaker_segments,
                'stats': list(speaker_stats.values())
            }
        })
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def save_result(result: dict) -> str:
    """Save analysis result to JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analysis_{timestamp}.json"
    filepath = RESULTS_DIR / filename
    
    # Add metadata
    result['saved_at'] = datetime.now().isoformat()
    result['filename'] = filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    return filename


@app.route('/history', methods=['GET'])
def get_history():
    """Get list of all saved analysis results."""
    try:
        results = []
        
        # Scan results directory
        for filepath in sorted(RESULTS_DIR.glob("analysis_*.json"), reverse=True):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                results.append({
                    'filename': filepath.name,
                    'date': data.get('saved_at', data.get('analyzed_at', '')),
                    'score': data.get('overall_score', 0),
                    'errors': data.get('grammar', {}).get('total_errors', 0),
                    'transcript': data.get('transcript', '')[:100]  # Preview
                })
            except Exception as e:
                print(f"Error loading {filepath.name}: {e}")
                continue
        
        return jsonify(results)
    
    except Exception as e:
        print(f"❌ Error getting history: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/result/<filename>', methods=['GET'])
def get_result(filename):
    """Get specific analysis result."""
    try:
        # Security: only allow alphanumeric + underscore + .json
        if not filename.endswith('.json') or not all(c.isalnum() or c in '_.json' for c in filename):
            return jsonify({'error': 'Invalid filename'}), 400
        
        filepath = RESULTS_DIR / filename
        
        if not filepath.exists():
            return jsonify({'error': 'Result not found'}), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify(data)
    
    except Exception as e:
        print(f"❌ Error loading result: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("🚀 Starting English Practice Backend Server...")
    print("📍 http://localhost:8780")
    print("")
    
    # Check environment
    hf_token = os.getenv('HUGGINGFACE_TOKEN')
    if hf_token:
        print("✅ Hugging Face token found (speaker diarization enabled)")
    else:
        print("⚠️  Hugging Face token not found (speaker diarization disabled)")
        print("   Set HUGGINGFACE_TOKEN in .env to enable")
    
    print("")
    print("Endpoints:")
    print("  GET  /health")
    print("  POST /analyze")
    print("  POST /speakers")
    print("  GET  /history")
    print("  GET  /result/<filename>")
    print("")
    
    app.run(host='127.0.0.1', port=8780, debug=False)
