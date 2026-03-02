"""Assignment and problem retrieval endpoints."""

import json
from fastapi import APIRouter, HTTPException
from autota.web.db import get_db_connection

router = APIRouter()


@router.get("/assignment/{student_id}")
async def get_assignment(student_id: str):
    """Get assignment data for a student including their assigned variants."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get student info
    cursor.execute("SELECT id, name FROM students WHERE id = ?", (student_id,))
    student_row = cursor.fetchone()
    if not student_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")

    student_data = dict(student_row)

    # Get student's latest attempt info
    cursor.execute(
        """SELECT id, attempt_number, status, started_at, submitted_at
           FROM attempts
           WHERE student_id = ? AND assignment_id = ?
           ORDER BY attempt_number DESC LIMIT 1""",
        (student_id, "hw5")
    )
    attempt_row = cursor.fetchone()
    if attempt_row:
        attempt_id = attempt_row["id"]
        attempt_number = attempt_row["attempt_number"]
        attempt_status = attempt_row["status"]
    else:
        attempt_id = None
        attempt_number = 1
        attempt_status = "not_started"

    # Get assignment info (including new fields)
    cursor.execute(
        """SELECT id, title, course, instructions, max_attempts, type,
                  time_limit_minutes, opens_at, closes_at
           FROM assignments WHERE id = ?""",
        ("hw5",)
    )
    assignment_row = cursor.fetchone()
    if not assignment_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment_dict = dict(assignment_row)
    assignment_dict["instructions"] = json.loads(assignment_dict["instructions"])
    assignment_dict["course_name"] = "Logic Design of Digital Systems"
    assignment_dict["quarter"] = "Spring 2026"
    assignment_dict["instructor"] = "Prof. Mani Srivastava"
    assignment_dict["max_attempts"] = assignment_dict.get("max_attempts", 1)

    # Get all problems for the assignment (including new fields)
    cursor.execute(
        """SELECT id, parent_label, sub_label, display_order, text, hint,
                  answer_format, placeholder, problem_type, points
           FROM problems
           WHERE assignment_id = ?
           ORDER BY display_order""",
        ("hw5",)
    )
    problem_rows = cursor.fetchall()

    problems = []
    for row in problem_rows:
        problem = dict(row)

        # Get variant assignment for this problem and student
        cursor.execute(
            """SELECT variant_json FROM variant_assignments
               WHERE student_id = ? AND problem_id = ? AND attempt_number = ?""",
            (student_id, problem["id"], attempt_number)
        )
        variant_row = cursor.fetchone()

        if variant_row:
            # Parse variant JSON
            variant_data = json.loads(variant_row["variant_json"])
            # Add minterms and don't_cares to problem
            params = variant_data.get("parameters", {})
            minterms = params.get("minterms", [])
            dont_cares = params.get("dont_cares", [])

            if minterms:
                problem["minterms"] = "m(" + ", ".join(map(str, sorted(minterms))) + ")"
            else:
                problem["minterms"] = None

            if dont_cares:
                problem["dont_cares"] = "d(" + ", ".join(map(str, sorted(dont_cares))) + ")"
            else:
                problem["dont_cares"] = None
        else:
            problem["minterms"] = None
            problem["dont_cares"] = None

        problems.append(problem)

    # Get existing answers (from submissions table - last saved answer for each problem)
    cursor.execute(
        """SELECT problem_id, answer FROM submissions
           WHERE student_id = ? AND variant_assignment_id IN (
               SELECT id FROM variant_assignments
               WHERE student_id = ? AND attempt_number = ?
           )
           ORDER BY submitted_at DESC""",
        (student_id, student_id, attempt_number)
    )
    submission_rows = cursor.fetchall()

    existing_answers = {}
    seen_problems = set()
    for row in submission_rows:
        problem_id = row["problem_id"]
        if problem_id not in seen_problems:
            existing_answers[problem_id] = row["answer"]
            seen_problems.add(problem_id)

    # Fill in empty answers for problems without submissions
    for problem in problems:
        if problem["id"] not in existing_answers:
            existing_answers[problem["id"]] = ""

    # Calculate can_retry and attempts_remaining
    max_attempts = assignment_dict.get("max_attempts", 1)
    can_retry = (attempt_status in ["graded", "submitted"]) and (attempt_number < max_attempts)
    attempts_remaining = max(0, max_attempts - attempt_number)

    conn.close()

    return {
        "assignment": assignment_dict,
        "student": {
            "id": student_data["id"],
            "name": student_data["name"],
            "attempt_number": attempt_number
        },
        "attempt": {
            "id": attempt_id,
            "attempt_number": attempt_number,
            "status": attempt_status
        },
        "problems": problems,
        "existing_answers": existing_answers,
        "can_retry": can_retry,
        "attempts_remaining": attempts_remaining
    }
