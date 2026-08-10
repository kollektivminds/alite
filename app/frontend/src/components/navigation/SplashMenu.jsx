import React, { useState } from "react";
import { WordsMenu } from "../words/WordsMenu.tsx";
import SentencesMenu from "../sentences/SentencesMenu.jsx";
import ParagraphsMenu from "../paragraphs/ParagraphsMenu.jsx";
import { useTranslation } from 'react-i18next';


function SplashMenu() {
  const { t } = useTranslation();

  const [activeMenu, setActiveMenu] = useState(null);

  const handleSelect = (menu) => {
    setActiveMenu(menu);
  };

  const handleBack = () => {
    setActiveMenu(null);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-2">
      <div className="relative flex flex-col items-center">
        {/* Banner always visible */}
        <div
          className={`bg-blue-500 text-white text-xl font-semibold rounded-2xl px-6 py-3 shadow-lg mb-6 ${
            activeMenu ? "absolute -top-12" : ""
          } transition-all duration-300`}
          style={activeMenu ? { width: "fit-content" } : {}}
        >
          {activeMenu
            ? t('im_studying_what', { item : t(`splashMenu.${activeMenu}`)})
            : t('im_studying')}
        </div>

        {/* Menu buttons or submenu */}
        <div className={`flex flex-col space-y-4 ${activeMenu ? "pt-16" : ""}`}>
          {!activeMenu && (
            <div className="bg-stone-100 rounded-2xl shadow-xl p-6 flex space-x-6">
              <button
                onClick={() => handleSelect("words")}
                className="text-lg font-bold p-4 rounded bg-blue-500 text-white hover:bg-blue-600"
              >
                {t('splashMenu.words')}
              </button>
              <button
                onClick={() => handleSelect("sentences")}
                className="text-lg font-bold p-4 rounded bg-green-500 text-white hover:bg-green-600"
              >
                {t('splashMenu.sentences')}
              </button>
              <button
                onClick={() => handleSelect("paragraphs")}
                className="text-lg font-bold p-4 rounded bg-purple-500 text-white hover:bg-purple-600"
              >
                {t('splashMenu.paragraphs')}
              </button>
            </div>
          )}
          {activeMenu === "words" && <WordsMenu onBack={handleBack} />}
          {activeMenu === "sentences" && <SentencesMenu onBack={handleBack} />}
          {activeMenu === "paragraphs" && <ParagraphsMenu onBack={handleBack} />}
        </div>
      </div>
    </div>
  );
}
// console.log("Is this logging?");
export default SplashMenu;