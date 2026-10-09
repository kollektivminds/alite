/**
 * src/features/exercises/ItemFormatRouter.tsx
 */

import React from "react";
import { AttemptRecord, ExerciseItem } from "../../types/exercise";
import { FITBDisplay } from "./FITBDisplay";
import { FlashcardDisplay } from "./FlashcardDisplay";
import { MCQDisplay } from "./MCQDisplay";
import { UnscrambleDisplay } from "./UnscrambleDisplay";

interface ItemFormatRouterProps {
  item: ExerciseItem;
  attemptsRecord: AttemptRecord;
  onEvaluate: (responseToken: string) => void;
  isResolved: boolean;
}

export const ItemFormatRouter: React.FC<ItemFormatRouterProps> = ({
  item,
  attemptsRecord,
  onEvaluate,
  isResolved,
}) => {
  switch (item.item_format) {
    case "mcq":
      return (
        <MCQDisplay
          key={item.item_id}
          item={item}
          attemptsRecord={attemptsRecord}
          onEvaluate={onEvaluate}
          isResolved={isResolved}
        />
      );

    case "fitb":
      return (
        <FITBDisplay
          key={item.item_id}
          item={item}
          attemptsRecord={attemptsRecord}
          onEvaluate={onEvaluate}
          isResolved={isResolved}
        />
      );

    case "unscramble":
      return (
        <UnscrambleDisplay
          key={item.item_id}
          item={item}
          attemptsRecord={attemptsRecord}
          onEvaluate={onEvaluate}
          isResolved={isResolved}
        />
      );

    case "flashcard":
      return (
        <FlashcardDisplay
          key={item.item_id}
          item={item}
          onEvaluate={onEvaluate}
          isResolved={isResolved}
        />
      );

    default:
      return (
        <div className="p-4 rounded-lg bg-red-50 text-red-700 text-center font-medium">
          Неподдерживаемый формат задания:{" "}
          <code className="font-mono font-bold">
            {(item as any).item_format}
          </code>
        </div>
      );
  }
};
