"""HTTP endpoint tests for Phase 2.2 instructor dashboard routes.

Uses FastAPI TestClient with the instructor_db fixture (seeded_db + graded hw1).
All tests are isolated; no production DB is touched.
"""

import pytest


# ── Dashboard ─────────────────────────────────────────────────────────────────

class TestDashboard:
    def test_dashboard_returns_expected_structure(self, instr_client):
        r = instr_client.get("/api/instructor/dashboard")
        assert r.status_code == 200
        data = r.json()
        assert "offering" in data
        assert "assignments" in data
        assert "total_enrolled" in data
        assert "class_avg_pct" in data

    def test_dashboard_lists_all_assignments(self, instr_client):
        r = instr_client.get("/api/instructor/dashboard")
        assignments = r.json()["assignments"]
        ids = [a["id"] for a in assignments]
        assert "quiz1" in ids
        assert "hw1" in ids

    def test_dashboard_assignment_has_stats_keys(self, instr_client):
        r = instr_client.get("/api/instructor/dashboard")
        for asgn in r.json()["assignments"]:
            for key in ("submitted", "not_submitted", "submission_rate", "mean"):
                assert key in asgn, f"Missing '{key}' in assignment {asgn['id']}"

    def test_dashboard_hw1_has_one_submission(self, instr_client):
        r = instr_client.get("/api/instructor/dashboard")
        hw1 = next(a for a in r.json()["assignments"] if a["id"] == "hw1")
        assert hw1["submitted"] == 1

    def test_dashboard_class_avg_is_numeric(self, instr_client):
        r = instr_client.get("/api/instructor/dashboard")
        avg = r.json()["class_avg_pct"]
        assert isinstance(avg, (int, float))

    def test_dashboard_category_summary_present(self, instr_client):
        r = instr_client.get("/api/instructor/dashboard")
        assert "category_summary" in r.json()


# ── Gradebook ─────────────────────────────────────────────────────────────────

class TestGradebook:
    def test_gradebook_returns_students_and_assignments(self, instr_client):
        r = instr_client.get("/api/instructor/gradebook")
        assert r.status_code == 200
        data = r.json()
        assert "students" in data
        assert "assignments" in data

    def test_gradebook_includes_both_students(self, instr_client):
        r = instr_client.get("/api/instructor/gradebook")
        names = [s["name"] for s in r.json()["students"]]
        assert "Alice" in names
        assert "Bob" in names

    def test_gradebook_alice_hw1_score_is_100(self, instr_client):
        r = instr_client.get("/api/instructor/gradebook")
        alice = next(s for s in r.json()["students"] if s["name"] == "Alice")
        assert alice["scores"]["hw1"] == 100.0

    def test_gradebook_bob_hw1_score_is_null(self, instr_client):
        r = instr_client.get("/api/instructor/gradebook")
        bob = next(s for s in r.json()["students"] if s["name"] == "Bob")
        assert bob["scores"]["hw1"] is None

    def test_gradebook_student_has_submitted_count(self, instr_client):
        r = instr_client.get("/api/instructor/gradebook")
        alice = next(s for s in r.json()["students"] if s["name"] == "Alice")
        assert alice["submitted_count"] >= 1

    def test_gradebook_student_has_overall_avg(self, instr_client):
        r = instr_client.get("/api/instructor/gradebook")
        alice = next(s for s in r.json()["students"] if s["name"] == "Alice")
        assert alice["overall_avg"] is not None


# ── Gradebook CSV export ──────────────────────────────────────────────────────

class TestGradebookExport:
    def test_export_returns_csv_content_type(self, instr_client):
        r = instr_client.get("/api/instructor/gradebook/export")
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]

    def test_export_has_content_disposition(self, instr_client):
        r = instr_client.get("/api/instructor/gradebook/export")
        assert "attachment" in r.headers.get("content-disposition", "")
        assert "gradebook.csv" in r.headers.get("content-disposition", "")

    def test_export_has_header_row(self, instr_client):
        r = instr_client.get("/api/instructor/gradebook/export")
        lines = r.text.strip().split("\n")
        assert len(lines) >= 2  # header + at least one student
        header = lines[0]
        assert "Student ID" in header
        assert "Name" in header

    def test_export_includes_both_students(self, instr_client):
        r = instr_client.get("/api/instructor/gradebook/export")
        assert "Alice" in r.text
        assert "Bob" in r.text

    def test_export_alice_hw1_score(self, instr_client):
        r = instr_client.get("/api/instructor/gradebook/export")
        # Find Alice's row
        lines = r.text.strip().split("\n")
        alice_line = next(l for l in lines if "Alice" in l)
        assert "100.0" in alice_line


# ── Assignment detail ─────────────────────────────────────────────────────────

class TestAssignmentDetail:
    def test_hw1_detail_returns_expected_keys(self, instr_client):
        r = instr_client.get("/api/instructor/assignment/hw1")
        assert r.status_code == 200
        data = r.json()
        for key in ("assignment", "stats", "problem_stats", "students"):
            assert key in data, f"Missing key: {key}"

    def test_hw1_stats_show_one_submission(self, instr_client):
        r = instr_client.get("/api/instructor/assignment/hw1")
        assert r.json()["stats"]["submitted"] == 1

    def test_hw1_student_list_includes_alice(self, instr_client):
        r = instr_client.get("/api/instructor/assignment/hw1")
        names = [s["name"] for s in r.json()["students"]]
        assert "Alice" in names

    def test_unknown_assignment_returns_404(self, instr_client):
        r = instr_client.get("/api/instructor/assignment/nonexistent")
        assert r.status_code == 404

    def test_quiz1_detail_has_problems(self, instr_client):
        r = instr_client.get("/api/instructor/assignment/quiz1")
        assert r.status_code == 200
        assert len(r.json()["problem_stats"]) == 2


# ── Student detail ────────────────────────────────────────────────────────────

class TestStudentDetail:
    def test_alice_detail_returns_expected_structure(self, instr_client):
        r = instr_client.get("/api/instructor/student/S1")
        assert r.status_code == 200
        data = r.json()
        for key in ("student", "assignments"):
            assert key in data

    def test_alice_name_correct(self, instr_client):
        r = instr_client.get("/api/instructor/student/S1")
        assert r.json()["student"]["name"] == "Alice"

    def test_alice_has_hw1_attempt(self, instr_client):
        r = instr_client.get("/api/instructor/student/S1")
        asgn_ids = [a["id"] for a in r.json()["assignments"]]
        assert "hw1" in asgn_ids

    def test_unknown_student_returns_404(self, instr_client):
        r = instr_client.get("/api/instructor/student/NOBODY")
        assert r.status_code == 404


# ── Roster ────────────────────────────────────────────────────────────────────

class TestRoster:
    def test_roster_returns_students(self, instr_client):
        r = instr_client.get("/api/instructor/roster")
        assert r.status_code == 200
        data = r.json()
        assert "students" in data
        assert len(data["students"]) == 2

    def test_roster_student_has_expected_fields(self, instr_client):
        r = instr_client.get("/api/instructor/roster")
        for s in r.json()["students"]:
            for key in ("id", "name", "email"):
                assert key in s

    def test_roster_sorted_by_name(self, instr_client):
        r = instr_client.get("/api/instructor/roster")
        names = [s["name"] for s in r.json()["students"]]
        assert names == sorted(names)


# ── Auth on dashboard endpoints ───────────────────────────────────────────────

class TestDashboardAuth:
    """When token is configured, instructor dashboard endpoints require it."""

    ENDPOINTS = [
        ("GET", "/api/instructor/dashboard"),
        ("GET", "/api/instructor/gradebook"),
        ("GET", "/api/instructor/gradebook/export"),
        ("GET", "/api/instructor/assignment/hw1"),
        ("GET", "/api/instructor/student/S1"),
        ("GET", "/api/instructor/roster"),
    ]

    def test_missing_token_returns_401(self, authed_client):
        for method, url in self.ENDPOINTS:
            r = authed_client.request(method, url)
            assert r.status_code == 401, f"{method} {url} should be 401 without token"

    def test_correct_token_allows_access(self, authed_client):
        headers = {"X-Instructor-Token": authed_client._token}
        r = authed_client.get("/api/instructor/dashboard", headers=headers)
        assert r.status_code == 200
