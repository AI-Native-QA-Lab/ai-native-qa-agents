from __future__ import annotations

from typing import Any

import pytest


def test_model_response_retains_explicit_fallback_metadata() -> None:
    from qa_agent.model_runtime import ModelFallbackMetadata, ModelResponse

    response = ModelResponse(
        "injected",
        "test-model",
        structured_output={"links": []},
        fallback=ModelFallbackMetadata(True, "primary", "secondary", "primary unavailable"),
    )

    assert response.fallback.fallback_used is True
    assert response.fallback.selected_provider == "secondary"


@pytest.mark.parametrize(
    "payload",
    [
        {"links": [{"mutant_id": "M-1", "intent_id": "UNKNOWN", "rationale": "reason"}]},
        {"links": [{"mutant_id": "M-1", "rationale": ""}]},
        {
            "links": [
                {"mutant_id": "M-1", "rationale": "first"},
                {"mutant_id": "M-1", "rationale": "duplicate"},
            ]
        },
        {"links": [{"mutant_id": "M-1", "rationale": "reason", "unexpected": "value"}]},
    ],
)
def test_invalid_model_mapping_is_not_accepted(payload: dict[str, Any]) -> None:
    from qa_agent.effectiveness_service import validate_model_mapping

    result = validate_model_mapping(payload, {"mutant_ids": {"M-1"}, "intent_ids": {"TI-1"}})

    assert result == []


def test_valid_model_mapping_is_normalized_to_fixed_schema() -> None:
    from qa_agent.effectiveness_service import validate_model_mapping

    result = validate_model_mapping(
        {
            "links": [
                {
                    "mutant_id": "M-1",
                    "requirement_id": "REQ-1",
                    "intent_id": "TI-1",
                    "scenario_id": "TS-1",
                    "oracle": "checkout total is correct",
                    "rationale": "The selected test asserts the business behavior.",
                }
            ]
        },
        {
            "mutant_ids": {"M-1"},
            "requirement_ids": {"REQ-1"},
            "intent_ids": {"TI-1"},
            "scenario_ids": {"TS-1"},
        },
    )

    assert result == [
        {
            "mutant_id": "M-1",
            "requirement_id": "REQ-1",
            "intent_id": "TI-1",
            "scenario_id": "TS-1",
            "oracle": "checkout total is correct",
            "rationale": "The selected test asserts the business behavior.",
        }
    ]


def test_model_response_positional_call_sites_remain_compatible() -> None:
    from qa_agent.model_runtime import ModelResponse

    response = ModelResponse("provider", "model", "content", {"links": []})

    assert response.provider == "provider"
    assert response.structured_output == {"links": []}
    assert response.fallback.fallback_used is False
