import * as Dialog from "@radix-ui/react-dialog";
import { useTranslation } from "react-i18next";
import DashboardContent from "./DashboardModal";
import FeedbackModal from "./FeedbackModal";
import InfoModal from "./InfoModal";
import SettingsModal from "./SettingsModal";

/*
 * Reflexive modal that swaps content based on `activePage` prop
 */
export default function AppModal({ open, onClose, activePage, setActivePage }) {
  const { t } = useTranslation();

  return (
    <Dialog.Root open={open} onOpenChange={onClose}>
      <Dialog.Portal>
        {/* Background overlay */}
        <Dialog.Overlay className="fixed inset-0 bg-black/40 z-40" />
        <Dialog.Content
          className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                    bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100
                    rounded-2xl shadow-2xl p-6 z-50
                    w-full h-auto max-w-2xl max-h-[75vh] overflow-auto
                    flex flex-col border border-transparent dark:border-slate-800"
        >
          {/* Modal Title */}
          <Dialog.Title className="content-center text-lg font-semibold mb-4 capitalize flex-shrink-0 pb-4 border-b border-slate-200 dark:border-slate-800">
            {t(`modal.menu.${activePage}`)}
          </Dialog.Title>

          {/* Navigation buttons inside modal */}
          <div className="flex gap-4 mb-6 border-b border-slate-100 pb-2 dark:border-slate-800/60">
            {["dashboard", "settings", "info", "feedback"].map((page) => (
              <button
                key={page}
                onClick={() => setActivePage(page)}
                className={`font-medium transition-colors ${
                  activePage === page
                    ? "text-indigo-600 dark:text-indigo-400 font-semibold"
                    : "text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                }`}
              >
                {t(`modal.menu.${page}`)}
              </button>
            ))}
          </div>

          {/* Modal content swapping based on activePage */}
          <div className="space-y-4">
            {activePage === "dashboard" && <DashboardContent />}
            {activePage === "settings" && <SettingsModal />}
            {activePage === "info" && <InfoModal />}
            {activePage === "feedback" && <FeedbackModal />}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
