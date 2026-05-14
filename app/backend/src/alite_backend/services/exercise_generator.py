# app/backend/src/alite_backend/services/exercise_generator.py
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from alite_backend.db import models, schemas
import random

def generate_grammar_exercise(db: Session, request: schemas.ExerciseRequest):
    # --- CREATE KEY BANK ---
    
    # Start the query joining WordForm -> Lemma -> GramProp
    query = (
        db.query(models.WordForm)
        .join(models.Lemma, models.WordForm.lem_id == models.Lemma.id)
        .join(models.GramProp, models.WordForm.gram_id == models.GramProp.id)
        # Join the junction tables to filter by lesson
        .join(models.LemmaInLessonList, models.Lemma.id == models.LemmaInLessonList.lem_id)
        .filter(models.LemmaInLessonList.less_list_id == request.less_list_id)
    )

    # Apply the user's flexible filters (e.g., pos="noun", subst_case="genitive")
    if request.target_props:
        if "pos" in request.target_props:
            query = query.filter(models.Lemma.pos == request.target_props["pos"])
        if "subst_case" in request.target_props:
            query = query.filter(models.GramProp.subst_case == request.target_props["subst_case"])
        # ... map other properties ...

    # Get exactly 10 random correct answers
    targets = query.order_by(func.random()).limit(request.question_count).all()

    if not targets:
        return []

    # --- 2. FETCH DISTRACTORS (Incorrect Answers) ---
    
    # We need distractors for the lemmas we just selected.
    target_lemma_ids = [target.lem_id for target in targets]
    target_form_ids = [target.id for target in targets] # To exclude the correct answers

    # Bulk query all other forms for these specific lemmas
    all_distractors = (
        db.query(models.WordForm)
        .filter(models.WordForm.lem_id.in_(target_lemma_ids))
        .filter(models.WordForm.id.not_in(target_form_ids))
        .all()
    )

    # --- 3. ASSEMBLE THE PAYLOAD ---
    exercise_data = []
    
    for target in targets:
        # Filter the bulk distractors down to just the ones for THIS lemma
        valid_distractors = [d for d in all_distractors if d.lem_id == target.lem_id]
        
        # Randomly select 3 distractors
        selected_distractors = random.sample(
            valid_distractors, 
            min(request.distractor_count, len(valid_distractors))
        )

        exercise_data.append({
            "question_type": "grammar",
            "lemma": target.word_form_lemma.lem_text,
            "target_property": request.target_props,
            "correct_answer": target.word_form_lexicon.lex_text,
            "distractors": [d.word_form_lexicon.lex_text for d in selected_distractors]
        })

    return exercise_data