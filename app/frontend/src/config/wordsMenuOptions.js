// This object defines the main categories of exercises the user can choose.
export const exerciseTypes = [
    {
      id: 'semantics',
      displayName: 'Vocabulary & Meaning',
      description: 'Practice connecting words to their definitions (e.g., flashcards, definition matching).',
    },
    {
      id: 'identification',
      displayName: 'Grammar Identification & Analysis',
      description: 'Analyze existing word forms and identify their grammatical properties (e.g., "What case is this word?").',
    },
    {
      id: 'production',
      displayName: 'Grammar Production & Synthesis',
      description: 'Actively create the correct word forms based on grammatical rules (e.g., "Decline this noun into the genitive plural.").',
    },
  ];

// grammar option list
/**
* This file defines the structure for all sentence-based exercises.
* Each object describes a unique question format that can be generated
* from the parsed sentence dataset.
*/
export const wordsMenuOpts = [
    // --- Category: Sentence Deconstruction (Analysis & Comprehension) ---
    {
    id: 'grammatical_role_id',
    displayName: 'Grammatical Role ID',
    category: 'Deconstruction',
    description: 'Identify the grammatical role of a highlighted word in a sentence.',
    requiredData: ['sentence_text', 'target_word', 'dependency_role', 'distractors'],
    },
    {
    id: 'why_the_case',
    displayName: 'Why the Case?',
    category: 'Deconstruction',
    description: 'Explain why a word is in a specific grammatical case based on its context.',
    requiredData: ['sentence_text', 'target_word', 'governing_word', 'case_rule'],
    },
    {
    id: 'interactive_analysis_subject',
    displayName: 'Click the Subject',
    category: 'Deconstruction',
    description: 'Find and click on the subject of the main verb in a sentence.',
    requiredData: ['sentence_text', 'dependency_tree'],
    },

    // --- Category: Sentence Reconstruction (Production & Synthesis) ---
    {
    id: 'fill_in_the_blank_cloze',
    displayName: 'Fill-in-the-Blank (Cloze)',
    category: 'Reconstruction',
    description: 'Decline or conjugate a word correctly to complete a sentence.',
    requiredData: ['sentence_with_blank', 'prompt_lemma', 'correct_form'],
    },
    {
    id: 'jumbled_sentence',
    displayName: 'Jumbled Sentence',
    category: 'Reconstruction',
    description: 'Arrange a shuffled set of words into a grammatically correct sentence.',
    requiredData: ['shuffled_words', 'correct_sentence_text'],
    },

    // --- Category: Contextual Vocabulary ---
    {
    id: 'definition_in_context',
    displayName: 'Definition in Context',
    category: 'Vocabulary',
    description: 'Choose the correct meaning of a word as it is used in a sentence.',
    requiredData: ['sentence_text', 'target_word', 'correct_definition', 'distractor_definitions'],
    },
    {
    id: 'case_in_context',
    displayName: 'Case in Context',
    category: 'Vocabulary',
    description: 'Choose the correct case of a word as it is used in a sentence.',
    requiredData: ['sentence_text', 'target_word', 'correct_case', 'distractor_cases'],
    },
    {
    id: 'choose_the_right_word_aspect',
    displayName: 'Choose the Right Aspect',
    category: 'Vocabulary',
    description: 'Select the correct verb aspect (perfective/imperfective) to fit the sentence.',
    requiredData: ['sentence_with_blank', 'verb_pair', 'correct_verb_form'],
    },
];