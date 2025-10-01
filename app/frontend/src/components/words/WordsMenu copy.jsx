import { usePreferencesStore } from "../../state/usePreferencesStore";
import WordSelector from "./WordSelector";
import VerbsSubMenu from "./VerbSubMenu";
import NounsSubMenu from "./NounsSubMenu";
import { AnimatePresence, motion } from "framer-motion";

export default function WordsMenu() {
  const { togglePartOfSpeech, selectedPartsOfSpeech, openPartOfSpeechMenus } =
    usePreferencesStore();

  const categories = ["Verbs", "Nouns", "Adjectives", "Participles"];

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Word Forms</h1>

      <WordSelector />

      <div className="grid grid-cols-4 gap-4 mt-6">
        {categories.map((category) => {
          const key = category.toLowerCase();
          return (
            <div key={category} className="border p-4 rounded-xl shadow">
              <button
                onClick={() => togglePartOfSpeech(key)}
                className={`w-full p-2 rounded-lg text-lg ${
                  selectedPartsOfSpeech.includes(key)
                    ? "bg-blue-600 text-white"
                    : "bg-gray-200"
                }`}
              >
                {category}
              </button>
              <AnimatePresence>
                {openPartOfSpeechMenus[key] && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                    className="mt-4"
                  >
                    {key === "verbs" && <VerbsSubMenu />}
                    {key === "nouns" && <NounsSubMenu />}
                    {key === "adjectives" && <AdjectivesSubMenu />}
                    {key === "participles" && <ParticiplesSubMenu />}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>
    </div>
  );
}
