# 🎙️ Call Recording Setup Guide

This guide will help you set up **Call Recording Mode** for the English Practice app, which allows teachers to record online lessons (Zoom, Skype, Discord, etc.) and get automatic analysis for both teacher and student.

## Overview

To record **both sides** of an online call (your microphone + system audio from the app), you need to create an **Aggregate Device** that combines:

1. **Your microphone** (for your voice)
2. **BlackHole** virtual audio device (for system audio/app audio)

This setup captures everything in one stereo recording that can then be analyzed with speaker diarization.

---

## Step 1: Install BlackHole

BlackHole is a free, open-source virtual audio driver for macOS that allows apps to pass audio to other apps.

### Installation via Homebrew (Recommended)

```bash
brew install blackhole-2ch
```

### Manual Installation

1. Download BlackHole from: https://github.com/ExistentialAudio/BlackHole/releases
2. Choose **BlackHole 2ch** (stereo)
3. Open the downloaded `.pkg` file and follow the installer
4. Restart your Mac after installation

### Verify Installation

1. Open **Audio MIDI Setup** (press `Cmd+Space`, type "Audio MIDI")
2. You should see **BlackHole 2ch** in the list of devices

---

## Step 2: Create an Aggregate Device

An Aggregate Device combines multiple audio inputs into one virtual device.

### Steps:

1. **Open Audio MIDI Setup**
   - Press `Cmd+Space` and type "Audio MIDI Setup"
   - Or go to: `/Applications/Utilities/Audio MIDI Setup.app`

2. **Create Aggregate Device**
   - Click the **"+"** button at the bottom-left
   - Select **"Create Aggregate Device"**

3. **Configure the Aggregate Device**
   - **Name it:** `Call Recording Device` (or any name you prefer)
   
   - **Check these boxes (in this order):**
     - ✅ **Your Microphone** (e.g., "MacBook Pro Microphone" or external mic)
     - ✅ **BlackHole 2ch**
   
   - **Important:** Microphone should be first, BlackHole second
   
   - **Set Clock Source:** Select your microphone as the clock source (under "Drift Correction")

4. **Create Multi-Output Device (For Monitoring)**
   - Click the **"+"** button again
   - Select **"Create Multi-Output Device"**
   
   - **Name it:** `Call Output` (optional, for hearing yourself)
   
   - **Check these boxes:**
     - ✅ **Your Speakers/Headphones** (e.g., "MacBook Pro Speakers")
     - ✅ **BlackHole 2ch**
   
   - **Set Master Device:** Select your speakers/headphones

---

## Step 3: Configure Your Call App (Zoom/Skype/Discord)

To record the online lesson, you need to route your call app's audio through BlackHole.

### For Zoom:

1. Open **Zoom Settings** → **Audio**
2. **Microphone:** Select `Call Recording Device` (Aggregate Device)
3. **Speaker:** Select `Call Output` (Multi-Output Device)
4. This way you can hear the student and they can hear you, while everything is recorded

### For Discord:

1. Open **Discord Settings** → **Voice & Video**
2. **Input Device:** Select `Call Recording Device`
3. **Output Device:** Select `Call Output`

### For Skype:

1. Open **Skype Preferences** → **Audio & Video**
2. **Microphone:** Select `Call Recording Device`
3. **Speakers:** Select `Call Output`

### For Google Meet / Browser-based:

1. When joining a call, click the audio/video settings icon
2. Select **Microphone:** `Call Recording Device`
3. Select **Speakers:** `Call Output`

---

## Step 4: Test the Setup

Before your first lesson, **test the recording**:

1. **Open English Practice app** from menu bar
2. Click **"🎙️ Select Audio Device"**
3. Find and select your **"Call Recording Device"** (Aggregate Device)
4. Join a test call (or use system audio test)
5. Click **"📞 Start Call Recording"**
6. Speak for 10-20 seconds
7. Play some system audio (YouTube video, music)
8. Click **"⏹️ Stop Call"**
9. Check if the recording captured both your voice and system audio

---

## Step 5: Record a Real Lesson

Once everything is set up:

1. **Before the lesson:**
   - Make sure your call app is configured to use:
     - **Microphone:** `Call Recording Device`
     - **Speakers:** `Call Output`

2. **Start recording:**
   - Open **English Practice** menu bar app
   - Click **"📞 Start Call Recording"**
   - You'll see: `🔴 Recording 00:00` in the menu bar

3. **During the lesson:**
   - The timer will update: `🔴 Recording 05:32`, etc.
   - Teach as normal — both you and student are being recorded

4. **Stop recording:**
   - Click the menu bar icon
   - Click **"⏹️ Stop Call"**
   - The app will automatically analyze the recording

5. **View results:**
   - You'll get a notification with scores for both speakers:
     ```
     🎓 Урок завершён
     
     Ученик (Speaker 1): 3 ошибки (Grammar: 85/100)
     Преподаватель (Speaker 0): 1 ошибка (Grammar: 95/100)
     
     → Смотреть отчёт
     ```
   
   - Full reports are saved in: `~/.english_practice/call_recordings/`

---

## Troubleshooting

### Issue: Can't find Aggregate Device in English Practice

**Solution:**
- Make sure you created the Aggregate Device in Audio MIDI Setup
- Restart the English Practice app after creating the device
- Manually select it via **"🎙️ Select Audio Device"** menu

### Issue: Only recording my voice, not the student

**Solution:**
- Check that your call app (Zoom/Discord/Skype) is using **BlackHole** for output
- Make sure the **Multi-Output Device** includes BlackHole
- Test by playing a YouTube video — you should hear it AND it should be captured in the recording

### Issue: Can't hear the student during the call

**Solution:**
- Make sure you're using the **Multi-Output Device** (`Call Output`) in your call app's speaker settings
- This routes audio to both your speakers AND BlackHole (for recording)

### Issue: Echo or feedback during calls

**Solution:**
- Make sure you're using headphones, not speakers
- Check that "Drift Correction" is enabled in the Aggregate Device settings
- Reduce microphone volume if needed

### Issue: Recording is mono, not stereo

**Solution:**
- Make sure you installed **BlackHole 2ch** (not 16ch)
- Check that CHANNELS is set to 2 in the app code (should be by default for call recording)

### Issue: Analysis shows only one speaker

**Solution:**
- This is expected if only one person spoke during the call
- If both people spoke but only one speaker detected:
  - Try speaking louder or adjusting microphone levels
  - Check that diarization is enabled in the backend (requires Hugging Face token)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Computer                            │
│                                                             │
│  ┌──────────────┐         ┌──────────────────────┐        │
│  │ Your         │────────▶│  Call Recording      │        │
│  │ Microphone   │         │  Device (Aggregate)  │◀───────┼─ English Practice App
│  └──────────────┘         │                      │        │     (Records from this)
│                           │  + BlackHole 2ch     │        │
│  ┌──────────────┐         └──────────────────────┘        │
│  │ Zoom/Discord │                                          │
│  │ (Call App)   │         ┌──────────────────────┐        │
│  │              │────────▶│  Call Output         │        │
│  │ Output       │         │  (Multi-Output)      │        │
│  └──────────────┘         │                      │        │
│                           │  → Your Speakers     │        │
│                           │  → BlackHole ────────┼────┐   │
│                           └──────────────────────┘    │   │
│                                                       │   │
└───────────────────────────────────────────────────────┼───┘
                                                        │
                                      System audio goes to BlackHole
                                      which is part of Aggregate Device
                                      so it gets recorded together with mic
```

---

## Advanced: Privacy & Data Security

### Where are recordings saved?

- **Quick Practice:** `~/.english_practice/recordings/`
- **Call Recordings:** `~/.english_practice/call_recordings/`

### How to delete old recordings?

```bash
# Delete all call recordings older than 30 days
find ~/.english_practice/call_recordings/ -name "*.wav" -mtime +30 -delete
```

### Is audio sent to the cloud?

- **No.** All recordings stay on your Mac
- The backend analysis runs **locally** on your machine
- Only language analysis is performed (grammar/pronunciation checking)
- Student data never leaves your computer

### GDPR / Student Privacy Considerations

If you're recording lessons with students:

1. **Inform students** that the lesson will be recorded
2. **Get consent** before starting recording
3. **Store recordings securely** (the app saves them in a hidden folder by default)
4. **Delete recordings** after analysis if not needed for long-term review
5. Consider using the **Quick Practice mode** for students to self-record instead

---

## Summary

✅ **Install BlackHole** (virtual audio driver)  
✅ **Create Aggregate Device** (Microphone + BlackHole)  
✅ **Create Multi-Output Device** (Speakers + BlackHole)  
✅ **Configure call app** to use these devices  
✅ **Test recording** before first lesson  
✅ **Record lessons** and get automatic analysis  

**Need help?** Check the [English Practice GitHub Issues](https://github.com/your-repo) or contact support.

---

## Reference Links

- **BlackHole:** https://github.com/ExistentialAudio/BlackHole
- **Audio MIDI Setup Guide (Apple):** https://support.apple.com/guide/audio-midi-setup/
- **macOS Aggregate Devices:** https://support.apple.com/en-us/HT202000

---

**Happy teaching! 🎓**
