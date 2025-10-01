import React from 'react';
import { motion } from 'motion/react';
import { useTranslation } from 'react-i18next';

function WordFormCategories() {
  const { t } = useTranslation();

  const categories = [
    { label: 'verbs', color: 'bg-blue-300' },
    { label: 'nouns', color: 'bg-green-300' },
    { label: 'adjectives', color: 'bg-yellow-300' },
    { label: 'participles', color: 'bg-pink-300' },
    { label: 'numerals', color: 'bg-red-300' },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 mt-8">
      {categories.map((cat) => (
        <motion.button
          key={cat.label}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className={`text-lg font-bold p-6 rounded-xl shadow-md text-white ${cat.color} transition`}
        >
          {cat.label}
        </motion.button>
      ))}
    </div>
  );
}

export default WordFormCategories;