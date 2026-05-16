from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from alite_backend.services import exercise_generator, flashcard_generator
from alite_backend.db import models, schemas
from alite_backend.api import deps

router = APIRouter()

@router.post("/evaluate-answer", response_model=schemas.AnswerResult)
def evaluate_student_answer(
    submission: schemas.AnswerSubmission,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    # fetch the real correct answer from the database securely
    actual_correct_answer = fetch_correct_answer_from_db(db, submission.question_id)
    
    # compare
    is_correct = (submission.selected_option == actual_correct_answer)
    
    # log it in your existing StudentResponse table for analytics!
    response_record = models.StudentResponse(
        session_id=submission.session_id,
        item_id=submission.question_id,
        student_answer=submission.selected_option,
        is_correct=is_correct,
        response_time_ms=submission.response_time_ms
    )
    db.add(response_record)
    db.commit()

    # return the result to the UI
    return schemas.AnswerResult(
        is_correct=is_correct,
        correct_answer=actual_correct_answer
    )

@router.post("/generate-exercise")
def create_custom_exercise(
    request: schemas.ExerciseRequest, 
    db: Session = Depends(deps.get_db)
):
    if request.exercise_type == "grammar_forms":
        return exercise_generator.generate_grammar_exercise(db, request)
        
    # elif request.exercise_type == "definitions":
    #     return exercise_generator.generate_definition_exercise(db, request)
        
    else:
        raise HTTPException(status_code=400, detail="Unknown exercise type")