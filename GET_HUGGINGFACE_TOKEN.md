# How to Get Hugging Face Token (for Speaker Diarization)

**Speaker diarization** uses `pyannote.audio` which requires a free Hugging Face account.

## Steps:

### 1. Create Account
Go to: https://huggingface.co/join

### 2. Accept Model License
Visit: https://huggingface.co/pyannote/speaker-diarization-3.1

Click: **"Agree and access repository"**

### 3. Get Access Token
1. Go to: https://huggingface.co/settings/tokens
2. Click: **"New token"**
3. Name: `openclaw-diarization` (or any name)
4. Type: **Read**
5. Click: **"Generate"**
6. **Copy the token** (starts with `hf_...`)

### 4. Save Token to .env

```bash
cd /Users/kilril/dev/4_openclaw/english_phonetics_analyzer
echo "HUGGINGFACE_TOKEN=hf_your_token_here" >> .env
```

**Replace `hf_your_token_here` with your actual token!**

### 5. Verify

```bash
python -c "from pyannote.audio import Pipeline; print('✅ Token works!')"
```

---

## Why Needed?

Speaker diarization identifies **who is speaking when** in audio:
- Separates your voice from others during calls
- Adds timestamps to each speaker segment
- Allows analyzing only YOUR speech

**Free tier:** Unlimited use for research/personal projects.
