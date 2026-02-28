"""Boolean algebra verifier for truth table and expression verification."""

import re
from typing import Callable, Dict, List, Set
from autota.models import ProblemVariant, VerificationResult, GradeResult
from autota.verify.base import Verifier
from autota.verify.registry import register_verifier


class BooleanExpressionParser:
    """Parser for Boolean expressions supporting standard notation.

    Supported syntax:
    - OR: +
    - AND: * (or implicit concatenation like AB)
    - NOT: ' (postfix) or ~ (prefix)
    - Parentheses: ()
    - Variables: A-Z, a-z (case-sensitive)

    Examples:
    - A'B + CD
    - (A + B)(C + D)
    - ~A * B + C'D'
    """

    def __init__(self, expression: str, variables: List[str]):
        """Initialize the parser.

        Args:
            expression: Boolean expression string
            variables: List of variable names used in the expression
        """
        self.expression = expression.strip()
        self.variables = variables
        self.var_set = set(variables)

    def parse(self) -> Callable[[Dict[str, bool]], bool]:
        """Parse the expression and return an evaluation function.

        Returns:
            A function that takes a variable assignment dict and returns bool

        Raises:
            ValueError: If the expression is invalid
        """
        # Normalize the expression
        expr = self._normalize(self.expression)

        # Convert to Python expression
        python_expr = self._to_python(expr)

        # Create and return evaluation function
        def evaluate(assignment: Dict[str, bool]) -> bool:
            # Create local namespace with variable assignments
            namespace = {var: assignment[var] for var in self.variables}
            try:
                result = eval(python_expr, {"__builtins__": {}}, namespace)
                return bool(result)
            except Exception as e:
                raise ValueError(f"Error evaluating expression '{python_expr}': {e}")

        return evaluate

    def _normalize(self, expr: str) -> str:
        """Normalize the expression to canonical form.

        Args:
            expr: Input expression

        Returns:
            Normalized expression
        """
        # Remove all whitespace
        expr = re.sub(r"\s+", "", expr)

        # Convert ~A to A' (prefix NOT to postfix NOT)
        expr = self._convert_prefix_not(expr)

        # Add explicit * for implicit AND (e.g., AB -> A*B)
        expr = self._make_and_explicit(expr)

        return expr

    def _convert_prefix_not(self, expr: str) -> str:
        """Convert prefix NOT (~) to postfix NOT (').

        Args:
            expr: Expression that may contain ~

        Returns:
            Expression with only postfix NOT
        """
        result = []
        i = 0
        while i < len(expr):
            if expr[i] == "~":
                # Find what comes after ~
                i += 1
                if i < len(expr):
                    if expr[i] == "(":
                        # Find matching closing paren
                        paren_count = 1
                        j = i + 1
                        while j < len(expr) and paren_count > 0:
                            if expr[j] == "(":
                                paren_count += 1
                            elif expr[j] == ")":
                                paren_count -= 1
                            j += 1
                        # Add the parenthesized expression with ' after
                        result.append(expr[i:j] + "'")
                        i = j
                    elif expr[i].isalnum():
                        # Single variable
                        result.append(expr[i] + "'")
                        i += 1
                    else:
                        raise ValueError(f"Invalid character after ~ at position {i}")
            else:
                result.append(expr[i])
                i += 1

        return "".join(result)

    def _make_and_explicit(self, expr: str) -> str:
        """Add explicit * for implicit AND operations.

        Args:
            expr: Expression that may have implicit AND

        Returns:
            Expression with explicit * for all AND operations
        """
        result = []
        i = 0
        while i < len(expr):
            result.append(expr[i])

            # Check if we need to insert * after this character
            if i < len(expr) - 1:
                curr = expr[i]
                next_char = expr[i + 1]

                # Insert * between:
                # - variable/literal and variable (AB -> A*B)
                # - ) and variable/( (e.g., (A)B -> (A)*B)
                # - ' and variable/( (e.g., A'B -> A'*B)
                should_insert = False

                if curr.isalnum() and next_char.isalnum():
                    should_insert = True
                elif curr.isalnum() and next_char == "(":
                    should_insert = True
                elif curr == ")" and (next_char.isalnum() or next_char == "("):
                    should_insert = True
                elif curr == "'" and (next_char.isalnum() or next_char == "("):
                    should_insert = True

                if should_insert:
                    result.append("*")

            i += 1

        return "".join(result)

    def _to_python(self, expr: str) -> str:
        """Convert Boolean expression to valid Python expression.

        Args:
            expr: Normalized Boolean expression

        Returns:
            Python-compatible expression string
        """
        # Replace operators
        expr = expr.replace("+", " or ")
        expr = expr.replace("*", " and ")

        # Replace postfix NOT (A' -> not A)
        # Handle multi-character variables and literals
        expr = self._convert_postfix_not(expr)

        return expr

    def _convert_postfix_not(self, expr: str) -> str:
        """Convert postfix NOT (') to Python's prefix not.

        Args:
            expr: Expression with postfix NOT

        Returns:
            Expression with prefix not
        """
        result = []
        i = 0
        while i < len(expr):
            if expr[i] == "'":
                # Find what came before the '
                if not result:
                    raise ValueError("Invalid ' at start of expression")

                # Pop the last token (could be variable or closing paren)
                if result[-1] == ")":
                    # Find matching opening paren
                    paren_count = 1
                    j = len(result) - 2
                    while j >= 0 and paren_count > 0:
                        if result[j] == ")":
                            paren_count += 1
                        elif result[j] == "(":
                            paren_count -= 1
                        j -= 1
                    # Extract the parenthesized part
                    paren_expr = "".join(result[j + 1 :])
                    result = result[: j + 1]
                    result.append(f"(not {paren_expr})")
                else:
                    # Simple variable - scan backwards to get full identifier
                    var_chars = []
                    while result and (result[-1].isalnum() or result[-1] == "_"):
                        var_chars.insert(0, result.pop())
                    var_name = "".join(var_chars)
                    result.append(f"(not {var_name})")

                i += 1
            else:
                result.append(expr[i])
                i += 1

        return "".join(result)


@register_verifier
class BooleanVerifier(Verifier):
    """Verifier for Boolean algebra problems.

    Validates that a Boolean expression correctly represents a given
    set of minterms and don't-cares by comparing truth tables.
    """

    @property
    def problem_type(self) -> str:
        return "kmap_simplification"

    def verify(self, variant: ProblemVariant) -> VerificationResult:
        """Verify a Boolean expression against minterms.

        Args:
            variant: Problem variant with solution containing 'expression' field
                    and parameters containing 'minterms', 'dont_cares', 'variables'

        Returns:
            VerificationResult indicating pass/fail with details
        """
        try:
            # Extract data from variant
            expression = variant.solution.get("expression")
            if not expression:
                return VerificationResult(
                    variant_id=variant.variant_id,
                    passed=False,
                    error_message="No 'expression' field in solution",
                )

            minterms = set(variant.parameters.get("minterms", []))
            dont_cares = set(variant.parameters.get("dont_cares", []))
            variables = variant.parameters.get("variables", [])

            if not variables:
                return VerificationResult(
                    variant_id=variant.variant_id,
                    passed=False,
                    error_message="No 'variables' field in parameters",
                )

            # Parse the Boolean expression
            parser = BooleanExpressionParser(expression, variables)
            eval_func = parser.parse()

            # Generate truth table and check
            num_vars = len(variables)
            num_rows = 2**num_vars
            mismatches = []

            for row_idx in range(num_rows):
                # Create variable assignment for this row
                assignment = self._row_to_assignment(row_idx, variables)

                # Evaluate the expression
                expr_output = eval_func(assignment)

                # Determine expected output
                expected_output = self._expected_output(row_idx, minterms, dont_cares)

                # Check match
                if expected_output == "must_be_1" and not expr_output:
                    mismatches.append(
                        {
                            "row": row_idx,
                            "assignment": assignment,
                            "expected": True,
                            "actual": expr_output,
                            "reason": "minterm",
                        }
                    )
                elif expected_output == "must_be_0" and expr_output:
                    mismatches.append(
                        {
                            "row": row_idx,
                            "assignment": assignment,
                            "expected": False,
                            "actual": expr_output,
                            "reason": "non-minterm",
                        }
                    )
                # Don't-cares can be either 0 or 1, so no mismatch

            # Return result
            if mismatches:
                return VerificationResult(
                    variant_id=variant.variant_id,
                    passed=False,
                    error_message=f"Expression incorrect: {len(mismatches)} mismatched rows",
                    details={
                        "mismatches": mismatches[:5],  # Limit to first 5 for readability
                        "total_mismatches": len(mismatches),
                    },
                )
            else:
                # TODO: Verify minimality of the expression
                return VerificationResult(
                    variant_id=variant.variant_id,
                    passed=True,
                    details={
                        "note": "Correctness verified. Minimality check not yet implemented."
                    },
                )

        except Exception as e:
            return VerificationResult(
                variant_id=variant.variant_id,
                passed=False,
                error_message=f"Verification error: {str(e)}",
            )

    def _row_to_assignment(self, row_idx: int, variables: List[str]) -> Dict[str, bool]:
        """Convert a truth table row index to variable assignments.

        Args:
            row_idx: Row index (0 to 2^n - 1)
            variables: List of variable names (ordered, e.g., ['A', 'B', 'C', 'D'])

        Returns:
            Dict mapping variable names to boolean values
        """
        num_vars = len(variables)
        assignment = {}

        for i, var in enumerate(variables):
            # Bit position: MSB is first variable
            bit_pos = num_vars - 1 - i
            assignment[var] = bool((row_idx >> bit_pos) & 1)

        return assignment

    def _expected_output(
        self, row_idx: int, minterms: Set[int], dont_cares: Set[int]
    ) -> str:
        """Determine expected output for a truth table row.

        Args:
            row_idx: Row index
            minterms: Set of minterm indices
            dont_cares: Set of don't-care indices

        Returns:
            'must_be_1', 'must_be_0', or 'dont_care'
        """
        if row_idx in minterms:
            return "must_be_1"
        elif row_idx in dont_cares:
            return "dont_care"
        else:
            return "must_be_0"

    def grade(self, variant: ProblemVariant, student_answer: str) -> GradeResult:
        """Grade a student's Boolean expression answer.

        Args:
            variant: Problem variant with correct solution
            student_answer: Student's submitted expression

        Returns:
            GradeResult with score and feedback
        """
        try:
            # Extract problem parameters
            minterms = set(variant.parameters.get("minterms", []))
            dont_cares = set(variant.parameters.get("dont_cares", []))
            variables = variant.parameters.get("variables", [])

            if not variables:
                return GradeResult(
                    variant_id=variant.variant_id,
                    student_answer=student_answer,
                    correct=False,
                    feedback="Error: Problem has no variables specified.",
                )

            # Parse and evaluate student's expression
            try:
                parser = BooleanExpressionParser(student_answer, variables)
                student_eval = parser.parse()
            except Exception as e:
                return GradeResult(
                    variant_id=variant.variant_id,
                    student_answer=student_answer,
                    correct=False,
                    feedback=f"Syntax error in your expression: {str(e)}. Please check your Boolean algebra syntax.",
                    partial_credit=0.0,
                )

            # Check student's expression against truth table
            num_vars = len(variables)
            num_rows = 2**num_vars
            errors = []

            for row_idx in range(num_rows):
                assignment = self._row_to_assignment(row_idx, variables)
                student_output = student_eval(assignment)
                expected = self._expected_output(row_idx, minterms, dont_cares)

                # Check for errors
                if expected == "must_be_1" and not student_output:
                    errors.append((row_idx, assignment, "should be 1, got 0"))
                elif expected == "must_be_0" and student_output:
                    errors.append((row_idx, assignment, "should be 0, got 1"))

            # Calculate score
            if not errors:
                # Perfect! Expression is functionally correct
                # Note: We don't check minimality for grading
                return GradeResult(
                    variant_id=variant.variant_id,
                    student_answer=student_answer,
                    correct=True,
                    feedback="Correct! Your expression produces the right output for all input combinations.",
                    partial_credit=1.0,
                )
            else:
                # Partial credit based on percentage correct
                correct_rows = num_rows - len(errors)
                partial = correct_rows / num_rows

                # Build detailed feedback
                error_details = []
                for row_idx, assignment, reason in errors[:3]:  # Show first 3 errors
                    vars_str = ", ".join(f"{k}={int(v)}" for k, v in assignment.items())
                    error_details.append(f"  Row {row_idx} ({vars_str}): {reason}")

                if len(errors) > 3:
                    error_details.append(f"  ... and {len(errors) - 3} more errors")

                feedback = f"Incorrect. Your expression fails on {len(errors)}/{num_rows} rows:\n" + "\n".join(error_details)

                return GradeResult(
                    variant_id=variant.variant_id,
                    student_answer=student_answer,
                    correct=False,
                    feedback=feedback,
                    partial_credit=partial,
                )

        except Exception as e:
            return GradeResult(
                variant_id=variant.variant_id,
                student_answer=student_answer,
                correct=False,
                feedback=f"Grading error: {str(e)}. Please contact your instructor.",
                partial_credit=0.0,
            )
