#!/usr/bin/env python3
"""
Generate complete grammar rules database using AI.
Creates explanations for all LanguageTool error codes.
"""

import language_tool_python
import json

# All detected rule codes
RULE_CODES = [
    "ADMIT_ENJOY_VB", "AFRAID_FROM_OF", "AGREEMENT_SENT_START",
    "BEEN_PART_AGREEMENT", "BETWEEN_YOU_AND_I", "CONDITIONAL_CLAUSE",
    "CONFUSION_OF_ME_I", "DEPEND_ON", "DOUBLE_NEGATIVE", "EN_A_VS_AN",
    "FEWER_LESS", "GOOD_IN_AT", "HAVE_PART_AGREEMENT", "HE_VERB_AGR",
    "IT_IS", "I_AM_VB", "MANY_NN_U", "MD_BASEFORM", 
    "MISSING_TO_BEFORE_A_VERB", "MORFOLOGIK_RULE_EN_US", 
    "MOST_COMPARATIVE", "MOST_SUPERLATIVE", "MUCH_COUNTABLE",
    "MUST_HAVE_TO", "NON3PRS_VERB", "PERS_PRONOUN_AGREEMENT",
    # Add more common ones
    "DID_BASEFORM", "THE", "PREP", "MODAL_VERB_BASEFORM",
    "WORD_ORDER", "PLURAL_NOUN", "TO_BASEFORM", "COMPARATIVE",
    "BASE_FORM", "PAST_PARTICIPLE", "HAVE_PAST_PARTICIPLE",
]

# Template for generating explanations
EXPLANATION_TEMPLATE = {
    "title": "",
    "explanation": "",
    "examples": [],
    "cambridge_unit": "",
    "book": "English Grammar in Use (Intermediate)",
    "difficulty": "Intermediate"
}


# Manual explanations for common rules
MANUAL_EXPLANATIONS = {
    "ADMIT_ENJOY_VB": {
        "title": "Verb + Gerund (enjoy swimming, not enjoy to swim)",
        "explanation": (
            "Some verbs (enjoy, admit, avoid, finish, etc.) must be followed by gerund (-ing form), "
            "not infinitive (to + verb)."
        ),
        "examples": [
            "✅ I enjoy swimming",
            "✅ She admitted making a mistake",
            "✅ We avoid eating fast food",
            "❌ I enjoy to swim",
            "❌ She admitted to make a mistake"
        ],
        "cambridge_unit": "Unit 52-53 (Verb + -ing or to...)",
        "difficulty": "Intermediate"
    },
    
    "AFRAID_FROM_OF": {
        "title": "Afraid OF (not afraid FROM)",
        "explanation": (
            "The correct preposition with 'afraid' is OF, not FROM. "
            "Many adjectives require specific prepositions."
        ),
        "examples": [
            "✅ I'm afraid of spiders",
            "✅ She's afraid of flying",
            "❌ I'm afraid from spiders",
            "❌ She's afraid from flying"
        ],
        "cambridge_unit": "Unit 128-135 (Prepositions)",
        "difficulty": "Elementary"
    },
    
    "GOOD_IN_AT": {
        "title": "Good AT (not good IN)",
        "explanation": (
            "Use 'good AT' for skills and activities, not 'good IN'. "
            "We also say 'bad AT', 'terrible AT', 'excellent AT'."
        ),
        "examples": [
            "✅ I'm good at math",
            "✅ She's good at playing piano",
            "❌ I'm good in math",
            "❌ She's good in playing piano"
        ],
        "cambridge_unit": "Unit 129 (Adjective + preposition)",
        "difficulty": "Elementary"
    },
    
    "DEPEND_ON": {
        "title": "Depend ON (not depend OF)",
        "explanation": (
            "The correct preposition with 'depend' is ON. "
            "'It depends on the weather' = the weather determines the result."
        ),
        "examples": [
            "✅ It depends on you",
            "✅ Success depends on hard work",
            "❌ It depends of you",
            "❌ Success depends from hard work"
        ],
        "cambridge_unit": "Unit 132 (Verb + preposition)",
        "difficulty": "Elementary"
    },
    
    "DOUBLE_NEGATIVE": {
        "title": "Double Negatives (don't say 'don't have nothing')",
        "explanation": (
            "In standard English, don't use two negatives together. "
            "Use 'anything' with 'don't', not 'nothing'."
        ),
        "examples": [
            "✅ I don't have anything",
            "✅ She didn't do anything",
            "✅ I have nothing (one negative)",
            "❌ I don't have nothing",
            "❌ She didn't do nothing"
        ],
        "cambridge_unit": "Unit 86-87 (some/any/no)",
        "difficulty": "Elementary"
    },
    
    "BETWEEN_YOU_AND_I": {
        "title": "Between you and ME (not between you and I)",
        "explanation": (
            "After prepositions (between, with, for, to), use object pronouns: "
            "me, him, her, us, them (NOT I, he, she, we, they)."
        ),
        "examples": [
            "✅ Between you and me",
            "✅ Come with me",
            "✅ For him and her",
            "❌ Between you and I",
            "❌ Come with I"
        ],
        "cambridge_unit": "Unit 82 (I and me, he and him, etc.)",
        "difficulty": "Intermediate"
    },
    
    "CONFUSION_OF_ME_I": {
        "title": "Me vs I (subject vs object)",
        "explanation": (
            "Use I (subject): I go, John and I went. "
            "Use me (object): with me, John and me (in casual speech after 'and')."
        ),
        "examples": [
            "✅ I went to the store",
            "✅ John and I went (formal)",
            "✅ Come with me",
            "❌ Me went to the store",
            "❌ Come with I"
        ],
        "cambridge_unit": "Unit 82 (I and me)",
        "difficulty": "Elementary"
    },
    
    "CONDITIONAL_CLAUSE": {
        "title": "Conditionals (If I go... / If I went...)",
        "explanation": (
            "First conditional (real future): If + present, will + verb. "
            "Second conditional (unreal present): If + past, would + verb. "
            "Don't use 'will' or 'would' in the IF clause."
        ),
        "examples": [
            "✅ If I see him, I will tell him (1st conditional)",
            "✅ If I saw him, I would tell him (2nd conditional)",
            "❌ If I will see him, I will tell him",
            "❌ If I would see him, I would tell him"
        ],
        "cambridge_unit": "Unit 38-40 (Conditionals)",
        "difficulty": "Intermediate"
    },
    
    "MANY_NN_U": {
        "title": "Many + Countable (not many + uncountable)",
        "explanation": (
            "Use 'many' with countable nouns (books, people). "
            "Use 'much' with uncountable nouns (water, money)."
        ),
        "examples": [
            "✅ Many books",
            "✅ Much water",
            "✅ A lot of books / A lot of water (both)",
            "❌ Many water",
            "❌ Much books"
        ],
        "cambridge_unit": "Unit 84 (much, many, little, few)",
        "difficulty": "Elementary"
    },
    
    "FEWER_LESS": {
        "title": "Fewer vs Less (countable vs uncountable)",
        "explanation": (
            "Use 'fewer' with countable nouns. "
            "Use 'less' with uncountable nouns."
        ),
        "examples": [
            "✅ Fewer people",
            "✅ Less money",
            "✅ Fewer mistakes",
            "❌ Less people",
            "❌ Fewer money"
        ],
        "cambridge_unit": "Unit 84 (much, many, little, few)",
        "difficulty": "Intermediate"
    },
    
    "MUST_HAVE_TO": {
        "title": "Must vs Have to",
        "explanation": (
            "Must = strong obligation from speaker. "
            "Have to = external obligation. "
            "Mustn't = prohibited. Don't have to = not necessary."
        ),
        "examples": [
            "✅ I must finish this (I decide)",
            "✅ I have to work tomorrow (external rule)",
            "✅ You mustn't smoke here (prohibited)",
            "✅ You don't have to come (optional)",
            "❌ You mustn't come (wrong: mustn't ≠ don't have to)"
        ],
        "cambridge_unit": "Unit 29-30 (must, have to, should)",
        "difficulty": "Intermediate"
    },
    
    "AGREEMENT_SENT_START": {
        "title": "Subject-Verb Agreement at sentence start",
        "explanation": (
            "Make sure the verb agrees with the subject, especially at the beginning of sentences."
        ),
        "examples": [
            "✅ There are many people",
            "✅ There is a problem",
            "❌ There is many people",
            "❌ There are a problem"
        ],
        "cambridge_unit": "Unit 5-6 (Present Simple)",
        "difficulty": "Elementary"
    },
    
    "BEEN_PART_AGREEMENT": {
        "title": "Been + Past Participle",
        "explanation": (
            "After 'been' (have/has/had been), use the past participle (3rd form), not base form."
        ),
        "examples": [
            "✅ I have been told",
            "✅ She has been working",
            "❌ I have been tell",
            "❌ She has been work"
        ],
        "cambridge_unit": "Unit 15-16 (Present Perfect Continuous)",
        "difficulty": "Intermediate"
    },
    
    "IT_IS": {
        "title": "It's vs Its (contraction vs possessive)",
        "explanation": (
            "It's = it is OR it has (contraction with apostrophe). "
            "Its = possessive (no apostrophe), like his/her."
        ),
        "examples": [
            "✅ It's raining (it is)",
            "✅ It's been a long day (it has)",
            "✅ The dog lost its tail (possessive)",
            "❌ Its raining",
            "❌ The dog lost it's tail"
        ],
        "cambridge_unit": "Appendix 6 (Spelling)",
        "difficulty": "Elementary"
    },
    
    "I_AM_VB": {
        "title": "I am + adjective/noun (not I am + base verb)",
        "explanation": (
            "After 'I am', use an adjective, noun, or present participle (-ing), not base verb."
        ),
        "examples": [
            "✅ I am happy (adjective)",
            "✅ I am a teacher (noun)",
            "✅ I am working (present participle)",
            "❌ I am work",
            "❌ I am agree"
        ],
        "cambridge_unit": "Unit 1-4 (Present tenses)",
        "difficulty": "Elementary"
    },
}


def generate_full_database():
    """Generate complete grammar rules database."""
    
    print("📚 Generating complete grammar rules database...\n")
    
    # Start with manual explanations
    all_rules = MANUAL_EXPLANATIONS.copy()
    
    # For codes without manual explanation, create basic template
    for code in RULE_CODES:
        if code not in all_rules:
            all_rules[code] = {
                "title": f"Grammar Rule: {code.replace('_', ' ').title()}",
                "explanation": "This construction doesn't follow standard English grammar patterns.",
                "examples": [],
                "cambridge_unit": "Check grammar reference",
                "book": "English Grammar in Use (Intermediate)",
                "difficulty": "Intermediate"
            }
    
    print(f"✅ Generated {len(all_rules)} rules:")
    print(f"   - {len(MANUAL_EXPLANATIONS)} with full explanations")
    print(f"   - {len(all_rules) - len(MANUAL_EXPLANATIONS)} with templates")
    print()
    
    # Save to JSON
    output_file = "cambridge_grammar_rules_FULL.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_rules, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved to {output_file}")
    print(f"\n📊 Coverage:")
    print(f"   Total rules: {len(all_rules)}")
    print(f"   Fully explained: {len(MANUAL_EXPLANATIONS)}")
    print(f"   Templates: {len(all_rules) - len(MANUAL_EXPLANATIONS)}")
    
    return all_rules


if __name__ == "__main__":
    rules = generate_full_database()
    
    print("\n" + "="*60)
    print("Next steps:")
    print("="*60)
    print("1. Review generated rules")
    print("2. Add more manual explanations for important codes")
    print("3. Test with real student errors")
    print("4. Update cambridge_grammar_rules.py")
