// import SentenceListSelector from './SentenceListSelector';
import { useTranslation } from "react-i18next";
import FileDropdown from "../../components/navigation/FileDropdown";
import ParagraphFormCategories from "./ParagraphFormCategories";

function ParagraphFormsMenu({ onBack }) {
  const { t } = useTranslation();
  return (
    <div className="p-8 w-full max-w-6xl">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-3xl font-bold">
          {t("paragraphsMenu.paragraph_forms")}
        </h2>
        <button
          onClick={onBack}
          className="text-sm font-semibold bg-gray-300 hover:bg-gray-400 px-3 py-1 rounded"
        >
          ← {t("back")}
        </button>
      </div>
      <FileDropdown />
      <input
        type="text"
        placeholder="Add a Sentence..."
        className="border p-2 rounded w-64"
      />
      <ParagraphFormCategories />
    </div>
  );
}

export default ParagraphFormsMenu;
