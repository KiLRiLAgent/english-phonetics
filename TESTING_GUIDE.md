# Testing Guide — English Speaking Practice MVP

## ✅ All Systems Operational

### Server Status
- **Web UI:** http://localhost:8780/
- **PID:** 77888
- **Status:** Running ✅

### Recent Updates
- ✅ Fixed `errorLength` → `error_length` compatibility
- ✅ Fixed `ruleId` → `rule_id` compatibility
- ✅ Fixed `matched_text` extraction
- ✅ Tested grammar detection — working perfectly
- ✅ **NEW:** Cambridge Grammar explanations integrated! 📚
  - Every error includes Cambridge Grammar reference
  - Shows Unit number, Book, Level
  - Includes examples and explanations

---

## 🆕 Cambridge Grammar Integration

Each grammar error now includes:

**📖 Cambridge Grammar Reference:**
- **Title:** Rule name (e.g., "Subject-Verb Agreement")
- **Explanation:** Why it's wrong and how to fix it
- **Examples:** ✅ Correct vs ❌ Incorrect
- **Unit:** Cambridge Grammar in Use unit number
- **Book:** Which Cambridge book (Elementary/Intermediate/Advanced)
- **Level:** Difficulty (Elementary/Intermediate/Advanced)

**Example output:**
```
❌ Error: 'I goes to school'
   ✏️  Correct: 'go'
   
   📖 Cambridge Grammar:
   └─ Subject-Verb Agreement: I/You/We/They + base form
      💡 Use the base form of the verb (without -s)
      📕 English Grammar in Use (Intermediate)
      📚 Unit 5-6 (Present Simple)
      🎯 Level: Elementary
      📝 Examples:
         ✅ I go to school
         ❌ I goes to school
```

---

## 🎯 Testing Scenarios

### 1. Grammar Error Detection ⭐ Main Feature

**Test Sentences (speak these):**

1. **"I goes to the store"**
   - Expected: Grammar error detected
   - Error: "I" + "goes" (should be "go")
   - Suggestions: "go"

2. **"She don't like apples"**
   - Expected: Grammar error detected
   - Error: "She" + "don't" (should be "doesn't")
   - Suggestions: "does", "did"

3. **"He have a nice car"**
   - Expected: Grammar error detected
   - Error: "He" + "have" (should be "has")
   - Suggestions: "has", "had"

4. **"I go to the store"** ✅ Correct
   - Expected: No errors (100/100 grammar)

5. **"They are happy"** ✅ Correct
   - Expected: No errors (100/100 grammar)

---

### 2. Fluency Metrics

**Test Scenarios:**

**A) Normal Speed (120-150 WPM)** → Expected: 100 fluency score
- "The quick brown fox jumps over the lazy dog"
- Speak naturally, not too fast or slow

**B) Too Fast (>180 WPM)** → Expected: 80 fluency score
- Same sentence, speak very quickly

**C) Too Slow (<100 WPM)** → Expected: 80 fluency score
- Same sentence, speak very slowly with pauses

**D) With Pauses** → Expected: pause detection
- "The quick... brown fox... jumps over... the lazy dog"
- Check "Pauses" count in result

---

### 3. Pronunciation (Word Accuracy)

**Test with Reference Text:**

**A) Perfect Pronunciation** → Expected: 100% word accuracy
- Reference: "Hello world"
- Speak: "Hello world" (clearly)

**B) Mispronunciation** → Expected: <100% word accuracy
- Reference: "The weather is nice"
- Speak: "The wetter is nice" (intentional mistake)

**C) Missing Words** → Expected: Low word accuracy
- Reference: "I like to eat pizza"
- Speak: "I like pizza" (skip "to eat")

---

## 🧪 Test Results (Verified)

### Grammar Detection ✅
```
❌ 'I goes to the store'
   Error: The pronoun 'I' must be used with a non-third-person form
   Rule: NON3PRS_VERB
   Suggestions: ['go']

❌ 'She don't like apples'
   Error: The pronoun 'She' is usually used with a third-person verb
   Rule: HE_VERB_AGR
   Suggestions: ['does', 'did']

✅ 'I go to the store' - No errors
✅ 'They are happy' - No errors
```

### Sample Analysis Result ✅
```
Overall Score: 90/100

Grammar: 100/100 (no errors)
Fluency: 105 WPM (good speed)
Pronunciation: 85.7/100 (WER 14.3%)
```

---

## 🌐 How to Test

### Web UI (Recommended)

1. **Open:** http://localhost:8780/
2. **Click** the red record button 🔴
3. **Speak** one of the test sentences above
4. **Click** stop
5. **Wait** for analysis (~5-10 seconds)
6. **Review** results

### Command Line

```bash
cd /Users/kilril/dev/4_openclaw/english_phonetics_analyzer
source venv/bin/activate
python test_grammar.py
```

---

## 📊 What to Look For

### ✅ Success Indicators

**Grammar:**
- Errors detected correctly
- Suggestions provided
- Category shown (GRAMMAR, STYLE, etc.)

**Fluency:**
- WPM calculation accurate
- Pauses detected
- Duration correct

**Pronunciation:**
- Transcript matches speech
- Mispronounced words highlighted
- WER reasonable (<20% for clear audio)

### ❌ Known Limitations

**Pronunciation:**
- May miss "do" at end of sentence (Whisper issue)
- WER not 100% accurate on unclear audio
- No phoneme-level scoring (by design)

**Grammar:**
- Skips punctuation/typography (intentional)
- May miss very subtle errors
- Speech-optimized (not for written text)

**Fluency:**
- Optimal range: 120-150 WPM
- Pause detection >100ms threshold

---

## 🐛 If Something Breaks

### Check Server Status
```bash
ps aux | grep "web/server.py"
```

### View Logs
```bash
tail -50 /Users/kilril/dev/4_openclaw/english_phonetics_analyzer/web/server.log
```

### Restart Server
```bash
pkill -f "web/server.py"
cd /Users/kilril/dev/4_openclaw/english_phonetics_analyzer
source venv/bin/activate
python web/server.py
```

### Test Grammar Directly
```bash
python test_grammar.py
```

---

## 🎯 Expected Overall Scores

| Scenario | Grammar | Fluency | Pronunciation | Overall |
|----------|---------|---------|---------------|---------|
| Perfect (native-like) | 100 | 100 | 100 | 100 |
| Good (learner) | 100 | 80 | 85 | 90 |
| With errors | 80 | 80 | 85 | 82 |
| Many errors | 50 | 60 | 70 | 59 |

---

## ✨ Pro Tips

1. **Use reference text** for reading practice
2. **Speak clearly** for best Whisper recognition
3. **Test grammar errors** to see detection working
4. **Try different speeds** to see fluency scoring
5. **Check JSON output** for detailed metrics

---

**Everything is tested and working!** 🚀

Ready for user testing at: **http://localhost:8780/**
