import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import translationEN from './locales/en/translations.json';
import translationRU from './locales/ru/translations.json';

const resources = {
  en: { translation: translationEN },
  ru: { translation: translationRU }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'en',
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false
    }
  });

i18n.use({
  type: 'postProcessor',
  name: 'capitalize',
  process(value) {
    return value.charAt(0).toUpperCase() + value.slice(1);
  }
});

i18n.use({
  type: 'postProcessor',
  name: 'lowercase',
  process(value) {
    return value.charAt(0).toLowerCase() + value.slice(1);
  }
});

export default i18n;
