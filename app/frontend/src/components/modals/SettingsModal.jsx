// src/components/modals/SettingsModal.jsx
import { useTranslation } from "react-i18next";
import { usePreferencesStore } from "../../state/usePreferencesStore";

export default function SettingsModal() {
  const {
    difficulty,
    setDifficulty,
    theme,
    setTheme,
    fontSize,
    setFontSize,
    reducedMotion,
    toggleReducedMotion,
    language,
    setLanguage,
  } = usePreferencesStore();

  const { t, i18n } = useTranslation();

  const handleLanguageChange = (e) => {
    const selectedLang = e.target.value;
    setLanguage(selectedLang);
    i18n.changeLanguage(selectedLang);
  };

  return (
    <div className="space-y-6 text-slate-800 dark:text-slate-100">
      {/* Target Difficulty Level */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-4 dark:border-slate-800">
        <div>
          <label htmlFor="difficulty-select" className="font-medium block">
            {t("modal.settings.difficulty", "Default Difficulty")}
          </label>
          <span className="text-xs text-slate-500 dark:text-slate-400">
            {t(
              "modal.settings.difficulty_desc",
              "Initial difficulty rating for new drills",
            )}
          </span>
        </div>
        <select
          id="difficulty-select"
          value={difficulty}
          onChange={(e) => setDifficulty(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
        >
          <option value="easy">
            {t("modal.settings.easy", "Novice / Easy")}
          </option>
          <option value="medium">
            {t("modal.settings.medium", "Intermediate")}
          </option>
          <option value="hard">{t("modal.settings.hard", "Advanced")}</option>
        </select>
      </div>

      {/* Theme Selection */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-4 dark:border-slate-800">
        <div>
          <label htmlFor="theme-select" className="font-medium block">
            {t("modal.settings.theme", "Color Theme")}
          </label>
          <span className="text-xs text-slate-500 dark:text-slate-400">
            {t("modal.settings.theme_desc", "Adjust interface luminance")}
          </span>
        </div>
        <select
          id="theme-select"
          value={theme}
          onChange={(e) => setTheme(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
        >
          <option value="light">{t("modal.settings.light", "Light")}</option>
          <option value="dark">{t("modal.settings.dark", "Dark")}</option>
          <option value="system">
            {t("modal.settings.system", "System Default")}
          </option>
        </select>
      </div>

      {/* Font Size / UI Scaling */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-4 dark:border-slate-800">
        <div>
          <label htmlFor="fontsize-select" className="font-medium block">
            {t("modal.settings.font_size", "Display Font Size")}
          </label>
          <span className="text-xs text-slate-500 dark:text-slate-400">
            {t(
              "modal.settings.font_size_desc",
              "Improve legibility of Russian typography",
            )}
          </span>
        </div>
        <select
          id="fontsize-select"
          value={fontSize}
          onChange={(e) => setFontSize(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
        >
          <option value="sm">
            {t("modal.settings.font_sm", "Compact (14px)")}
          </option>
          <option value="base">
            {t("modal.settings.font_base", "Standard (16px)")}
          </option>
          <option value="lg">
            {t("modal.settings.font_lg", "Large (18px)")}
          </option>
          <option value="xl">
            {t("modal.settings.font_xl", "Extra Large (20px)")}
          </option>
        </select>
      </div>

      {/* Reduced Motion Toggle */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-4 dark:border-slate-800">
        <div>
          <label htmlFor="reduced-motion" className="font-medium block">
            {t("modal.settings.reduce_motion", "Reduce Motion")}
          </label>
          <span className="text-xs text-slate-500 dark:text-slate-400">
            {t(
              "modal.settings.reduce_motion_desc",
              "Disable decorative interface animations",
            )}
          </span>
        </div>
        <input
          id="reduced-motion"
          type="checkbox"
          checked={reducedMotion}
          onChange={toggleReducedMotion}
          className="h-5 w-5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800"
        />
      </div>

      {/* Interface Language */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <label htmlFor="language-select" className="font-medium block">
            {t("modal.settings.language", "Interface Language")}
          </label>
          <span className="text-xs text-slate-500 dark:text-slate-400">
            {t(
              "modal.settings.language_desc",
              "Platform localization language",
            )}
          </span>
        </div>
        <select
          id="language-select"
          value={language}
          onChange={handleLanguageChange}
          className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
        >
          <option value="en">{t("languages.english", "English")}</option>
          <option value="ru">{t("languages.russian", "Русский")}</option>
        </select>
      </div>
    </div>
  );
}
