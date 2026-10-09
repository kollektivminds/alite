/**
 * src/utils/pluralization.ts
 *
 * Language-agnostic pluralization helper based on standard ECMAScript Intl API.
 */

export type SupportedLanguage = "en" | "ru";

export interface RussianPluralForms {
  /** Used for numbers ending in 1 (except 11): e.g., "вопрос" */
  one: string;
  /** Used for numbers ending in 2-4 (except 12-14): e.g., "вопроса" */
  few: string;
  /** Used for numbers ending in 5-0 and 11-14: e.g., "вопросов" */
  many: string;
}

export interface EnglishPluralForms {
  /** Singular: e.g., "question" */
  one: string;
  /** Plural: e.g., "questions" */
  multiple: string;
}

export type PluralFormsMap = {
  ru: RussianPluralForms;
  en: EnglishPluralForms;
};

/**
 * Resolves the correct plural form based on language code and numeric quantity.
 *
 * @param count - The quantity to evaluate
 * @param forms - Map containing plural suffixes or full words per language
 * @param lang - Target ISO-639-1 language code ('ru' | 'en')
 * @returns The grammatically correct word/suffix
 */
export function getPluralForm<L extends SupportedLanguage>(
  count: number,
  forms: PluralFormsMap[L],
  lang: L,
): string {
  // 1. Resolve CLDR plural category via native browser Intl engine
  const pr = new Intl.PluralRules(lang);
  const rule = pr.select(count);

  // 2. Select appropriate form based on language-specific rule mapping
  if (lang === "ru") {
    const ruForms = forms as RussianPluralForms;
    switch (rule) {
      case "one":
        return ruForms.one;
      case "few":
        return ruForms.few;
      case "many":
      default:
        return ruForms.many;
    }
  }

  // English fallback: 'one' -> singular, everything else -> 'other'
  const enForms = forms as EnglishPluralForms;
  return rule === "one" ? enForms.one : enForms.multiple;
}
