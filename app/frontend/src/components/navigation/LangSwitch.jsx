import { useTranslation } from 'react-i18next';
import i18n from '../../i18n';

export default function LanguageSwitcher() {
  const { i18n, t } = useTranslation();

  const toggleLanguage = () => {
    i18n.changeLanguage(i18n.language === 'en' ? 'ru' : 'en');
  };

  return (
    <button
      onClick={toggleLanguage}
      className="button"
      >
        {t('language')}: {i18n.language === 'en' ? 'Eng' : 'Рус'}
    </button>
  );
}
