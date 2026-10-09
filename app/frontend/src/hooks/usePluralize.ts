/**
 * src/hooks/usePluralize.ts
 */

import { useCallback } from "react";
import { preferencesStore } from "../state/usePreferencesStore";
import {
  getPluralForm,
  PluralFormsMap,
  SupportedLanguage,
} from "../utils/pluralization";

export function usePluralize() {
  // Subscribe specifically to the language slice of your Zustand store
  const language = preferencesStore(
    (state) => state.language as SupportedLanguage,
  );

  /**
   * Pluralize a term based on the current active UI language
   */
  const pluralize = useCallback(
    (count: number, forms: PluralFormsMap[SupportedLanguage]) => {
      return getPluralForm(count, forms as any, language);
    },
    [language],
  );

  return { pluralize, language };
}
