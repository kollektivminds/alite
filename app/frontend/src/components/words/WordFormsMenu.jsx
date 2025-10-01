import React from 'react';
import WordListSelector from './WordListSelector';
import WordFormCategories from './WordFormCategories';
import FileDropdown from '../navigation/FileDropdown'
import { useTranslation } from 'react-i18next';

function WordFormsMenu({ onBack }) {
  const { t } = useTranslation();

  return (
    <div className="p-8 w-full max-w-6xl">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-3xl font-bold">{t('wordsMenu.wordForms')}</h2>
        <button onClick={onBack} className="text-sm font-semibold bg-gray-300 hover:bg-gray-400 px-3 py-1 rounded">← {t('back', { postProcess: 'lowercase' })}</button>
      </div>
      <FileDropdown />
      <input type="text" placeholder="Add a word..." className="border p-2 rounded w-64" />
      <WordFormCategories />
    </div>
  );
}

export default WordFormsMenu;