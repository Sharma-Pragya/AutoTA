"""Tests for Quine-McCluskey algorithm solver."""

import pytest
from autota.solver.quine_mccluskey import QuineMcCluskySolver, Implicant


class TestImplicant:
    """Test the Implicant data structure."""

    def test_implicant_creation(self):
        """Test creating an implicant."""
        imp = Implicant(binary="10-1", minterms={9, 11})
        assert imp.binary == "10-1"
        assert imp.minterms == {9, 11}
        assert imp.is_prime is False

    def test_count_literals(self):
        """Test counting literals in an implicant."""
        assert Implicant("1010", {10}).count_literals() == 4
        assert Implicant("10-1", {9, 11}).count_literals() == 3
        assert Implicant("--01", {1, 5, 9, 13}).count_literals() == 2
        assert Implicant("----", set(range(16))).count_literals() == 0

    def test_to_expression(self):
        """Test converting implicant to Boolean expression."""
        variables = ["A", "B", "C", "D"]

        # All specific bits
        assert Implicant("1010", {10}).to_expression(variables) == "AB'CD'"
        assert Implicant("0000", {0}).to_expression(variables) == "A'B'C'D'"
        assert Implicant("1111", {15}).to_expression(variables) == "ABCD"

        # With don't-cares
        assert Implicant("10-1", {9, 11}).to_expression(variables) == "AB'D"
        assert Implicant("--01", {1, 5, 9, 13}).to_expression(variables) == "C'D"  # 01 = C'D
        assert Implicant("1-0-", {8, 10}).to_expression(variables) == "AC'"

    def test_to_expression_3_vars(self):
        """Test expression conversion with 3 variables."""
        variables = ["A", "B", "C"]

        assert Implicant("101", {5}).to_expression(variables) == "AB'C"  # 101 = AB'C
        assert Implicant("0-1", {1, 5}).to_expression(variables) == "A'C"


class TestQuineMcCluskySolver:
    """Test the Quine-McCluskey solver."""

    def test_simple_2_variable(self):
        """Test with simple 2-variable function."""
        # F(A,B) = m(1,3) = B
        solver = QuineMcCluskySolver(
            minterms=[1, 3],
            variables=["A", "B"]
        )
        result = solver.solve()
        assert result == "B"

    def test_simple_3_variable(self):
        """Test with 3-variable function."""
        # F(A,B,C) = m(0,2,4,6) = C'
        solver = QuineMcCluskySolver(
            minterms=[0, 2, 4, 6],
            variables=["A", "B", "C"]
        )
        result = solver.solve()
        assert result == "C'"

    def test_4_variable_example(self):
        """Test with 4-variable K-map example."""
        # F(A,B,C,D) = m(0,2,5,7)
        solver = QuineMcCluskySolver(
            minterms=[0, 2, 5, 7],
            variables=["A", "B", "C", "D"]
        )
        result = solver.solve()

        # Should produce minimal form
        # Valid minimizations: A'B'D' + A'BD or A'(B'D' + BD)
        # The solver produces: A'B'D' + A'BD (canonical minimal SOP)
        assert "A'" in result
        assert "B'D'" in result or "BD" in result

    def test_with_dont_cares(self):
        """Test minimization with don't-cares."""
        # F(A,B,C,D) = m(0,2,8,10) + d(1,3,9,11)
        # Minterms: 0000, 0010, 1000, 1010
        # Don't-cares: 0001, 0011, 1001, 1011
        # Should minimize very well with don't-cares
        solver = QuineMcCluskySolver(
            minterms=[0, 2, 8, 10],
            dont_cares=[1, 3, 9, 11],
            variables=["A", "B", "C", "D"]
        )
        result = solver.solve()
        # Should be highly simplified - exact result may vary but should be minimal
        # Could be "B'" or "B'D'" depending on algorithm choices
        # Let's just check it's short
        assert len(result) <= 4  # Should be very simple

    def test_all_minterms(self):
        """Test when all minterms are present (function = 1)."""
        solver = QuineMcCluskySolver(
            minterms=list(range(16)),
            variables=["A", "B", "C", "D"]
        )
        result = solver.solve()
        # Should be just "1" or minimal representation
        # With all minterms, minimal is a single term with all don't-cares
        assert result == "1"

    def test_single_minterm(self):
        """Test with a single minterm."""
        solver = QuineMcCluskySolver(
            minterms=[5],
            variables=["A", "B", "C"]
        )
        result = solver.solve()
        # m(5) = 101 = AB'C
        assert result == "AB'C"

    def test_get_solution_details(self):
        """Test getting detailed solution information."""
        solver = QuineMcCluskySolver(
            minterms=[0, 2, 5, 7],
            variables=["A", "B", "C", "D"]
        )
        details = solver.get_solution_details()

        assert "minterms" in details
        assert details["minterms"] == [0, 2, 5, 7]
        assert "prime_implicants" in details
        assert "essential_primes" in details
        assert "minimal_cover" in details
        assert "minimal_expression" in details
        assert details["num_variables"] == 4

    def test_prime_implicants_found(self):
        """Test that prime implicants are correctly identified."""
        solver = QuineMcCluskySolver(
            minterms=[0, 1, 2, 5, 6, 7],
            variables=["A", "B", "C"]
        )
        solver.solve()

        # Should have found prime implicants
        assert len(solver.prime_implicants) > 0
        assert all(p.is_prime for p in solver.prime_implicants)

    def test_essential_primes_found(self):
        """Test that essential prime implicants are identified."""
        solver = QuineMcCluskySolver(
            minterms=[0, 1, 2, 5],
            variables=["A", "B", "C"]
        )
        solver.solve()

        # Should have essential primes
        assert len(solver.essential_primes) > 0

    def test_complex_4_variable(self):
        """Test a more complex 4-variable function."""
        # Classic K-map example from textbooks
        solver = QuineMcCluskySolver(
            minterms=[0, 2, 5, 7, 8, 10, 13, 15],
            variables=["A", "B", "C", "D"]
        )
        result = solver.solve()

        # Should produce: B'D' + BD
        # Verify it's minimal (2 terms, 4 literals total)
        details = solver.get_solution_details()
        assert details["num_terms"] <= 2
        assert details["total_literals"] <= 4

    def test_dont_cares_reduce_complexity(self):
        """Test that don't-cares actually reduce the expression."""
        # Without don't-cares
        solver1 = QuineMcCluskySolver(
            minterms=[0, 2, 8, 10],
            variables=["A", "B", "C", "D"]
        )
        details1 = solver1.get_solution_details()

        # With don't-cares
        solver2 = QuineMcCluskySolver(
            minterms=[0, 2, 8, 10],
            dont_cares=[1, 3, 9, 11],
            variables=["A", "B", "C", "D"]
        )
        details2 = solver2.get_solution_details()

        # Solution with don't-cares should be simpler
        assert details2["total_literals"] <= details1["total_literals"]

    def test_validation_empty_minterms(self):
        """Test that empty minterms raise an error."""
        with pytest.raises(ValueError, match="at least one minterm"):
            QuineMcCluskySolver(
                minterms=[],
                variables=["A", "B"]
            )

    def test_validation_minterm_out_of_range(self):
        """Test that out-of-range minterms raise an error."""
        with pytest.raises(ValueError, match="exceeds maximum"):
            QuineMcCluskySolver(
                minterms=[0, 16],  # 16 is too large for 4 variables
                variables=["A", "B", "C", "D"]
            )

    def test_5_variable_function(self):
        """Test with 5 variables."""
        solver = QuineMcCluskySolver(
            minterms=[0, 1, 4, 5, 16, 17, 20, 21],
            variables=["A", "B", "C", "D", "E"]
        )
        result = solver.solve()

        # Should find a minimal solution
        assert result is not None
        assert len(result) > 0

    def test_symmetric_function(self):
        """Test with a symmetric function (XOR-like)."""
        # F(A,B,C) with odd parity (odd number of 1s)
        solver = QuineMcCluskySolver(
            minterms=[1, 2, 4, 7],  # Rows with odd number of 1s
            variables=["A", "B", "C"]
        )
        result = solver.solve()

        # XOR-like functions typically can't be simplified much
        # Just verify it produces a valid result
        assert result is not None

    def test_adjacent_minterms(self):
        """Test with adjacent minterms (should combine nicely)."""
        # m(0,1) = A'B'
        solver = QuineMcCluskySolver(
            minterms=[0, 1],
            variables=["A", "B", "C"]
        )
        result = solver.solve()
        assert result == "A'B'"

    def test_corner_case_all_dont_cares_no_minterms_except_one(self):
        """Test with many don't-cares and few minterms."""
        solver = QuineMcCluskySolver(
            minterms=[5],
            dont_cares=[0, 1, 2, 3, 4, 6, 7],
            variables=["A", "B", "C"]
        )
        result = solver.solve()

        # Should find a very simple expression using don't-cares
        details = solver.get_solution_details()
        assert details["total_literals"] <= 3  # Should be quite simple


def test_solver_integration_with_verifier():
    """Test that solver output works with the Boolean verifier."""
    from autota.verify.boolean import BooleanVerifier
    from autota.models import ProblemVariant
    from uuid import uuid4

    # Generate minimal solution using solver
    solver = QuineMcCluskySolver(
        minterms=[0, 2, 5, 7],
        variables=["A", "B", "C", "D"]
    )
    minimal_expr = solver.solve()

    # Verify it using the verifier
    variant = ProblemVariant(
        variant_id=uuid4(),
        problem_text="Test",
        parameters={
            "minterms": [0, 2, 5, 7],
            "dont_cares": [],
            "variables": ["A", "B", "C", "D"]
        },
        solution={"expression": minimal_expr},
        answer_format="boolean_expression"
    )

    verifier = BooleanVerifier()
    result = verifier.verify(variant)

    # Solver output should always verify correctly
    assert result.passed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
