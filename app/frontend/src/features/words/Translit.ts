// src/utils/Translit.ts

// 1. Digraphs processed first to prevent partial character collisions
export const DIGRAPH_MAP: readonly [string, string][] = [
  ["shch", "щ"],
  ["yo", "ё"],
  ["zh", "ж"],
  ["kh", "х"],
  ["ts", "ц"],
  ["ch", "ч"],
  ["sh", "ш"],
  ["yu", "ю"],
  ["ya", "я"],
  ["ye", "е"],
  ["šč", "щ"],
];

// 2. Single-character mapping table (Latin -> Cyrillic)[cite: 11]
export const SINGLE_CHAR_MAP: Record<string, string> = {
  a: "а",
  b: "б",
  v: "в",
  w: "в",
  g: "г",
  d: "д",
  e: "е",
  z: "з",
  i: "и",
  j: "й",
  k: "к",
  l: "л",
  m: "м",
  n: "н",
  o: "о",
  p: "п",
  r: "р",
  s: "с",
  t: "т",
  u: "у",
  f: "ф",
  h: "х",
  c: "ц",
  y: "ы",
  "'": "ь",
  '"': "ъ",
  č: "ч",
  š: "ш",
  ž: "ж",
};

/**
 * Categorized rule sets for UI scaffolding and tooltip reference.
 * Grouped to help language learners identify challenging orthographic patterns.
 */
export interface TranslitRuleGroup {
  categoryKey: string;
  pairs: { latin: string; cyrillic: string }[];
}

export const TRANSLIT_GUIDE_GROUPS: TranslitRuleGroup[] = [
  {
    categoryKey: "exercises.wordsMenu.translitGuide.digraphs",
    pairs: [
      { latin: "zh", cyrillic: "ж" },
      { latin: "kh", cyrillic: "х" },
      { latin: "ts", cyrillic: "ц" },
      { latin: "ch", cyrillic: "ч" },
      { latin: "sh", cyrillic: "ш" },
      { latin: "shch", cyrillic: "щ" },
    ],
  },
  {
    categoryKey: "exercises.wordsMenu.translitGuide.vowels",
    pairs: [
      { latin: "ya", cyrillic: "я" },
      { latin: "yu", cyrillic: "ю" },
      { latin: "yo", cyrillic: "ё" },
      { latin: "ye", cyrillic: "е" },
      { latin: "y", cyrillic: "ы" },
    ],
  },
  {
    categoryKey: "exercises.wordsMenu.translitGuide.signs",
    pairs: [
      { latin: "'", cyrillic: "ь (soft)" },
      { latin: '"', cyrillic: "ъ (hard)" },
      { latin: "j", cyrillic: "й" },
    ],
  },
];

const LATIN_REGEXP = /[a-zA-Z\u00C0-\u024F]/;

export function isLatin(text: string): boolean {
  return LATIN_REGEXP.test(text);
}

export function latinToCyrillic(text: string): string {
  if (!text) return "";
  let result = text.trim().toLowerCase();

  for (const [latin, cyrillic] of DIGRAPH_MAP) {
    if (result.includes(latin)) {
      result = result.replaceAll(latin, cyrillic);
    }
  }

  return Array.from(result)
    .map((char) => SINGLE_CHAR_MAP[char] ?? char)
    .join("");
}
