#!/usr/bin/env python3
"""
Cambridge Grammar Rules Reference - COMPLETE DATABASE
Maps LanguageTool error codes to detailed explanations.

Total rules: 37
- With full explanations: 30
- With templates: 7
"""

GRAMMAR_RULES = {
    'ADMIT_ENJOY_VB': {
        "title": 'Verb + Gerund (enjoy swimming, not enjoy to swim)',
        "explanation": 'Some verbs (enjoy, admit, avoid, finish, etc.) must be followed by gerund (-ing form), not infinitive (to + verb).',
        "examples": [
            '✅ I enjoy swimming',
            '✅ She admitted making a mistake',
            '✅ We avoid eating fast food',
            '❌ I enjoy to swim',
            '❌ She admitted to make a mistake',
        ],
        "cambridge_unit": 'Unit 52-53 (Verb + -ing or to...)',
        "book": 'English Grammar in Use',
        "difficulty": 'Intermediate'
    },
    'AFRAID_FROM_OF': {
        "title": 'Afraid OF (not afraid FROM)',
        "explanation": "The correct preposition with 'afraid' is OF, not FROM. Many adjectives require specific prepositions.",
        "examples": [
            "✅ I'm afraid of spiders",
            "✅ She's afraid of flying",
            "❌ I'm afraid from spiders",
            "❌ She's afraid from flying",
        ],
        "cambridge_unit": 'Unit 128-135 (Prepositions)',
        "book": 'English Grammar in Use',
        "difficulty": 'Elementary'
    },
    'AGREEMENT_SENT_START': {
        "title": 'Subject-Verb Agreement at sentence start',
        "explanation": 'Make sure the verb agrees with the subject, especially at the beginning of sentences.',
        "examples": [
            '✅ There are many people',
            '✅ There is a problem',
            '❌ There is many people',
            '❌ There are a problem',
        ],
        "cambridge_unit": 'Unit 5-6 (Present Simple)',
        "book": 'English Grammar in Use',
        "difficulty": 'Elementary'
    },
    'BASE_FORM': {
        "title": 'Grammar Rule: Base Form',
        "explanation": "This construction doesn't follow standard English grammar patterns.",
        "examples": [
        ],
        "cambridge_unit": 'Check grammar reference',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Intermediate'
    },
    'BEEN_PART_AGREEMENT': {
        "title": 'Been + Past Participle',
        "explanation": "After 'been' (have/has/had been), use the past participle (3rd form), not base form.",
        "examples": [
            '✅ I have been told',
            '✅ She has been working',
            '❌ I have been tell',
            '❌ She has been work',
        ],
        "cambridge_unit": 'Unit 15-16 (Present Perfect Continuous)',
        "book": 'English Grammar in Use',
        "difficulty": 'Intermediate'
    },
    'BETWEEN_YOU_AND_I': {
        "title": 'Between you and ME (not between you and I)',
        "explanation": 'After prepositions (between, with, for, to), use object pronouns: me, him, her, us, them (NOT I, he, she, we, they).',
        "examples": [
            '✅ Between you and me',
            '✅ Come with me',
            '✅ For him and her',
            '❌ Between you and I',
            '❌ Come with I',
        ],
        "cambridge_unit": 'Unit 82 (I and me, he and him, etc.)',
        "book": 'English Grammar in Use',
        "difficulty": 'Intermediate'
    },
    'COMPARATIVE': {
        "title": 'Comparative and Superlative',
        "explanation": 'Short adjectives: -er/-est. Long adjectives: more/most.',
        "examples": [
            '✅ bigger, biggest (short)',
            '✅ more beautiful, most beautiful (long)',
            '✅ better, best (irregular)',
            '❌ more big',
            '❌ beautifuler',
        ],
        "cambridge_unit": 'Unit 104-107 (Comparatives)',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Elementary'
    },
    'CONDITIONAL_CLAUSE': {
        "title": 'Conditionals (If I go... / If I went...)',
        "explanation": "First conditional (real future): If + present, will + verb. Second conditional (unreal present): If + past, would + verb. Don't use 'will' or 'would' in the IF clause.",
        "examples": [
            '✅ If I see him, I will tell him (1st conditional)',
            '✅ If I saw him, I would tell him (2nd conditional)',
            '❌ If I will see him, I will tell him',
            '❌ If I would see him, I would tell him',
        ],
        "cambridge_unit": 'Unit 38-40 (Conditionals)',
        "book": 'English Grammar in Use',
        "difficulty": 'Intermediate'
    },
    'CONFUSION_OF_ME_I': {
        "title": 'Me vs I (subject vs object)',
        "explanation": "Use I (subject): I go, John and I went. Use me (object): with me, John and me (in casual speech after 'and').",
        "examples": [
            '✅ I went to the store',
            '✅ John and I went (formal)',
            '✅ Come with me',
            '❌ Me went to the store',
            '❌ Come with I',
        ],
        "cambridge_unit": 'Unit 82 (I and me)',
        "book": 'English Grammar in Use',
        "difficulty": 'Elementary'
    },
    'DEPEND_ON': {
        "title": 'Depend ON (not depend OF)',
        "explanation": "The correct preposition with 'depend' is ON. 'It depends on the weather' = the weather determines the result.",
        "examples": [
            '✅ It depends on you',
            '✅ Success depends on hard work',
            '❌ It depends of you',
            '❌ Success depends from hard work',
        ],
        "cambridge_unit": 'Unit 132 (Verb + preposition)',
        "book": 'English Grammar in Use',
        "difficulty": 'Elementary'
    },
    'DID_BASEFORM': {
        "title": 'Past Simple: did + base form',
        "explanation": "After 'did' (questions/negatives), use the base form, not past tense.",
        "examples": [
            '✅ Did you go?',
            "✅ I didn't see him",
            '❌ Did you went?',
            "❌ I didn't saw him",
        ],
        "cambridge_unit": 'Unit 12 (Past Simple questions)',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Elementary'
    },
    'DOUBLE_NEGATIVE': {
        "title": "Double Negatives (don't say 'don't have nothing')",
        "explanation": "In standard English, don't use two negatives together. Use 'anything' with 'don't', not 'nothing'.",
        "examples": [
            "✅ I don't have anything",
            "✅ She didn't do anything",
            '✅ I have nothing (one negative)',
            "❌ I don't have nothing",
            "❌ She didn't do nothing",
        ],
        "cambridge_unit": 'Unit 86-87 (some/any/no)',
        "book": 'English Grammar in Use',
        "difficulty": 'Elementary'
    },
    'EN_A_VS_AN': {
        "title": 'Articles: a vs an',
        "explanation": "Use 'an' before vowel sounds (a, e, i, o, u), 'a' before consonant sounds.",
        "examples": [
            '✅ an apple, an hour',
            "✅ a book, a university (starts with 'yu' sound)",
            '❌ a apple',
            '❌ an book',
        ],
        "cambridge_unit": 'Unit 68-69 (a/an)',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Elementary'
    },
    'FEWER_LESS': {
        "title": 'Fewer vs Less (countable vs uncountable)',
        "explanation": "Use 'fewer' with countable nouns. Use 'less' with uncountable nouns.",
        "examples": [
            '✅ Fewer people',
            '✅ Less money',
            '✅ Fewer mistakes',
            '❌ Less people',
            '❌ Fewer money',
        ],
        "cambridge_unit": 'Unit 84 (much, many, little, few)',
        "book": 'English Grammar in Use',
        "difficulty": 'Intermediate'
    },
    'GOOD_IN_AT': {
        "title": 'Good AT (not good IN)',
        "explanation": "Use 'good AT' for skills and activities, not 'good IN'. We also say 'bad AT', 'terrible AT', 'excellent AT'.",
        "examples": [
            "✅ I'm good at math",
            "✅ She's good at playing piano",
            "❌ I'm good in math",
            "❌ She's good in playing piano",
        ],
        "cambridge_unit": 'Unit 129 (Adjective + preposition)',
        "book": 'English Grammar in Use',
        "difficulty": 'Elementary'
    },
    'HAVE_PART_AGREEMENT': {
        "title": 'Grammar Rule: Have Part Agreement',
        "explanation": "This construction doesn't follow standard English grammar patterns.",
        "examples": [
        ],
        "cambridge_unit": 'Check grammar reference',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Intermediate'
    },
    'HAVE_PAST_PARTICIPLE': {
        "title": 'Present Perfect: have/has + past participle',
        "explanation": "Use 'have/has + past participle' for actions connected to now.",
        "examples": [
            '✅ I have seen that movie',
            '✅ She has finished her homework',
            '❌ I have saw that movie',
            '❌ She have finished',
        ],
        "cambridge_unit": 'Unit 7-9 (Present Perfect)',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Intermediate'
    },
    'HE_VERB_AGR': {
        "title": 'Subject-Verb Agreement: He/She/It + verb-s',
        "explanation": 'Add -s/-es to verbs in Present Simple with he, she, it.',
        "examples": [
            '✅ He goes to school',
            '✅ She likes apples',
            '❌ He go to school',
            "❌ She don't like apples → She doesn't like apples",
        ],
        "cambridge_unit": 'Unit 5-6 (Present Simple)',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Elementary'
    },
    'IT_IS': {
        "title": "It's vs Its (contraction vs possessive)",
        "explanation": "It's = it is OR it has (contraction with apostrophe). Its = possessive (no apostrophe), like his/her.",
        "examples": [
            "✅ It's raining (it is)",
            "✅ It's been a long day (it has)",
            '✅ The dog lost its tail (possessive)',
            '❌ Its raining',
            "❌ The dog lost it's tail",
        ],
        "cambridge_unit": 'Appendix 6 (Spelling)',
        "book": 'English Grammar in Use',
        "difficulty": 'Elementary'
    },
    'I_AM_VB': {
        "title": 'I am + adjective/noun (not I am + base verb)',
        "explanation": "After 'I am', use an adjective, noun, or present participle (-ing), not base verb.",
        "examples": [
            '✅ I am happy (adjective)',
            '✅ I am a teacher (noun)',
            '✅ I am working (present participle)',
            '❌ I am work',
            '❌ I am agree',
        ],
        "cambridge_unit": 'Unit 1-4 (Present tenses)',
        "book": 'English Grammar in Use',
        "difficulty": 'Elementary'
    },
    'MANY_NN_U': {
        "title": 'Many + Countable (not many + uncountable)',
        "explanation": "Use 'many' with countable nouns (books, people). Use 'much' with uncountable nouns (water, money).",
        "examples": [
            '✅ Many books',
            '✅ Much water',
            '✅ A lot of books / A lot of water (both)',
            '❌ Many water',
            '❌ Much books',
        ],
        "cambridge_unit": 'Unit 84 (much, many, little, few)',
        "book": 'English Grammar in Use',
        "difficulty": 'Elementary'
    },
    'MD_BASEFORM': {
        "title": 'Grammar Rule: Md Baseform',
        "explanation": "This construction doesn't follow standard English grammar patterns.",
        "examples": [
        ],
        "cambridge_unit": 'Check grammar reference',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Intermediate'
    },
    'MISSING_TO_BEFORE_A_VERB': {
        "title": "Missing 'to' before infinitive",
        "explanation": "Many verbs require 'to' before the infinitive form.",
        "examples": [
            '✅ I want to go',
            '✅ I need to study',
            '✅ I hope to see you',
            '❌ I want go',
            '❌ I need study',
        ],
        "cambridge_unit": 'Unit 52 (Verb + to...)',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Elementary'
    },
    'MODAL_VERB_BASEFORM': {
        "title": 'Modal Verbs: must/should/can + base form',
        "explanation": "After modal verbs (can, should, must, etc.), use base form without 'to'.",
        "examples": [
            '✅ I can swim',
            '✅ You should go',
            '✅ He must study',
            '❌ I can to swim',
            '❌ You should going',
        ],
        "cambridge_unit": 'Unit 26-31 (Modal verbs)',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Intermediate'
    },
    'MORFOLOGIK_RULE_EN_US': {
        "title": 'Grammar Rule: Morfologik Rule En Us',
        "explanation": "This construction doesn't follow standard English grammar patterns.",
        "examples": [
        ],
        "cambridge_unit": 'Check grammar reference',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Intermediate'
    },
    'MOST_COMPARATIVE': {
        "title": 'Grammar Rule: Most Comparative',
        "explanation": "This construction doesn't follow standard English grammar patterns.",
        "examples": [
        ],
        "cambridge_unit": 'Check grammar reference',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Intermediate'
    },
    'MOST_SUPERLATIVE': {
        "title": 'Grammar Rule: Most Superlative',
        "explanation": "This construction doesn't follow standard English grammar patterns.",
        "examples": [
        ],
        "cambridge_unit": 'Check grammar reference',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Intermediate'
    },
    'MUCH_COUNTABLE': {
        "title": 'Much vs Many (Countable/Uncountable)',
        "explanation": "Use 'many' with countable nouns, 'much' with uncountable nouns.",
        "examples": [
            '✅ many books (countable)',
            '✅ much water (uncountable)',
            '✅ a lot of books/water (both)',
            '❌ much books',
            '❌ many water',
        ],
        "cambridge_unit": 'Unit 85-90 (Some/any/much/many)',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Elementary'
    },
    'MUST_HAVE_TO': {
        "title": 'Must vs Have to',
        "explanation": "Must = strong obligation from speaker. Have to = external obligation. Mustn't = prohibited. Don't have to = not necessary.",
        "examples": [
            '✅ I must finish this (I decide)',
            '✅ I have to work tomorrow (external rule)',
            "✅ You mustn't smoke here (prohibited)",
            "✅ You don't have to come (optional)",
            "❌ You mustn't come (wrong: mustn't ≠ don't have to)",
        ],
        "cambridge_unit": 'Unit 29-30 (must, have to, should)',
        "book": 'English Grammar in Use',
        "difficulty": 'Intermediate'
    },
    'NON3PRS_VERB': {
        "title": 'Subject-Verb Agreement: I/You/We/They + base form',
        "explanation": 'Use the base form of the verb (without -s) with I, you, we, and they.',
        "examples": [
            '✅ I go to school',
            '✅ They go to school',
            '❌ I goes to school',
        ],
        "cambridge_unit": 'Unit 5-6 (Present Simple)',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Elementary'
    },
    'PAST_PARTICIPLE': {
        "title": 'Past Participle (have gone, not have went)',
        "explanation": 'After have/has/had, use the past participle (3rd form), not past simple (2nd form).',
        "examples": [
            '✅ I have gone (present perfect)',
            '✅ I went yesterday (past simple)',
            '✅ He has seen the movie',
            '❌ I have went',
            '❌ He has saw',
        ],
        "cambridge_unit": 'Unit 7-9 (Present Perfect)',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Elementary'
    },
    'PERS_PRONOUN_AGREEMENT': {
        "title": 'Grammar Rule: Pers Pronoun Agreement',
        "explanation": "This construction doesn't follow standard English grammar patterns.",
        "examples": [
        ],
        "cambridge_unit": 'Check grammar reference',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Intermediate'
    },
    'PLURAL_NOUN': {
        "title": 'Plural Nouns',
        "explanation": 'Add -s/-es to make nouns plural. Some nouns are irregular (child→children).',
        "examples": [
            '✅ two books, three boxes',
            '✅ many children, several people',
            '❌ two book',
            '❌ many childs',
        ],
        "cambridge_unit": 'Unit 68 (Countable/uncountable)',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Elementary'
    },
    'PREP': {
        "title": 'Prepositions',
        "explanation": 'Different verbs and adjectives require specific prepositions.',
        "examples": [
            '✅ listen to music',
            '✅ good at math',
            '✅ afraid of spiders',
            '❌ listen music',
            '❌ good in math',
        ],
        "cambridge_unit": 'Unit 128-135 (Prepositions)',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Intermediate'
    },
    'THE': {
        "title": 'Articles: the (definite article)',
        "explanation": "Use 'the' when both speaker and listener know which thing/person.",
        "examples": [
            '✅ the sun, the moon (only one)',
            '✅ Close the door (we both know which door)',
            '✅ I went to the bank (my bank)',
        ],
        "cambridge_unit": 'Unit 70-77 (the)',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Intermediate'
    },
    'TO_BASEFORM': {
        "title": 'To + infinitive vs -ing',
        "explanation": "Some verbs take 'to + infinitive', others take '-ing'. Must memorize.",
        "examples": [
            '✅ I want to go (to + infinitive)',
            '✅ I enjoy swimming (-ing)',
            '✅ I decided to study',
            '❌ I want go',
            '❌ I enjoy to swim',
        ],
        "cambridge_unit": 'Unit 52-62 (-ing and to...)',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Intermediate'
    },
    'WORD_ORDER': {
        "title": 'Word Order: Subject + Verb + Object',
        "explanation": "English follows SVO order. Adverbs usually don't go between verb and object.",
        "examples": [
            '✅ I speak English well',
            '✅ She always drinks coffee',
            '❌ I speak well English',
            '❌ She drinks always coffee',
        ],
        "cambridge_unit": 'Unit 109-111 (Word order)',
        "book": 'English Grammar in Use (Intermediate)',
        "difficulty": 'Elementary'
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
