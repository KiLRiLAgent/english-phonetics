# Gentle Integration Guide

## What is Gentle?

Gentle is a robust forced aligner built on Kaldi.

**Key features:**
- ✅ **Phoneme-level** alignment (exactly what we need!)
- ✅ **Pre-built** Docker image (no compilation nightmares)
- ✅ **HTTP API** (easy integration)
- ✅ **Word + phoneme timestamps**

## Architecture:

```
┌──────────────┐
│ Gentle       │
│ Docker       │  Port 8765
│ Container    │◄─────────┐
└──────────────┘          │
                          │ HTTP POST
                          │
┌──────────────┐          │
│ Web Server   │──────────┘
│ (server.py)  │
└──────────────┘
      │
      ▼
┌──────────────┐
│ Student      │
│ Browser      │
└──────────────┘
```

## Installation:

### 1. Start Docker Desktop

```bash
open -a Docker
```

### 2. Pull Gentle image

```bash
docker pull lowerquality/gentle
```

### 3. Run Gentle server

```bash
docker run -p 8765:8765 lowerquality/gentle
```

Server will be available at `http://localhost:8765`

## API Usage:

### Request:

```bash
curl -F "audio=@recording.wav" \
     -F "transcript=hello world" \
     http://localhost:8765/transcriptions?async=false
```

### Response:

```json
{
  "words": [
    {
      "word": "hello",
      "case": "success",
      "start": 0.0,
      "end": 0.5,
      "phones": [
        {"phone": "HH", "duration": 0.08},
        {"phone": "AH", "duration": 0.10},
        {"phone": "L", "duration": 0.12},
        {"phone": "OW", "duration": 0.20}
      ]
    },
    {
      "word": "world",
      "case": "success",
      "start": 0.6,
      "end": 1.0,
      "phones": [...]
    }
  ],
  "transcript": "hello world"
}
```

## Integration with web server:

### `phoneme_gentle.py`:

Handles communication with Gentle API:
- Sends audio + reference text
- Receives phoneme-level alignment
- Scores pronunciation based on alignment success

### `web/server.py`:

Replace `PHONEME_SCORER` import:

```python
# OLD:
# from phoneme_gop import get_scorer

# NEW:
from phoneme_gentle import get_scorer

PHONEME_SCORER = get_scorer()
```

## Scoring logic:

1. **Aligned word** (case="success"):
   - Gentle found the word in audio → pronunciation is correct
   - Score based on duration (too fast/slow = lower score)
   - GREEN (score ≥ 75)

2. **Not found** (case="not-found-in-audio"):
   - Word was skipped or completely mispronounced
   - RED (score = 0)

3. **Partial match**:
   - Word found but with issues
   - YELLOW (score 50-74)

## Advantages over Wav2Vec2:

| Feature | Wav2Vec2 | Gentle |
|---------|----------|--------|
| Phoneme-level | ❌ Unreliable | ✅ Accurate |
| Reference text | Optional | Required |
| False positives | High | Low |
| Setup | Easy | Docker |
| Speed | Fast (~1s) | Slower (~3-5s) |

## Testing:

```bash
# 1. Start Gentle
docker run -p 8765:8765 lowerquality/gentle

# 2. Test with curl
curl -F "audio=@test.wav" \
     -F "transcript=test phrase" \
     http://localhost:8765/transcriptions?async=false

# 3. Test Python integration
cd /Users/kilril/dev/4_openclaw/english_phonetics_analyzer
./venv/bin/python3 phoneme_gentle.py
```

## Production deployment:

For production, run Gentle as a background service:

```bash
docker run -d --restart=always \
  -p 8765:8765 \
  --name gentle \
  lowerquality/gentle
```

This will:
- Run in background (`-d`)
- Auto-restart on crash (`--restart=always`)
- Persist across reboots

## Limitations:

- ⏱️ **Slower than Wav2Vec2** (3-5 seconds per audio)
- 🐳 **Requires Docker** (not standalone Python)
- 💾 **Memory usage** (~2GB for Docker image)

But these are acceptable tradeoffs for **accuracy**.

## Next steps:

1. ✅ Install Docker + Gentle
2. ⏳ Test alignment with sample audio
3. ⏳ Integrate into web server
4. ⏳ Deploy to production
