# Web Server Integration Checklist

## Current state:

- ❌ Wav2Vec2 (phoneme_gop.py) — unreliable, gives false positives
- ✅ Gentle Docker — downloading, will be ready soon

## Changes needed:

### 1. Update `web/server.py`

**Before:**
```python
from phoneme_gop import get_scorer
PHONEME_SCORER = get_scorer()
```

**After:**
```python
from phoneme_gentle import get_scorer
PHONEME_SCORER = get_scorer()
```

### 2. Add reference text input

Currently, the web UI only records audio.  
Gentle **requires reference text** (what the student should say).

**UI Flow:**
1. Teacher provides text: "Don't you tell me what to do"
2. Student records themselves reading it
3. Gentle aligns audio ↔ text
4. System shows which words were pronounced correctly

**HTML changes** (`web/index.html`):

Add input field:
```html
<textarea id="referenceText" placeholder="Enter text to read..."></textarea>
<button onclick="startRecording()">🎙 Record</button>
```

**Server changes** (`web/server.py`):

Update `/api/analyze` endpoint:
```python
def do_POST(self):
    if self.path == "/api/analyze":
        # Get audio + reference text from multipart form
        audio_data = ...
        reference_text = ...
        
        # Score with Gentle
        result = PHONEME_SCORER.score_pronunciation(
            audio_path, 
            reference_text
        )
```

### 3. Handle Gentle server checks

Before scoring, check if Gentle is running:

```python
if not PHONEME_SCORER.check_server():
    return {"error": "Gentle server not running. Start with: docker run -p 8765:8765 lowerquality/gentle"}
```

### 4. Update scoring thresholds

Gentle gives different output than Wav2Vec2.

**Scoring:**
- `case == "success"` → Green (90-100)
- Duration ratio 0.7-1.5 → Green
- Duration ratio 0.5-2.0 → Yellow
- `case == "not-found-in-audio"` → Red (0)

## Testing plan:

### 1. Start Gentle

```bash
docker run -p 8765:8765 lowerquality/gentle
```

### 2. Test with curl

```bash
curl -F "audio=@test.wav" \
     -F "transcript=hello world" \
     http://localhost:8765/transcriptions?async=false
```

Expected: JSON with aligned words + phonemes

### 3. Test Python integration

```bash
cd /Users/kilril/dev/4_openclaw/english_phonetics_analyzer
./venv/bin/python3 phoneme_gentle.py
```

### 4. Test web UI

1. Start web server: `./venv/bin/python3 web/server.py`
2. Open http://localhost:8780
3. Enter text: "Don't you tell me what to do"
4. Record audio (say it twice: correct, then with accent)
5. Check results: first words green, second words red

## Deployment:

### Local (development):

```bash
# Terminal 1: Gentle
docker run -p 8765:8765 lowerquality/gentle

# Terminal 2: Web server
cd /Users/kilril/dev/4_openclaw/english_phonetics_analyzer
./venv/bin/python3 web/server.py
```

### Production (VPS):

```bash
# Background Gentle
docker run -d --restart=always \
  -p 8765:8765 \
  --name gentle \
  lowerquality/gentle

# Background web server (use systemd/supervisor)
```

## Expected timeline:

- ✅ Docker + Gentle setup: **10-15 minutes** (almost done)
- ⏳ Python integration: **15-20 minutes**
- ⏳ Web UI updates: **20-30 minutes**
- ⏳ Testing: **10-15 minutes**

**Total: ~1-1.5 hours from now**

## Risks:

1. **Gentle might not work on Mac ARM** (M1/M2)
   - Mitigation: Image is multi-arch, should work
   
2. **Alignment might be slow** (3-5s per audio)
   - Mitigation: Acceptable for demo, can optimize later
   
3. **Gentle might require exact word match**
   - Mitigation: If student says "gonna" instead of "going to", it might fail
   - Solution: Normalize text before alignment

## Success criteria:

✅ Student records "Don't you tell me what to do" correctly → all green  
✅ Student says it with Indian accent → red on mispronounced words  
✅ System shows phoneme-level feedback ("expected /t/, got /d/")
