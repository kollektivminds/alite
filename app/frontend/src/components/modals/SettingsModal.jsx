import React from 'react';
import { usePreferencesStore } from '../../state/usePreferencesStore';
import { useTranslation } from 'react-i18next';
import { useReducedMotion } from 'framer-motion';

export default function SettingsPage() {
  // Grab all the state values and action functions from the store
  const {
    difficulty,
    setDifficulty,
    theme,
    setTheme,
    useReducedMotion,
    toggleReducedMotion,
    language,
    setLanguage,
  } = usePreferencesStore();
  
  const { t, i18n } = useTranslation();

  return (
    <div className="settings-page">

      <div className="setting-item">
        <label htmlFor="difficulty-select">{t('modalSettings.difficulty')}</label>
        <select
          id="difficulty-select"
          value={difficulty}
          onChange={(e) => setDifficulty(e.target.value)}
        >
          <option value="easy">{t('modalSettings.easy')}</option>
          <option value="medium">{t('modalSettings.medium')}</option>
          <option value="hard">{t('modalSettings.hard')}</option>
        </select>
      </div>

      <div className="setting-item">
        <label htmlFor="theme-select">{t('modalSettings.theme')}</label>
        <select
          id="theme-select"
          value={theme}
          onChange={(e) => setTheme(e.target.value)}
        >
          <option value="light">{t('modalSettings.light')}</option>
          <option value="dark">{t('modalSettings.dark')}</option>
          <option value="system">{t('modalSettings.system')}</option>
        </select>
      </div>
      
      <div className="setting-item">
        <label>
          <input
            type="checkbox"
            checked={useReducedMotion}
            onChange={toggleReducedMotion}
          />
          {t('modalSettings.reduce_motion')}
        </label>
      </div>
      
      <div className="setting-item">
        <label htmlFor="difficulty-select">{t('Language')}</label>
        <select
          id="language-select"
          value={language}
          // onChange={languageToggle}
        >
          <option value="en">{t('languages.english')}</option>
          <option value="ru">{t('languages.russian')}</option>
=        </select>
      </div>

    </div>
  );
}