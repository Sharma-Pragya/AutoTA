"""Quiz mode API endpoints — Phase 2.3.

Student endpoints:  POST /api/quiz/{code}/join
                    GET  /api/quiz/{code}/status
                    POST /api/quiz/{code}/submit

Instructor endpoints: POST /api/instructor/quiz/create
                      POST /api/instructor/quiz/{code}/start
                      POST /api/instructor/quiz/{code}/close
                      POST /api/instructor/quiz/{code}/review
                      GET  /api/instructor/quiz/{code}/live
                      GET  /api/instructor/quiz/{code}/results
"""

import json
import random
import string
from datetime import datetime, timezone
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from autota.web.db import db_conn
from autota.web.auth import require_instructor
from autota.verify.registry import get_verifier
from autota.models import ProblemVariant
from uuid import UUID

router = APIRouter(tags=["quiz"])

# ── Helpers ───────────────────────────────────────────────────────────────────

def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _now_dt():
    return datetime.now(timezone.utc)


def _parse_dt(s: Optional[str]):
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        # SQLite stores naive UTC strings; make them timezone-aware for arithmetic
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _seconds_remaining(session: dict) -> Optional[int]:
    """Compute seconds remaining. Returns None if not started, 0 if expired."""
    started_at = _parse_dt(session["started_at"])
    if not started_at:
        return None
    limit = int(session["time_limit_seconds"] or 600)
    elapsed = (_now_dt() - started_at).total_seconds()
    remaining = limit - elapsed
    return max(0, int(remaining))


def _auto_close_if_expired(cursor, session: dict) -> dict:
    """If quiz has started and timer expired, close it automatically."""
    if session["status"] != "active":
        return session
    secs = _seconds_remaining(session)
    if secs is not None and secs <= 0 and session["status"] == "active":
        now = _now_iso()
        cursor.execute(
            "UPDATE quiz_sessions SET status = 'closed', closed_at = ? WHERE id = ?",
            (now, session["id"])
        )
        _write_best_scores_to_grades(cursor, session["id"])
        session = dict(session)
        session["status"] = "closed"
        session["closed_at"] = now
    return session


def _get_session(cursor, code: str) -> dict:
    """Fetch quiz session by code, raising 404 if not found."""
    cursor.execute(
        "SELECT id, assignment_id, code, status, time_limit_seconds, "
        "started_at, closed_at, created_at, created_by "
        "FROM quiz_sessions WHERE code = ?",
        (code.upper(),)
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return dict(row)


def _get_problems(cursor, assignment_id: str) -> list:
    cursor.execute(
        "SELECT id, parent_label, sub_label, display_order, text, points, answer_format "
        "FROM problems WHERE assignment_id = ? ORDER BY display_order",
        (assignment_id,)
    )
    return [dict(r) for r in cursor.fetchall()]


def _draw_variants_for_student(cursor, student_id: str, session_id: int, assignment_id: str) -> dict:
    """Draw one variant per problem from the pool. Returns {problem_id: pool_row_dict}."""
    # Get already-seen variant IDs for this student in this quiz
    cursor.execute(
        "SELECT variant_assignments_json FROM quiz_participants "
        "WHERE quiz_session_id = ? AND student_id = ?",
        (session_id, student_id)
    )
    row = cursor.fetchone()
    if row and row["variant_assignments_json"]:
        # Already drawn — return existing
        return json.loads(row["variant_assignments_json"])

    problems = _get_problems(cursor, assignment_id)
    result = {}
    for p in problems:
        pid = p["id"]
        cursor.execute(
            "SELECT id, problem_id, parameters_json, minterms, dont_cares, solution_json, problem_text "
            "FROM variant_pool WHERE problem_id = ? ORDER BY RANDOM() LIMIT 1",
            (pid,)
        )
        pool_row = cursor.fetchone()
        if pool_row:
            result[pid] = {
                "pool_id": pool_row["id"],
                "minterms": pool_row["minterms"],
                "dont_cares": pool_row["dont_cares"],
                "solution_json": pool_row["solution_json"],
                "problem_text": pool_row["problem_text"],
                "parameters_json": pool_row["parameters_json"],
            }
    return result


def _grade_answer(cursor, assignment_id: str, problem_id: str,
                  answer: str, variant_data: dict) -> dict:
    """Grade a single answer using the BooleanExpressionVerifier pipeline."""
    solution_data = json.loads(variant_data["solution_json"])
    params_data = json.loads(variant_data["parameters_json"])

    # Reconstruct a minimal ProblemVariant for grading
    try:
        variant = ProblemVariant(
            variant_id=UUID(variant_data["pool_id"].replace("-", "").ljust(32, "0")[:32]
                            if len(variant_data["pool_id"]) < 32
                            else variant_data["pool_id"]),
            problem_text=variant_data.get("problem_text", ""),
            parameters={
                "minterms": params_data.get("minterms", []),
                "dont_cares": params_data.get("dont_cares", []),
                "variables": ["A", "B", "C", "D"],
            },
            solution=solution_data,
            answer_format="boolean_expression",
        )
    except Exception:
        # Fallback — try pool_id as-is
        import uuid as _uuid
        variant = ProblemVariant(
            variant_id=_uuid.uuid4(),
            problem_text=variant_data.get("problem_text", ""),
            parameters={
                "minterms": params_data.get("minterms", []),
                "dont_cares": params_data.get("dont_cares", []),
                "variables": ["A", "B", "C", "D"],
            },
            solution=solution_data,
            answer_format="boolean_expression",
        )

    verifier = get_verifier("kmap_simplification")
    result = verifier.grade(variant, answer.strip())
    score = result.partial_credit if result.partial_credit is not None else (1.0 if result.correct else 0.0)
    return {"score": score, "correct": result.correct, "feedback": result.feedback}


def _best_scores_for_student(cursor, quiz_session_id: int, student_id: str) -> dict:
    """Return {problem_id: best_score} from all quiz_submissions for this student."""
    cursor.execute(
        "SELECT scores_json FROM quiz_submissions "
        "WHERE quiz_session_id = ? AND student_id = ? ORDER BY id",
        (quiz_session_id, student_id)
    )
    rows = cursor.fetchall()
    best: Dict[str, dict] = {}
    for row in rows:
        if not row["scores_json"]:
            continue
        scores = json.loads(row["scores_json"])
        for pid, s in scores.items():
            if pid not in best or s["score"] > best[pid]["score"]:
                best[pid] = s
    return best


def _write_best_scores_to_grades(cursor, quiz_session_id: int):
    """After quiz closes, copy best quiz scores into attempt/submission/grade tables."""
    cursor.execute(
        "SELECT assignment_id FROM quiz_sessions WHERE id = ?",
        (quiz_session_id,)
    )
    row = cursor.fetchone()
    if not row:
        return
    assignment_id = row["assignment_id"]

    # Find all participants who submitted
    cursor.execute(
        "SELECT DISTINCT student_id FROM quiz_submissions WHERE quiz_session_id = ?",
        (quiz_session_id,)
    )
    student_ids = [r["student_id"] for r in cursor.fetchall()]

    problems = _get_problems(cursor, assignment_id)
    total_pts = sum(p["points"] for p in problems)

    for student_id in student_ids:
        best = _best_scores_for_student(cursor, quiz_session_id, student_id)
        if not best:
            continue

        points_earned = sum(
            best.get(p["id"], {}).get("score", 0) * p["points"]
            for p in problems
        )
        weighted_score = points_earned / total_pts if total_pts else 0
        problems_correct = sum(1 for p in problems if best.get(p["id"], {}).get("correct", False))

        # Create or update attempt row
        cursor.execute(
            "SELECT id FROM attempts WHERE student_id = ? AND assignment_id = ? "
            "AND attempt_number = 1",
            (student_id, assignment_id)
        )
        existing_attempt = cursor.fetchone()
        if existing_attempt:
            attempt_id = existing_attempt["id"]
            cursor.execute(
                "UPDATE attempts SET status = 'graded', total_score = ?, "
                "submitted_at = datetime('now'), attestation_signed = 0 WHERE id = ?",
                (round(weighted_score, 4), attempt_id)
            )
        else:
            cursor.execute(
                "INSERT INTO attempts (student_id, assignment_id, attempt_number, status, "
                "total_score, submitted_at, attestation_signed) "
                "VALUES (?, ?, 1, 'graded', ?, datetime('now'), 0)",
                (student_id, assignment_id, round(weighted_score, 4))
            )
            attempt_id = cursor.lastrowid

        # Insert attempt_results (skip if already exists)
        cursor.execute(
            "SELECT id FROM attempt_results WHERE attempt_id = ?", (attempt_id,)
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO attempt_results "
                "(attempt_id, total_score, total_points_earned, total_points_possible, "
                "problems_correct, problems_total) VALUES (?, ?, ?, ?, ?, ?)",
                (attempt_id, round(weighted_score, 4), round(points_earned, 4),
                 total_pts, problems_correct, len(problems))
            )

        # Insert submission + grade per problem
        cursor.execute(
            "SELECT variant_assignments_json FROM quiz_participants "
            "WHERE quiz_session_id = ? AND student_id = ?",
            (quiz_session_id, student_id)
        )
        part_row = cursor.fetchone()
        variant_map = json.loads(part_row["variant_assignments_json"]) if part_row and part_row["variant_assignments_json"] else {}

        for p in problems:
            pid = p["id"]
            score_data = best.get(pid)
            if not score_data:
                continue

            # Ensure a dummy variant_assignment exists
            cursor.execute(
                "SELECT id FROM variant_assignments WHERE student_id = ? AND problem_id = ? AND attempt_number = 1",
                (student_id, pid)
            )
            va_row = cursor.fetchone()
            if not va_row:
                vmap = variant_map.get(pid, {})
                dummy_variant = json.dumps({
                    "variant_id": vmap.get("pool_id", f"quiz-{student_id}-{pid}"),
                    "problem_text": vmap.get("problem_text", p["text"]),
                    "parameters": json.loads(vmap["parameters_json"]) if vmap.get("parameters_json") else {},
                    "answer_format": "boolean_expression",
                })
                dummy_solution = vmap.get("solution_json", json.dumps({"answer": "unknown"}))
                cursor.execute(
                    "INSERT OR IGNORE INTO variant_assignments "
                    "(student_id, problem_id, variant_id, variant_json, solution_json, attempt_number, attempt_id) "
                    "VALUES (?, ?, ?, ?, ?, 1, ?)",
                    (student_id, pid,
                     vmap.get("pool_id", f"quiz-{student_id}-{pid}"),
                     dummy_variant, dummy_solution, attempt_id)
                )
                cursor.execute(
                    "SELECT id FROM variant_assignments WHERE student_id = ? AND problem_id = ? AND attempt_number = 1",
                    (student_id, pid)
                )
                va_row = cursor.fetchone()

            va_id = va_row["id"] if va_row else None
            if not va_id:
                continue

            # Get best answer text from submissions
            cursor.execute(
                "SELECT answers_json, scores_json FROM quiz_submissions "
                "WHERE quiz_session_id = ? AND student_id = ? ORDER BY id",
                (quiz_session_id, student_id)
            )
            best_answer = ""
            for sub_row in cursor.fetchall():
                ans_map = json.loads(sub_row["answers_json"])
                if pid in ans_map:
                    sc = json.loads(sub_row["scores_json"] or "{}").get(pid, {})
                    if sc.get("score", 0) >= score_data["score"]:
                        best_answer = ans_map[pid]
                        break

            cursor.execute(
                "INSERT OR IGNORE INTO submissions "
                "(student_id, problem_id, variant_assignment_id, answer, score, correct, feedback, graded_at, attestation_signed) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), 0)",
                (student_id, pid, va_id, best_answer,
                 round(score_data["score"], 4),
                 1 if score_data["correct"] else 0,
                 score_data.get("feedback", ""))
            )
            sub_id = cursor.lastrowid
            if sub_id:
                cursor.execute(
                    "INSERT OR IGNORE INTO grades "
                    "(submission_id, score, correct, feedback, grading_tier, grading_status, graded_by) "
                    "VALUES (?, ?, ?, ?, 'deterministic', 'graded', 'quiz_auto')",
                    (sub_id, round(score_data["score"], 4),
                     1 if score_data["correct"] else 0,
                     score_data.get("feedback", ""))
                )


# ── Pydantic models ───────────────────────────────────────────────────────────

class JoinRequest(BaseModel):
    student_id: str


class SubmitRequest(BaseModel):
    student_id: str
    answers: Dict[str, str]


class CreateQuizRequest(BaseModel):
    assignment_id: str
    time_limit_seconds: int = 600


# ── Student endpoints ─────────────────────────────────────────────────────────

@router.post("/api/quiz/{code}/join")
async def join_quiz(code: str, request: JoinRequest):
    with db_conn() as conn:
        cursor = conn.cursor()
        session = _get_session(cursor, code)
        session = _auto_close_if_expired(cursor, session)

        if session["status"] in ("closed", "review"):
            raise HTTPException(status_code=403, detail="Quiz is closed")

        student_id = request.student_id

        # Draw variants (idempotent)
        variant_map = _draw_variants_for_student(cursor, student_id, session["id"], session["assignment_id"])

        # Record participant
        cursor.execute(
            "INSERT OR IGNORE INTO quiz_participants (quiz_session_id, student_id, variant_assignments_json) "
            "VALUES (?, ?, ?)",
            (session["id"], student_id, json.dumps(variant_map))
        )
        if cursor.rowcount == 0:
            cursor.execute(
                "UPDATE quiz_participants SET variant_assignments_json = ? "
                "WHERE quiz_session_id = ? AND student_id = ? AND variant_assignments_json IS NULL",
                (json.dumps(variant_map), session["id"], student_id)
            )
        conn.commit()

        problems = _get_problems(cursor, session["assignment_id"])
        problems_out = []
        for p in problems:
            vdata = variant_map.get(p["id"], {})
            problems_out.append({
                "id": p["id"],
                "label": f"Q{p['parent_label']}",
                "points": p["points"],
                "text": p["text"],
                "minterms": vdata.get("minterms"),
                "dont_cares": vdata.get("dont_cares"),
                "answer_format": p["answer_format"],
                "placeholder": "e.g. A'B + CD'",
            })

        secs_remaining = _seconds_remaining(session)
        best = _best_scores_for_student(cursor, session["id"], student_id)
        return {
            "quiz_session_id": session["id"],
            "status": session["status"],
            "quiz_title": None,
            "time_remaining_seconds": secs_remaining,
            "problems": problems_out,
            "best_scores": {pid: s["score"] for pid, s in best.items()},
        }


@router.get("/api/quiz/{code}/status")
async def quiz_status(code: str):
    with db_conn() as conn:
        cursor = conn.cursor()
        session = _get_session(cursor, code)
        session = _auto_close_if_expired(cursor, session)
        conn.commit()
        return {
            "status": session["status"],
            "time_remaining_seconds": _seconds_remaining(session),
        }


@router.post("/api/quiz/{code}/submit")
async def submit_quiz(code: str, request: SubmitRequest):
    with db_conn() as conn:
        cursor = conn.cursor()
        session = _get_session(cursor, code)
        session = _auto_close_if_expired(cursor, session)
        conn.commit()

        if session["status"] != "active":
            raise HTTPException(status_code=403, detail="quiz_closed")

        secs = _seconds_remaining(session)
        if secs is not None and secs <= 0:
            raise HTTPException(status_code=403, detail="quiz_closed")

        student_id = request.student_id

        cursor.execute(
            "SELECT variant_assignments_json FROM quiz_participants "
            "WHERE quiz_session_id = ? AND student_id = ?",
            (session["id"], student_id)
        )
        part_row = cursor.fetchone()
        if not part_row:
            variant_map = _draw_variants_for_student(cursor, student_id, session["id"], session["assignment_id"])
            cursor.execute(
                "INSERT OR IGNORE INTO quiz_participants (quiz_session_id, student_id, variant_assignments_json) "
                "VALUES (?, ?, ?)",
                (session["id"], student_id, json.dumps(variant_map))
            )
        else:
            variant_map = json.loads(part_row["variant_assignments_json"] or "{}")

        problems = _get_problems(cursor, session["assignment_id"])
        scores = {}
        total_pts = sum(p["points"] for p in problems)
        total_earned = 0.0

        for p in problems:
            pid = p["id"]
            answer = request.answers.get(pid, "").strip()
            if not answer:
                scores[pid] = {"score": 0.0, "correct": False, "feedback": "No answer submitted."}
                continue
            vdata = variant_map.get(pid)
            if not vdata:
                scores[pid] = {"score": 0.0, "correct": False, "feedback": "No variant found."}
                continue
            grade = _grade_answer(cursor, session["assignment_id"], pid, answer, vdata)
            scores[pid] = grade
            total_earned += grade["score"] * p["points"]

        total_score = total_earned / total_pts if total_pts else 0.0

        cursor.execute(
            "SELECT COALESCE(MAX(attempt_number), 0) FROM quiz_submissions "
            "WHERE quiz_session_id = ? AND student_id = ?",
            (session["id"], student_id)
        )
        attempt_number = cursor.fetchone()[0] + 1

        # Compute per-problem best (merging previous attempts with current)
        prev_best = _best_scores_for_student(cursor, session["id"], student_id)
        new_best_per_problem: Dict[str, dict] = {}
        for p in problems:
            pid = p["id"]
            this_score = scores.get(pid, {}).get("score", 0.0)
            prev = prev_best.get(pid, {}).get("score", 0.0)
            new_best_per_problem[pid] = scores[pid] if this_score >= prev else prev_best[pid]

        best_total_earned = sum(
            new_best_per_problem.get(p["id"], {}).get("score", 0.0) * p["points"]
            for p in problems
        )
        best_total_score = best_total_earned / total_pts if total_pts else 0.0

        # is_best: mark previous submissions not-best, then set correctly below
        cursor.execute(
            "UPDATE quiz_submissions SET is_best = 0 WHERE quiz_session_id = ? AND student_id = ?",
            (session["id"], student_id)
        )

        now = _now_iso()
        # is_best = 1 only if this attempt's total equals the new best total
        is_best = 1 if round(total_score, 4) >= round(best_total_score, 4) else 0
        cursor.execute(
            "INSERT INTO quiz_submissions "
            "(quiz_session_id, student_id, attempt_number, answers_json, scores_json, "
            "total_score, total_points_earned, is_best, submitted_at, graded_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (session["id"], student_id, attempt_number,
             json.dumps(request.answers), json.dumps(scores),
             round(total_score, 4), round(total_earned, 4), is_best, now, now)
        )
        conn.commit()

        return {
            "attempt_number": attempt_number,
            "scores": scores,
            "total_score": round(total_score, 4),
            "best_scores": {pid: s["score"] for pid, s in new_best_per_problem.items()},
            "best_score_details": new_best_per_problem,
            "best_total_score": round(best_total_score, 4),
            "time_remaining_seconds": secs,
        }


# ── Instructor endpoints ──────────────────────────────────────────────────────

@router.post("/api/instructor/quiz/create", dependencies=[Depends(require_instructor)])
async def create_quiz(request: CreateQuizRequest):
    with db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM assignments WHERE id = ?", (request.assignment_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Assignment not found")

        for _ in range(20):
            code = "QZ" + "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
            cursor.execute("SELECT id FROM quiz_sessions WHERE code = ?", (code,))
            if not cursor.fetchone():
                break

        cursor.execute(
            "INSERT INTO quiz_sessions (assignment_id, code, status, time_limit_seconds, created_at) "
            "VALUES (?, ?, 'pending', ?, datetime('now'))",
            (request.assignment_id, code, request.time_limit_seconds)
        )
        quiz_id = cursor.lastrowid
        conn.commit()
        return {"quiz_session_id": quiz_id, "code": code, "status": "pending"}


@router.post("/api/instructor/quiz/{code}/start", dependencies=[Depends(require_instructor)])
async def start_quiz(code: str):
    with db_conn() as conn:
        cursor = conn.cursor()
        session = _get_session(cursor, code)
        if session["status"] != "pending":
            raise HTTPException(status_code=400, detail=f"Cannot start: status is {session['status']}")
        now = _now_iso()
        cursor.execute(
            "UPDATE quiz_sessions SET status = 'active', started_at = ? WHERE id = ?",
            (now, session["id"])
        )
        conn.commit()
        from datetime import timedelta
        limit = int(session["time_limit_seconds"] or 600)
        expires_at = (datetime.fromisoformat(now.replace("Z", "+00:00")) + timedelta(seconds=limit)).strftime("%Y-%m-%dT%H:%M:%SZ")
        return {"status": "active", "started_at": now, "expires_at": expires_at}


@router.post("/api/instructor/quiz/{code}/close", dependencies=[Depends(require_instructor)])
async def close_quiz(code: str):
    with db_conn() as conn:
        cursor = conn.cursor()
        session = _get_session(cursor, code)
        if session["status"] not in ("active", "pending"):
            raise HTTPException(status_code=400, detail=f"Cannot close: status is {session['status']}")
        now = _now_iso()
        cursor.execute(
            "UPDATE quiz_sessions SET status = 'closed', closed_at = ? WHERE id = ?",
            (now, session["id"])
        )
        _write_best_scores_to_grades(cursor, session["id"])
        conn.commit()
        return {"status": "closed", "closed_at": now}


@router.post("/api/instructor/quiz/{code}/review", dependencies=[Depends(require_instructor)])
async def set_review(code: str):
    with db_conn() as conn:
        cursor = conn.cursor()
        session = _get_session(cursor, code)
        if session["status"] != "closed":
            raise HTTPException(status_code=400, detail="Quiz must be closed before review")
        cursor.execute(
            "UPDATE quiz_sessions SET status = 'review' WHERE id = ?",
            (session["id"],)
        )
        conn.commit()
        return {"status": "review"}


@router.get("/api/instructor/quiz/{code}/live", dependencies=[Depends(require_instructor)])
async def get_live_stats(code: str):
    with db_conn() as conn:
        cursor = conn.cursor()
        session = _get_session(cursor, code)
        session = _auto_close_if_expired(cursor, session)
        conn.commit()

        quiz_id = session["id"]
        secs = _seconds_remaining(session)

        # Total enrolled in the course offering
        cursor.execute(
            "SELECT COUNT(*) FROM students"
        )
        total_enrolled = cursor.fetchone()[0]

        # Participants who submitted
        cursor.execute(
            "SELECT COUNT(DISTINCT student_id) FROM quiz_submissions WHERE quiz_session_id = ?",
            (quiz_id,)
        )
        submitted_count = cursor.fetchone()[0]

        # Total submission rows (for retry count)
        cursor.execute(
            "SELECT COUNT(*) FROM quiz_submissions WHERE quiz_session_id = ?",
            (quiz_id,)
        )
        total_submissions = cursor.fetchone()[0]
        retry_count = max(0, total_submissions - submitted_count)

        # Avg best score and avg first score
        cursor.execute(
            "SELECT student_id, MIN(attempt_number) as first_num "
            "FROM quiz_submissions WHERE quiz_session_id = ? GROUP BY student_id",
            (quiz_id,)
        )
        first_rows = {r["student_id"]: r["first_num"] for r in cursor.fetchall()}

        cursor.execute(
            "SELECT student_id, attempt_number, total_score FROM quiz_submissions "
            "WHERE quiz_session_id = ? ORDER BY student_id, attempt_number",
            (quiz_id,)
        )
        all_subs = cursor.fetchall()

        best_by_student: Dict[str, float] = {}
        first_by_student: Dict[str, float] = {}
        for row in all_subs:
            sid = row["student_id"]
            sc = row["total_score"] or 0.0
            if sid not in best_by_student or sc > best_by_student[sid]:
                best_by_student[sid] = sc
            if row["attempt_number"] == first_rows.get(sid):
                first_by_student[sid] = sc

        avg_best = sum(best_by_student.values()) / len(best_by_student) if best_by_student else 0
        avg_first = sum(first_by_student.values()) / len(first_by_student) if first_by_student else 0

        # Score distribution (best scores, 10 bins)
        dist = [0] * 10
        for sc in best_by_student.values():
            dist[min(9, int(sc * 10))] += 1

        # Recent submissions (last 15)
        cursor.execute(
            "SELECT qs.student_id, s.name, qs.total_score, qs.attempt_number, qs.submitted_at "
            "FROM quiz_submissions qs "
            "LEFT JOIN students s ON s.id = qs.student_id "
            "WHERE qs.quiz_session_id = ? "
            "ORDER BY qs.submitted_at DESC LIMIT 15",
            (quiz_id,)
        )
        recent = []
        for r in cursor.fetchall():
            is_retry = (r["attempt_number"] or 1) > 1
            recent.append({
                "name": r["name"] or r["student_id"],
                "score": round(r["total_score"] or 0, 3),
                "is_retry": is_retry,
                "submitted_at": r["submitted_at"],
            })

        # Students who haven't submitted
        submitted_ids = set(best_by_student.keys())
        cursor.execute("SELECT id, name FROM students")
        not_submitted = [
            {"name": r["name"], "uid": r["id"]}
            for r in cursor.fetchall()
            if r["id"] not in submitted_ids
        ]

        return {
            "status": session["status"],
            "time_remaining_seconds": secs,
            "total_enrolled": total_enrolled,
            "submitted_count": submitted_count,
            "retry_count": retry_count,
            "not_submitted_count": total_enrolled - submitted_count,
            "avg_best_score": round(avg_best, 3),
            "avg_first_score": round(avg_first, 3),
            "score_distribution": dist,
            "recent_submissions": recent,
            "not_submitted": not_submitted[:50],
        }


@router.get("/api/instructor/quiz/{code}/results", dependencies=[Depends(require_instructor)])
async def get_results(code: str):
    with db_conn() as conn:
        cursor = conn.cursor()
        session = _get_session(cursor, code)
        session = _auto_close_if_expired(cursor, session)
        conn.commit()
        quiz_id = session["id"]

        # Aggregate stats
        cursor.execute(
            "SELECT student_id, total_score, attempt_number FROM quiz_submissions "
            "WHERE quiz_session_id = ? ORDER BY student_id, attempt_number",
            (quiz_id,)
        )
        all_subs = cursor.fetchall()
        best_by_student: Dict[str, float] = {}
        first_by_student: Dict[str, float] = {}
        for row in all_subs:
            sid = row["student_id"]
            sc = row["total_score"] or 0.0
            if sid not in best_by_student or sc > best_by_student[sid]:
                best_by_student[sid] = sc
            if sid not in first_by_student:
                first_by_student[sid] = sc

        submitted_count = len(best_by_student)
        avg_best = sum(best_by_student.values()) / submitted_count if submitted_count else 0
        avg_first = sum(first_by_student.values()) / submitted_count if submitted_count else 0
        sorted_best = sorted(best_by_student.values())
        n = len(sorted_best)
        median_best = (sorted_best[n // 2 - 1] + sorted_best[n // 2]) / 2 if n % 2 == 0 and n > 0 else (sorted_best[n // 2] if n > 0 else 0)

        retry_students = {sid for sid, cnt in
                         [(r["student_id"], r["attempt_number"]) for r in all_subs if r["attempt_number"] > 1]}
        retry_count = len(retry_students)
        improved = sum(1 for sid in retry_students if best_by_student.get(sid, 0) > first_by_student.get(sid, 0))
        improvement_rate = improved / retry_count if retry_count else 0

        # Per-problem breakdown
        problems = _get_problems(cursor, session["assignment_id"])
        problems_out = []

        for p in problems:
            pid = p["id"]

            # All answers for this problem across all submissions
            cursor.execute(
                "SELECT qs.answers_json, qs.scores_json, qs.student_id "
                "FROM quiz_submissions qs WHERE qs.quiz_session_id = ?",
                (quiz_id,)
            )
            sub_rows = cursor.fetchall()

            correct_count = 0
            all_answers = []
            best_answer_per_student: Dict[str, dict] = {}

            for row in sub_rows:
                ans_map = json.loads(row["answers_json"])
                sc_map = json.loads(row["scores_json"] or "{}")
                if pid not in ans_map:
                    continue
                answer = ans_map[pid]
                score_info = sc_map.get(pid, {})
                score = score_info.get("score", 0.0)
                sid = row["student_id"]
                if sid not in best_answer_per_student or score > best_answer_per_student[sid]["score"]:
                    best_answer_per_student[sid] = {"answer": answer, "score": score, "correct": score_info.get("correct", False)}

            for sid, info in best_answer_per_student.items():
                if info["correct"]:
                    correct_count += 1
                all_answers.append(info["answer"])

            # Common wrong answers
            wrong = {}
            for sid, info in best_answer_per_student.items():
                if not info["correct"] and info["answer"]:
                    wrong[info["answer"]] = wrong.get(info["answer"], 0) + 1
            common_errors = sorted([{"answer": a, "count": c} for a, c in wrong.items()],
                                   key=lambda x: -x["count"])[:5]

            # Get correct answer from variant pool (use first participant's variant)
            cursor.execute(
                "SELECT variant_assignments_json FROM quiz_participants "
                "WHERE quiz_session_id = ? LIMIT 1",
                (quiz_id,)
            )
            part = cursor.fetchone()
            correct_answer = None
            minterms = None
            dont_cares = None
            if part and part["variant_assignments_json"]:
                vmap = json.loads(part["variant_assignments_json"])
                vdata = vmap.get(pid, {})
                minterms = vdata.get("minterms")
                dont_cares = vdata.get("dont_cares")
                sol = json.loads(vdata.get("solution_json", "{}"))
                correct_answer = sol.get("simplified_expression") or sol.get("expression") or str(sol)

            problems_out.append({
                "id": pid,
                "label": f"Q{p['parent_label']}",
                "points": p["points"],
                "text": p["text"],
                "minterms": minterms,
                "dont_cares": dont_cares,
                "correct_answer": correct_answer,
                "pct_correct": round(correct_count / submitted_count, 3) if submitted_count else 0,
                "correct_count": correct_count,
                "common_errors": common_errors,
            })

        return {
            "status": session["status"],
            "submitted_count": submitted_count,
            "avg_best_score": round(avg_best, 3),
            "avg_first_score": round(avg_first, 3),
            "median_best_score": round(median_best, 3),
            "retry_count": retry_count,
            "improvement_rate": round(improvement_rate, 3),
            "problems": problems_out,
        }


@router.get("/api/instructor/quiz/{code}/meta", dependencies=[Depends(require_instructor)])
async def get_quiz_meta(code: str):
    """Returns quiz metadata for the instructor pending/control screen."""
    with db_conn() as conn:
        cursor = conn.cursor()
        session = _get_session(cursor, code)
        session = _auto_close_if_expired(cursor, session)
        conn.commit()

        cursor.execute(
            "SELECT id, title, type FROM assignments WHERE id = ?",
            (session["assignment_id"],)
        )
        asgn = cursor.fetchone()
        problems = _get_problems(cursor, session["assignment_id"])
        total_enrolled = cursor.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        secs = _seconds_remaining(session)

        return {
            "quiz_session_id": session["id"],
            "code": session["code"],
            "status": session["status"],
            "assignment_id": session["assignment_id"],
            "assignment_title": asgn["title"] if asgn else session["assignment_id"],
            "time_limit_seconds": session["time_limit_seconds"],
            "time_remaining_seconds": secs,
            "started_at": session["started_at"],
            "closed_at": session["closed_at"],
            "problem_count": len(problems),
            "total_pts": sum(p["points"] for p in problems),
            "total_enrolled": total_enrolled,
        }
