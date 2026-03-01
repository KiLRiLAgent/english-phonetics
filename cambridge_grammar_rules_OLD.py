#!/usr/bin/env python3
"""
Cambridge Grammar Rules Reference
Maps LanguageTool error codes to Cambridge Grammar in Use explanations.
"""

# Cambridge Grammar in Use (Murphy) - Intermediate (Blue book)
# Essential Grammar in Use (Murphy) - Elementary (Red book)
# Advanced Grammar in Use (Hewings) - Advanced (Green book)

GRAMMAR_RULES = {
    # Subject-Verb Agreement
    "NON3PRS_VERB": {
        "title": "Subject-Verb Agreement: I/You/We/They + base form",
        "explanation": "Use the base form of the verb (without -s) with I, you, we, and they.",
        "examples": [
            "✅ I go to school",
            "✅ They go to school",
            "❌ I goes to school"
        ],
        "cambridge_unit": "Unit 5-6 (Present Simple)",
        "book": "English Grammar in Use (Intermediate)",
        "difficulty": "Elementary"
    },
    
    "HE_VERB_AGR": {
        "title": "Subject-Verb Agreement: He/She/It + verb-s",
        "explanation": "Add -s/-es to verbs in Present Simple with he, she, it.",
        "examples": [
            "✅ He goes to school",
            "✅ She likes apples",
            "❌ He go to school",
            "❌ She don't like apples → She doesn't like apples"
        ],
        "cambridge_unit": "Unit 5-6 (Present Simple)",
        "book": "English Grammar in Use (Intermediate)",
        "difficulty": "Elementary"
    },
    
    # Went vs Gone
    "PAST_PARTICIPLE": {
        "title": "Past Participle (have gone, not have went)",
        "explanation": "After have/has/had, use the past participle (3rd form), not past simple (2nd form).",
        "examples": [
            "✅ I have gone (present perfect)",
            "✅ I went yesterday (past simple)",
            "✅ He has seen the movie",
            "❌ I have went",
            "❌ He has saw"
        ],
        "cambridge_unit": "Unit 7-9 (Present Perfect)",
        "book": "English Grammar in Use (Intermediate)",
        "difficulty": "Elementary"
    },
    
    # Present Perfect vs Past Simple
    "HAVE_PAST_PARTICIPLE": {
        "title": "Present Perfect: have/has + past participle",
        "explanation": "Use 'have/has + past participle' for actions connected to now.",
        "examples": [
            "✅ I have seen that movie",
            "✅ She has finished her homework",
            "❌ I have saw that movie",
            "❌ She have finished"
        ],
        "cambridge_unit": "Unit 7-9 (Present Perfect)",
        "book": "English Grammar in Use (Intermediate)",
        "difficulty": "Intermediate"
    },
    
    # Did vs Done
    "DID_BASEFORM": {
        "title": "Past Simple: did + base form",
        "explanation": "After 'did' (questions/negatives), use the base form, not past tense.",
        "examples": [
            "✅ Did you go?",
            "✅ I didn't see him",
            "❌ Did you went?",
            "❌ I didn't saw him"
        ],
        "cambridge_unit": "Unit 12 (Past Simple questions)",
        "book": "English Grammar in Use (Intermediate)",
        "difficulty": "Elementary"
    },
    
    # Articles
    "EN_A_VS_AN": {
        "title": "Articles: a vs an",
        "explanation": "Use 'an' before vowel sounds (a, e, i, o, u), 'a' before consonant sounds.",
        "examples": [
            "✅ an apple, an hour",
            "✅ a book, a university (starts with 'yu' sound)",
            "❌ a apple",
            "❌ an book"
        ],
        "cambridge_unit": "Unit 68-69 (a/an)",
        "book": "English Grammar in Use (Intermediate)",
        "difficulty": "Elementary"
    },
    
    "THE": {
        "title": "Articles: the (definite article)",
        "explanation": "Use 'the' when both speaker and listener know which thing/person.",
        "examples": [
            "✅ the sun, the moon (only one)",
            "✅ Close the door (we both know which door)",
            "✅ I went to the bank (my bank)"
        ],
        "cambridge_unit": "Unit 70-77 (the)",
        "book": "English Grammar in Use (Intermediate)",
        "difficulty": "Intermediate"
    },
    
    # Prepositions
    "PREP": {
        "title": "Prepositions",
        "explanation": "Different verbs and adjectives require specific prepositions.",
        "examples": [
            "✅ listen to music",
            "✅ good at math",
            "✅ afraid of spiders",
            "❌ listen music",
            "❌ good in math"
        ],
        "cambridge_unit": "Unit 128-135 (Prepositions)",
        "book": "English Grammar in Use (Intermediate)",
        "difficulty": "Intermediate"
    },
    
    # Modal Verbs
    "MODAL_VERB_BASEFORM": {
        "title": "Modal Verbs: must/should/can + base form",
        "explanation": "After modal verbs (can, should, must, etc.), use base form without 'to'.",
        "examples": [
            "✅ I can swim",
            "✅ You should go",
            "✅ He must study",
            "❌ I can to swim",
            "❌ You should going"
        ],
        "cambridge_unit": "Unit 26-31 (Modal verbs)",
        "book": "English Grammar in Use (Intermediate)",
        "difficulty": "Intermediate"
    },
    
    # Word Order
    "WORD_ORDER": {
        "title": "Word Order: Subject + Verb + Object",
        "explanation": "English follows SVO order. Adverbs usually don't go between verb and object.",
        "examples": [
            "✅ I speak English well",
            "✅ She always drinks coffee",
            "❌ I speak well English",
            "❌ She drinks always coffee"
        ],
        "cambridge_unit": "Unit 109-111 (Word order)",
        "book": "English Grammar in Use (Intermediate)",
        "difficulty": "Elementary"
    },
    
    # Plural
    "PLURAL_NOUN": {
        "title": "Plural Nouns",
        "explanation": "Add -s/-es to make nouns plural. Some nouns are irregular (child→children).",
        "examples": [
            "✅ two books, three boxes",
            "✅ many children, several people",
            "❌ two book",
            "❌ many childs"
        ],
        "cambridge_unit": "Unit 68 (Countable/uncountable)",
        "book": "English Grammar in Use (Intermediate)",
        "difficulty": "Elementary"
    },
    
    # Missing TO
    "MISSING_TO_BEFORE_A_VERB": {
        "title": "Missing 'to' before infinitive",
        "explanation": "Many verbs require 'to' before the infinitive form.",
        "examples": [
            "✅ I want to go",
            "✅ I need to study",
            "✅ I hope to see you",
            "❌ I want go",
            "❌ I need study"
        ],
        "cambridge_unit": "Unit 52 (Verb + to...)",
        "book": "English Grammar in Use (Intermediate)",
        "difficulty": "Elementary"
    },
    
    # To + infinitive vs -ing
    "TO_BASEFORM": {
        "title": "To + infinitive vs -ing",
        "explanation": "Some verbs take 'to + infinitive', others take '-ing'. Must memorize.",
        "examples": [
            "✅ I want to go (to + infinitive)",
            "✅ I enjoy swimming (-ing)",
            "✅ I decided to study",
            "❌ I want go",
            "❌ I enjoy to swim"
        ],
        "cambridge_unit": "Unit 52-62 (-ing and to...)",
        "book": "English Grammar in Use (Intermediate)",
        "difficulty": "Intermediate"
    },
    
    # Comparative/Superlative
    "COMPARATIVE": {
        "title": "Comparative and Superlative",
        "explanation": "Short adjectives: -er/-est. Long adjectives: more/most.",
        "examples": [
            "✅ bigger, biggest (short)",
            "✅ more beautiful, most beautiful (long)",
            "✅ better, best (irregular)",
            "❌ more big",
            "❌ beautifuler"
        ],
        "cambridge_unit": "Unit 104-107 (Comparatives)",
        "book": "English Grammar in Use (Intermediate)",
        "difficulty": "Elementary"
    },
    
    # Countable/Uncountable
    "MUCH_COUNTABLE": {
        "title": "Much vs Many (Countable/Uncountable)",
        "explanation": "Use 'many' with countable nouns, 'much' with uncountable nouns.",
        "examples": [
            "✅ many books (countable)",
            "✅ much water (uncountable)",
            "✅ a lot of books/water (both)",
            "❌ much books",
            "❌ many water"
        ],
        "cambridge_unit": "Unit 85-90 (Some/any/much/many)",
        "book": "English Grammar in Use (Intermediate)",
        "difficulty": "Elementary"
    },
}


# Fallback rule for unknown errors
DEFAULT_RULE = {
    "title": "Grammar Rule",
    "explanation": "This construction doesn't follow standard English grammar patterns.",
    "examples": [],
    "cambridge_unit": "Check grammar reference",
    "book": "English Grammar in Use",
    "difficulty": "Unknown"
}


def get_grammar_explanation(rule_id: str) -> dict:
    """
    Get Cambridge Grammar explanation for a LanguageTool rule.
    
    Args:
        rule_id: LanguageTool rule ID (e.g., 'NON3PRS_VERB')
    
    Returns:
        Dict with title, explanation, examples, cambridge_unit, book, difficulty
    """
    # Aliases for common LanguageTool rule variants
    RULE_ALIASES = {
        'HAVE_PART_AGREEMENT': 'PAST_PARTICIPLE',
        'MD_BASEFORM': 'MODAL_VERB_BASEFORM',
        'MOST_COMPARATIVE': 'COMPARATIVE',
        'PERS_PRONOUN_AGREEMENT': 'HE_VERB_AGR',
        'BASE_FORM': 'HE_VERB_AGR',
    }
    
    # Check alias first
    if rule_id in RULE_ALIASES:
        return GRAMMAR_RULES[RULE_ALIASES[rule_id]]
    
    # Direct match
    if rule_id in GRAMMAR_RULES:
        return GRAMMAR_RULES[rule_id]
    
    # Partial match (some rules have variants)
    for key in GRAMMAR_RULES:
        if key in rule_id or rule_id in key:
            return GRAMMAR_RULES[key]
    
    # Fallback
    return DEFAULT_RULE


def format_grammar_help(rule_id: str, error_message: str) -> str:
    """Format grammar help as readable text."""
    rule = get_grammar_explanation(rule_id)
    
    output = []
    output.append(f"📚 {rule['title']}")
    output.append(f"\n💡 {rule['explanation']}")
    
    if rule['examples']:
        output.append("\n\n📝 Examples:")
        for example in rule['examples']:
            output.append(f"   {example}")
    
    output.append(f"\n\n📖 Cambridge Reference: {rule['cambridge_unit']}")
    output.append(f"📕 Book: {rule['book']}")
    output.append(f"🎯 Level: {rule['difficulty']}")
    
    return "".join(output)


if __name__ == "__main__":
    # Test
    test_rules = [
        "NON3PRS_VERB",
        "HE_VERB_AGR",
        "EN_A_VS_AN",
        "UNKNOWN_RULE"
    ]
    
    for rule_id in test_rules:
        print("="*60)
        print(f"Rule: {rule_id}")
        print("="*60)
        print(format_grammar_help(rule_id, "Example error"))
        print("\n")
