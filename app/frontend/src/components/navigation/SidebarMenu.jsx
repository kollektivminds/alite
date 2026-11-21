// app/frontend/src/components/navigation/SidebarMenu.jsx
import {
  Info,
  Languages,
  LayoutDashboard,
  MessageCirclePlus,
  Settings2,
} from "lucide-react";
import { useState } from "react";
import "../../css/LanguageButton.css";
import i18n from "../../i18n";
import AppModal from "../modals/AppModal";

export default function Sidebar({ onSelectDashboard, isDashboardActive = false }) {
  // Only settings, info, and feedback use AppModal; dashboard uses full-screen view state[cite: 27, 30].
  const [activeModalPage, setActiveModalPage] = useState(null);

  const toggleLanguage = () => {
    i18n.changeLanguage(i18n.language === "en" ? "ru" : "en");
  };

  const handleDashboardClick = () => {
    setActiveModalPage(null);
    if (typeof onSelectDashboard === "function") {
      onSelectDashboard();
    }
  };

  return (
    <>
      <nav
        aria-label="Workspace navigation"
        className="fixed left-0 top-1/2 -translate-y-1/2 bg-gray-800 p-2 rounded-r-2xl flex flex-col space-y-4 z-50"
      >
        <button
          type="button"
          onClick={handleDashboardClick}
          aria-pressed={isDashboardActive}
          title="Dashboard"
          className={isDashboardActive ? "ring-2 ring-indigo-400 rounded p-1" : "p-1"}
        >
          <LayoutDashboard className="text-white" />
        </button>

        <button
          type="button"
          onClick={() => setActiveModalPage("settings")}
          title="Settings"
          className="p-1"
        >
          <Settings2 className="text-white" />
        </button>

        <button
          type="button"
          onClick={() => setActiveModalPage("info")}
          title="Info"
          className="p-1"
        >
          <Info className="text-white" />
        </button>

        <button
          type="button"
          onClick={() => setActiveModalPage("feedback")}
          title="Feedback"
          className="p-1"
        >
          <MessageCirclePlus className="text-white" />
        </button>

        <button
          type="button"
          onClick={toggleLanguage}
          title="Language"
          className="language-button"
        >
          <Languages />
        </button>
      </nav>

      <AppModal
        open={!!activeModalPage}
        onClose={() => setActiveModalPage(null)}
        activePage={activeModalPage}
        setActivePage={setActiveModalPage}
      />
    </>
  );
}
