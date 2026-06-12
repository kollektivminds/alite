# app/backend/src/alite_backend/services/items/base.py
from abc import ABC, abstractmethod
import logging
import re
import json
import random
from collections import defaultdict
from sqlalchemy import select, func
from sqlalchemy.orm import Session, declarative_base
import logging
from typing import List, Any, Dict, Tuple, Optional
from enum import Enum
from alite_backend.db import schemas, models

logger = logging.getLogger(__name__)


class BaseExerciseStrategy(ABC):
    """Base class for creating exercises"""

    def __init__(self, db_session: Session, request_context: schemas.ExerciseContext):
        self.db = db_session
        # self.type_counts = request.type_counts
        self.context_dict = request_context.model_dump()
        self.less_list_ids = self.context_dict.get("less_list_ids", [])
        self.mod_ids = self.context_dict.get("mod_ids", [])
        self.lem_ids = self.context_dict.get("lem_ids", [])
        self.formats = self.context_dict.get("ex_formats", [])
        # self.num_items = self.context_dict.get("num_items", 10)
        self.max_keys = self.context_dict.get("max_keys", 1)
        self.max_distractors = self.context_dict.get("max_distractors", 3)

    # --- HELPER METHODS ---

    def get_scoped_stmt(self):

        stmt = select(models.Lemma)

        if self.less_list_ids:
            stmt = stmt.join(models.LemmaInLessonList).where(
                models.LemmaInLessonList.less_list_id.in_(self.less_list_ids)
            )

        if self.mod_ids:
            stmt = (
                stmt.join(models.LemmaInLessonList)
                .join(
                    models.LessonListInModule,
                    models.LessonListInModule.less_list_id
                    == models.LemmaInLessonList.less_list_id,
                )
                .where(models.LessonListInModule.mod_id.in_(self.mod_ids))
            )

        if self.lem_ids:
            stmt = stmt.where(models.Lemma.id.in_(self.lem_ids))

        return stmt

    def get_enum_distractors(self, correct_enum: Enum, num_distractors: int):
        """To get distractors with an enum class"""
        all_options = [
            e.value for e in correct_enum.__class__ if e != correct_enum.value
        ]
        return random.sample(all_options, min(num_distractors, len(all_options)))

    def _fetch_grouped_paradigms(
        self, 
        pos_target: models.EnumPartOfSpeech, 
        num_lemmas: int, 
        *gram_filters
    ) -> Dict[int, List[Tuple]]:
        """
        UNIVERSAL HELPER: Fetches fully joined morphological paradigms for a set of random lemmas.
        Returns a dictionary grouped by lemma.id.
        """
        # 1. SUBQUERY: Get exactly `num_lemmas` distinct base words
        lemma_stmt = (
            self.get_scoped_stmt()
            .with_only_columns(models.Lemma.id)
            .where(models.Lemma.pos == pos_target)
            .order_by(func.random())
            .limit(num_lemmas)
        )
        
        # 2. MAIN QUERY: The identical relational pathway
        stmt = (
            select(models.Lemma, models.WordForm, models.Lexeme, models.GramProp)
            .join(models.WordForm, models.WordForm.lem_id == models.Lemma.id)
            .join(models.Lexeme, models.WordForm.lex_id == models.Lexeme.id)
            .join(models.GramProp, models.WordForm.gram_id == models.GramProp.id)
            .where(models.Lemma.id.in_(lemma_stmt.scalar_subquery()))
        )

        # Apply any specific grammatical filters passed by the child strategy
        if gram_filters:
            stmt = stmt.where(*gram_filters)

        results = self.db.execute(stmt).all()

        # 3. PYTHON GROUPING: Organize by Lemma ID for easy distractor picking
        grouped_results = defaultdict(list)
        for lemma, word_form, lexeme, gram_prop in results:
            grouped_results[lemma.id].append((lemma, word_form, lexeme, gram_prop))

        return grouped_results
    
    def _get_trait_mapping(self, focus: str) -> Tuple[str, List[str]]:
        """
        UNIVERSAL MAPPING ENGINE: Translates an API focus selection into structural database column sets.
        Returns: (target_column_name, [list_of_static_column_names])
        """
        # Group definitions by major structural domains
        substantive_cols: List[str] = ["subst_case", "gram_num", "gram_gender"]
        verb_cols: List[str] = ["gram_tense", "conj_person", "gram_num", "verb_mood", "gram_gender"]
        participle_cols: List[str] = ["gram_tense", "part_type", "part_voice"]
        
        strat_id = r"(subst_)(.*)$"
        groups = re.findall(strat_id, focus)
        type_cols = groups[0][0]
        focus_gram = groups[0][1]
        
        
        
        # 1. SUBSTANTIVES' FOCI
        if type_cols == "subst_":
            return focus, [c for c in substantive_cols if focus_gram not in c]
        # 2. VERBS' FOCI
        elif type_cols == "verb_":
            return focus, [c for c in verb_cols if focus_gram not in c]
        # 3. PARTICIPLES' FOCI
        elif type_cols == "part_":
            return focus, [c for c in participle_cols if focus_gram not in c]
        # 4. FALLBACK / MIXED GENERAL STUDY ("ALL")
        # Returning "all" signals the child generator loop to bypass variable isolation
        return "all", []
    
    # --- ABSTRACT METHOD ---

    @abstractmethod
    def generate_item_blueprints(
        self, 
        num_items: int, 
        max_keys: int, 
        max_distractors: int,
        config: schemas.StrategyConfigs | None = None
    ) -> List[schemas.ItemBlueprint]:
        """generate_item_blueprints _summary_

        Args:
            limit (int): _description_
            max_distractors (int): _description_

        Returns:
            List[schemas.ItemBlueprint]: _description_
        """
        pass
