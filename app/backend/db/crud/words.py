from sqlalchemy.orm import Session
import app.backend.db.models as models
import app.backend.db.schemas as schemas

def get_or_create_lemma(db: Session, lemma_data: schemas.LemmasRecord) -> models.Lemma:
    """
    Finds a lemma by its text and POS. If it doesn't exist, it creates it.
    """
    # Try to find the lemma first
    db_lemma = db.query(models.Lemma).filter(
        models.Lemma.lemma_text == lemma_data.lemma_text,
        models.Lemma.part_of_speech == lemma_data.part_of_speech
    ).first()

    if db_lemma:
        return db_lemma

    # If not found, create a new one
    db_lemma = models.Lemma(**lemma_data.dict())
    db.add(db_lemma)
    db.commit()
    db.refresh(db_lemma)
    return db_lemma

def create_lexeme(db: Session, lexeme_data: schemas.LexiconRecord, lemma_id: int) -> models.Lexeme:
    """
    Creates a new lexeme entry and links it to its lemma.
    """
    db_lexeme = models.Lexeme(**lexeme_data.dict(), lemma_id=lemma_id)
    db.add(db_lexeme)
    db.commit()
    db.refresh(db_lexeme)
    return db_lexeme

# creating definitions, gram_props and linking them together in join tables
