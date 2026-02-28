"""Pydantic models for AutoTA problem specs, variants, and results."""

from typing import Any, Dict, List, Optional, Annotated
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field
from pydantic.functional_serializers import PlainSerializer


class ProblemSpec(BaseModel):
    """Problem specification parsed from YAML."""

    problem_type: str = Field(..., description="Type of problem (e.g., kmap_simplification)")
    topic: str = Field(..., description="Human-readable topic name")
    description: str = Field(..., description="Detailed description of the problem")
    num_variants: int = Field(..., gt=0, description="Number of unique variants to generate")
    parameters: Dict[str, Any] = Field(
        ..., description="Problem-specific parameters and constraints"
    )
    reference_material: Optional[str] = Field(
        None, description="Path to reference material (PDF, txt, md)"
    )
    answer_format: str = Field(..., description="Expected format of the answer")
    difficulty: str = Field(
        default="medium", description="Difficulty level (easy, medium, hard)"
    )


class ProblemVariant(BaseModel):
    """A single generated problem variant."""

    variant_id: Annotated[UUID, PlainSerializer(lambda x: str(x), return_type=str)] = Field(
        default_factory=uuid4, description="Unique identifier"
    )
    problem_text: str = Field(..., description="Student-facing problem statement")
    parameters: Dict[str, Any] = Field(
        ..., description="Specific parameters for this variant (e.g., minterms, don't-cares)"
    )
    solution: Dict[str, Any] = Field(
        ..., description="Correct solution with method and any intermediate steps"
    )
    answer_format: str = Field(..., description="Expected format of the answer")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Optional metadata (generation timestamp, difficulty, etc.)"
    )


class VerificationResult(BaseModel):
    """Result of verifying a problem variant."""

    variant_id: Annotated[UUID, PlainSerializer(lambda x: str(x), return_type=str)] = Field(
        ..., description="ID of the verified variant"
    )
    passed: bool = Field(..., description="Whether verification succeeded")
    error_message: Optional[str] = Field(
        None, description="Error message if verification failed"
    )
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional verification details (mismatched rows, etc.)"
    )


class GenerationBatch(BaseModel):
    """Collection of variants from one API call with statistics."""

    model_config = ConfigDict(protected_namespaces=())

    variants: List[ProblemVariant] = Field(..., description="Generated variants")
    num_requested: int = Field(..., description="Number of variants requested")
    num_generated: int = Field(..., description="Number of variants actually generated")
    api_call_timestamp: Optional[str] = Field(None, description="Timestamp of API call")
    model_used: Optional[str] = Field(None, description="Claude model used for generation")


class GradeResult(BaseModel):
    """Result of grading a student's answer (future use)."""

    variant_id: Annotated[UUID, PlainSerializer(lambda x: str(x), return_type=str)] = Field(
        ..., description="ID of the problem variant"
    )
    student_answer: str = Field(..., description="Student's submitted answer")
    correct: bool = Field(..., description="Whether the answer is correct")
    feedback: Optional[str] = Field(None, description="Feedback for the student")
    partial_credit: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Partial credit score (0.0 to 1.0)"
    )
