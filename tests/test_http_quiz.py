"""HTTP endpoint tests for Phase 2.3 quiz routes.

Uses FastAPI TestClient with a temporary SQLite DB (conftest.py fixtures).
No real DB is touched; all tests are fully isolated.
"""

import json
import sqlite3
import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _activate_quiz(db_path, code="TEST1"):
    """Set a quiz session to 'active' with started_at = now."""
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "UPDATE quiz_sessions SET status='active', started_at=datetime('now') WHERE code=?",
        (code,)
    )
    conn.commit()
    conn.close()


def _close_quiz(db_path, code="TEST1"):
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "UPDATE quiz_sessions SET status='closed', closed_at=datetime('now') WHERE code=?",
        (code,)
    )
    conn.commit()
    conn.close()


# ── Student: join ─────────────────────────────────────────────────────────────

class TestJoinQuiz:
    def test_join_pending_quiz_succeeds(self, client):
        r = client.post("/api/quiz/TEST1/join", json={"student_id": "S1"})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "pending"
        assert "problems" in data
        assert len(data["problems"]) == 2

    def test_join_active_quiz_returns_problems_and_timer(self, client, seeded_db):
        _activate_quiz(seeded_db)
        r = client.post("/api/quiz/TEST1/join", json={"student_id": "S1"})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "active"
        assert data["time_remaining_seconds"] is not None
        assert data["time_remaining_seconds"] > 0

    def test_join_closed_quiz_is_forbidden(self, client, seeded_db):
        _close_quiz(seeded_db)
        r = client.post("/api/quiz/TEST1/join", json={"student_id": "S1"})
        assert r.status_code == 403

    def test_join_unknown_code_returns_404(self, client):
        r = client.post("/api/quiz/ZZZZZ/join", json={"student_id": "S1"})
        assert r.status_code == 404

    def test_join_is_idempotent(self, client):
        """Joining twice returns the same problems (not duplicated)."""
        r1 = client.post("/api/quiz/TEST1/join", json={"student_id": "S1"})
        r2 = client.post("/api/quiz/TEST1/join", json={"student_id": "S1"})
        assert r1.status_code == r2.status_code == 200
        assert len(r1.json()["problems"]) == len(r2.json()["problems"]) == 2

    def test_join_returns_best_scores_empty_before_submit(self, client):
        r = client.post("/api/quiz/TEST1/join", json={"student_id": "S1"})
        assert r.json()["best_scores"] == {}

    def test_join_case_insensitive_code(self, client):
        r = client.post("/api/quiz/test1/join", json={"student_id": "S1"})
        assert r.status_code == 200


# ── Student: status ───────────────────────────────────────────────────────────

class TestQuizStatus:
    def test_status_pending(self, client):
        r = client.get("/api/quiz/TEST1/status")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "pending"
        assert data["time_remaining_seconds"] is None

    def test_status_active(self, client, seeded_db):
        _activate_quiz(seeded_db)
        r = client.get("/api/quiz/TEST1/status")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "active"
        assert isinstance(data["time_remaining_seconds"], int)
        assert data["time_remaining_seconds"] > 0

    def test_status_closed(self, client, seeded_db):
        _close_quiz(seeded_db)
        r = client.get("/api/quiz/TEST1/status")
        assert r.status_code == 200
        assert r.json()["status"] == "closed"

    def test_status_unknown_code_404(self, client):
        r = client.get("/api/quiz/ZZZZZ/status")
        assert r.status_code == 404


# ── Student: submit ───────────────────────────────────────────────────────────

class TestSubmitQuiz:
    def _submit(self, client, answers=None, student_id="S1"):
        if answers is None:
            answers = {"p1": "A'B'", "p2": "A'B'"}
        return client.post("/api/quiz/TEST1/submit", json={
            "student_id": student_id,
            "answers": answers,
        })

    def test_submit_returns_403_when_not_active(self, client):
        r = self._submit(client)
        assert r.status_code == 403

    def test_submit_active_returns_scores(self, client, seeded_db):
        _activate_quiz(seeded_db)
        # Join first so variants are drawn
        client.post("/api/quiz/TEST1/join", json={"student_id": "S1"})
        r = self._submit(client)
        assert r.status_code == 200
        data = r.json()
        assert "scores" in data
        assert "total_score" in data
        assert "best_scores" in data
        assert data["attempt_number"] == 1

    def test_submit_increments_attempt_number(self, client, seeded_db):
        _activate_quiz(seeded_db)
        client.post("/api/quiz/TEST1/join", json={"student_id": "S1"})
        r1 = self._submit(client)
        r2 = self._submit(client)
        assert r1.json()["attempt_number"] == 1
        assert r2.json()["attempt_number"] == 2

    def test_submit_best_score_is_nondecreasing(self, client, seeded_db):
        _activate_quiz(seeded_db)
        client.post("/api/quiz/TEST1/join", json={"student_id": "S1"})
        # First submit with wrong answer
        r1 = self._submit(client, {"p1": "WRONG", "p2": "WRONG"})
        best1 = r1.json()["best_total_score"]
        # Second submit with correct answer
        r2 = self._submit(client, {"p1": "A'B'", "p2": "A'B'"})
        best2 = r2.json()["best_total_score"]
        assert best2 >= best1

    def test_submit_closed_quiz_returns_403(self, client, seeded_db):
        _close_quiz(seeded_db)
        r = self._submit(client)
        assert r.status_code == 403

    def test_submit_returns_time_remaining(self, client, seeded_db):
        _activate_quiz(seeded_db)
        client.post("/api/quiz/TEST1/join", json={"student_id": "S1"})
        r = self._submit(client)
        assert r.json()["time_remaining_seconds"] is not None

    def test_best_scores_visible_on_rejoin(self, client, seeded_db):
        """After submitting, re-joining returns non-empty best_scores."""
        _activate_quiz(seeded_db)
        client.post("/api/quiz/TEST1/join", json={"student_id": "S1"})
        self._submit(client, {"p1": "A'B'", "p2": "A'B'"})
        r = client.post("/api/quiz/TEST1/join", json={"student_id": "S1"})
        assert r.json()["best_scores"] != {}


# ── Instructor: create ────────────────────────────────────────────────────────

class TestCreateQuiz:
    def test_create_quiz_for_valid_assignment(self, client):
        r = client.post("/api/instructor/quiz/create", json={
            "assignment_id": "quiz1",
            "time_limit_seconds": 300,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "pending"
        assert data["code"].startswith("QZ")
        assert len(data["code"]) == 6

    def test_create_quiz_for_unknown_assignment_returns_404(self, client):
        r = client.post("/api/instructor/quiz/create", json={
            "assignment_id": "nonexistent",
        })
        assert r.status_code == 404

    def test_create_quiz_returns_unique_codes(self, client):
        codes = set()
        for _ in range(5):
            r = client.post("/api/instructor/quiz/create", json={"assignment_id": "quiz1"})
            assert r.status_code == 200
            codes.add(r.json()["code"])
        assert len(codes) == 5


# ── Instructor: start ─────────────────────────────────────────────────────────

class TestStartQuiz:
    def test_start_pending_quiz(self, client):
        r = client.post("/api/instructor/quiz/TEST1/start")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "active"
        assert "started_at" in data
        assert "expires_at" in data

    def test_start_already_active_returns_400(self, client, seeded_db):
        _activate_quiz(seeded_db)
        r = client.post("/api/instructor/quiz/TEST1/start")
        assert r.status_code == 400

    def test_start_closed_quiz_returns_400(self, client, seeded_db):
        _close_quiz(seeded_db)
        r = client.post("/api/instructor/quiz/TEST1/start")
        assert r.status_code == 400


# ── Instructor: close ─────────────────────────────────────────────────────────

class TestCloseQuiz:
    def test_close_active_quiz(self, client, seeded_db):
        _activate_quiz(seeded_db)
        r = client.post("/api/instructor/quiz/TEST1/close")
        assert r.status_code == 200
        assert r.json()["status"] == "closed"

    def test_close_pending_quiz(self, client):
        r = client.post("/api/instructor/quiz/TEST1/close")
        assert r.status_code == 200
        assert r.json()["status"] == "closed"

    def test_close_already_closed_returns_400(self, client, seeded_db):
        _close_quiz(seeded_db)
        r = client.post("/api/instructor/quiz/TEST1/close")
        assert r.status_code == 400

    def test_close_writes_grades_for_submitted_students(self, client, seeded_db):
        """After close, attempt rows should exist for students who submitted."""
        _activate_quiz(seeded_db)
        client.post("/api/quiz/TEST1/join", json={"student_id": "S1"})
        client.post("/api/quiz/TEST1/submit", json={
            "student_id": "S1",
            "answers": {"p1": "A'B'", "p2": "A'B'"},
        })
        r = client.post("/api/instructor/quiz/TEST1/close")
        assert r.status_code == 200

        # Verify grades were written
        conn = sqlite3.connect(str(seeded_db))
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM attempts WHERE student_id='S1' AND assignment_id='quiz1'"
        ).fetchone()
        conn.close()
        assert row is not None
        assert row["status"] == "graded"


# ── Instructor: review ────────────────────────────────────────────────────────

class TestReviewMode:
    def test_set_review_after_close(self, client, seeded_db):
        _close_quiz(seeded_db)
        r = client.post("/api/instructor/quiz/TEST1/review")
        assert r.status_code == 200
        assert r.json()["status"] == "review"

    def test_set_review_on_active_quiz_returns_400(self, client, seeded_db):
        _activate_quiz(seeded_db)
        r = client.post("/api/instructor/quiz/TEST1/review")
        assert r.status_code == 400


# ── Instructor: live stats ────────────────────────────────────────────────────

class TestLiveStats:
    def test_live_returns_expected_keys(self, client, seeded_db):
        _activate_quiz(seeded_db)
        r = client.get("/api/instructor/quiz/TEST1/live")
        assert r.status_code == 200
        data = r.json()
        for key in ("status", "time_remaining_seconds", "submitted_count",
                    "retry_count", "avg_best_score", "score_distribution",
                    "recent_submissions"):
            assert key in data, f"Missing key: {key}"

    def test_live_submitted_count_increments(self, client, seeded_db):
        _activate_quiz(seeded_db)
        r_before = client.get("/api/instructor/quiz/TEST1/live")
        assert r_before.json()["submitted_count"] == 0

        client.post("/api/quiz/TEST1/join", json={"student_id": "S1"})
        client.post("/api/quiz/TEST1/submit", json={
            "student_id": "S1",
            "answers": {"p1": "A'B'", "p2": "A'B'"},
        })

        r_after = client.get("/api/instructor/quiz/TEST1/live")
        assert r_after.json()["submitted_count"] == 1

    def test_live_retry_count(self, client, seeded_db):
        _activate_quiz(seeded_db)
        client.post("/api/quiz/TEST1/join", json={"student_id": "S1"})
        # Submit twice (one retry)
        client.post("/api/quiz/TEST1/submit", json={"student_id": "S1", "answers": {"p1": "A", "p2": "A"}})
        client.post("/api/quiz/TEST1/submit", json={"student_id": "S1", "answers": {"p1": "A'B'", "p2": "A'B'"}})

        r = client.get("/api/instructor/quiz/TEST1/live")
        assert r.json()["retry_count"] == 1


# ── Instructor: results ───────────────────────────────────────────────────────

class TestResults:
    def test_results_empty_when_no_submissions(self, client, seeded_db):
        _close_quiz(seeded_db)
        r = client.get("/api/instructor/quiz/TEST1/results")
        assert r.status_code == 200
        data = r.json()
        assert data["submitted_count"] == 0
        assert len(data["problems"]) == 2

    def test_results_after_submissions(self, client, seeded_db):
        _activate_quiz(seeded_db)
        client.post("/api/quiz/TEST1/join", json={"student_id": "S1"})
        client.post("/api/quiz/TEST1/submit", json={
            "student_id": "S1",
            "answers": {"p1": "A'B'", "p2": "A'B'"},
        })
        _close_quiz(seeded_db)

        r = client.get("/api/instructor/quiz/TEST1/results")
        assert r.status_code == 200
        data = r.json()
        assert data["submitted_count"] == 1
        assert "avg_best_score" in data
        assert "problems" in data

    def test_results_improvement_rate_calculated(self, client, seeded_db):
        _activate_quiz(seeded_db)
        client.post("/api/quiz/TEST1/join", json={"student_id": "S1"})
        # Two submits — one is a retry
        client.post("/api/quiz/TEST1/submit", json={"student_id": "S1", "answers": {"p1": "WRONG", "p2": "WRONG"}})
        client.post("/api/quiz/TEST1/submit", json={"student_id": "S1", "answers": {"p1": "A'B'", "p2": "A'B'"}})
        _close_quiz(seeded_db)

        r = client.get("/api/instructor/quiz/TEST1/results")
        data = r.json()
        assert data["retry_count"] == 1
        assert data["improvement_rate"] == 1.0


# ── Instructor: meta ──────────────────────────────────────────────────────────

class TestQuizMeta:
    def test_meta_returns_expected_keys(self, client):
        r = client.get("/api/instructor/quiz/TEST1/meta")
        assert r.status_code == 200
        data = r.json()
        for key in ("code", "status", "assignment_id", "time_limit_seconds",
                    "problem_count", "total_enrolled"):
            assert key in data

    def test_meta_code_is_uppercase(self, client):
        r = client.get("/api/instructor/quiz/test1/meta")
        assert r.status_code == 200
        assert r.json()["code"] == "TEST1"


# ── Auth enforcement ──────────────────────────────────────────────────────────

class TestAuthEnforcement:
    """When a token is configured, instructor endpoints require the header."""

    INSTR_ENDPOINTS = [
        ("GET", "/api/instructor/quiz/TEST1/meta"),
        ("GET", "/api/instructor/quiz/TEST1/live"),
        ("GET", "/api/instructor/quiz/TEST1/results"),
        ("POST", "/api/instructor/quiz/TEST1/start"),
        ("POST", "/api/instructor/quiz/TEST1/close"),
        ("POST", "/api/instructor/quiz/TEST1/review"),
    ]

    def test_missing_token_returns_401(self, authed_client):
        for method, url in self.INSTR_ENDPOINTS:
            r = authed_client.request(method, url)
            assert r.status_code == 401, f"{method} {url} should return 401 without token"

    def test_wrong_token_returns_401(self, authed_client):
        headers = {"X-Instructor-Token": "wrong-token"}
        for method, url in self.INSTR_ENDPOINTS:
            r = authed_client.request(method, url, headers=headers)
            assert r.status_code == 401, f"{method} {url} should return 401 with wrong token"

    def test_correct_token_is_accepted(self, authed_client, seeded_db):
        _close_quiz(seeded_db)
        headers = {"X-Instructor-Token": authed_client._token}
        r = authed_client.get("/api/instructor/quiz/TEST1/meta", headers=headers)
        assert r.status_code == 200

    def test_student_endpoints_dont_require_token(self, authed_client):
        """Student join/status are public — should not require auth token."""
        r = authed_client.get("/api/quiz/TEST1/status")
        assert r.status_code == 200
