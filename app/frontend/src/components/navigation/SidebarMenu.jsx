import { useState } from "react";
import { LayoutDashboard, Settings2, Info, MessageCirclePlus, Languages } from "lucide-react";
import AppModal from "../modals/AppModal";
import '../../css/LanguageButton.css';
import i18n from '../../i18n';

export default function Sidebar() {
  // Modal state: which page is open
  const [activeModalPage, setActiveModalPage] = useState(null);
  // toggle the language selection for the entire page
  const toggleLanguage = () => {
    i18n.changeLanguage(i18n.language === 'en' ? 'ru' : 'en');
  };
  return (
    <>
      {/* Movable Sidebar */}
      <div className="fixed left-0 top-1/2 -translate-y-1/2 bg-gray-800 p-2 rounded-r-2xl flex flex-col space-y-4 z-50">
        {/* Each button sets activeModalPage state */}
        <button onClick={() => setActiveModalPage("dashboard")} size="icon">
          <LayoutDashboard className="text-white" />
        </button>
        <button
          onClick={() => setActiveModalPage("settings")}
          size="icon"
          >
            <Settings2 className="text-white" />
        </button>
        <button 
          onClick={() => setActiveModalPage("info")} 
          size="icon"
          >
            <Info className="text-white" />
        </button>
        <button 
          onClick={() => setActiveModalPage("feedback")}
          size="icon"
          >
            <MessageCirclePlus className="text-white" />
        </button>
        <button
          onClick={toggleLanguage}
          size="icon"
          className="language-button"
          >
            <Languages />
        </button>
      </div>

      {/* Modal, controlled via state */}
      <AppModal
        open={!!activeModalPage}
        onClose={() => setActiveModalPage(null)}
        activePage={activeModalPage}
        setActivePage={setActiveModalPage}
      />
    </>
  );
}
