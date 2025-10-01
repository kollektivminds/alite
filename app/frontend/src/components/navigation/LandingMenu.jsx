import { motion } from "framer-motion";
import { usePreferencesStore } from "../../state/usePreferencesStore";

export default function LandingMenu({ onSelect }) {
  const setContentType = usePreferencesStore((state) => state.setContentType);

  const handleClick = (type) => {
    setContentType(type);
    onSelect();
  };

  return (
    <motion.div
      className="flex justify-center items-center h-screen"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <div className="bg-white rounded-2xl p-8 shadow-xl flex space-x-8">
        {["Words", "Sentences", "Paragraphs"].map((item) => (
          <button
            key={item}
            onClick={() => handleClick(item.toLowerCase())}
            className="text-xl font-semibold px-6 py-3 rounded-lg bg-blue-500 text-white hover:bg-blue-600"
          >
            {item}
          </button>
        ))}
      </div>
    </motion.div>
  );
}