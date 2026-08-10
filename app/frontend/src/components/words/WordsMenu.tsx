import React, { useState, useEffect, useCallback } from 'react';

/**
 * Domain Interfaces for the Word Exercise Creator.
 * Direct TypeScript types for DB entities and custom user inputs.
 */
export interface Lemma {
  id: number;
  lemText: string;
  pos: string;
}

export interface CustomToken {
  id: string;
  lemText: string;
  isCustom: true;
}

export type PoolItem = Lemma | CustomToken;

/**
 * Props Contract for the Triptych Lemma Pool Selector
 */
export interface WordsMenuProps {
  initialPool?: PoolItem[];
  onPoolChange?: (pool: PoolItem[]) => void;
}

export const WordsMenu: React.FC<WordsMenuProps> = ({ 
  initialPool = [], 
  onPoolChange 
}) => {
  // 1. Single Source of Truth for the selected lemma pool
  const [pool, setPool] = useState<PoolItem[]>(initialPool);

  // Sync state changes with parent component if callback provided
  useEffect(() => {
    if (onPoolChange) {
      onPoolChange(pool);
    }
  }, [pool, onPoolChange]);

  /**
   * Deduplicates and appends new items to the pool.
   * Prevents adding duplicates based on 'lemText'.
   */
  const handleAddItems = useCallback((itemsToAdd: PoolItem[]) => {
    setPool((currentPool) => {
      const existingTexts = new Set(currentPool.map((item) => item.lemText.toLowerCase()));
      const uniqueNewItems = itemsToAdd.filter(
        (item) => !existingTexts.has(item.lemText.toLowerCase())
      );
      return [...currentPool, ...uniqueNewItems];
    });
  }, []);

  /**
   * Removes a single item from the pool by its text value.
   */
  const handleRemoveItem = useCallback((lemText: string) => {
    setPool((currentPool) => 
      currentPool.filter((item) => item.lemText.toLowerCase() !== lemText.toLowerCase())
    );
  }, []);
  
  return (
    <div className="w-full max-w-7xl mx-auto p-4 space-y-4">
      <header className="border-b pb-3 dark:border-slate-700">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
          Word-Level Exercise Creator: Pool Builder
        </h1>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Select modules, query database lemmas, or add custom words to build your study pool.
        </p>
      </header>

      {/* Triptych Grid: 1 column on mobile, 3 columns on desktop */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 min-h-[500px]">
        
        {/* PANEL 1: Module & Lesson Collections */}
        <section className="p-4 border rounded-xl bg-white dark:bg-slate-800 dark:border-slate-700 shadow-sm flex flex-col">
          <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-3">
            1. Select Collections
          </h2>
          <div className="flex-1 flex items-center justify-center border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-lg text-slate-400 text-sm">
            {/* Module / LessonList Checkbox Selector Placeholder */}
            <span>Module & Lesson Lists Panel</span>
          </div>
        </section>

        {/* PANEL 2: Search Box & Custom Entry */}
        <section className="p-4 border rounded-xl bg-white dark:bg-slate-800 dark:border-slate-700 shadow-sm flex flex-col">
          <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-3">
            2. Search & Add Lemmas
          </h2>
          <LemmaSearchPanel onAddSingle={(item) => handleAddItems([item])} />
        </section>

        {/* PANEL 3: Active Pool Window */}
        <section className="p-4 border rounded-xl bg-slate-50 dark:bg-slate-900 dark:border-slate-700 shadow-sm flex flex-col">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200">
              3. Active Lemma Pool
            </h2>
            <span className="text-xs font-mono bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-300 px-2 py-1 rounded-full font-bold">
              {pool.length} {pool.length === 1 ? 'word' : 'words'}
            </span>
          </div>

          <ActivePoolViewer items={pool} onRemove={handleRemoveItem} />
        </section>

      </div>
    </div>
  );
};

/**
 * Panel 2 Search Component Handling Local Search State & Debouncing
 */
interface LemmaSearchPanelProps {
  onAddSingle: (item: PoolItem) => void;
}

const LemmaSearchPanel: React.FC<LemmaSearchPanelProps> = ({ onAddSingle }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = searchTerm.trim();
    if (!trimmed) return;

    // Create a CustomToken payload if word is typed manually
    const customItem: CustomToken = {
      id: `custom-${Date.now()}`,
      lemText: trimmed,
      isCustom: true,
    };

    onAddSingle(customItem);
    setSearchTerm('');
  };

  return (
    <form onSubmit={handleCustomSubmit} className="space-y-4 flex-1 flex flex-col">
      <div className="flex gap-2">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Type Cyrillic lemma or search..."
          className="flex-1 px-3 py-2 border rounded-lg dark:bg-slate-800 dark:text-slate-100 dark:border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg text-sm transition-colors"
        >
          Add
        </button>
      </div>

      <div className="flex-1 border rounded-lg p-3 bg-slate-50 dark:bg-slate-800/50 text-xs text-slate-500 dark:text-slate-400">
        Autocomplete dropdown suggestions matching DB `lemmas.lem_text` will render here.
      </div>
    </form>
  );
};

/**
 * Panel 3 Viewer Component for Displaying Active Pool Items
 */
interface ActivePoolViewerProps {
  items: PoolItem[];
  onRemove: (lemText: string) => void;
}

const ActivePoolViewer: React.FC<ActivePoolViewerProps> = ({ items, onRemove }) => {
  if (items.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-lg text-slate-400 text-sm">
        Pool is currently empty.
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto max-h-[420px] space-y-2 pr-1">
      {items.map((item) => {
        const isCustom = 'isCustom' in item;
        return (
          <div
            key={'id' in item ? item.id : item.lemText}
            className="flex items-center justify-between p-2.5 bg-white dark:bg-slate-800 border dark:border-slate-700 rounded-lg shadow-sm"
          >
            <div className="flex items-center space-x-2">
              <span className="font-bold text-slate-900 dark:text-slate-100">
                {item.lemText}
              </span>
              {isCustom ? (
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300 rounded">
                  Custom / FreeDict
                </span>
              ) : (
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded">
                  {item.pos}
                </span>
              )}
            </div>

            <button
              onClick={() => onRemove(item.lemText)}
              className="text-slate-400 hover:text-red-500 p-1 text-sm transition-colors"
              title="Remove from pool"
            >
              ✕
            </button>
          </div>
        );
      })}
    </div>
  );
};