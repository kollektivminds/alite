import * as Popover from '@radix-ui/react-popover';
import { useState } from 'react';

const versionUpdates = [
  {
    version: 'v1.2.0',
    date: '2025-06-01',
    details: 'Added user profile editing and improved dashboard performance.',
  },
  {
    version: 'v1.1.0',
    date: '2025-05-15',
    details: 'Fixed login issues and updated database schema for orders.',
  },
  {
    version: 'v1.0.0',
    date: '2025-05-01',
    details: 'Initial launch with basic CRUD features.',
  },
];

export default function VersionLogPopover() {
  const [open, setOpen] = useState(false);

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700">
          📋 Version Log
        </button>
      </Popover.Trigger>
      <Popover.Content sideOffset={8} className="p-4 w-80 rounded shadow-lg bg-white border border-gray-200">
        <h2 className="text-lg font-semibold mb-2">📜 Update History</h2>
        <ul className="space-y-2">
          {versionUpdates.map((update) => (
            <li key={update.version}>
              <strong>{update.version}</strong> <span className="text-gray-500">({update.date})</span>
              <p className="text-sm">{update.details}</p>
            </li>
          ))}
        </ul>
        <Popover.Close asChild>
          <button className="mt-3 px-3 py-1 text-sm rounded bg-gray-200 hover:bg-gray-300">
            Close
          </button>
        </Popover.Close>
      </Popover.Content>
    </Popover.Root>
  );
}
