"""Abstract base class for problem verifiers."""

from abc import ABC, abstractmethod
from autota.models import ProblemVariant, VerificationResult, GradeResult


class Verifier(ABC):
    """Base class for all problem verifiers.

    Verifiers are deterministic, computational checkers that:
    1. Validate generated problem solutions (verify method)
    2. Grade student submissions (grade method)

    They NEVER use LLMs - only code-based verification.
    """

    @abstractmethod
    def verify(self, variant: ProblemVariant) -> VerificationResult:
        """Check that the solution is correct for the given parameters.

        Used at generation time (Layer 1) to verify LLM-produced solutions.

        Args:
            variant: The problem variant to verify

        Returns:
            VerificationResult with pass/fail status and details
        """
        pass

    @abstractmethod
    def grade(self, variant: ProblemVariant, student_answer: str) -> GradeResult:
        """Grade a student submission against the variant's solution.

        Used at submission time (Layer 3) to grade student answers.

        Args:
            variant: The problem variant with correct solution
            student_answer: The student's submitted answer

        Returns:
            GradeResult with score, feedback, and confidence level
        """
        pass

    @property
    @abstractmethod
    def problem_type(self) -> str:
        """String identifier matching the spec's problem_type field.

        Returns:
            Problem type string (e.g., 'kmap_simplification')
        """
        pass

    @property
    def confidence_level(self) -> str:
        """Confidence level for grading results.

        Returns:
            'deterministic' for pure computational grading,
            'llm_assisted' for LLM-based grading,
            'human_reviewed' for manually reviewed grades
        """
        return "deterministic"
