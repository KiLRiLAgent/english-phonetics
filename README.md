# English Phonetics & Grammar Analyzer

AI-powered tool for analyzing English pronunciation (phoneme-level) and grammar.

## Stack
- **Whisper** — speech-to-text transcription
- **Montreal Forced Aligner (MFA)** — phoneme-level alignment
- **GOP scoring** — pronunciation quality per phoneme
- **LanguageTool** — grammar error detection (local server)

## Setup
```bash
pip install -r requirements.txt

# Install MFA
conda install -c conda-forge montreal-forced-aligner

# Download MFA English models
mfa model download acoustic english_us_arpa
mfa model download dictionary english_us_arpa

# Start LanguageTool server (Docker)
docker run -d -p 8081:8010 erikvl87/languagetool
```

## Usage
```bash
python analyze.py audio.wav
```

## API Keys needed
None — fully local/open source.
