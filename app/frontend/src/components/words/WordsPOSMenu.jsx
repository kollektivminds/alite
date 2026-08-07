import {
  usePreferencesStore,
  preferencesStore,
} from "../../state/usePreferencesStore";
import { AnimatePresence, motion } from "framer-motion";
import VerbSubMenu from "./VerbSubMenu";
import NounSubMenu from "./NounSubMenu";
import AdjectiveSubMenu from "./AdjectiveSubMenu";
import ParticipleSubMenu from "./ParticipleSubMenu";
import FileDropdown from '../navigation/FileDropdown';
import WordFormsMenu from "./WordFormsMenu";
import axios from "axios";
import { useTranslation } from 'react-i18next';

console.log("Store instance:", preferencesStore.getState());

export default function WordsPOSMenu({ onBack }) {
  const { t } = useTranslation();

  const openPartOfSpeechMenus = usePreferencesStore(
    (state) => state.openPartOfSpeechMenus
  );
  const togglePartOfSpeech = usePreferencesStore(
    (state) => state.togglePartOfSpeech
  );
  
/*   const handleSubmit = async () => {
    const data = preferencesStore.getState();
    console.log("Submitting data:", data);
  
    try {
      const response = await axios.post(
        "http://localhost:8000/make/", // adjust to your actual API endpoint
        data
      );
      console.log("Response:", response.data);
    } catch (error) {
      console.error("Error submitting preferences:", error);
    }
  }; */

  console.log("WordsMenu rendering");

const categories = ['verbs', 'nouns', 'adjectives', 'participles', 'numerals'];

const buttonColors = {
  verbs: "bg-red-500 text-white",
  nouns: "bg-green-500 text-white",
  adjectives: "bg-blue-500 text-white",
  participles: "bg-yellow-500 text-black",
  numerals: "bg-purple-500 text-black"
};

const submenuColors = {
  verbs: "bg-red-100",
  nouns: "bg-green-100",
  adjectives: "bg-blue-100",
  participles: "bg-yellow-100",
  numerals: "bg-purple-100"
};

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">{t('wordsMenu.wordForms')}</h1>
      <button onClick={onBack} className="text-sm font-semibold bg-gray-300 hover:bg-gray-400 px-3 py-1 rounded">← {t('back')}</button>
      <FileDropdown />
      <input type="text" placeholder="Add a Word..." className="border p-2 rounded w-64" />
      <div className="grid grid-cols-4 gap-4 mt-6">
        {categories.map((category) => {
          const key = category.toLowerCase();
          console.log(`Rendering ${category}:`, openPartOfSpeechMenus[key]);

          return (
            <div key={category} className="border p-4 rounded-xl shadow">
              <button
                onClick={() => {
                  console.log(`Toggling ${key}`);
                  togglePartOfSpeech(key);
                }}
                className={`w-full p-2 rounded-lg text-lg ${
                  openPartOfSpeechMenus[key]
                    ? buttonColors[key]
                    : "bg-gray-200 text-black"
                }`}
              >
                {t(`wordsMenu.${key}`)}
              </button>
              
              <AnimatePresence>
                {openPartOfSpeechMenus[key] && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.5, ease: "easeInOut" }}
                    className={`mt-4 p-2 rounded ${submenuColors[key]} overflow-hidden`}
                  >
                    {key === "verbs" && <VerbSubMenu />}
                    {key === "nouns" && <NounSubMenu />}
                    {key === "adjectives" && <AdjectiveSubMenu />}
                    {key === "participles" && <ParticipleSubMenu />}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
        {/* <button
                onClick={handleSubmit}
                className="mt-8 p-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                Submit Preferences
        </button> */}
      </div>
    </div>
  );
}
