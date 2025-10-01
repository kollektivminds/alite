import { createStore } from "zustand/vanilla";
import { useStore } from "zustand";
import { persist } from 'zustand/middleware';

export const preferencesStore = createStore(
  persist(
    (set, get) => ({
      // ===================================
      // 1. PERSISTENT STATE
      // ===================================
      theme: 'system',
      language: 'en',
      difficulty: 'easy',
      useReducedMotion: false, // Initial default value
      
      favorites: [],

      // ===================================
      // 2. TRANSIENT (IN-MEMORY) STATE
      // ===================================
      selectedPartsOfSpeech: [],
      openPartOfSpeechMenus: {},
      verbOptions: [],
      nounOptions: [],
      pronounOptions: [],
      adjectiveOptions: [],
      participleOptions: [],
      numeralOptions: [],

      // ===================================
      // 3. ACTIONS
      // ===================================

      setTheme: (newTheme) => set({ theme: newTheme }),
      setLanguage: (newLang) => set({ language: newLang }),
      setDifficulty: (newDifficulty) => set({ difficulty: newDifficulty }),
      toggleReducedMotion: () => set((state) => ({ useReducedMotion: !state.useReducedMotion })),

      // --- Actions for the 'Favorites' feature ---
      saveFavorite: (name) => {
        const { selectedPartsOfSpeech, verbOptions, nounOptions, pronounOptions, adjectiveOptions, participleOptions, numeralOptions } = get();
        const newFavorite = {
          id: Date.now().toString(),
          name: name,
          config: { selectedPartsOfSpeech, verbOptions, nounOptions, pronounOptions, adjectiveOptions, participleOptions, numeralOptions }
        };
        set((state) => ({ favorites: [...state.favorites, newFavorite] }));
      },

      loadFavorite: (id) => {
        const favorite = get().favorites.find(fav => fav.id === id);
        if (favorite) {
          set({ ...favorite.config });
        }
      },

      deleteFavorite: (id) => {
        set((state) => ({ favorites: state.favorites.filter(fav => fav.id !== id) }));
      },

      // --- Actions for temporary selections ---
      resetCurrentSelection: () => {
        set({
          selectedPartsOfSpeech: [], verbOptions: [], nounOptions: [],
          pronounOptions: [], adjectiveOptions: [], participleOptions: [], numeralOptions: [],
        });
      },
      
      togglePartOfSpeech: (partOfSpeech) =>
        set((state) => ({
          openPartOfSpeechMenus: {
            ...state.openPartOfSpeechMenus,
            [partOfSpeech]: !state.openPartOfSpeechMenus[partOfSpeech],
          },
          selectedPartsOfSpeech: state.selectedPartsOfSpeech.includes(partOfSpeech)
            ? state.selectedPartsOfSpeech.filter((pos) => pos !== partOfSpeech)
            : [...state.selectedPartsOfSpeech, partOfSpeech],
        })),

      toggleVerbOption: (option) =>
        set((state) => ({
          verbOptions: state.verbOptions.includes(option)
            ? state.verbOptions.filter((o) => o !== option)
            : [...state.verbOptions, option],
        })),
    }),
    {
      name: 'app-preferences-storage',
      // We tell 'partialize' which parts of the state to save.
      partialize: (state) => ({
        theme: state.theme,
        language: state.language,
        difficulty: state.difficulty,
        favorites: state.favorites,
        useReducedMotion: state.useReducedMotion,
      }),
    }
  )
);

export const usePreferencesStore = (selector) => useStore(preferencesStore, selector);
