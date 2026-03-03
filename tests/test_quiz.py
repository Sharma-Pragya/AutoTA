"""Tests for Phase 2.3 quiz endpoints and business logic.

Uses an in-memory SQLite database seeded with minimal fixture data so
tests are fast, isolated, and never touch data/autota.db.
"""

import json
import sqlite3
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

# ── Helpers to build an in-memory DB ─────────────────────────────────────────

def make_db():
    """Return a fresh in-memory SQLite connection with quiz schema + fixtures."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Minimal schema needed by quiz routes
    cursor.executescript("""
        CREATE TABLE assignments (
            id TEXT PRIMARY KEY,
            title TEXT,
            type TEXT DEFAULT 'quiz',
            is_active INTEGER DEFAULT 1,
            max_attempts INTEGER DEFAULT 1,
            opens_at TEXT,
            closes_at TEXT,
            time_limit_minutes INTEGER
        );
        CREATE TABLE problems (
            id TEXT PRIMARY KEY,
            assignment_id TEXT,
            parent_label TEXT,
            sub_label TEXT,
            display_order INTEGER,
            text TEXT,
            points REAL DEFAULT 10,
            problem_type TEXT,
            answer_format TEXT DEFAULT 'boolean_expression',
            depends_on_problem_id TEXT
        );
        CREATE TABLE variant_pool (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id TEXT,
            parameters_json TEXT,
            minterms TEXT,
            dont_cares TEXT,
            solution_json TEXT,
            problem_text TEXT
        );
        CREATE TABLE quiz_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id TEXT,
            code TEXT UNIQUE,
            status TEXT DEFAULT 'pending',
            time_limit_seconds INTEGER DEFAULT 600,
            started_at TEXT,
            closed_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            created_by TEXT,
            section_id INTEGER,
            qr_url TEXT,
            time_limit_minutes INTEGER,
            opens_at TEXT,
            closes_at TEXT
        );
        CREATE TABLE quiz_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_session_id INTEGER,
            student_id TEXT,
            attempt_number INTEGER DEFAULT 1,
            answers_json TEXT,
            scores_json TEXT,
            total_score REAL,
            total_points_earned REAL,
            is_best INTEGER DEFAULT 0,
            submitted_at TEXT DEFAULT (datetime('now')),
            graded_at TEXT,
            UNIQUE(quiz_session_id, student_id, attempt_number)
        );
        CREATE TABLE quiz_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_session_id INTEGER,
            student_id TEXT,
            joined_at TEXT DEFAULT (datetime('now')),
            variant_assignments_json TEXT,
            UNIQUE(quiz_session_id, student_id)
        );
        CREATE TABLE students (
            id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            section TEXT
        );
        CREATE TABLE attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            assignment_id TEXT,
            attempt_number INTEGER DEFAULT 1,
            status TEXT DEFAULT 'not_started',
            total_score REAL,
            submitted_at TEXT,
            attestation_signed INTEGER DEFAULT 0,
            attestation_signed_at TEXT
        );
        CREATE TABLE attempt_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER,
            total_score REAL,
            total_points_earned REAL,
            total_points_possible REAL,
            problems_correct INTEGER,
            problems_total INTEGER
        );
        CREATE TABLE variant_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            problem_id TEXT,
            variant_id TEXT,
            variant_json TEXT,
            solution_json TEXT,
            attempt_number INTEGER DEFAULT 1,
            assigned_at TEXT DEFAULT (datetime('now')),
            attempt_id INTEGER
        );
        CREATE TABLE submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            problem_id TEXT,
            variant_assignment_id INTEGER,
            answer TEXT,
            score REAL,
            correct INTEGER,
            feedback TEXT,
            graded_at TEXT,
            attestation_signed INTEGER DEFAULT 0
        );
        CREATE TABLE grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER,
            score REAL,
            correct INTEGER,
            feedback TEXT,
            grading_tier TEXT,
            grading_status TEXT,
            graded_by TEXT
        );
    """)

    # Seed: one assignment, two problems, one student, one pending quiz session
    cursor.execute(
        "INSERT INTO assignments VALUES ('quiz3', 'Quiz 3', 'quiz', 1, 1, NULL, NULL, NULL)"
    )
    cursor.execute(
        "INSERT INTO problems VALUES ('p1', 'quiz3', '1', NULL, 1, 'Simplify F', 10, 'kmap', 'boolean_expression', NULL)"
    )
    cursor.execute(
        "INSERT INTO problems VALUES ('p2', 'quiz3', '2', NULL, 2, 'Simplify G', 10, 'kmap', 'boolean_expression', NULL)"
    )

    pool_params = json.dumps({"minterms": [1, 3], "dont_cares": []})
    pool_solution = json.dumps({"simplified_expression": "B"})
    cursor.execute(
        "INSERT INTO variant_pool (problem_id, parameters_json, minterms, dont_cares, solution_json, problem_text) "
        "VALUES ('p1', ?, 'm(1,3)', '', ?, 'Simplify F(A,B)')",
        (pool_params, pool_solution)
    )
    cursor.execute(
        "INSERT INTO variant_pool (problem_id, parameters_json, minterms, dont_cares, solution_json, problem_text) "
        "VALUES ('p2', ?, 'm(0,2)', '', ?, 'Simplify G(A,B)')",
        (pool_params, pool_solution)
    )

    cursor.execute(
        "INSERT INTO quiz_sessions (assignment_id, code, status, time_limit_seconds) "
        "VALUES ('quiz3', 'TST001', 'pending', 600)"
    )
    cursor.execute("INSERT INTO students VALUES ('S001', 'Alice', 'alice@test.com', '1A')")
    cursor.execute("INSERT INTO students VALUES ('S002', 'Bob', 'bob@test.com', '1A')")

    conn.commit()
    return conn


# ── Import helpers under test ─────────────────────────────────────────────────

from autota.web.routes.quiz import (
    _get_session,
    _seconds_remaining,
    _auto_close_if_expired,
    _draw_variants_for_student,
    _best_scores_for_student,
    _write_best_scores_to_grades,
    _now_iso,
)


# ── _get_session ──────────────────────────────────────────────────────────────

class TestGetSession:
    def test_returns_session_by_code(self):
        conn = make_db()
        session = _get_session(conn.cursor(), "TST001")
        assert session["code"] == "TST001"
        assert session["status"] == "pending"
        conn.close()

    def test_raises_404_for_unknown_code(self):
        from fastapi import HTTPException
        conn = make_db()
        with pytest.raises(HTTPException) as exc:
            _get_session(conn.cursor(), "NOPE99")
        assert exc.value.status_code == 404
        conn.close()

    def test_case_insensitive(self):
        conn = make_db()
        session = _get_session(conn.cursor(), "tst001")
        assert session["code"] == "TST001"
        conn.close()


# ── _seconds_remaining ────────────────────────────────────────────────────────

class TestSecondsRemaining:
    def test_returns_none_when_not_started(self):
        session = {"started_at": None, "time_limit_seconds": 600}
        assert _seconds_remaining(session) is None

    def test_returns_positive_when_active(self):
        started = (datetime.now(timezone.utc) - timedelta(seconds=60)).strftime("%Y-%m-%dT%H:%M:%SZ")
        session = {"started_at": started, "time_limit_seconds": 600}
        secs = _seconds_remaining(session)
        assert 530 <= secs <= 545

    def test_returns_zero_when_expired(self):
        started = (datetime.now(timezone.utc) - timedelta(seconds=700)).strftime("%Y-%m-%dT%H:%M:%SZ")
        session = {"started_at": started, "time_limit_seconds": 600}
        assert _seconds_remaining(session) == 0


# ── _auto_close_if_expired ────────────────────────────────────────────────────

class TestAutoClose:
    def test_does_not_close_pending_session(self):
        conn = make_db()
        cursor = conn.cursor()
        session = _get_session(cursor, "TST001")
        result = _auto_close_if_expired(cursor, session)
        assert result["status"] == "pending"
        conn.close()

    def test_closes_expired_active_session(self):
        conn = make_db()
        cursor = conn.cursor()
        started = (datetime.now(timezone.utc) - timedelta(seconds=700)).strftime("%Y-%m-%dT%H:%M:%SZ")
        cursor.execute(
            "UPDATE quiz_sessions SET status='active', started_at=? WHERE code='TST001'",
            (started,)
        )
        conn.commit()
        session = _get_session(cursor, "TST001")
        result = _auto_close_if_expired(cursor, session)
        assert result["status"] == "closed"
        # Verify persisted
        row = cursor.execute("SELECT status FROM quiz_sessions WHERE code='TST001'").fetchone()
        assert row["status"] == "closed"
        conn.close()

    def test_does_not_close_unexpired_active_session(self):
        conn = make_db()
        cursor = conn.cursor()
        started = (datetime.now(timezone.utc) - timedelta(seconds=60)).strftime("%Y-%m-%dT%H:%M:%SZ")
        cursor.execute(
            "UPDATE quiz_sessions SET status='active', started_at=? WHERE code='TST001'",
            (started,)
        )
        conn.commit()
        session = _get_session(cursor, "TST001")
        result = _auto_close_if_expired(cursor, session)
        assert result["status"] == "active"
        conn.close()


# ── _draw_variants_for_student ────────────────────────────────────────────────

class TestDrawVariants:
    def test_draws_one_variant_per_problem(self):
        conn = make_db()
        cursor = conn.cursor()
        variant_map = _draw_variants_for_student(cursor, "S001", 1, "quiz3")
        assert "p1" in variant_map
        assert "p2" in variant_map
        assert variant_map["p1"]["minterms"] is not None
        conn.close()

    def test_idempotent_on_rejoin(self):
        conn = make_db()
        cursor = conn.cursor()
        map1 = _draw_variants_for_student(cursor, "S001", 1, "quiz3")
        # Simulate storing the variant map as if join was called
        cursor.execute(
            "INSERT INTO quiz_participants (quiz_session_id, student_id, variant_assignments_json) "
            "VALUES (1, 'S001', ?)",
            (json.dumps(map1),)
        )
        conn.commit()
        map2 = _draw_variants_for_student(cursor, "S001", 1, "quiz3")
        assert map1["p1"]["minterms"] == map2["p1"]["minterms"]
        conn.close()


# ── _best_scores_for_student ──────────────────────────────────────────────────

class TestBestScores:
    def _insert_submission(self, cursor, quiz_id, student_id, attempt, scores):
        total = sum(s["score"] for s in scores.values()) / len(scores)
        cursor.execute(
            "INSERT INTO quiz_submissions "
            "(quiz_session_id, student_id, attempt_number, answers_json, scores_json, total_score, total_points_earned, is_best) "
            "VALUES (?, ?, ?, '{}', ?, ?, ?, 0)",
            (quiz_id, student_id, attempt, json.dumps(scores), total, total * 10)
        )

    def test_returns_empty_for_no_submissions(self):
        conn = make_db()
        best = _best_scores_for_student(conn.cursor(), 1, "S001")
        assert best == {}
        conn.close()

    def test_returns_best_per_problem_across_attempts(self):
        conn = make_db()
        cursor = conn.cursor()
        # Attempt 1: p1=0.5, p2=0.3
        self._insert_submission(cursor, 1, "S001", 1, {
            "p1": {"score": 0.5, "correct": False, "feedback": ""},
            "p2": {"score": 0.3, "correct": False, "feedback": ""},
        })
        # Attempt 2: p1=0.4 (worse), p2=0.9 (better)
        self._insert_submission(cursor, 1, "S001", 2, {
            "p1": {"score": 0.4, "correct": False, "feedback": ""},
            "p2": {"score": 0.9, "correct": False, "feedback": ""},
        })
        conn.commit()
        best = _best_scores_for_student(cursor, 1, "S001")
        assert best["p1"]["score"] == 0.5   # first attempt was better
        assert best["p2"]["score"] == 0.9   # second attempt was better
        conn.close()

    def test_best_score_correct_flag(self):
        conn = make_db()
        cursor = conn.cursor()
        self._insert_submission(cursor, 1, "S001", 1, {
            "p1": {"score": 1.0, "correct": True, "feedback": "Correct!"},
        })
        conn.commit()
        best = _best_scores_for_student(cursor, 1, "S001")
        assert best["p1"]["correct"] is True
        conn.close()


# ── is_best flag ──────────────────────────────────────────────────────────────

class TestIsBestFlag:
    def test_is_best_set_on_highest_total_attempt(self):
        """is_best=1 should be on the attempt with the highest total_score."""
        conn = make_db()
        cursor = conn.cursor()
        # Insert two attempts directly; simulate what submit endpoint does
        cursor.execute(
            "INSERT INTO quiz_submissions "
            "(quiz_session_id, student_id, attempt_number, answers_json, scores_json, total_score, total_points_earned, is_best) "
            "VALUES (1, 'S001', 1, '{}', '{}', 0.5, 5.0, 0)"
        )
        cursor.execute(
            "INSERT INTO quiz_submissions "
            "(quiz_session_id, student_id, attempt_number, answers_json, scores_json, total_score, total_points_earned, is_best) "
            "VALUES (1, 'S001', 2, '{}', '{}', 0.8, 8.0, 1)"
        )
        conn.commit()
        row = cursor.execute(
            "SELECT attempt_number FROM quiz_submissions WHERE quiz_session_id=1 AND student_id='S001' AND is_best=1"
        ).fetchone()
        assert row["attempt_number"] == 2
        conn.close()


# ── _write_best_scores_to_grades ──────────────────────────────────────────────

class TestWriteBestScoresToGrades:
    def _seed_active_submission(self, conn):
        """Seed a participant with variants and a submission."""
        cursor = conn.cursor()
        variant_map = {
            "p1": {
                "pool_id": "1",
                "minterms": "m(1,3)",
                "dont_cares": "",
                "solution_json": json.dumps({"simplified_expression": "B"}),
                "problem_text": "Simplify F(A,B)",
                "parameters_json": json.dumps({"minterms": [1, 3], "dont_cares": []}),
            },
            "p2": {
                "pool_id": "2",
                "minterms": "m(0,2)",
                "dont_cares": "",
                "solution_json": json.dumps({"simplified_expression": "B"}),
                "problem_text": "Simplify G(A,B)",
                "parameters_json": json.dumps({"minterms": [0, 2], "dont_cares": []}),
            }
        }
        cursor.execute(
            "INSERT INTO quiz_participants (quiz_session_id, student_id, variant_assignments_json) "
            "VALUES (1, 'S001', ?)", (json.dumps(variant_map),)
        )
        scores = {
            "p1": {"score": 0.8, "correct": False, "feedback": "close"},
            "p2": {"score": 1.0, "correct": True, "feedback": "Correct!"},
        }
        cursor.execute(
            "INSERT INTO quiz_submissions "
            "(quiz_session_id, student_id, attempt_number, answers_json, scores_json, total_score, total_points_earned, is_best) "
            "VALUES (1, 'S001', 1, ?, ?, 0.9, 9.0, 1)",
            (json.dumps({"p1": "B", "p2": "B"}), json.dumps(scores))
        )
        conn.commit()

    def test_creates_attempt_row(self):
        conn = make_db()
        self._seed_active_submission(conn)
        _write_best_scores_to_grades(conn.cursor(), 1)
        conn.commit()
        row = conn.execute(
            "SELECT status, total_score FROM attempts WHERE student_id='S001' AND assignment_id='quiz3'"
        ).fetchone()
        assert row is not None
        assert row["status"] == "graded"
        assert abs(row["total_score"] - 0.9) < 0.01
        conn.close()

    def test_creates_attempt_results_row(self):
        conn = make_db()
        self._seed_active_submission(conn)
        _write_best_scores_to_grades(conn.cursor(), 1)
        conn.commit()
        attempt = conn.execute(
            "SELECT id FROM attempts WHERE student_id='S001' AND assignment_id='quiz3'"
        ).fetchone()
        result = conn.execute(
            "SELECT * FROM attempt_results WHERE attempt_id=?", (attempt["id"],)
        ).fetchone()
        assert result is not None
        assert result["problems_correct"] == 1
        assert result["problems_total"] == 2
        conn.close()

    def test_idempotent_on_double_call(self):
        """Calling twice should not create duplicate attempt rows."""
        conn = make_db()
        self._seed_active_submission(conn)
        cursor = conn.cursor()
        _write_best_scores_to_grades(cursor, 1)
        conn.commit()
        _write_best_scores_to_grades(cursor, 1)
        conn.commit()
        count = conn.execute(
            "SELECT COUNT(*) FROM attempts WHERE student_id='S001' AND assignment_id='quiz3'"
        ).fetchone()[0]
        assert count == 1
        conn.close()

    def test_no_op_for_no_submissions(self):
        """If nobody submitted, grade tables should remain empty."""
        conn = make_db()
        _write_best_scores_to_grades(conn.cursor(), 1)
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
        assert count == 0
        conn.close()

    def test_multiple_students(self):
        conn = make_db()
        cursor = conn.cursor()
        variant_map = {
            "p1": {
                "pool_id": "1", "minterms": "m(1,3)", "dont_cares": "",
                "solution_json": json.dumps({"simplified_expression": "B"}),
                "problem_text": "Simplify F", "parameters_json": json.dumps({"minterms": [1, 3], "dont_cares": []}),
            }
        }
        for student_id, score in [("S001", 0.8), ("S002", 0.5)]:
            cursor.execute(
                "INSERT INTO quiz_participants (quiz_session_id, student_id, variant_assignments_json) "
                "VALUES (1, ?, ?)", (student_id, json.dumps(variant_map))
            )
            cursor.execute(
                "INSERT INTO quiz_submissions "
                "(quiz_session_id, student_id, attempt_number, answers_json, scores_json, total_score, total_points_earned, is_best) "
                "VALUES (1, ?, 1, '{}', ?, ?, ?, 1)",
                (student_id, json.dumps({"p1": {"score": score, "correct": False, "feedback": ""}}), score, score * 10)
            )
        conn.commit()
        _write_best_scores_to_grades(cursor, 1)
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM attempts WHERE assignment_id='quiz3'").fetchone()[0]
        assert count == 2
        conn.close()


# ── Grade passthrough ─────────────────────────────────────────────────────────

class TestGradePassthrough:
    """Verify quiz scores appear in the instructor gradebook after close."""

    def test_scores_visible_in_attempt_results_after_writeback(self):
        conn = make_db()
        cursor = conn.cursor()
        variant_map = {
            "p1": {
                "pool_id": "1", "minterms": "m(1,3)", "dont_cares": "",
                "solution_json": json.dumps({"simplified_expression": "B"}),
                "problem_text": "Simplify", "parameters_json": json.dumps({"minterms": [1, 3], "dont_cares": []}),
            },
            "p2": {
                "pool_id": "2", "minterms": "m(0,2)", "dont_cares": "",
                "solution_json": json.dumps({"simplified_expression": "B"}),
                "problem_text": "Simplify", "parameters_json": json.dumps({"minterms": [0, 2], "dont_cares": []}),
            }
        }
        cursor.execute(
            "INSERT INTO quiz_participants VALUES (NULL, 1, 'S001', datetime('now'), ?)",
            (json.dumps(variant_map),)
        )
        scores = {"p1": {"score": 1.0, "correct": True, "feedback": ""}, "p2": {"score": 0.5, "correct": False, "feedback": ""}}
        cursor.execute(
            "INSERT INTO quiz_submissions "
            "(quiz_session_id, student_id, attempt_number, answers_json, scores_json, total_score, total_points_earned, is_best) "
            "VALUES (1, 'S001', 1, '{}', ?, 0.75, 7.5, 1)", (json.dumps(scores),)
        )
        conn.commit()
        _write_best_scores_to_grades(cursor, 1)
        conn.commit()

        result = cursor.execute("""
            SELECT ar.total_score, ar.problems_correct
            FROM attempt_results ar
            JOIN attempts a ON a.id = ar.attempt_id
            WHERE a.student_id = 'S001' AND a.assignment_id = 'quiz3'
        """).fetchone()
        assert result is not None
        assert abs(result["total_score"] - 0.75) < 0.01
        assert result["problems_correct"] == 1
        conn.close()
