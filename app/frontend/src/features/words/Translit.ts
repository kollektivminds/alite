// src/utils/translit.ts

// 1. Digraphs must be processed first to prevent partial character collisions.
const DIGRAPH_MAP: readonly [string, string][] = [
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

// 2. Single-character mapping table (Latin -> Cyrillic)
const SINGLE_CHAR_MAP: Record<string, string> = {
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
  "`": "ъ",
  '"': "ъ",
  č: "ч",
  š: "ш",
  ž: "ж",
};

const LATIN_REGEXP = /[a-zA-Z\u00C0-\u024F]/;

/**
 * Evaluates whether the string contains Latin characters.
 */
export function isLatin(text: string): boolean {
  return LATIN_REGEXP.test(text);
}

/**
 * Projects a Latin string into canonical Cyrillic.
 */
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
