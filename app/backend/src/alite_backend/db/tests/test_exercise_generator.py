#
from typing import Literal, Any
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select, func
from alite_backend.db.tests.factories import ExerciseRequestFactory
from alite_backend.db import models
from alite_backend.db.schemas import (
    EnumWordItemType,
    EnumItemFormat,
    EnumGramExFocus,
    EnumSubstGramExFocus,
    EnumVerbGramExFocus,
    EnumPartGramExFocus,
)
from alite_backend.db.tests.factories import UserFactory
from sqlalchemy.orm.session import Session

CONFIG_MATRIX = [
    # Test 1: make paradigm drills
    {
        "exercise_context__ex_formats": [EnumItemFormat.MCQ],
        "type_counts": {
            EnumWordItemType.NOUN_GRAM_TO_FORM: 3,
            EnumWordItemType.NOUN_FORM_TO_GRAM: 3,
            EnumWordItemType.ADJV_GRAM_TO_FORM: 3,
            EnumWordItemType.ADJV_FORM_TO_GRAM: 3,
        },
        "grammar_focus": {
            "strategies": {
                "participles": [],
                "substantives": [
                    EnumSubstGramExFocus.SUBST_CASE,
                    EnumSubstGramExFocus.GRAM_NUM,
                ],
                "verbs": [],
            },
            "allow_odd_one_out": True,
        },
    },
    # Test 2: make single-query drills
    {
        "exercise_context__ex_formats": [EnumItemFormat.MCQ],
        "type_counts": {
            EnumWordItemType.VERB_TO_ASPT: 5,
            EnumWordItemType.ASPT_TO_VERB: 5,
            EnumWordItemType.VERB_TO_TYPE: 5,
            EnumWordItemType.TYPE_TO_VERB: 5,
            EnumWordItemType.NOUN_TO_ANIM: 5,
            EnumWordItemType.ANIM_TO_NOUN: 5,
            EnumWordItemType.NOUN_TO_GEND: 5,
            EnumWordItemType.GEND_TO_NOUN: 5,
        },
        "grammar_focus": {
            "strategies": {
                "participles": [],
                "substantives": [],
                "verbs": [],
            },
            "allow_odd_one_out": True,
        },
    },
    # Test 2: Highly constrained distractors
    # {
    #     "exercise_context__max_distractors": 1,
    #     "exercise_context__num_items": 5,
    # },
    # Test 3: Mixed strategy distribution
    # {
    #     "type_counts": {
    #         EnumWordItemType.NOUN_FORM_TO_GRAM: 2,
    #         # EnumWordItemType.LEM_TO_DEF: 2
    #     },
    #     "exercise_context__num_items": 4,
    # },
]


@pytest.mark.parametrize("factory_overrides", CONFIG_MATRIX)
def test_exercise_generation_configurations(
    api_client: TestClient, db_session: Session, factory_overrides: dict[str, Any]
):
    """
    Blasts the /generate endpoint with various valid configurations to ensure
    the orchestrator and strategies don't crash under different rulesets.
    """
    # ARRANGE
    # unpack the specific matrix overrides into our payload builder
    payload = ExerciseRequestFactory.build_payload(**factory_overrides)

    # from alite_backend.main import app
    # print("\nREGISTERED ROUTES:")
    # for route in app.routes:
    #     print(getattr(route, "path", "unknown"))

    # ACT
    response = api_client.post("/api/v1/exercises/generate", json=payload)

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    # ensure the requested item count exactly matches the output length
    expected_count = sum(payload["type_counts"].values())
    # assert data["total_questions"] == expected_count
    assert len(data["response_data"]) == expected_count
    # TODO assert type counts results


def get_valid_id_range(db_session, model):
    """
    Returns the absolute (min_id, max_id) range for a given database table.
    """
    result = db_session.execute(
        select(func.min(model.id), func.max(model.id))
    ).fetchone()
    return result if result else (None, None)


def test_exercise_generation_respects_valid_id_ranges(
    api_client: TestClient, db_session: Session
):
    """
    Justification: We extract a target ID straight from our live clone to verify
    the orchestrator maps it to valid structural parameters.
    """
    # ARRANGE: Dynamic discovery of current database bounds.
    min_lem_id, max_lem_id = get_valid_id_range(db_session, models.Lemma)

    # Ensure database clone actually contains target structural data
    assert min_lem_id is not None

    # Build a strictly explicit, deterministic payload structure
    request_payload = {
        "exercise_context": {
            "less_list_ids": None,
            "mod_ids": None,
            "lem_ids": [min_lem_id],  # Pass a known-valid lower boundary id
            "ex_formats": [EnumItemFormat.MCQ],
            "num_items": 3,
            "max_keys": 1,
            "max_distractors": 3,
        },
        "type_counts": {
            EnumWordItemType.NOUN_FORM_TO_GRAM: 3,
            # EnumWordItemType.LEM_TO_DEF.value: 2,
        },
    }

    # ACT: Prompt your orchestrator algorithm via HTTP POST
    response = api_client.post("/api/exercises/generate", json=request_payload)

    # ASSERT: Step-by-Step Contract Verification
    assert response.status_code == 200
    data = response.json()

    # 2. Cross-reference returned exercise item data against database ranges
    for item in data["items"]:
        # Verify item primary key values are logically constrained to reality
        assert (
            min_lem_id <= item["lemma_id"] <= max_lem_id
        ), f"Orchestrator selected a lemma out of bounds: {item['lemma_id']}"


@pytest.mark.parametrize(
    "invalid_modifier, expected_error_snippet",
    [
        ({"lem_ids": [-9999]}, "out of range"),  # Impossible ID lower constraint
        ({"lem_ids": [99999999]}, "not found"),  # Non-existent ID upper constraint
        ({"num_items": -5}, "greater than 0"),  # Broken business rule validation
        (
            {"max_distractors": 10},
            "too many distractors",
        ),  # Educational design policy constraint
    ],
)
def test_exercise_generation_gracefully_rejects_boundaries(
    api_client: TestClient,
    db_session: Session,
    invalid_modifier: dict[str, list[int]] | dict[str, int],
    expected_error_snippet: (
        Literal["out of range"]
        | Literal["not found"]
        | Literal["greater than 0"]
        | Literal["too many distractors"]
    ),
):
    """
    Verifies that invalid bounds don't cause 500 crashes, but are caught by ALITE's
    safety protocols.
    """
    # Base configuration template payload
    base_payload = {
        "exercise_context": {
            "less_list_ids": None,
            "mod_ids": None,
            "lem_ids": None,
            "ex_formats": [EnumItemFormat.MCQ.value],
            "num_items": 10,
            "max_keys": 1,
            "max_distractors": 3,
        },
        "type_counts": {
            EnumWordItemType.NOUN_FORM_TO_GRAM: 3,
            EnumWordItemType.LEM_TO_DEF.value: 2,
        },
    }

    # Dynamically inject the specific matrix condition mutation
    # For sub-dictionaries, we dynamically update the underlying inner context mapping block
    for key, value in invalid_modifier.items():
        base_payload["exercise_context"][key] = value

    # ACT
    response = api_client.post("/api/exercises/generate", json=base_payload)

    # ASSERT
    assert response.status_code in (400, 422, 404)

    error_detail = str(response.json())
    assert expected_error_snippet in error_detail.lower()
