"""Answer submission and grading endpoints."""

import json
from typing import Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from autota.web.db import get_db_connection
from autota.verify.registry import get_verifier
from autota.models import ProblemVariant
from uuid import UUID

router = APIRouter()


class SaveAnswerRequest(BaseModel):
    student_id: str
    problem_id: str
    answer: str
    attempt_id: int | None = None  # New: link to specific attempt


class SubmitRequest(BaseModel):
    student_id: str
    assignment_id: str
    answers: Dict[str, str]
    attestation_signed: bool
    attempt_id: int | None = None  # New: link to specific attempt


@router.post("/save-answer")
async def save_answer(request: SaveAnswerRequest):
    """Auto-save a single answer to draft_answers table (Phase 2.1)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get attempt_id if not provided
        if not request.attempt_id:
            cursor.execute(
                """SELECT id FROM attempts
                   WHERE student_id = ? AND assignment_id LIKE ?
                   ORDER BY attempt_number DESC LIMIT 1""",
                (request.student_id, request.problem_id.split('_')[0] + '%')
            )
            attempt_row = cursor.fetchone()
            if attempt_row:
                attempt_id = attempt_row["id"]
            else:
                # No attempt exists yet - this shouldn't happen in normal flow
                conn.close()
                raise HTTPException(status_code=400, detail="No active attempt found")
        else:
            attempt_id = request.attempt_id

        # Upsert into draft_answers (Phase 2.1 separated draft layer)
        cursor.execute(
            """INSERT INTO draft_answers (attempt_id, problem_id, answer_raw, updated_at)
               VALUES (?, ?, ?, datetime('now'))
               ON CONFLICT(attempt_id, problem_id)
               DO UPDATE SET answer_raw = ?, updated_at = datetime('now')""",
            (attempt_id, request.problem_id, request.answer, request.answer)
        )

        conn.commit()
        conn.close()

        return {"saved": True}

    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit")
async def submit_answers(request: SubmitRequest):
    """Submit all answers for grading using Layer 3 verifiers (Phase 2.1 with weighted scoring)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get attempt_id
        if not request.attempt_id:
            cursor.execute(
                """SELECT id FROM attempts
                   WHERE student_id = ? AND assignment_id = ?
                   ORDER BY attempt_number DESC LIMIT 1""",
                (request.student_id, request.assignment_id)
            )
            attempt_row = cursor.fetchone()
            if not attempt_row:
                conn.close()
                raise HTTPException(status_code=400, detail="No active attempt found")
            attempt_id = attempt_row["id"]
        else:
            attempt_id = request.attempt_id

        # Verify attempt status is in_progress
        cursor.execute("SELECT status FROM attempts WHERE id = ?", (attempt_id,))
        attempt_status_row = cursor.fetchone()
        if not attempt_status_row:
            conn.close()
            raise HTTPException(status_code=404, detail="Attempt not found")

        if attempt_status_row["status"] not in ["created", "in_progress"]:
            conn.close()
            raise HTTPException(
                status_code=400,
                detail=f"Cannot submit: attempt status is '{attempt_status_row['status']}'"
            )

        results = {}
        total_points_earned = 0.0
        total_points_possible = 0.0
        problems_correct = 0
        problems_total = 0

        for problem_id, answer in request.answers.items():
            # Get problem info (including points)
            cursor.execute(
                "SELECT answer_format, points FROM problems WHERE id = ?",
                (problem_id,)
            )
            problem_row = cursor.fetchone()
            if not problem_row:
                continue

            answer_format = problem_row["answer_format"]
            problem_points = problem_row["points"] or 1.0
            problems_total += 1
            total_points_possible += problem_points

            # Get variant assignment
            cursor.execute(
                """SELECT id, variant_json, solution_json FROM variant_assignments
                   WHERE student_id = ? AND problem_id = ?
                   ORDER BY attempt_number DESC LIMIT 1""",
                (request.student_id, problem_id)
            )
            variant_row = cursor.fetchone()

            if variant_row:
                # Reconstruct ProblemVariant for grading
                variant_data = json.loads(variant_row["variant_json"])
                solution_data = json.loads(variant_row["solution_json"])
                variant_data["solution"] = solution_data

                variant = ProblemVariant(
                    variant_id=UUID(variant_data["variant_id"]),
                    problem_text=variant_data["problem_text"],
                    parameters=variant_data["parameters"],
                    solution=solution_data,
                    answer_format=variant_data["answer_format"],
                    metadata=variant_data.get("metadata")
                )

                # Get verifier and grade
                verifier = get_verifier("kmap_simplification")
                grade_result = verifier.grade(variant, answer)

                # Calculate score (0.0 to 1.0 for this problem)
                score = grade_result.partial_credit or (1.0 if grade_result.correct else 0.0)
                points_earned = score * problem_points
                total_points_earned += points_earned

                if grade_result.correct:
                    problems_correct += 1

                results[problem_id] = {
                    "correct": grade_result.correct,
                    "score": score,
                    "points_earned": points_earned,
                    "points_possible": problem_points,
                    "feedback": grade_result.feedback
                }

                # Store submission (immutable record)
                cursor.execute(
                    """INSERT INTO submissions
                       (student_id, problem_id, variant_assignment_id, answer,
                        score, correct, feedback, attestation_signed)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        request.student_id,
                        problem_id,
                        variant_row["id"],
                        answer,
                        score,
                        1 if grade_result.correct else 0,
                        grade_result.feedback,
                        1 if request.attestation_signed else 0
                    )
                )
                submission_id = cursor.lastrowid

                # Store grade (separate table in Phase 2.1)
                cursor.execute(
                    """INSERT INTO grades
                       (submission_id, score, correct, feedback, grading_tier, grading_status, graded_by)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        submission_id,
                        score,
                        1 if grade_result.correct else 0,
                        grade_result.feedback,
                        'deterministic',
                        'graded',
                        'autota_verifier'
                    )
                )
            else:
                # No variant - simple exact match for value/number questions
                if answer_format in ["value", "number"]:
                    # For now, mark as correct (would need expected answer in DB)
                    points_earned = problem_points
                    total_points_earned += points_earned
                    problems_correct += 1

                    results[problem_id] = {
                        "correct": True,
                        "score": 1.0,
                        "points_earned": points_earned,
                        "points_possible": problem_points,
                        "feedback": "Answer recorded."
                    }

        # Calculate weighted total score
        weighted_score = total_points_earned / total_points_possible if total_points_possible > 0 else 0

        # Insert attempt_results (denormalized aggregate)
        cursor.execute(
            """INSERT INTO attempt_results
               (attempt_id, total_score, total_points_earned, total_points_possible,
                problems_correct, problems_total)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                attempt_id,
                weighted_score,
                total_points_earned,
                total_points_possible,
                problems_correct,
                problems_total
            )
        )

        # Update attempt record to 'graded' status
        cursor.execute(
            """UPDATE attempts
               SET submitted_at = datetime('now'), total_score = ?, status = ?,
                   attestation_signed = ?, attestation_signed_at = datetime('now')
               WHERE id = ?""",
            (weighted_score, "graded", 1 if request.attestation_signed else 0, attempt_id)
        )

        # Check if can retry
        cursor.execute(
            """SELECT assignment_id, attempt_number FROM attempts WHERE id = ?""",
            (attempt_id,)
        )
        attempt_info = cursor.fetchone()
        assignment_id = attempt_info["assignment_id"]
        attempt_number = attempt_info["attempt_number"]

        cursor.execute(
            """SELECT max_attempts FROM assignments WHERE id = ?""",
            (assignment_id,)
        )
        max_attempts_row = cursor.fetchone()
        max_attempts = max_attempts_row["max_attempts"] if max_attempts_row else 1

        can_retry = attempt_number < max_attempts
        attempts_remaining = max(0, max_attempts - attempt_number)

        conn.commit()
        conn.close()

        return {
            "submitted": True,
            "timestamp": "now",
            "results": results,
            "total_score": weighted_score,
            "total_points_earned": total_points_earned,
            "total_points_possible": total_points_possible,
            "problems_correct": problems_correct,
            "problems_total": problems_total,
            "can_retry": can_retry,
            "attempts_remaining": attempts_remaining
        }

    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
