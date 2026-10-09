import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import translationEN from "./locales/en/translations.json";
import translationRU from "./locales/ru/translations.json";

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: translationEN },
    ru: { translation: translationRU },
  },
  lng: "en",
  fallbackLng: "ru",

  // CRITICAL: Forces i18next to use CLDR text suffixes (_one, _few, _many, _other)
  // rather than legacy numerical suffixes (_0, _1, _2).
  compatibilityJSON: "v4",

  interpolation: {
    escapeValue: false, // React already escapes values to prevent XSS
  },
});

i18n.use({
  type: "postProcessor",
  name: "capitalize",
  process(value) {
    return value.charAt(0).toUpperCase() + value.slice(1);
  },
});

i18n.use({
  type: "postProcessor",
  name: "lowercase",
  process(value) {
    return value.charAt(0).toLowerCase() + value.slice(1);
  },
});

export default i18n;
