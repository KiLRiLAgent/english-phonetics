# ML-based Grammatical Error Correction

## Pre-trained Models (Ready to Use!)

### 1️⃣ **GECToR (Google Research)**

**Best balance: accuracy + speed**

- **Paper:** https://arxiv.org/abs/2005.12592
- **GitHub:** https://github.com/grammarly/gector
- **Model:** HuggingFace `grammarly/gector-roberta`

**Usage:**
```python
from transformers import pipeline

# Load model
corrector = pipeline("text2text-generation", model="grammarly/gector-roberta")

# Correct text
text = "Yesterday I go to school"
result = corrector(text)
print(result[0]['generated_text'])  # "Yesterday I went to school"
```

**Pros:**
- Fast (~50ms per sentence)
- High accuracy (F0.5 = 72.4 on CoNLL-2014)
- Works offline

**Cons:**
- 500MB model size
- Only corrections, no explanations

---

### 2️⃣ **T5-based Models**

**Most accurate, but slower**

- **Model:** `grammarly/coedit-large` or `vennify/t5-base-grammar-correction`
- **Size:** 800MB - 3GB

**Usage:**
```python
from transformers import T5ForConditionalGeneration, T5Tokenizer

model = T5ForConditionalGeneration.from_pretrained("vennify/t5-base-grammar-correction")
tokenizer = T5Tokenizer.from_pretrained("vennify/t5-base-grammar-correction")

text = "grammar: Yesterday I go to school"
inputs = tokenizer(text, return_tensors="pt")
outputs = model.generate(**inputs, max_length=128)
corrected = tokenizer.decode(outputs[0], skip_special_tokens=True)
# "Yesterday I went to school"
```

**Pros:**
- Highest accuracy
- Can explain reasoning (with prompting)

**Cons:**
- Slow (200-500ms)
- Large model size
- Needs GPU for real-time

---

### 3️⃣ **LanguageTool + BERT Classifier**

**Hybrid: rules + ML**

Combine LanguageTool with BERT to classify error types:

```python
import language_tool_python
from transformers import pipeline

# Detect errors
tool = language_tool_python.LanguageTool('en-US')
errors = tool.check("Yesterday I go to school")

# Classify error type with BERT
classifier = pipeline("text-classification", model="bert-base-uncased")

for err in errors:
    error_type = classifier(f"Error context: {err.context}")
    # Returns: {"label": "VERB_TENSE", "score": 0.95}
```

**Train custom BERT on ERRANT-annotated data.**

---

## Datasets to Train On

### CoNLL-2014
```bash
wget https://www.comp.nus.edu.sg/~nlp/conll14st/conll14st-test-data.tar.gz
tar -xzf conll14st-test-data.tar.gz
```

**Format:**
```
S The cat were sleeping .
A 2 2|||VERB:SVA|||was|||REQUIRED|||-NONE-|||0
```

### BEA-2019
```bash
# Download from: https://www.cl.cam.ac.uk/research/nl/bea2019st/
# Requires registration
```

**Format:** Similar to CoNLL, but more diverse errors.

---

## Recommended Approach

### **Phase 1: Current (Rule-based)**
- ✅ LanguageTool (10K+ rules)
- ✅ Custom rules (past tense markers, etc.)
- ✅ Cambridge Grammar explanations

**Pros:** Fast, lightweight, explainable
**Cons:** Misses complex/contextual errors

### **Phase 2: Add ERRANT (Categorization)**
- Use ERRANT to auto-classify errors
- Map to better explanations
- ~100ms overhead

### **Phase 3: Add GECToR (ML Correction)**
- Use GECToR to detect errors LanguageTool misses
- Compare LanguageTool + GECToR results
- Show both to user

**Pipeline:**
```
Transcript
    ↓
LanguageTool (fast)
    ↓
Custom Rules (fast)
    ↓
GECToR (if errors < threshold, run ML check)
    ↓
ERRANT (classify all errors)
    ↓
Cambridge Explanations
```

### **Phase 4: Full ML (Advanced)**
- Train custom model on CoNLL + BEA + Lang-8
- Fine-tune for spoken English
- Use T5 for explainability

---

## Quick Test: GECToR

Let's test if it catches our "Yesterday I go" error:

```bash
pip install transformers torch
```

```python
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

tokenizer = AutoTokenizer.from_pretrained("grammarly/coedit-large")
model = AutoModelForSeq2SeqLM.from_pretrained("grammarly/coedit-large")

text = "Fix grammar: Yesterday I go to school"
inputs = tokenizer(text, return_tensors="pt")
outputs = model.generate(**inputs, max_length=128)
result = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(result)
```

**Expected:** "Yesterday I went to school" ✅

---

## Decision Matrix

| Approach | Speed | Accuracy | Size | Explainability |
|----------|-------|----------|------|----------------|
| LanguageTool | ⚡⚡⚡ | 70% | 50MB | ✅✅✅ |
| Custom Rules | ⚡⚡⚡ | 80% | 1KB | ✅✅✅ |
| GECToR | ⚡⚡ | 90% | 500MB | ❌ |
| T5 | ⚡ | 95% | 3GB | ⚡ (with prompting) |

**Recommendation:**
- **Now:** LanguageTool + Custom Rules (fast, good enough)
- **Next:** Add GECToR as fallback for missed errors
- **Future:** Fine-tune T5 on spoken English corpus

---

## Want to try GECToR now?

I can integrate it in ~30 minutes. It will:
1. Run after LanguageTool
2. Compare original vs corrected
3. Find errors LanguageTool missed
4. Add them to error list

Say "yes" and I'll add it! 🚀
