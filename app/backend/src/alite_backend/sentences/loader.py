import logging
from sqlalchemy import insert, select
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from alite_backend.db.models import (
    Document,
    Sentence,
    SentenceToken,
    Lemma,
    WordForm,
    Lexeme,
)

logger = logging.getLogger(__name__)


def load_parsed_data(
    session: Session,
    doc_data: Dict[str, Any],
    sentences_data: List[Dict[str, Any]],
    tokens_data: List[Dict[str, Any]],
) -> None:
    """
    Loads parsed SynTagRus data into the database using SQLAlchemy Core.
    Operates within a single transaction managed by the caller.
    """

    # insert document
    doc_stmt = insert(Document).values(**doc_data).returning(Document.id)
    # scalar_one() extracts the exact integer ID from the returned row
    doc_id = session.execute(doc_stmt).scalar_one()

    # map & insert sentences
    for sentence in sentences_data:
        sentence["doc_id"] = doc_id

    # bulk insert sentences and request db id and sentence index
    sent_stmt = insert(Sentence).returning(Sentence.id, Sentence.sent_idx)

    # execute the bulk insert. 'sent_results' is an iterable of Row objects.
    sent_results = session.execute(sent_stmt, sentences_data).all()

    # create sentence id to db id mapping dictionary
    sent_id_map = {row.sent_idx: row.id for row in sent_results}

    # lookup to connect with currently lemma db
    if tokens_data:
        unique_lemmas = {t.get("lem_raw") for t in tokens_data if t.get("lem_raw")}
        unique_lexemes = {t.get("lex_raw") for t in tokens_data if t.get("lex_raw")}

        lemma_map = {}
        lexeme_map = {}
        word_form_map = {}

        if unique_lemmas:
            lem_stmt = select(Lemma.id, Lemma.lem_text).where(
                Lemma.lem_text.in_(unique_lemmas)
            )
            lem_results = session.execute(lem_stmt).all()
            lemma_map = {row.lem_text: row.id for row in lem_results}

        if unique_lexemes:
            wf_stmt = (
                select(
                    WordForm.id.label("wf_id"),
                    Lexeme.id.label("lex_id"),
                    Lexeme.lex_text_clean,
                )
                .select_from(WordForm)
                .join(Lexeme, WordForm.lex_id == Lexeme.id)
                .where(Lexeme.lex_text_clean.in_(unique_lexemes))
            )
            wf_results = session.execute(wf_stmt).all()

            # create maps
            lexeme_map = {row.lex_text_clean: row.lex_id for row in wf_results}
            word_form_map = {row.lex_text_clean: row.wf_id for row in wf_results}

        # map & insert tokens
        for token in tokens_data:
            # .pop() removes 'sent_idx' while simultaneously returning its value
            s_idx = token.pop("sent_idx", None)

            # inject the true Foreign Key
            if s_idx is not None:
                token["sent_id"] = sent_id_map.get(s_idx)

            raw_lem = token.get("lem_raw")
            raw_lex = token.get("lex_raw")

            # FIX: Correctly map raw_lex to the lexeme and word form dictionaries
            token["lem_id"] = lemma_map.get(raw_lem)
            token["lex_id"] = lexeme_map.get(raw_lex)
            token["wf_id"] = word_form_map.get(raw_lex)

    # bulk insert all tokens for the entire document in one massive query
    if tokens_data:
        session.execute(insert(SentenceToken), tokens_data)

    # the orchestrator commits
