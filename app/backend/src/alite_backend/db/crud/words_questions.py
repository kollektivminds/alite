# app/backend/db/crud/words_questions.py
import logging
import random
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from alite_backend.db import models, schemas
from alite_backend.db.models import (
    EnumItemFormat,
    EnumPartOfSpeech,
    EnumRelLemType,
    EnumWordItemType,
    Lemma,
)
from alite_backend.services.item_factory import ItemFormatFactory
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

logger = logging.getLogger(__name__)


class WordExerciseGenerator:
    """
    Pedagogical item generation engine with capacity-aware quota allocation,
    grammatically constrained distractor synthesis, and format degradation fallbacks.
    """

    def __init__(self, db: Session):
        self.db = db

    def evaluate_strategy_capacity(
        self, staged_lemmas: List[Lemma]
    ) -> Dict[EnumWordItemType, List[Lemma]]:
        """
        Builds a strategy-to-eligible-lemmas index.

        Calculates the theoretical upper bound of items each strategy can produce
        based strictly on the morphological properties present in the staged pool.
        """
        capacity_map: Dict[EnumWordItemType, List[Lemma]] = defaultdict(list)

        for lem in staged_lemmas:
            pos = lem.pos
            has_defs = bool(lem.definitions)
            has_prons = bool(lem.pronunciations)
            form_count = len(lem.lemma_word_form) if lem.lemma_word_form else 0

            # 1. Base Headword Strategies (Require definition or pronunciation)
            if has_defs:
                capacity_map[EnumWordItemType.LEM_TO_DEF].append(lem)
                capacity_map[EnumWordItemType.DEF_TO_LEM].append(lem)

            if has_prons:
                capacity_map[EnumWordItemType.LEM_TO_PRON].append(lem)
                capacity_map[EnumWordItemType.PRON_TO_LEM].append(lem)

            if pos:
                capacity_map[EnumWordItemType.LEM_TO_POS].append(lem)
                capacity_map[EnumWordItemType.POS_TO_LEM].append(lem)

            # 2. Substantive & Noun Strategies
            if pos == EnumPartOfSpeech.NOUN:
                if lem.noun_gender:
                    capacity_map[EnumWordItemType.NOUN_TO_GEND].append(lem)
                    capacity_map[EnumWordItemType.GEND_TO_NOUN].append(lem)
                if lem.noun_animacy is not None:
                    capacity_map[EnumWordItemType.NOUN_TO_ANIM].append(lem)
                    capacity_map[EnumWordItemType.ANIM_TO_NOUN].append(lem)
                if form_count > 0:
                    capacity_map[EnumWordItemType.NOUN_FORM_TO_GRAM].append(lem)
                    capacity_map[EnumWordItemType.NOUN_GRAM_TO_FORM].append(lem)

            # 3. Verb Strategies
            elif pos == EnumPartOfSpeech.VERB:
                if lem.verb_aspect:
                    capacity_map[EnumWordItemType.VERB_TO_ASPT].append(lem)
                    capacity_map[EnumWordItemType.ASPT_TO_VERB].append(lem)

                # Aspectual pairs require established relational edges in lem_rels
                has_aspect_pair = any(
                    r.rel_type
                    in (
                        EnumRelLemType.PERFECTIVE_PAIR_OF,
                        EnumRelLemType.IMPERFECTIVE_PAIR_OF,
                    )
                    for r in (lem.related_to or [])
                )
                if has_aspect_pair:
                    capacity_map[EnumWordItemType.VERB_TO_ASPT_PAIR].append(lem)

                if form_count > 0:
                    capacity_map[EnumWordItemType.VERB_TO_CONJ_FORM].append(lem)

            # 4. Adjective Strategies
            elif pos == EnumPartOfSpeech.ADJECTIVE:
                if form_count > 0:
                    capacity_map[EnumWordItemType.ADJV_FORM_TO_GRAM].append(lem)
                    capacity_map[EnumWordItemType.ADJV_GRAM_TO_FORM].append(lem)

        return capacity_map

    def rebalance_quotas(
        self,
        requested_counts: Dict[str, int],
        capacity_map: Dict[EnumWordItemType, List[Lemma]],
        target_total: int,
    ) -> Dict[EnumWordItemType, int]:
        """
        Executes a water-filling rebalance.

        Guarantees that no strategy is allocated more items than its available key candidates,
        and reallocates deficits to strategies with surplus capacity until target_total is met.
        """
        final_allocations: Dict[EnumWordItemType, int] = {}
        deficit = 0

        # Phase 1: Cap allocations to actual strategy capacities
        for strat_key, count in requested_counts.items():
            try:
                strat_enum = EnumWordItemType(strat_key)
            except ValueError:
                continue

            available_keys = len(capacity_map.get(strat_enum, []))
            actual_alloc = min(count, available_keys)
            deficit += count - actual_alloc
            final_allocations[strat_enum] = actual_alloc

        # Phase 2: Redistribute deficit across strategies with remaining headroom
        if deficit > 0:
            surplus_strategies = [
                s
                for s, lemmas in capacity_map.items()
                if len(lemmas) > final_allocations.get(s, 0)
            ]

            while deficit > 0 and surplus_strategies:
                progress = False
                for s in list(surplus_strategies):
                    headroom = len(capacity_map[s]) - final_allocations.get(s, 0)
                    if headroom > 0 and deficit > 0:
                        final_allocations[s] = final_allocations.get(s, 0) + 1
                        deficit -= 1
                        progress = True
                    else:
                        surplus_strategies.remove(s)

                if not progress:
                    # Staged pool is mathematically exhausted; cannot satisfy remaining deficit
                    break

        return final_allocations

    def generate_exercise_session(
        self, request: schemas.ExerciseRequest
    ) -> schemas.ExerciseResponse:
        """
        Primary generation pipeline:
        Loads entities eagerly, rebalances quotas, and synthesizes items with format degradation.
        """
        lemma_ids = [int(lid) for lid in (request.exercise_context.lem_ids or [])]
        session_formats = set(request.exercise_context.ex_formats)

        # 1. Eagerly load all staged lemmas with required relationship nodes
        stmt = (
            select(Lemma)
            .where(Lemma.id.in_(lemma_ids))
            .options(
                selectinload(Lemma.definitions),
                selectinload(Lemma.pronunciations),
                selectinload(Lemma.lemma_word_form).joinedload(
                    models.WordForm.word_form_lexicon
                ),
                selectinload(Lemma.lemma_word_form).joinedload(
                    models.WordForm.word_form_gram
                ),
                selectinload(Lemma.related_to).joinedload(
                    models.LemmaRelation.target_lemma
                ),
            )
        )
        staged_lemmas = list(self.db.scalars(stmt).unique().all())
        if not staged_lemmas:
            return schemas.ExerciseResponse(
                exercise_id=0, num_questions=0, response_data=[]
            )

        # 2. Evaluate strategy capacity across the staged pool
        capacity_map = self.evaluate_strategy_capacity(staged_lemmas)

        # 3. Rebalance requested quotas against empirical capacities
        target_total = sum(request.type_counts.values())
        balanced_quotas = self.rebalance_quotas(
            request.type_counts, capacity_map, target_total
        )

        # 4. Generate items with format fallbacks
        generated_items = []
        item_counter = 1

        for strategy_key, count in balanced_quotas.items():
            candidate_lemmas = list(capacity_map[strategy_key])
            selected_for_strat = candidate_lemmas[:count]

            for lemma in selected_for_strat:
                # 1. Extract raw prompt and key
                prompt, key = self._extract_prompt_and_key(lemma, strategy_key)

                # 2. Harvest distractors from DB
                distractors = self._harvest_distractors(
                    lemma, strategy_key, staged_lemmas
                )

                # 3. Build the raw blueprint
                blueprint = schemas.ItemBlueprint(
                    prompt=prompt, keys=key, distractors=distractors, lem_id=lemma.id
                )

                # 4. Pass the blueprint to the Factory
                formatted_item = ItemFormatFactory.create_formatted_item(
                    strategy=strategy_key,
                    blueprint=blueprint,
                    allowed_session_formats=request.exercise_context.ex_formats,
                    item_id=item_counter,
                )

                if formatted_item:
                    generated_items.append(formatted_item)
                    item_counter += 1

        return schemas.ExerciseResponse(
            exercise_id=0,
            num_questions=len(generated_items),
            response_data=generated_items,
        )

    def _materialize_item_with_fallback(
        self,
        lemma: Lemma,
        strategy: EnumWordItemType,
        allowed_formats: Set[EnumItemFormat],
        staged_pool: List[Lemma],
        item_id: int,
    ) -> Optional[schemas.ExerciseItems]:
        """
        Synthesizes an item. If distractor generation fails for MCQ,
        it degrades gracefully to an open-response (FITB) or recall (Flashcard) format.
        """
        compatible_formats = schemas.STRATEGY_FORMAT_COMPATIBILITY.get(
            strategy, frozenset()
        )
        viable_formats = list(compatible_formats.intersection(allowed_formats))
        if not viable_formats:
            return None

        # Build raw blueprint components (prompt, key, distractor pool)
        prompt, key = self._extract_prompt_and_key(lemma, strategy)
        if not prompt or not key:
            return None

        # Format Materialization Priority: Preferred format -> Degraded fallback
        # Prioritize MCQ if requested, but fall back if distractors cannot be gathered
        if EnumItemFormat.MCQ in viable_formats:
            distractors = self._harvest_distractors(
                target_lemma=lemma,
                strategy=strategy,
                staged_pool=staged_pool,
                required_count=3,
            )
            if len(distractors) >= 2:  # Accept minimum 2 distractors (3 choices total)
                options = [key] + distractors
                random.shuffle(options)
                return schemas.MultipleChoiceResponse(
                    item_id=item_id,
                    prompt=prompt,
                    options=options,
                )
            # MCQ failed due to distractor shortage: fall through to alternate viable format
            viable_formats.remove(EnumItemFormat.MCQ)

        if EnumItemFormat.FITB in viable_formats:
            return schemas.FillInTheBlankResponse(
                item_id=item_id,
                prompt=prompt,
                parts=[f"{prompt}: ", ""],
            )

        if EnumItemFormat.FLASHCARD in viable_formats:
            return schemas.FlashcardResponse(
                item_id=item_id,
                prompt=prompt,
                back_text=key,
            )

        return None

    def _extract_prompt_and_key(
        self, lemma: Lemma, strategy: EnumWordItemType
    ) -> Tuple[Optional[str], Optional[str]]:
        """Extracts the pedagogical prompt and target answer key for a strategy."""
        lem_display = lemma.lem_canon or lemma.lem_text

        if strategy == EnumWordItemType.LEM_TO_DEF:
            if not lemma.definitions:
                return None, None
            return lem_display, lemma.definitions[0].def_text

        if strategy == EnumWordItemType.DEF_TO_LEM:
            if not lemma.definitions:
                return None, None
            return lemma.definitions[0].def_text, lem_display

        if strategy == EnumWordItemType.LEM_TO_POS:
            return lem_display, lemma.pos.value

        if strategy == EnumWordItemType.POS_TO_LEM:
            return f"Which word is a {lemma.pos.value}?", lem_display

        if strategy == EnumWordItemType.NOUN_TO_GEND:
            return lem_display, lemma.noun_gender.value if lemma.noun_gender else None

        if strategy == EnumWordItemType.VERB_TO_ASPT:
            return lem_display, lemma.verb_aspect.value if lemma.verb_aspect else None

        if strategy == EnumWordItemType.VERB_TO_ASPT_PAIR:
            for rel in lemma.related_to:
                if rel.rel_type in (
                    EnumRelLemType.PERFECTIVE_PAIR_OF,
                    EnumRelLemType.IMPERFECTIVE_PAIR_OF,
                ):
                    target = rel.target_lemma
                    target_display = target.lem_canon or target.lem_text
                    return f"{lem_display} (aspectual partner)", target_display

        return None, None

    def _harvest_distractors(
        self,
        target_lemma: Lemma,
        strategy: EnumWordItemType,
        staged_pool: List[Lemma],
        required_count: int = 3,
    ) -> List[str]:
        """
        Samples plausible distractors. First inspects the staged pool;
        if the staged pool is exhausted, queries the global database for matching POS peers.
        """
        distractors: List[str] = []
        target_display = target_lemma.lem_canon or target_lemma.lem_text

        # 1. First Pass: Sample from local staged lemmas of identical POS
        peer_lemmas = [
            l
            for l in staged_pool
            if l.id != target_lemma.id and l.pos == target_lemma.pos
        ]
        random.shuffle(peer_lemmas)

        for peer in peer_lemmas:
            _, peer_val = self._extract_prompt_and_key(peer, strategy)
            if peer_val and peer_val != target_display and peer_val not in distractors:
                distractors.append(peer_val)
                if len(distractors) >= required_count:
                    return distractors

        # 2. Second Pass: Global Database Expansion if staged pool is depleted
        if len(distractors) < required_count:
            needed = required_count - len(distractors)
            global_stmt = (
                select(Lemma)
                .where(
                    Lemma.pos == target_lemma.pos,
                    Lemma.id != target_lemma.id,
                )
                .options(selectinload(Lemma.definitions))
                .limit(needed * 4)  # Fetch extra to accommodate definition validation
            )
            global_peers = list(self.db.scalars(global_stmt).all())
            random.shuffle(global_peers)

            for g_peer in global_peers:
                _, g_val = self._extract_prompt_and_key(g_peer, strategy)
                if g_val and g_val != target_display and g_val not in distractors:
                    distractors.append(g_val)
                    if len(distractors) >= required_count:
                        break

        return distractors
