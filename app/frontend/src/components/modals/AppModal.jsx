import * as Dialog from "@radix-ui/react-dialog";
import DashboardContent from "./DashboardModal";
import SettingsModal from "./SettingsModal";
import InfoModal from "./InfoModal";
import FeedbackModal from "./FeedbackModal";
import { useTranslation } from 'react-i18next';

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
                    bg-white rounded-2xl shadow-2xl p-6 z-50 
                    w-full h-auto max-w-2xl max-h-[75vh] overflow-auto
                    flex flex-col"
        >  
          {/* Modal Title */}
          <Dialog.Title className="content-center text-lg font-semibold mb-4 capitalize flex-shrink-0 p-6 border-b">
            {t(`modalMenu.${activePage}`)}
          </Dialog.Title>

          {/* Navigation buttons inside modal */}
          <div className="flex gap-4 mb-6">
            <button onClick={() => setActivePage("dashboard")} className="text-blue-600 font-medium">{t('modalMenu.dashboard')}</button>
            <button onClick={() => setActivePage("settings")} className="text-blue-600 font-medium">{t('modalMenu.settings')}</button>
            <button onClick={() => setActivePage("info")} className="text-blue-600 font-medium">{t('modalMenu.info')}</button>
            <button onClick={() => setActivePage("feedback")} className="text-blue-600 font-medium">{t('modalMenu.feedback')}</button>
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
