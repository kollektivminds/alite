// This object defines the main categories of exercises the user can choose.
export const exerciseTypes = [
    {
      id: 'deconstruction',
      displayName: 'Vocabulary & Meaning',
      description: 'Practice connecting words to their definitions (e.g., flashcards, definition matching).',
    },
    {
      id: 'reconstruction',
      displayName: 'Grammar Identification & Analysis',
      description: 'Analyze existing word forms and identify their grammatical properties (e.g., "What case is this word?").',
    },
    {
      id: 'contextual',
      displayName: 'Grammar Production & Synthesis',
      description: 'Actively create the correct word forms based on grammatical rules (e.g., "Decline this noun into the genitive plural.").',
    },
  ];

// grammar option list
export const sentsMenuOpts = [
  {
    id: "pos",
    display_name: "Part of Speech",
    options: [
      {
        id: "adjective",
        display_name: "Adjective",
        db_column: "pos",
        db_value: 0,
      },
      {
        id: "adverb",
        display_name: "Adverb",
        db_column: "pos",
        db_value: 1,
      },
      {
        id: "noun",
        display_name: "Noun",
        db_column: "pos",
        db_value: 2,
      },
      {
        id: "number",
        display_name: "Number",
        db_column: "pos",
        db_value: 3,
      },
      {
        id: "participle",
        display_name: "Participle",
        db_column: "pos",
        db_value: 4,
      },
      {
        id: "pronoun",
        display_name: "Pronoun",
        db_column: "pos",
        db_value: 5,
      },
      {
        id: "verb",
        display_name: "Verb",
        db_column: "pos",
        db_value: 6,
      },
    ]
  },
  {
    id: "case",
    display_name: "Case",
    options: [],
  },
  {
    id: "aspect",
    display_name: "Case",
    options: [],
  },
  {
    id: "aspect",
    display_name: "Case",
    options: [],
  },
];
