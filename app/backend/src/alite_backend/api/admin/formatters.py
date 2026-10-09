"""
app/backend/admin/formatters.py

Reusable column formatters for SQLAdmin in ALITE.
Handles foreign keys, relationships, and sequential token streams.
"""

from typing import Any, Callable, Optional

from markupsafe import Markup, escape


def format_empty() -> Markup:
    """Standard fallback for null or missing values."""
    return Markup('<span class="text-muted">—</span>')


# ============================================================================
# 1. Foreign Key & Relationship Link Formatter
# ============================================================================


def format_document_link(model: Any, attribute: str) -> Markup:
    """
    Formats doc_id or document relationship on Sentence/Document views.
    Resolves Document.title for the badge label.
    """
    # Handle whether attribute is 'doc_id' (int) or 'document' (relationship)
    doc = getattr(model, "document", None) if hasattr(model, "document") else model
    doc_id = getattr(model, "doc_id", None) or getattr(doc, "id", None)

    if not doc_id:
        return format_empty()

    # Prefer Document.title, fallback to #doc-{id}
    label = getattr(doc, "title", None) if doc else None
    display_text = str(label) if label else f"#doc-{doc_id}"

    url = f"/admin/document/details/{escape(str(doc_id))}"
    return Markup(
        f'<a href="{url}" class="badge bg-warning-subtle text-warning-emphasis border border-warning-subtle text-decoration-none">'
        f'<i class="fa-solid fa-file-lines me-1"></i>{escape(display_text)}'
        f"</a>"
    )


def format_lemma_link(model: Any, attribute: str) -> Markup:
    """
    Formats lem_id or lemma relationship on SentenceToken/LemmaInItem views.
    Resolves Lemma.lem_canon or Lemma.lem_text for the badge label.
    """
    lemma = getattr(model, "lemma", None) if hasattr(model, "lemma") else model
    lem_id = getattr(model, "lem_id", None) or getattr(lemma, "id", None)

    if not lem_id:
        return format_empty()

    # Prefer lem_canon, then lem_text, fallback to #lem-{id}
    label = None
    if lemma:
        label = getattr(lemma, "lem_canon", None) or getattr(lemma, "lem_text", None)
    display_text = str(label) if label else f"#lem-{lem_id}"

    url = f"/admin/lemma/details/{escape(str(lem_id))}"
    return Markup(
        f'<a href="{url}" class="badge bg-success-subtle text-success-emphasis border border-success-subtle text-decoration-none">'
        f'<i class="fa-solid fa-book me-1"></i>{escape(display_text)}'
        f"</a>"
    )


def format_lexeme_link(model: Any, attribute: str) -> Markup:
    """
    Formats lex_id or lexeme relationship on SentenceToken.
    Resolves Lexeme.lex_text for the badge label.
    """
    lexeme = getattr(model, "lexeme", None) if hasattr(model, "lexeme") else model
    lex_id = getattr(model, "lex_id", None) or getattr(lexeme, "id", None)

    if not lex_id:
        return format_empty()

    label = getattr(lexeme, "lex_text", None) if lexeme else None
    display_text = str(label) if label else f"#lex-{lex_id}"

    url = f"/admin/lexeme/details/{escape(str(lex_id))}"
    return Markup(
        f'<a href="{url}" class="badge bg-light text-dark border text-decoration-none">'
        f'<i class="fa-solid fa-font me-1"></i>{escape(display_text)}'
        f"</a>"
    )


def format_word_form_link(model: Any, attribute: str) -> Markup:
    """
    Formats wf_id or word_form relationship on SentenceToken.
    Traverses to word_form_lexicon.lex_text or word_form_lemma.lem_text.
    """
    wf = getattr(model, "word_form", None) if hasattr(model, "word_form") else model
    wf_id = getattr(model, "wf_id", None) or getattr(wf, "id", None)

    if not wf_id:
        return format_empty()

    # Try resolving surface wordform and base lemma: "домами (дом)"
    display_text = f"#wf-{wf_id}"
    if wf:
        surface = getattr(getattr(wf, "word_form_lexicon", None), "lex_text", None)
        headword = getattr(getattr(wf, "word_form_lemma", None), "lem_text", None)
        if surface and headword:
            display_text = f"{surface} ({headword})"
        elif surface:
            display_text = surface

    url = f"/admin/word-form/details/{escape(str(wf_id))}"
    return Markup(
        f'<a href="{url}" class="badge bg-info-subtle text-info-emphasis border border-info-subtle text-decoration-none">'
        f'<i class="fa-solid fa-cube me-1"></i>{escape(display_text)}'
        f"</a>"
    )


# ============================================================================
# 2. Sentence.tokens Stream Formatter (Fixes the character-split bug)
# ============================================================================


def format_sentence_tokens(model: Any, attribute: str) -> Markup:
    """
    Formats Sentence.tokens as sequential, parenthesized, clickable links:
    (Подбивая) (в) (конце) (дня) ...

    Directly returns a Markup string. DO NOT wrap this in an external loop!
    """
    tokens = getattr(model, attribute, None) or []
    if not tokens:
        return format_empty()
    # print(f"Tokens: {tokens}")
    # Sort tokens in sequential order by token_idx
    sorted_tokens = sorted(tokens, key=lambda t: getattr(t, "token_idx", 0))

    # Cap visible tokens on table view to prevent layout blowouts
    max_visible = 15
    visible = sorted_tokens[:max_visible]

    badges: list[str] = []
    for tok in visible:
        tok_id = str(tok.id)
        word = str(tok.lex_raw or f"#{tok.token_idx}")
        url = f"/admin/sentence-token/details/{tok_id}"

        # Clean parenthesized link per token
        badges.append(
            f'<a href="{url}" class="badge bg-light text-dark border text-decoration-none me-1 mb-1 font-monospace">'
            f"({word})"
            f"</a>"
        )

    if len(sorted_tokens) > max_visible:
        overflow = len(sorted_tokens) - max_visible
        badges.append(
            f'<span class="badge bg-secondary-subtle text-secondary border mb-1" '
            f'title="{len(sorted_tokens)} total tokens">+{overflow} more</span>'
        )

    return Markup(" ".join(badges))


"""
app/backend/admin/formatters.py

Plain text label formatters for SQLAdmin fields.
Avoids manual HTML string construction to prevent Jinja escaping collisions.
"""


def format_document_title(model: Any, attribute: str) -> str:
    """Extracts Document title or falls back to ID string."""
    doc = getattr(model, "document", None)
    doc_id = getattr(model, "doc_id", None)
    if doc and hasattr(doc, "title") and doc.title:
        return str(doc.title)
    return f"#doc-{doc_id}" if doc_id else "—"


def format_lemma_label(model: Any, attribute: str) -> str:
    """Extracts Lemma canonical text or headword."""
    lemma = getattr(model, "lemma", None)
    lem_id = getattr(model, "lem_id", None)
    if lemma:
        return str(
            getattr(lemma, "lem_canon", None)
            or getattr(lemma, "lem_text", None)
            or f"#lem-{lem_id}"
        )
    return f"#lem-{lem_id}" if lem_id else "—"


def format_lexeme_label(model: Any, attribute: str) -> str:
    """Extracts Lexeme surface text."""
    lexeme = getattr(model, "lexeme", None)
    lex_id = getattr(model, "lex_id", None)
    if lexeme and hasattr(lexeme, "lex_text"):
        return str(lexeme.lex_text)
    return f"#lex-{lex_id}" if lex_id else "—"


def format_word_form_label(model: Any, attribute: str) -> str:
    """Extracts WordForm surface representation with headword context."""
    wf = getattr(model, "word_form", None)
    wf_id = getattr(model, "wf_id", None)
    if wf:
        surface = getattr(getattr(wf, "word_form_lexicon", None), "lex_text", None)
        headword = getattr(getattr(wf, "word_form_lemma", None), "lem_text", None)
        if surface and headword:
            return f"{surface} ({headword})"
        if surface:
            return surface
    return f"#wf-{wf_id}" if wf_id else "—"


def format_token_text(model: Any, attribute: str) -> str:
    """Extracts raw token surface string for sentence streams."""
    if hasattr(model, "lex_raw") and model.lex_raw:
        return str(model.lex_raw)
    return f"#{getattr(model, 'token_idx', 0)}"
