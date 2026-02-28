"""Tests for Pydantic models."""

import pytest
from uuid import UUID
from autota.models import (
    ProblemSpec,
    ProblemVariant,
    VerificationResult,
    GenerationBatch,
)


def test_problem_spec_creation():
    """Test creating a valid ProblemSpec."""
    spec = ProblemSpec(
        problem_type="kmap_simplification",
        topic="Karnaugh Maps",
        description="Simplify Boolean functions using K-maps",
        num_variants=5,
        parameters={"num_variables": 4},
        answer_format="boolean_expression",
        difficulty="medium",
    )

    assert spec.problem_type == "kmap_simplification"
    assert spec.num_variants == 5
    assert spec.difficulty == "medium"


def test_problem_spec_validation():
    """Test ProblemSpec validation."""
    # num_variants must be positive
    with pytest.raises(Exception):
        ProblemSpec(
            problem_type="test",
            topic="Test",
            description="Test",
            num_variants=0,
            parameters={},
            answer_format="text",
        )


def test_problem_variant_creation():
    """Test creating a ProblemVariant."""
    variant = ProblemVariant(
        problem_text="Simplify the function with minterms [0, 2, 5, 7]",
        parameters={"minterms": [0, 2, 5, 7], "dont_cares": []},
        solution={"expression": "A'C' + BC", "method": "kmap"},
        answer_format="boolean_expression",
    )

    assert isinstance(variant.variant_id, UUID)
    assert variant.problem_text is not None
    assert variant.parameters["minterms"] == [0, 2, 5, 7]


def test_verification_result_creation():
    """Test creating a VerificationResult."""
    from uuid import uuid4

    variant_id = uuid4()
    result = VerificationResult(
        variant_id=variant_id,
        passed=True,
        details={"note": "All tests passed"},
    )

    assert result.variant_id == variant_id
    assert result.passed is True
    assert result.error_message is None


def test_generation_batch_creation():
    """Test creating a GenerationBatch."""
    variants = [
        ProblemVariant(
            problem_text="Problem 1",
            parameters={},
            solution={},
            answer_format="text",
        )
    ]

    batch = GenerationBatch(
        variants=variants,
        num_requested=5,
        num_generated=1,
    )

    assert batch.num_requested == 5
    assert batch.num_generated == 1
    assert len(batch.variants) == 1
