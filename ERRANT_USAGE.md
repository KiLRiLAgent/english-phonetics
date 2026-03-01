# ERRANT Integration Plan

## What is ERRANT?

ERRANT (ERRor ANnotation Toolkit) automatically classifies grammatical errors into linguistic categories.

**GitHub:** https://github.com/chrisjbryant/errant

## Error Categories (55 types)

- **VERB:** verb form, tense, subject-verb agreement
- **NOUN:** number (singular/plural)
- **DET:** article errors (a/an/the)
- **PREP:** preposition errors
- **ADJ:** adjective form
- **ADV:** adverb form
- **CONJ:** conjunction errors
- **PRON:** pronoun errors
- **SPELL:** spelling mistakes
- **ORTH:** orthography (capitalization, etc.)
- **PUNCT:** punctuation
- **WO:** word order
- **OTHER:** unclassified

## Example

**Original:** Yesterday I go to school
**Corrected:** Yesterday I went to school

**ERRANT Output:**
```
Error type: VERB:TENSE
Original span: go
Corrected span: went
Position: token 2
```

## Integration Steps

### 1. Install ERRANT

```bash
pip install errant
python -m spacy download en_core_web_sm
```

### 2. Annotate Errors

```python
import errant

# Initialize annotator
annotator = errant.load('en')

# Original and corrected sentences
orig = annotator.parse("Yesterday I go to school")
cor = annotator.parse("Yesterday I went to school")

# Align and classify edits
edits = annotator.annotate(orig, cor)

for e in edits:
    print(f"Type: {e.type}")          # VERB:TENSE
    print(f"Original: {e.o_str}")     # go
    print(f"Correction: {e.c_str}")   # went
```

### 3. Enhance Our Explanations

Use ERRANT types to provide better explanations:

```python
ERRANT_EXPLANATIONS = {
    "VERB:TENSE": {
        "title": "Verb Tense Error",
        "explanation": "Wrong tense used for the context",
        "examples": [...]
    },
    "VERB:SVA": {  # Subject-Verb Agreement
        "title": "Subject-Verb Agreement",
        "explanation": "Verb doesn't match the subject",
        "examples": [...]
    },
    "NOUN:NUM": {  # Number
        "title": "Singular/Plural Error",
        "explanation": "Wrong noun number",
        "examples": [...]
    }
}
```

### 4. Workflow

```
User speech
    ↓ Whisper
Transcript: "Yesterday I go"
    ↓ LanguageTool / Custom Rules
Error detected: "go" → "went"
    ↓ ERRANT
Error type: VERB:TENSE
    ↓ Our explanation DB
Full explanation + examples + Cambridge ref
```

## Benefits

1. **Better categorization** — 55 fine-grained types
2. **Aligned with research** — standard NLP taxonomy
3. **Easier to extend** — add explanations per category
4. **ML-ready** — can train models later

## Trade-offs

- **Dependency:** Requires spaCy model (100MB)
- **Speed:** Adds ~100ms per analysis
- **Complexity:** More code to maintain

## Recommendation

**Phase 1 (Current):** Rule-based (LanguageTool + Custom)
**Phase 2:** Add ERRANT for better categorization
**Phase 3:** ML model trained on CoNLL/BEA datasets

---

**Start small, scale when needed.**
