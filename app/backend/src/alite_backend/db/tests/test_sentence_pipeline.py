# app/backend/tests/sentences/test_pipeline.py
import pytest
import xml.etree.ElementTree as ET
import datetime
from unittest.mock import MagicMock

from alite_backend.sentences.parser import parse_tgt_file
from alite_backend.sentences.write_sentences import run_syntagrus_pipeline

# --- FIXTURES ---


@pytest.fixture
def sample_tgt_xml(tmp_path):
    """
    Creates a temporary SynTagRus-formatted XML file for isolated testing.
    tmp_path is a built-in pytest fixture that automatically cleans up after tests.
    """
    xml_content = """<?xml version="1.0" encoding="utf-8" standalone="no"?>
    <text ver="1.1">
        <inf>
            <author>Л. Серова</author>
            <date>22.12.2003</date>
            <source>Наука и жизнь, № 2, 2003</source>
            <title>А он, мятежный, просит бури...</title>
        </inf>
        <body>
            <S ID="1">
                "<W DOM="_root" FEAT="CONJ" ID="1" KSNAME="А1" LEMMA="А">А</W> 
                <W DOM="4" FEAT="S ЕД МУЖ ИМ ОД" ID="2" KSNAME="ОН" LEMMA="ОН" LINK="предик">ОН</W>"
            </S>
        </body>
    </text>
    """
    # Create a dummy file in the temp directory
    file_path = tmp_path / "test_corpus.tgt"
    file_path.write_text(xml_content, encoding="utf-8")
    return file_path


# --- 1. PARSER TESTS (Data Integrity) ---


def test_parse_tgt_file_extracts_correctly(sample_tgt_xml):
    """
    Validates that the XML parsing correctly maps nodes to Python dictionaries,
    bypassing the need for Pandas while preserving SynTagRus relationships.
    """
    doc_data, sentences, tokens = parse_tgt_file(str(sample_tgt_xml))

    # Assert Document Metadata
    assert doc_data["title"] == "А он, мятежный, просит бури..."
    assert doc_data["author"] == "Л. Серова"
    assert doc_data["date"].year == 2003  # Ensures our date split logic works

    # Assert Sentences
    assert len(sentences) == 1
    assert sentences[0]["sentence_index"] == 1
    # Ensures itertext() ignores XML tags and grabs raw characters
    assert "А ОН" in sentences[0]["raw_text"]

    # Assert Tokens
    assert len(tokens) == 2

    token_1 = tokens[0]
    assert token_1["lemma_raw"] == "А"
    assert token_1["head_index"] is None  # "_root" should be parsed as None

    token_2 = tokens[1]
    assert token_2["token_index"] == 2
    assert token_2["head_index"] == 4  # DOM="4" should be cast to integer
    assert token_2["dep_rel"] == "предик"


# --- 2. ORCHESTRATOR TESTS (Transactional Integrity) ---


def test_pipeline_commits_on_success(mocker, tmp_path, sample_tgt_xml):
    """
    Validates that a successful file process results in a session.commit().
    We mock the DB session and the load function to prevent actual DB IO.
    """
    # 1. Setup Mocks
    # Mock the SQLAlchemy session manager
    mock_session = MagicMock()
    mock_session_local = mocker.patch(
        "alite_backend.sentences.write_sentences.SessionLocal",
        return_value=MagicMock(__enter__=MagicMock(return_value=mock_session)),
    )
    # Mock the load function so we don't try to insert into a non-existent DB
    mock_load = mocker.patch("alite_backend.sentences.write_sentences.load_parsed_data")

    # 2. Execute Orchestrator
    # Pass the tmp_path directory which contains our sample_tgt_xml fixture
    run_syntagrus_pipeline(str(tmp_path))

    # 3. Assertions
    # Verify the load function was called once for our single file
    assert mock_load.call_count == 1
    # Verify the transaction was committed
    mock_session.commit.assert_called_once()
    # Verify rollback was NEVER called
    mock_session.rollback.assert_not_called()


def test_pipeline_rolls_back_on_failure(mocker, tmp_path, sample_tgt_xml):
    """
    Validates the Atomic Transaction constraint. If load_parsed_data fails
    (e.g., due to a schema violation), the session must roll back.
    """
    mock_session = MagicMock()
    mocker.patch(
        "alite_backend.sentences.write_sentences.SessionLocal",
        return_value=MagicMock(__enter__=MagicMock(return_value=mock_session)),
    )

    # Force the load function to throw an exception, simulating a DB error
    mock_load = mocker.patch(
        "alite_backend.sentences.write_sentences.load_parsed_data",
        side_effect=Exception("Simulated Database Error"),
    )

    # 2. Execute Orchestrator
    run_syntagrus_pipeline(str(tmp_path))

    # 3. Assertions
    mock_load.assert_called_once()

    # Verify commit was skipped
    mock_session.commit.assert_not_called()
    # Verify rollback was called to preserve DB integrity
    mock_session.rollback.assert_called_once()
