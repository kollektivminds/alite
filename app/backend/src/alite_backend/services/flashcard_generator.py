# app/backend/src/alite_backend/services/flashcard_generator.py
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from alite_backend.db import models, schemas
import random
from sqlalchemy import text

def make_flashcards(db, context, num_cards):
    card_dict = {}
    
    return card_dict