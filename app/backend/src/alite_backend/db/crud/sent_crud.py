import logging
from sqlalchemy import select
from sqlalchemy.orm import Session
from alite_backend.db.models import Document, Sentence, SentenceToken
from alite_backend.db.schemas import (
    DocumentCreate,
    DocumentUpdate,
    DocumentReturn,
    SentenceCreate,
    SentenceUpdate,
    SentenceReturn,
    SentenceTokenCreate,
    SentenceTokenUpdate,
    SentenceTokenReturn,
)
from alite_backend.db.crud.crud_base import CRUDBase

logger = logging.getLogger(__name__)

#
# DOCUMENTS
#


class CRUDDocument(CRUDBase[Document, DocumentCreate, DocumentUpdate]):
    pass


crud_document = CRUDDocument(Document)


#
# SENTENCES
#


class CRUDSentence(CRUDBase[Sentence, SentenceCreate, SentenceUpdate]):
    pass


crud_sentence = CRUDSentence(Sentence)


#
# SENTENCE TOKENS
#


class CRUDSentenceToken(
    CRUDBase[SentenceToken, SentenceTokenCreate, SentenceTokenUpdate]
):
    pass


crud_sentence_token = CRUDSentenceToken(SentenceToken)
