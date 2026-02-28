"""Integration tests for the full pipeline."""

import json
from pathlib import Path
from uuid import uuid4
from autota.models import ProblemVariant
from autota.verify.registry import get_verifier


def test_full_verification_pipeline(tmp_path):
    """Test that we can verify a variant from JSON."""
    # Create a test variant
    variant = ProblemVariant(
        variant_id=uuid4(),
        problem_text="Simplify F(A,B) where minterms are [1,3]",
        parameters={
            "minterms": [1, 3],
            "dont_cares": [],
            "variables": ["A", "B"],
        },
        solution={"expression": "B", "method": "kmap"},
        answer_format="boolean_expression",
    )

    # Write to file
    variant_file = tmp_path / "test_variant.json"
    with open(variant_file, "w") as f:
        json.dump(variant.model_dump(), f, default=str)

    # Read back from file
    with open(variant_file) as f:
        variant_dict = json.load(f)

    loaded_variant = ProblemVariant(**variant_dict)

    # Verify
    verifier = get_verifier("kmap_simplification")
    result = verifier.verify(loaded_variant)

    assert result.passed is True
    assert result.variant_id == loaded_variant.variant_id


def test_verifier_registry():
    """Test that the verifier registry works."""
    from autota.verify.registry import list_registered_types

    types = list_registered_types()
    assert "kmap_simplification" in types


def test_boolean_parser_edge_cases():
    """Test edge cases in Boolean expression parsing."""
    from autota.verify.boolean import BooleanExpressionParser

    # Test with single variable
    parser = BooleanExpressionParser("A", ["A"])
    eval_func = parser.parse()
    assert eval_func({"A": True}) is True
    assert eval_func({"A": False}) is False

    # Test double negation
    parser = BooleanExpressionParser("(A')'", ["A"])
    eval_func = parser.parse()
    assert eval_func({"A": True}) is True
    assert eval_func({"A": False}) is False

    # Test complex nested expression
    parser = BooleanExpressionParser("(A+B)'(C+D)'", ["A", "B", "C", "D"])
    eval_func = parser.parse()
    # This is (A+B)' AND (C+D)', so true only when both A,B are false AND both C,D are false
    assert eval_func({"A": False, "B": False, "C": False, "D": False}) is True
    assert eval_func({"A": True, "B": False, "C": False, "D": False}) is False
    assert eval_func({"A": False, "B": False, "C": True, "D": False}) is False
