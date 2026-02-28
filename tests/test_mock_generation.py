"""Mock test to verify the generation pipeline without API calls."""

import json
from pathlib import Path
from uuid import uuid4
from autota.models import ProblemVariant
from autota.verify.boolean import BooleanVerifier


def test_manual_variant_verification(tmp_path):
    """Test the full pipeline with manually created variants."""

    # Create 3 manually crafted variants (simulating API output)
    variants = [
        ProblemVariant(
            variant_id=uuid4(),
            problem_text="Simplify the Boolean function F(A,B,C,D) defined by minterms m(0,2,5,7). Express as minimal sum-of-products.",
            parameters={
                "minterms": [0, 2, 5, 7],
                "dont_cares": [],
                "variables": ["A", "B", "C", "D"]
            },
            solution={
                "expression": "A'B'D' + A'BD",
                "method": "kmap"
            },
            answer_format="boolean_expression",
            metadata={
                "difficulty": "medium",
                "has_edge_wrap": False
            }
        ),
        ProblemVariant(
            variant_id=uuid4(),
            problem_text="Simplify F(A,B,C,D) with minterms m(0,2,5,7,8,10,13,15). Express as minimal sum-of-products.",
            parameters={
                "minterms": [0, 2, 5, 7, 8, 10, 13, 15],
                "dont_cares": [],
                "variables": ["A", "B", "C", "D"]
            },
            solution={
                "expression": "B'D' + BD",
                "method": "kmap"
            },
            answer_format="boolean_expression",
            metadata={
                "difficulty": "medium",
                "has_edge_wrap": True
            }
        ),
        ProblemVariant(
            variant_id=uuid4(),
            problem_text="Simplify F(A,B,C) with minterms m(0,2,4,6). Express as minimal sum-of-products.",
            parameters={
                "minterms": [0, 2, 4, 6],
                "dont_cares": [],
                "variables": ["A", "B", "C"]
            },
            solution={
                "expression": "C'",
                "method": "kmap"
            },
            answer_format="boolean_expression",
            metadata={
                "difficulty": "easy",
                "has_edge_wrap": False
            }
        ),
    ]

    # Verify each variant
    verifier = BooleanVerifier()
    results = []

    for variant in variants:
        result = verifier.verify(variant)
        results.append(result)

        # Write to output directory
        output_file = tmp_path / f"{variant.variant_id}.json"
        with open(output_file, "w") as f:
            json.dump(variant.model_dump(), f, indent=2, default=str)

    # Check all passed
    assert all(r.passed for r in results), "All variants should verify correctly"

    # Verify files were created
    json_files = list(tmp_path.glob("*.json"))
    assert len(json_files) == 3, "Should have 3 variant files"

    # Create a summary report
    report = {
        "total_generated": len(variants),
        "verified_count": sum(1 for r in results if r.passed),
        "failed_count": sum(1 for r in results if not r.passed),
        "success_rate": sum(1 for r in results if r.passed) / len(results) if results else 0,
    }

    report_file = tmp_path / "report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n✓ Generated and verified {report['verified_count']} variants")
    print(f"✓ Success rate: {report['success_rate']:.1%}")
    print(f"✓ Output directory: {tmp_path}")

    assert report["success_rate"] == 1.0


def test_variant_with_dont_cares():
    """Test verification with don't-care conditions."""
    variant = ProblemVariant(
        variant_id=uuid4(),
        problem_text="Simplify F(A,B,C,D) with minterms m(0,2,8,10) and don't-cares d(1,3,9,11).",
        parameters={
            "minterms": [0, 2, 8, 10],
            "dont_cares": [1, 3, 9, 11],
            "variables": ["A", "B", "C", "D"]
        },
        solution={
            "expression": "B'D'",  # This covers 0,1,2,3,8,9,10,11
            "method": "kmap"
        },
        answer_format="boolean_expression",
    )

    verifier = BooleanVerifier()
    result = verifier.verify(variant)

    assert result.passed, f"Should pass with don't-cares: {result.error_message}"


def test_complex_expression():
    """Test verification with a more complex expression."""
    # F(A,B,C,D) = minterms [1,3,5,7,9,11,13,15] (all rows where D=1)
    variant = ProblemVariant(
        variant_id=uuid4(),
        problem_text="Simplify F(A,B,C,D) where output is 1 when D=1.",
        parameters={
            "minterms": [1, 3, 5, 7, 9, 11, 13, 15],
            "dont_cares": [],
            "variables": ["A", "B", "C", "D"]
        },
        solution={
            "expression": "D",  # Minimal form
            "method": "kmap"
        },
        answer_format="boolean_expression",
    )

    verifier = BooleanVerifier()
    result = verifier.verify(variant)

    assert result.passed, f"Should pass with simple D: {result.error_message}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
