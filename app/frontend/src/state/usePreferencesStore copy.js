import { createStore } from "zustand/vanilla";

import { useStore } from "zustand";

// Create a store instance

export const preferencesStore = createStore((set) => ({
  openPartOfSpeechMenus: {},

  selectedPartsOfSpeech: [],

  verbOptions: [],

  nounOptions: [],

  adjectiveOptions: [],

  participleOptions: [],

  togglePartOfSpeech: (partOfSpeech) =>
    set((state) => {
      const alreadySelected =
        state.selectedPartsOfSpeech.includes(partOfSpeech);

      return {
        openPartOfSpeechMenus: {
          ...state.openPartOfSpeechMenus,

          [partOfSpeech]: !state.openPartOfSpeechMenus[partOfSpeech],
        },

        selectedPartsOfSpeech: alreadySelected
          ? state.selectedPartsOfSpeech.filter((pos) => pos !== partOfSpeech)
          : [...state.selectedPartsOfSpeech, partOfSpeech],
      };
    }),

  toggleVerbOption: (option) =>
    set((state) => ({
      verbOptions: state.verbOptions.includes(option)
        ? state.verbOptions.filter((o) => o !== option)
        : [...state.verbOptions, option],
    })),

  toggleNounOption: (option) =>
    set((state) => ({
      nounOptions: state.nounOptions.includes(option)
        ? state.nounOptions.filter((o) => o !== option)
        : [...state.nounOptions, option],
    })),

  togglePronounOption: (option) =>
    set((state) => ({
      pronounOptions: state.pronounOptions.includes(option)
        ? state.pronounOptions.filter((o) => o !== option)
        : [...state.pronounOptions, option],
    })),

  toggleAdjectiveOption: (option) =>
    set((state) => ({
      adjectiveOptions: state.adjectiveOptions.includes(option)
        ? state.adjectiveOptions.filter((o) => o !== option)
        : [...state.adjectiveOptions, option],
    })),

  toggleParticipleOption: (option) =>
    set((state) => ({
      participleOptions: state.participleOptions.includes(option)
        ? state.participleOptions.filter((o) => o !== option)
        : [...state.participleOptions, option],
    })),

  toggleNumerOption: (option) =>
    set((state) => ({
      numeralOptions: state.numeralOptions.includes(option)
        ? state.numeralOptions.filter((o) => o !== option)
        : [...state.numeralOptions, option],
    })),
}));

// Hook to use in components

export const usePreferencesStore = (selector) =>
  useStore(preferencesStore, selector);
