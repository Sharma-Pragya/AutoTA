"""Instructor dashboard API endpoints."""

import json
import math
from fastapi import APIRouter, HTTPException
from autota.web.db import get_db_connection

router = APIRouter(prefix="/api/instructor", tags=["instructor"])


def _mean(values):
    return sum(values) / len(values) if values else 0.0


def _median(values):
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2.0


def _stdev(values):
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / len(values))


def _get_assignment_stats(cursor, assignment_id, total_students):
    """Compute stats for one assignment."""
    cursor.execute("""
        SELECT ar.total_score, ar.total_points_earned, ar.total_points_possible,
               ar.problems_correct, ar.problems_total,
               a.attempt_number, a.submitted_at
        FROM attempt_results ar
        JOIN attempts a ON a.id = ar.attempt_id
        WHERE a.assignment_id = ? AND a.status = 'graded'
          AND a.attempt_number = (
              SELECT MIN(a2.attempt_number)
              FROM attempts a2
              WHERE a2.student_id = a.student_id
                AND a2.assignment_id = a.assignment_id
                AND a2.status = 'graded'
          )
    """, (assignment_id,))
    rows = cursor.fetchall()
    scores = [r["total_score"] for r in rows]
    submitted = len(rows)

    return {
        "submitted": submitted,
        "not_submitted": total_students - submitted,
        "submission_rate": round(submitted / total_students, 3) if total_students else 0,
        "mean": round(_mean(scores), 3),
        "median": round(_median(scores), 3),
        "min": round(min(scores), 3) if scores else 0,
        "max": round(max(scores), 3) if scores else 0,
        "stdev": round(_stdev(scores), 3),
    }


def _get_problem_stats(cursor, assignment_id):
    """Per-problem correctness % and averages."""
    cursor.execute("""
        SELECT p.id, p.parent_label, p.sub_label, p.points,
               COUNT(s.id) as attempts,
               SUM(s.correct) as correct_count,
               AVG(s.score) as avg_score
        FROM problems p
        LEFT JOIN submissions s ON s.problem_id = p.id
        WHERE p.assignment_id = ?
        GROUP BY p.id
        ORDER BY p.display_order
    """, (assignment_id,))
    rows = cursor.fetchall()
    result = []
    for r in rows:
        label = f"Q{r['parent_label']}"
        if r["sub_label"]:
            label += r["sub_label"]
        attempts = r["attempts"] or 0
        correct = r["correct_count"] or 0
        result.append({
            "id": r["id"],
            "label": label,
            "points": r["points"],
            "attempts": attempts,
            "correct_count": correct,
            "correctness_pct": round(correct / attempts, 3) if attempts else 0,
            "avg_score": round(r["avg_score"] or 0, 3),
        })
    return result


@router.get("/dashboard")
async def get_dashboard():
    """Main instructor dashboard: summary cards, all assignments overview."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Course info
    cursor.execute("""
        SELECT co.id, co.quarter, co.year, c.name as course_name
        FROM course_offerings co JOIN courses c ON c.id = co.course_id
        LIMIT 1
    """)
    offering = cursor.fetchone()

    # Section counts
    cursor.execute("""
        SELECT s.label, COUNT(e.student_id) as cnt
        FROM sections s
        JOIN enrollments e ON e.section_id = s.id
        WHERE e.dropped = 0
        GROUP BY s.label
    """)
    sections = [dict(r) for r in cursor.fetchall()]
    total_enrolled = sum(s["cnt"] for s in sections)

    # All assignments
    cursor.execute("""
        SELECT id, title, type, is_active, max_attempts, closes_at,
               (SELECT COALESCE(SUM(points), 0) FROM problems WHERE assignment_id = assignments.id) as total_pts,
               (SELECT COUNT(*) FROM problems WHERE assignment_id = assignments.id) as problem_count
        FROM assignments
        ORDER BY closes_at
    """)
    assignment_rows = cursor.fetchall()
    assignments_out = []

    for row in assignment_rows:
        stats = _get_assignment_stats(cursor, row["id"], total_enrolled)
        assignments_out.append({
            "id": row["id"],
            "title": row["title"],
            "type": row["type"],
            "is_active": bool(row["is_active"]),
            "max_attempts": row["max_attempts"],
            "closes_at": row["closes_at"],
            "total_pts": row["total_pts"],
            "problem_count": row["problem_count"],
            **stats,
        })

    # Overall class average (across all graded attempts)
    cursor.execute("""
        SELECT AVG(ar.total_score)
        FROM attempt_results ar
        JOIN attempts a ON a.id = ar.attempt_id
        WHERE a.status = 'graded'
    """)
    class_avg_row = cursor.fetchone()
    class_avg = round((class_avg_row[0] or 0) * 100, 1)

    # Category summary
    type_summary = {}
    for asgn in assignments_out:
        t = asgn["type"]
        if t not in type_summary:
            type_summary[t] = {"count": 0, "submitted_total": 0, "scores": []}
        type_summary[t]["count"] += 1
        type_summary[t]["submitted_total"] += asgn["submitted"]
        if asgn["mean"]:
            type_summary[t]["scores"].append(asgn["mean"])

    category_summary = []
    for t, d in type_summary.items():
        category_summary.append({
            "type": t,
            "count": d["count"],
            "submitted_total": d["submitted_total"],
            "avg_score": round(_mean(d["scores"]) * 100, 1) if d["scores"] else 0,
        })

    conn.close()

    return {
        "offering": {
            "course": "ECE M16",
            "course_name": "Logic Design of Digital Systems",
            "quarter": "Spring 2026",
            "instructor": "Prof. Mani Srivastava",
        },
        "sections": sections,
        "total_enrolled": total_enrolled,
        "class_avg_pct": class_avg,
        "assignments": assignments_out,
        "category_summary": category_summary,
    }


@router.get("/gradebook")
async def get_gradebook():
    """Full gradebook: all students × all assignments."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # All students
    cursor.execute("SELECT id, name, email, section FROM students ORDER BY name")
    student_rows = cursor.fetchall()

    # All assignments (ordered)
    cursor.execute("""
        SELECT id, title, type, is_active,
               (SELECT COALESCE(SUM(points), 0) FROM problems WHERE assignment_id = assignments.id) as total_pts
        FROM assignments ORDER BY closes_at
    """)
    assignment_rows = cursor.fetchall()
    assignments_meta = [dict(r) for r in assignment_rows]

    # For each student, get their score per assignment (latest graded attempt)
    students_out = []
    for s in student_rows:
        student_id = s["id"]
        scores = {}
        for a in assignments_meta:
            cursor.execute("""
                SELECT ar.total_score
                FROM attempt_results ar
                JOIN attempts a ON a.id = ar.attempt_id
                WHERE a.student_id = ? AND a.assignment_id = ? AND a.status = 'graded'
                ORDER BY a.attempt_number ASC
                LIMIT 1
            """, (student_id, a["id"]))
            row = cursor.fetchone()
            scores[a["id"]] = round(row["total_score"] * 100, 1) if row else None

        submitted_count = sum(1 for v in scores.values() if v is not None)
        overall = _mean([v for v in scores.values() if v is not None])

        students_out.append({
            "id": student_id,
            "name": s["name"],
            "email": s["email"],
            "section": s["section"],
            "scores": scores,
            "submitted_count": submitted_count,
            "overall_avg": round(overall, 1) if submitted_count else None,
        })

    conn.close()

    return {
        "assignments": assignments_meta,
        "students": students_out,
    }


@router.get("/assignment/{assignment_id}")
async def get_assignment_detail(assignment_id: str):
    """Detailed view for one assignment: stats, problem breakdown, per-student scores."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Assignment meta
    cursor.execute("""
        SELECT id, title, type, is_active, max_attempts, closes_at,
               (SELECT COALESCE(SUM(points), 0) FROM problems WHERE assignment_id = assignments.id) as total_pts
        FROM assignments WHERE id = ?
    """, (assignment_id,))
    asgn_row = cursor.fetchone()
    if not asgn_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Assignment not found")

    total_enrolled = cursor.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    stats = _get_assignment_stats(cursor, assignment_id, total_enrolled)
    problem_stats = _get_problem_stats(cursor, assignment_id)

    # Score distribution (10 bins: 0-10%, 10-20%, ..., 90-100%)
    cursor.execute("""
        SELECT ar.total_score
        FROM attempt_results ar
        JOIN attempts a ON a.id = ar.attempt_id
        WHERE a.assignment_id = ? AND a.status = 'graded'
    """, (assignment_id,))
    score_rows = cursor.fetchall()
    scores = [r["total_score"] for r in score_rows]

    bins = [0] * 10
    for s in scores:
        bucket = min(int(s * 10), 9)
        bins[bucket] += 1

    distribution = [
        {"range": f"{i*10}-{(i+1)*10}%", "count": bins[i]}
        for i in range(10)
    ]

    # Per-student scores for this assignment
    cursor.execute("""
        SELECT s.id, s.name, s.section,
               a.attempt_number, a.status, ar.total_score,
               ar.total_points_earned, ar.total_points_possible,
               ar.problems_correct, ar.problems_total
        FROM students s
        LEFT JOIN attempts a ON a.student_id = s.id AND a.assignment_id = ?
            AND a.status = 'graded'
        LEFT JOIN attempt_results ar ON ar.attempt_id = a.id
        ORDER BY s.name
    """, (assignment_id,))
    student_rows = cursor.fetchall()

    students_out = []
    for r in student_rows:
        # Per-problem scores for this student
        cursor.execute("""
            SELECT sub.problem_id, sub.score, sub.correct
            FROM submissions sub
            JOIN variant_assignments va ON va.id = sub.variant_assignment_id
            JOIN attempts a ON a.student_id = va.student_id AND a.assignment_id = ?
              AND a.status = 'graded'
            WHERE sub.student_id = ?
            ORDER BY sub.problem_id
        """, (assignment_id, r["id"]))
        problem_scores = {row["problem_id"]: {"score": row["score"], "correct": bool(row["correct"])}
                         for row in cursor.fetchall()}

        students_out.append({
            "id": r["id"],
            "name": r["name"],
            "section": r["section"],
            "status": r["status"] or "not_started",
            "attempt_number": r["attempt_number"],
            "total_score": round((r["total_score"] or 0) * 100, 1) if r["total_score"] is not None else None,
            "points_earned": r["total_points_earned"],
            "points_possible": r["total_points_possible"],
            "problems_correct": r["problems_correct"],
            "problems_total": r["problems_total"],
            "problem_scores": problem_scores,
        })

    conn.close()

    return {
        "assignment": {
            "id": asgn_row["id"],
            "title": asgn_row["title"],
            "type": asgn_row["type"],
            "is_active": bool(asgn_row["is_active"]),
            "max_attempts": asgn_row["max_attempts"],
            "closes_at": asgn_row["closes_at"],
            "total_pts": asgn_row["total_pts"],
        },
        "stats": stats,
        "distribution": distribution,
        "problem_stats": problem_stats,
        "students": students_out,
    }


@router.get("/student/{student_id}")
async def get_student_detail(student_id: str):
    """Full breakdown for one student across all assignments."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, email, section FROM students WHERE id = ?", (student_id,))
    student_row = cursor.fetchone()
    if not student_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")

    student = dict(student_row)

    # All assignments with this student's scores
    cursor.execute("""
        SELECT a_meta.id, a_meta.title, a_meta.type, a_meta.total_pts, a_meta.closes_at,
               att.attempt_number, att.status, att.total_score,
               att.submitted_at, ar.problems_correct, ar.problems_total,
               ar.total_points_earned, ar.total_points_possible
        FROM (
            SELECT id, title, type, closes_at,
                   (SELECT COALESCE(SUM(points), 0) FROM problems WHERE assignment_id = assignments.id) as total_pts
            FROM assignments
        ) a_meta
        LEFT JOIN attempts att ON att.assignment_id = a_meta.id
            AND att.student_id = ? AND att.status = 'graded'
        LEFT JOIN attempt_results ar ON ar.attempt_id = att.id
        ORDER BY a_meta.closes_at
    """, (student_id,))

    assignment_rows = cursor.fetchall()
    assignments_out = []
    scores_for_avg = []

    for r in assignment_rows:
        # Per-problem submissions for this student + this assignment
        cursor.execute("""
            SELECT sub.problem_id, p.parent_label, p.sub_label, p.points,
                   sub.answer, sub.score, sub.correct, sub.feedback
            FROM submissions sub
            JOIN problems p ON p.id = sub.problem_id
            WHERE sub.student_id = ? AND p.assignment_id = ?
            ORDER BY p.display_order
        """, (student_id, r["id"]))
        problem_rows = cursor.fetchall()

        problems_out = []
        for pr in problem_rows:
            label = f"Q{pr['parent_label']}"
            if pr["sub_label"]:
                label += pr["sub_label"]
            problems_out.append({
                "id": pr["problem_id"],
                "label": label,
                "points": pr["points"],
                "answer": pr["answer"],
                "score": pr["score"],
                "correct": bool(pr["correct"]),
                "feedback": pr["feedback"],
            })

        total_score_pct = round(r["total_score"] * 100, 1) if r["total_score"] is not None else None
        if total_score_pct is not None:
            scores_for_avg.append(r["total_score"])

        assignments_out.append({
            "id": r["id"],
            "title": r["title"],
            "type": r["type"],
            "total_pts": r["total_pts"],
            "status": r["status"] or "not_started",
            "attempt_number": r["attempt_number"],
            "total_score_pct": total_score_pct,
            "points_earned": r["total_points_earned"],
            "points_possible": r["total_points_possible"],
            "problems_correct": r["problems_correct"],
            "problems_total": r["problems_total"],
            "submitted_at": r["submitted_at"],
            "problems": problems_out,
        })

    overall_avg = round(_mean(scores_for_avg) * 100, 1) if scores_for_avg else None
    submitted_count = sum(1 for a in assignments_out if a["status"] == "graded")

    conn.close()

    return {
        "student": {
            **student,
            "overall_avg": overall_avg,
            "submitted_count": submitted_count,
            "total_assignments": len(assignments_out),
        },
        "assignments": assignments_out,
    }


@router.get("/roster")
async def get_roster():
    """Student roster with enrollment info."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.id, s.name, s.email, s.section,
               COUNT(DISTINCT a.assignment_id) as submitted_count
        FROM students s
        LEFT JOIN attempts a ON a.student_id = s.id AND a.status = 'graded'
        GROUP BY s.id
        ORDER BY s.section, s.name
    """)
    rows = cursor.fetchall()
    total_assignments = cursor.execute("SELECT COUNT(*) FROM assignments").fetchone()[0]
    conn.close()

    return {
        "students": [
            {
                "id": r["id"],
                "name": r["name"],
                "email": r["email"],
                "section": r["section"],
                "submitted_count": r["submitted_count"],
                "total_assignments": total_assignments,
            }
            for r in rows
        ],
        "total_enrolled": len(rows),
    }
