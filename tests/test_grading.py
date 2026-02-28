"""Tests for the grading functionality (Layer 3)."""

import pytest
from uuid import uuid4
from autota.models import ProblemVariant, GradeResult
from autota.verify.boolean import BooleanVerifier


class TestBooleanGrading:
    """Test grading student submissions for Boolean expressions."""

    def test_grade_correct_answer(self):
        """Test grading a correct student answer."""
        variant = ProblemVariant(
            variant_id=uuid4(),
            problem_text="Simplify F(A,B) where minterms are [1,3]",
            parameters={
                "minterms": [1, 3],
                "dont_cares": [],
                "variables": ["A", "B"]
            },
            solution={"expression": "B"},  # Correct minimal form
            answer_format="boolean_expression"
        )

        verifier = BooleanVerifier()

        # Student submits the correct answer
        result = verifier.grade(variant, "B")

        assert isinstance(result, GradeResult)
        assert result.correct is True
        assert result.partial_credit == 1.0
        assert "Correct" in result.feedback

    def test_grade_correct_but_not_minimal(self):
        """Test that functionally correct but non-minimal answers are accepted."""
        variant = ProblemVariant(
            variant_id=uuid4(),
            problem_text="Simplify F(A,B) where minterms are [1,3]",
            parameters={
                "minterms": [1, 3],
                "dont_cares": [],
                "variables": ["A", "B"]
            },
            solution={"expression": "B"},  # Minimal
            answer_format="boolean_expression"
        )

        verifier = BooleanVerifier()

        # Student submits non-minimal but correct expression
        result = verifier.grade(variant, "A'B + AB")  # Expands to B

        assert result.correct is True
        assert result.partial_credit == 1.0
        # We don't penalize for non-minimality in grading

    def test_grade_incorrect_answer(self):
        """Test grading an incorrect student answer."""
        variant = ProblemVariant(
            variant_id=uuid4(),
            problem_text="Simplify F(A,B) where minterms are [1,3]",
            parameters={
                "minterms": [1, 3],
                "dont_cares": [],
                "variables": ["A", "B"]
            },
            solution={"expression": "B"},
            answer_format="boolean_expression"
        )

        verifier = BooleanVerifier()

        # Student submits wrong answer
        result = verifier.grade(variant, "A")  # Wrong!

        assert result.correct is False
        assert result.partial_credit < 1.0
        assert "Incorrect" in result.feedback
        assert "Row" in result.feedback  # Should show which rows failed

    def test_grade_syntax_error(self):
        """Test grading with invalid Boolean expression syntax."""
        variant = ProblemVariant(
            variant_id=uuid4(),
            problem_text="Simplify F(A,B)",
            parameters={
                "minterms": [1, 3],
                "dont_cares": [],
                "variables": ["A", "B"]
            },
            solution={"expression": "B"},
            answer_format="boolean_expression"
        )

        verifier = BooleanVerifier()

        # Student submits invalid syntax
        result = verifier.grade(variant, "A +++ B")  # Invalid

        assert result.correct is False
        assert result.partial_credit == 0.0
        # Should mention error in feedback
        assert "error" in result.feedback.lower() or "syntax" in result.feedback.lower()

    def test_grade_partial_credit(self):
        """Test that partial credit is awarded correctly."""
        variant = ProblemVariant(
            variant_id=uuid4(),
            problem_text="Simplify F(A,B,C)",
            parameters={
                "minterms": [0, 2, 4, 6],  # C'
                "dont_cares": [],
                "variables": ["A", "B", "C"]
            },
            solution={"expression": "C'"},
            answer_format="boolean_expression"
        )

        verifier = BooleanVerifier()

        # Student submits an expression that's only partially correct
        # A'C' covers rows 0, 2 (correct) but misses 4, 6
        result = verifier.grade(variant, "A'C'")

        assert result.correct is False
        assert 0.0 < result.partial_credit < 1.0
        # Should get credit for the rows it covers correctly

    def test_grade_with_dont_cares(self):
        """Test grading with don't-care conditions."""
        variant = ProblemVariant(
            variant_id=uuid4(),
            problem_text="Simplify F(A,B,C,D)",
            parameters={
                "minterms": [0, 2, 8, 10],
                "dont_cares": [1, 3, 9, 11],
                "variables": ["A", "B", "C", "D"]
            },
            solution={"expression": "B'D'"},  # Uses don't-cares
            answer_format="boolean_expression"
        )

        verifier = BooleanVerifier()

        # Student submits a valid answer using don't-cares
        result1 = verifier.grade(variant, "B'D'")
        assert result1.correct is True

        # Student submits answer without using don't-cares
        # This should also be correct if it covers all minterms
        result2 = verifier.grade(variant, "A'B'C'D' + A'B'CD' + AB'C'D' + AB'CD'")
        assert result2.correct is True

    def test_grade_complex_expression(self):
        """Test grading a complex 4-variable expression."""
        variant = ProblemVariant(
            variant_id=uuid4(),
            problem_text="Simplify F(A,B,C,D) for minterms [0,2,5,7]",
            parameters={
                "minterms": [0, 2, 5, 7],
                "dont_cares": [],
                "variables": ["A", "B", "C", "D"]
            },
            solution={"expression": "A'B'D' + A'BD"},
            answer_format="boolean_expression"
        )

        verifier = BooleanVerifier()

        # Correct answer
        result1 = verifier.grade(variant, "A'B'D' + A'BD")
        assert result1.correct is True

        # Alternative correct form (factored)
        result2 = verifier.grade(variant, "A'(B'D' + BD)")
        assert result2.correct is True

        # Wrong answer
        result3 = verifier.grade(variant, "AB")
        assert result3.correct is False

    def test_grade_feedback_quality(self):
        """Test that feedback includes helpful error information."""
        variant = ProblemVariant(
            variant_id=uuid4(),
            problem_text="Simplify F(A,B)",
            parameters={
                "minterms": [1, 3],
                "dont_cares": [],
                "variables": ["A", "B"]
            },
            solution={"expression": "B"},
            answer_format="boolean_expression"
        )

        verifier = BooleanVerifier()
        result = verifier.grade(variant, "A")  # Wrong

        # Feedback should include:
        # - Number of incorrect rows
        # - Specific row examples
        # - What was expected vs what was received
        assert "fails on" in result.feedback.lower() or "incorrect" in result.feedback.lower()
        assert "Row" in result.feedback  # Should mention specific rows

    def test_grade_all_wrong(self):
        """Test grading when student answer is completely wrong."""
        variant = ProblemVariant(
            variant_id=uuid4(),
            problem_text="Simplify F(A,B)",
            parameters={
                "minterms": [1, 3],  # B
                "dont_cares": [],
                "variables": ["A", "B"]
            },
            solution={"expression": "B"},
            answer_format="boolean_expression"
        )

        verifier = BooleanVerifier()

        # Student submits B' (exact opposite)
        result = verifier.grade(variant, "B'")

        assert result.correct is False
        assert result.partial_credit == 0.0  # No credit for completely wrong


def test_grading_vs_verification():
    """Test that grading and verification use the same logic."""
    variant = ProblemVariant(
        variant_id=uuid4(),
        problem_text="Test problem",
        parameters={
            "minterms": [0, 2, 5, 7],
            "dont_cares": [],
            "variables": ["A", "B", "C", "D"]
        },
        solution={"expression": "A'B'D' + A'BD"},
        answer_format="boolean_expression"
    )

    verifier = BooleanVerifier()

    # Verify the solution
    verify_result = verifier.verify(variant)

    # Grade the same solution
    grade_result = verifier.grade(variant, "A'B'D' + A'BD")

    # Both should pass
    assert verify_result.passed is True
    assert grade_result.correct is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
