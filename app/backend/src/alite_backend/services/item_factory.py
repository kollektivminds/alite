# app/backend/services/item_factory.py
import random
from typing import List, Optional

from alite_backend.db import schemas
from alite_backend.db.models import EnumItemFormat


class ItemFormatFactory:
    """
    Transforms raw ItemBlueprints into client-deliverable format schemas.
    """

    @classmethod
    def create_formatted_item(
        cls,
        strategy: schemas.AnyItemType,
        blueprint: schemas.ItemBlueprint,
        allowed_session_formats: List[EnumItemFormat],
        item_id: int,
    ) -> Optional[schemas.ExerciseItems]:

        # 1. Fetch strict compatibility set from schemas.py
        compatible = schemas.STRATEGY_FORMAT_COMPATIBILITY.get(strategy, frozenset())
        viable_formats = [fmt for fmt in allowed_session_formats if fmt in compatible]

        if not viable_formats:
            return None

        # 2. Distractor check for MCQ
        if EnumItemFormat.MCQ in viable_formats:
            if not blueprint.distractors or len(blueprint.distractors) < 2:
                viable_formats.remove(EnumItemFormat.MCQ)

        if not viable_formats:
            return None

        # 3. Materialize the selected format
        selected_format = random.choice(viable_formats)

        if selected_format == EnumItemFormat.MCQ:
            options = [blueprint.keys] + blueprint.distractors[:3]
            random.shuffle(options)
            return schemas.MultipleChoiceResponse(
                item_id=item_id,
                prompt=blueprint.prompt,
                options=options,
            )

        if selected_format == EnumItemFormat.FITB:
            return schemas.FillInTheBlankResponse(
                item_id=item_id,
                prompt=blueprint.prompt,
                parts=[f"{blueprint.prompt}: ", ""],
            )

        if selected_format == EnumItemFormat.FLASHCARD:
            return schemas.FlashcardResponse(
                item_id=item_id,
                prompt=blueprint.prompt,
                back_text=blueprint.keys,
            )

        return None
