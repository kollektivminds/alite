import React from 'react';
import '../css/LanguageButton.css';
import { useTranslation } from 'react-i18next';
import { LayoutDashboard, Wrench, Info, MessageCircle, Languages } from "lucide-react";
import i18n from '../../i18n';

const LanguageButton = ({ language, onClick }) => {
    const { i18n, t } = useTranslation();
    const toggleLanguage = () => {
        i18n.changeLanguage(i18n.language === 'en' ? 'ru' : 'en');
  };
  return (
    <button
      onClick={toggleLanguage}
      size="icon"
      className="language-button"
      >
        {i18n.language === 'en' ? 'A-Z' : 'А-Я'}
    </button>
  );
};

export default LanguageButton;