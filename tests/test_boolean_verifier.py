"""Tests for Boolean expression verifier."""

import pytest
from uuid import uuid4
from autota.models import ProblemVariant, VerificationResult
from autota.verify.boolean import BooleanVerifier, BooleanExpressionParser


class TestBooleanExpressionParser:
    """Test Boolean expression parsing and evaluation."""

    def test_simple_variable(self):
        """Test parsing a single variable."""
        parser = BooleanExpressionParser("A", ["A"])
        eval_func = parser.parse()

        assert eval_func({"A": True}) is True
        assert eval_func({"A": False}) is False

    def test_not_operation_postfix(self):
        """Test NOT operation with postfix notation (A')."""
        parser = BooleanExpressionParser("A'", ["A"])
        eval_func = parser.parse()

        assert eval_func({"A": True}) is False
        assert eval_func({"A": False}) is True

    def test_not_operation_prefix(self):
        """Test NOT operation with prefix notation (~A)."""
        parser = BooleanExpressionParser("~A", ["A"])
        eval_func = parser.parse()

        assert eval_func({"A": True}) is False
        assert eval_func({"A": False}) is True

    def test_and_operation_implicit(self):
        """Test AND operation with implicit notation (AB)."""
        parser = BooleanExpressionParser("AB", ["A", "B"])
        eval_func = parser.parse()

        assert eval_func({"A": True, "B": True}) is True
        assert eval_func({"A": True, "B": False}) is False
        assert eval_func({"A": False, "B": True}) is False
        assert eval_func({"A": False, "B": False}) is False

    def test_and_operation_explicit(self):
        """Test AND operation with explicit notation (A*B)."""
        parser = BooleanExpressionParser("A*B", ["A", "B"])
        eval_func = parser.parse()

        assert eval_func({"A": True, "B": True}) is True
        assert eval_func({"A": True, "B": False}) is False

    def test_or_operation(self):
        """Test OR operation (A+B)."""
        parser = BooleanExpressionParser("A+B", ["A", "B"])
        eval_func = parser.parse()

        assert eval_func({"A": True, "B": True}) is True
        assert eval_func({"A": True, "B": False}) is True
        assert eval_func({"A": False, "B": True}) is True
        assert eval_func({"A": False, "B": False}) is False

    def test_complex_expression(self):
        """Test complex expression: A'B + CD."""
        parser = BooleanExpressionParser("A'B + CD", ["A", "B", "C", "D"])
        eval_func = parser.parse()

        # A'B term: A=0, B=1 should give True
        assert eval_func({"A": False, "B": True, "C": False, "D": False}) is True

        # CD term: C=1, D=1 should give True
        assert eval_func({"A": True, "B": False, "C": True, "D": True}) is True

        # Both false: A=1, B=any, C=any, D=0 should give False
        assert eval_func({"A": True, "B": True, "C": True, "D": False}) is False

    def test_parentheses(self):
        """Test parentheses: (A+B)(C+D)."""
        parser = BooleanExpressionParser("(A+B)(C+D)", ["A", "B", "C", "D"])
        eval_func = parser.parse()

        # Both terms true
        assert eval_func({"A": True, "B": False, "C": True, "D": False}) is True

        # First term false
        assert eval_func({"A": False, "B": False, "C": True, "D": False}) is False

        # Second term false
        assert eval_func({"A": True, "B": False, "C": False, "D": False}) is False

    def test_not_with_parentheses(self):
        """Test NOT with parentheses: (A+B)'."""
        parser = BooleanExpressionParser("(A+B)'", ["A", "B"])
        eval_func = parser.parse()

        # A+B is true, so (A+B)' should be false
        assert eval_func({"A": True, "B": False}) is False
        assert eval_func({"A": False, "B": True}) is False

        # A+B is false, so (A+B)' should be true
        assert eval_func({"A": False, "B": False}) is True

    def test_whitespace_handling(self):
        """Test that whitespace is properly ignored."""
        parser = BooleanExpressionParser(" A  +  B ", ["A", "B"])
        eval_func = parser.parse()

        assert eval_func({"A": True, "B": False}) is True

    def test_four_variable_kmap_example(self):
        """Test a realistic 4-variable K-map simplification example."""
        # Minterms: [0, 2, 5, 7, 8, 10, 13, 15]
        # One possible minimal expression: B'D' + BD
        parser = BooleanExpressionParser("B'D' + BD", ["A", "B", "C", "D"])
        eval_func = parser.parse()

        # Check each minterm
        minterms = [0, 2, 5, 7, 8, 10, 13, 15]
        for minterm in minterms:
            # Convert minterm to binary assignment
            assignment = {
                "A": bool((minterm >> 3) & 1),
                "B": bool((minterm >> 2) & 1),
                "C": bool((minterm >> 1) & 1),
                "D": bool(minterm & 1),
            }
            assert eval_func(assignment) is True, f"Minterm {minterm} should be True"

        # Check a non-minterm
        non_minterm_assignment = {
            "A": False,  # 0
            "B": False,  # 0
            "C": False,  # 0
            "D": True,  # 1
        }  # This is row 1
        assert eval_func(non_minterm_assignment) is False


class TestBooleanVerifier:
    """Test the BooleanVerifier class."""

    def test_verifier_problem_type(self):
        """Test that verifier reports correct problem type."""
        verifier = BooleanVerifier()
        assert verifier.problem_type == "kmap_simplification"

    def test_verify_correct_expression(self):
        """Test verification of a correct Boolean expression."""
        variant = ProblemVariant(
            variant_id=uuid4(),
            problem_text="Simplify F(A,B,C,D) with minterms [0,2,5,7]",
            parameters={
                "minterms": [0, 2, 5, 7],
                "dont_cares": [],
                "variables": ["A", "B", "C", "D"],
            },
            solution={"expression": "A'B'D' + A'BD"},
            answer_format="boolean_expression",
        )

        verifier = BooleanVerifier()
        result = verifier.verify(variant)

        assert isinstance(result, VerificationResult)
        assert result.passed is True
        assert result.variant_id == variant.variant_id

    def test_verify_incorrect_expression(self):
        """Test verification of an incorrect Boolean expression."""
        variant = ProblemVariant(
            variant_id=uuid4(),
            problem_text="Simplify F(A,B,C,D) with minterms [0,2,5,7]",
            parameters={
                "minterms": [0, 2, 5, 7],
                "dont_cares": [],
                "variables": ["A", "B", "C", "D"],
            },
            solution={
                "expression": "A'B'"
            },  # Wrong: this only covers minterms 0, not 2,5,7
            answer_format="boolean_expression",
        )

        verifier = BooleanVerifier()
        result = verifier.verify(variant)

        assert result.passed is False
        assert result.error_message is not None
        assert "mismatched" in result.error_message.lower()
        assert result.details is not None
        assert "mismatches" in result.details

    def test_verify_with_dont_cares(self):
        """Test verification with don't-cares."""
        # Expression that covers minterms and may or may not cover don't-cares
        variant = ProblemVariant(
            variant_id=uuid4(),
            problem_text="Simplify F(A,B,C,D)",
            parameters={
                "minterms": [0, 2],
                "dont_cares": [1, 3],
                "variables": ["A", "B", "C", "D"],
            },
            solution={
                "expression": "A'B'"
            },  # Covers 0,1,2,3 (all with A'B'), which includes minterms and don't-cares
            answer_format="boolean_expression",
        )

        verifier = BooleanVerifier()
        result = verifier.verify(variant)

        # Should pass: covers all minterms, and don't-cares can be 0 or 1
        assert result.passed is True

    def test_verify_missing_expression(self):
        """Test verification when expression is missing."""
        variant = ProblemVariant(
            variant_id=uuid4(),
            problem_text="Test",
            parameters={
                "minterms": [0],
                "dont_cares": [],
                "variables": ["A"],
            },
            solution={},  # No expression field
            answer_format="boolean_expression",
        )

        verifier = BooleanVerifier()
        result = verifier.verify(variant)

        assert result.passed is False
        assert "expression" in result.error_message.lower()

    def test_verify_missing_variables(self):
        """Test verification when variables are missing."""
        variant = ProblemVariant(
            variant_id=uuid4(),
            problem_text="Test",
            parameters={
                "minterms": [0],
                "dont_cares": [],
                # Missing variables field
            },
            solution={"expression": "A"},
            answer_format="boolean_expression",
        )

        verifier = BooleanVerifier()
        result = verifier.verify(variant)

        assert result.passed is False
        assert "variables" in result.error_message.lower()

    def test_two_variable_example(self):
        """Test with a simple 2-variable example."""
        # F(A,B) with minterms [1, 3] (rows where B=1)
        # Minimal expression: B
        variant = ProblemVariant(
            variant_id=uuid4(),
            problem_text="Simplify F(A,B)",
            parameters={
                "minterms": [1, 3],
                "dont_cares": [],
                "variables": ["A", "B"],
            },
            solution={"expression": "B"},
            answer_format="boolean_expression",
        )

        verifier = BooleanVerifier()
        result = verifier.verify(variant)

        assert result.passed is True

    def test_three_variable_example(self):
        """Test with a 3-variable example."""
        # F(A,B,C) with minterms [0,2,4,6] (rows where C=0)
        # Minimal expression: C'
        variant = ProblemVariant(
            variant_id=uuid4(),
            problem_text="Simplify F(A,B,C)",
            parameters={
                "minterms": [0, 2, 4, 6],
                "dont_cares": [],
                "variables": ["A", "B", "C"],
            },
            solution={"expression": "C'"},
            answer_format="boolean_expression",
        )

        verifier = BooleanVerifier()
        result = verifier.verify(variant)

        assert result.passed is True

    def test_registry_integration(self):
        """Test that BooleanVerifier is properly registered."""
        from autota.verify.registry import get_verifier

        verifier = get_verifier("kmap_simplification")
        assert isinstance(verifier, BooleanVerifier)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
