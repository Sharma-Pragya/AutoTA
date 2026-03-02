"""Retry endpoint for AutoTA.

Allows students to retry an assignment with fresh variants.
"""

import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from autota.web.db import get_db_connection
from autota.web.variant_draw import draw_variants


router = APIRouter(prefix="/api", tags=["retry"])


class RetryResponse(BaseModel):
    """Response for retry request."""
    attempt_id: int
    attempt_number: int
    message: str


@router.post("/retry/{student_id}/{assignment_id}", response_model=RetryResponse)
async def retry_assignment(student_id: str, assignment_id: str):
    """Create a new attempt for a student with fresh variants.

    Logic:
    1. Verify latest attempt is "graded" (or "submitted" with grades)
    2. Verify attempt_number < assignment.max_attempts
    3. Create new attempt (attempt_number + 1, status = "created")
    4. Call draw_variants() — gets fresh variants excluding prior ones
    5. Insert into variant_assignments
    6. Return new attempt_id + attempt_number

    Args:
        student_id: Student ID
        assignment_id: Assignment ID

    Returns:
        RetryResponse with new attempt details

    Raises:
        HTTPException: If retry conditions not met
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get the latest attempt for this student+assignment
    cursor.execute("""
        SELECT id, attempt_number, status, submitted_at
        FROM attempts
        WHERE student_id = ? AND assignment_id = ?
        ORDER BY attempt_number DESC
        LIMIT 1
    """, (student_id, assignment_id))

    latest_attempt = cursor.fetchone()

    if not latest_attempt:
        conn.close()
        raise HTTPException(status_code=404, detail="No existing attempt found")

    latest_id, latest_number, latest_status, submitted_at = latest_attempt

    # Verify the latest attempt is complete (graded or submitted)
    if latest_status not in ["graded", "submitted"]:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail=f"Cannot retry: latest attempt is '{latest_status}'. Complete it first."
        )

    # Get assignment max_attempts
    cursor.execute("""
        SELECT max_attempts
        FROM assignments
        WHERE id = ?
    """, (assignment_id,))

    assignment_row = cursor.fetchone()
    if not assignment_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Assignment not found")

    max_attempts = assignment_row[0]

    # Verify student hasn't exceeded max attempts
    if latest_number >= max_attempts:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail=f"Cannot retry: already at max attempts ({max_attempts})"
        )

    # Create new attempt
    new_attempt_number = latest_number + 1

    cursor.execute("""
        INSERT INTO attempts (student_id, assignment_id, attempt_number, status)
        VALUES (?, ?, ?, ?)
    """, (student_id, assignment_id, new_attempt_number, "created"))

    new_attempt_id = cursor.lastrowid

    # Draw fresh variants (excluding previously seen ones)
    variant_draws = draw_variants(student_id, assignment_id, new_attempt_id)

    # Insert variant assignments for the new attempt
    for problem_id, variant_data in variant_draws.items():
        # Reconstruct variant_json from pool data
        parameters = json.loads(variant_data["parameters_json"])
        variant_json = {
            "variant_id": variant_data["id"],
            "problem_text": variant_data["problem_text"],
            "parameters": {
                "minterms": parameters["minterms"],
                "dont_cares": parameters["dont_cares"],
                "variables": ["A", "B", "C", "D"]  # Hardcoded for now
            },
            "answer_format": "boolean_expression",
            "metadata": {
                "difficulty": "medium",
                "num_variables": parameters["num_vars"],
                "has_dont_cares": len(parameters["dont_cares"]) > 0,
                "generator": "pool"
            }
        }

        cursor.execute("""
            INSERT INTO variant_assignments
            (student_id, problem_id, variant_id, variant_json, solution_json,
             attempt_number, attempt_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            student_id,
            problem_id,
            variant_data["id"],
            json.dumps(variant_json),
            variant_data["solution_json"],
            new_attempt_number,
            new_attempt_id
        ))

    # Update attempt status to "in_progress"
    cursor.execute("""
        UPDATE attempts
        SET status = 'in_progress'
        WHERE id = ?
    """, (new_attempt_id,))

    conn.commit()
    conn.close()

    return RetryResponse(
        attempt_id=new_attempt_id,
        attempt_number=new_attempt_number,
        message=f"New attempt #{new_attempt_number} created with fresh variants"
    )
