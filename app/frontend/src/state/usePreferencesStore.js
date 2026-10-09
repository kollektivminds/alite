import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
// import { createStore } from "zustand/vanilla";
import i18n from "../i18n"; // Path to your initialized i18next instance
// import { ITEM_DIFFICULTY } from "../types";

// src/state/usePreferencesStore.js

/**
 * State store managing client-side personalization and pedagogical preferences.
 * Persisted in localStorage to eliminate theme/accessibility flicker on page reload.
 */
export const usePreferencesStore = create(
  persist(
    (set) => ({
      // Pedagogical baseline
      difficulty: "medium", // 'easy' | 'medium' | 'hard'
      setDifficulty: (difficulty) => set({ difficulty }),

      // Display & Accessibility preferences
      theme: "system", // 'light' | 'dark' | 'system'
      setTheme: (theme) => set({ theme }),

      fontSize: "base", // 'sm' | 'base' | 'lg' | 'xl'
      setFontSize: (fontSize) => set({ fontSize }),

      reducedMotion: false, // Renamed to avoid shadowing framer-motion's hook
      setReducedMotion: (reducedMotion) => set({ reducedMotion }),
      toggleReducedMotion: () =>
        set((state) => ({ reducedMotion: !state.reducedMotion })),

      // Interface Localization
      language: "ru", // 'en' | 'ru'
      setLanguage: (newLang) => {
        i18n.changeLanguage(newLang);
        set({ language: newLang });
      },
    }),
    {
      name: "alite-user-preferences",
      storage: createJSONStorage(() => localStorage),
    },
  ),
);
