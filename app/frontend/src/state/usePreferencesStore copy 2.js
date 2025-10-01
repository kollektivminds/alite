import { createStore } from "zustand/vanilla";
import { useStore } from "zustand";
import { persist } from 'zustand/middleware';

export const preferencesStore = createStore(
  persist(
    (set, get) => ({ // We need 'get' to access current state inside an action
      // ===================================
      // 1. PERSISTENT STATE
      // ===================================
      theme: 'system',
      language: 'en',
      difficulty: 'medium',
      reduceMotion: false,
      
      // This will hold all the user's saved configurations
      favorites: [], // e.g., [{ id: '123', name: 'My Verb Drill', config: {...} }]

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

      // --- Actions for preferences ---
      setTheme: (newTheme) => set({ theme: newTheme }),
      setLanguage: (newLang) => set({ language: newLang }),
      setDifficulty: (newDifficulty) => set({ difficulty: newDifficulty }),
      setReduceMotion: (newDifficulty) => set({ difficulty: newDifficulty }),

      // --- Actions for the 'Favorites' feature ---
      saveFavorite: (name) => {
        const { selectedPartsOfSpeech, verbOptions, nounOptions, pronounOptions, adjectiveOptions, participleOptions, numeralOptions } = get();
        
        const newFavorite = {
          id: Date.now().toString(), // Simple unique ID
          name: name,
          config: {
            selectedPartsOfSpeech,
            verbOptions,
            nounOptions,
            pronounOptions,
            adjectiveOptions,
            participleOptions,
            numeralOptions,
          }
        };

        set((state) => ({ favorites: [...state.favorites, newFavorite] }));
      },

      loadFavorite: (id) => {
        const favorite = get().favorites.find(fav => fav.id === id);
        if (favorite) {
          // Set all the transient selection states from the loaded favorite's config
          set({ ...favorite.config });
        }
      },

      deleteFavorite: (id) => {
        set((state) => ({
          favorites: state.favorites.filter(fav => fav.id !== id)
        }));
      },

      // --- Actions for temporary selections ---
      resetCurrentSelection: () => {
        set({
          selectedPartsOfSpeech: [],
          verbOptions: [],
          nounOptions: [],
          pronounOptions: [],
          adjectiveOptions: [],
          participleOptions: [],
          numeralOptions: [],
        });
      },
      
      // ... your existing toggle actions remain the same ...
      togglePartOfSpeech: (partOfSpeech) => set((state) => ({ /* ... */ })),
      toggleVerbOption: (option) => set((state) => ({ /* ... */ })),
      // etc.
    }),
    {
      name: 'app-preferences-storage',
      // We now tell 'partialize' to also save the 'favorites' array!
      partialize: (state) => ({
        theme: state.theme,
        language: state.language,
        difficulty: state.difficulty,
        favorites: state.favorites, // <-- CRUCIAL ADDITION
      }),
    }
  )
);

export const usePreferencesStore = (selector) => useStore(preferencesStore, selector);