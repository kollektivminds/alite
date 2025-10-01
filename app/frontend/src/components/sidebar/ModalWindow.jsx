import * as Dialog from '@radix-ui/react-dialog';

export function DashboardModal({ open, onClose }) {
  return (
    <Dialog.Root open={open} onOpenChange={onClose}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white p-6 rounded-2xl shadow-2xl max-w-lg z-50">
          <Dialog.Title className="text-xl font-bold mb-4">Dashboard</Dialog.Title>
          <p>Your dashboard content here!</p>
          <div className="mt-4 text-right">
            <button onClick={onClose} className="text-blue-600 font-semibold">Close</button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
