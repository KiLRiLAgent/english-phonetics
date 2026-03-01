# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered English speech analysis tool for ESL learners. Analyzes audio recordings for grammar, pronunciation, and fluency. Provides educational feedback referencing Cambridge Grammar in Use.

## Key Commands

```bash
# Setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Then fill in API keys

# Run backend API server (port 8780)
python backend/server.py

# Run web UI (port 8780, uses analyzer_mvp directly)
python web/server.py

# Run macOS menu bar app (connects to backend)
python macos_app/english_practice_app_microservice.py

# Run lecture transcript viewer (port 8899)
python lecture_server.py

# CLI analysis
python analyze.py audio.wav
python analyze.py audio.wav --reference "expected text"

# Build macOS .app bundle
cd macos_app && python setup_microservice.py py2app

# Run tests (no test runner configured — individual scripts)
python test_grammar.py
python test_cambridge.py
python test_call_recording.py
python test_diarization_errors.py
```

## Architecture

**Microservice pattern:** Lightweight frontends (macOS menu bar app, web UI) communicate via HTTP with a Flask backend that runs the heavy ML analysis pipeline.

### Analysis Pipeline (in `analyzer_diarization.py`)

Audio → Whisper transcription → Speaker diarization (pyannote) → Multi-layer grammar analysis → Fluency metrics → Pronunciation scoring → Weighted overall score

### Multi-Layer Grammar Checking

1. **LanguageTool** — rule-based grammar checking (200+ rules)
2. **CustomGrammarChecker** (`custom_grammar_rules.py`) — ESL-specific patterns LanguageTool misses
3. **GECToR** (`gector_checker.py`) — ML transformer-based error detection (optional, `USE_ML_CHECKER=true`)
4. **AIGrammarFilter** (`ai_grammar_filter.py`) — OpenAI/Ollama verification to filter false positives
5. **SmartGrammarFilter** (`smart_filter.py`) — NER + heuristic post-processing

### Scoring Formula

```
Overall = Grammar × 0.40 + Pronunciation × 0.35 + Fluency × 0.25
```

### Key Files

| Purpose | File |
|---------|------|
| Production analyzer (with diarization) | `analyzer_diarization.py` |
| MVP analyzer (single speaker) | `analyzer_mvp.py` |
| Backend REST API | `backend/server.py` |
| macOS menu bar app | `macos_app/english_practice_app_microservice.py` |
| Web UI server | `web/server.py` |
| Cambridge grammar rules (37 rules) | `cambridge_grammar_rules.py` |
| Custom ESL rules | `custom_grammar_rules.py` |
| ML grammar checker | `gector_checker.py` |
| AI false-positive filter | `ai_grammar_filter.py` |
| NER-based filter | `smart_filter.py` |
| CLI entry point | `analyze.py` |

### Backend API Endpoints

- `POST /analyze` — analyze audio file (form data: `file`, optional `reference`, `enable_diarization`, `target_speaker`)
- `POST /speakers` — speaker diarization only
- `GET /health` — server status
- `GET /history` — past analysis results
- `GET /result/<filename>` — specific saved result

### User Data Directories

- `~/.english_practice/recordings/` — quick practice recordings + reports
- `~/.english_practice/call_recordings/` — call recording mode files
- `~/.english_practice/results/` — backend analysis results (JSON)

## Environment Variables

Configured via `.env` (see `.env.example`):

- `WHISPER_MODEL` — Whisper model size (default: `large-v3-turbo`)
- `OPENAI_API_KEY` — for AI grammar filtering
- `HUGGINGFACE_TOKEN` — for pyannote speaker diarization
- `USE_AI_FILTER` — enable/disable AI filtering (default: true)
- `USE_ML_CHECKER` — enable/disable GECToR ML checker
- `AI_MODEL` — OpenAI model for filtering (default: `gpt-4o-mini`)

## Design Decisions

- **Lazy loading:** ML models (Whisper, pyannote, GECToR) load on first request, not at startup
- **Multiple analyzer versions:** `analyzer_diarization.py` is production; `analyzer_mvp.py` is the single-speaker fallback; older versions (`analyzer_v2.py`, `analyzer_simple.py`) exist but are not primary
- **No CI/CD, no test runner:** Tests are standalone Python scripts in the project root
- **No Docker:** App runs natively on macOS; Docker only used optionally for LanguageTool server
