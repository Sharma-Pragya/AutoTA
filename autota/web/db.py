"""Database setup and operations for AutoTA web application."""

import sqlite3
from pathlib import Path


DB_PATH = Path("data/autota.db")


def get_db_connection():
    """Get a connection to the SQLite database."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def init_db():
    """Initialize database schema with all tables."""
    DB_PATH.parent.mkdir(exist_ok=True)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Institutional hierarchy
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS course_offerings (
            id TEXT PRIMARY KEY,
            course_id TEXT NOT NULL REFERENCES courses(id),
            quarter TEXT NOT NULL,
            year INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS instructors (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT DEFAULT 'instructor'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sections (
            id TEXT PRIMARY KEY,
            offering_id TEXT NOT NULL REFERENCES course_offerings(id),
            label TEXT NOT NULL,
            instructor_id TEXT REFERENCES instructors(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL REFERENCES students(id),
            section_id TEXT NOT NULL REFERENCES sections(id),
            enrolled_at TEXT DEFAULT (datetime('now')),
            dropped INTEGER DEFAULT 0,
            UNIQUE(student_id, section_id)
        )
    """)

    # Students table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            section TEXT
        )
    """)

    # Assignments table (extended)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            course TEXT NOT NULL,
            spec_path TEXT NOT NULL,
            instructions TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            offering_id TEXT REFERENCES course_offerings(id),
            type TEXT DEFAULT 'homework',
            max_attempts INTEGER DEFAULT 1,
            time_limit_minutes INTEGER,
            opens_at TEXT,
            closes_at TEXT
        )
    """)

    # Problems table (extended)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS problems (
            id TEXT PRIMARY KEY,
            assignment_id TEXT NOT NULL REFERENCES assignments(id),
            parent_label TEXT NOT NULL,
            sub_label TEXT,
            display_order INTEGER NOT NULL,
            text TEXT NOT NULL,
            minterms TEXT,
            dont_cares TEXT,
            hint TEXT,
            answer_format TEXT NOT NULL,
            placeholder TEXT,
            problem_type TEXT DEFAULT 'kmap_simplification',
            points REAL DEFAULT 1.0,
            depends_on_problem_id TEXT REFERENCES problems(id)
        )
    """)

    # Variant pool
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS variant_pool (
            id TEXT PRIMARY KEY,
            problem_id TEXT NOT NULL REFERENCES problems(id),
            parameters_json TEXT NOT NULL,
            parameter_hash TEXT NOT NULL,
            problem_text TEXT,
            minterms TEXT,
            dont_cares TEXT,
            solution_json TEXT NOT NULL,
            generated_by TEXT DEFAULT 'template',
            verified INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Variant assignments table (extended)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS variant_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL REFERENCES students(id),
            problem_id TEXT NOT NULL REFERENCES problems(id),
            variant_id TEXT NOT NULL,
            variant_json TEXT NOT NULL,
            solution_json TEXT NOT NULL,
            attempt_number INTEGER NOT NULL DEFAULT 1,
            assigned_at TEXT DEFAULT (datetime('now')),
            attempt_id INTEGER REFERENCES attempts(id),
            UNIQUE(student_id, problem_id, attempt_number)
        )
    """)

    # Submissions table (extended)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL REFERENCES students(id),
            problem_id TEXT NOT NULL REFERENCES problems(id),
            variant_assignment_id INTEGER NOT NULL REFERENCES variant_assignments(id),
            answer TEXT NOT NULL,
            score REAL,
            correct INTEGER,
            feedback TEXT,
            graded_at TEXT,
            submitted_at TEXT DEFAULT (datetime('now')),
            attestation_signed INTEGER DEFAULT 0,
            answer_normalized TEXT
        )
    """)

    # Grades table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER NOT NULL REFERENCES submissions(id),
            score REAL NOT NULL,
            correct INTEGER NOT NULL,
            feedback TEXT,
            grading_tier TEXT DEFAULT 'deterministic',
            grading_status TEXT DEFAULT 'graded',
            graded_by TEXT DEFAULT 'autota_verifier',
            graded_at TEXT DEFAULT (datetime('now')),
            previous_score REAL,
            previous_feedback TEXT,
            regraded_at TEXT
        )
    """)

    # Attempts table (extended)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL REFERENCES students(id),
            assignment_id TEXT NOT NULL REFERENCES assignments(id),
            attempt_number INTEGER NOT NULL DEFAULT 1,
            started_at TEXT DEFAULT (datetime('now')),
            submitted_at TEXT,
            total_score REAL,
            status TEXT DEFAULT 'in_progress',
            attestation_signed INTEGER DEFAULT 0,
            attestation_signed_at TEXT,
            UNIQUE(student_id, assignment_id, attempt_number)
        )
    """)

    # Attempt results (denormalized aggregate)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attempt_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER NOT NULL REFERENCES attempts(id),
            total_score REAL NOT NULL,
            total_points_earned REAL NOT NULL,
            total_points_possible REAL NOT NULL,
            problems_correct INTEGER NOT NULL,
            problems_total INTEGER NOT NULL,
            computed_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Draft answers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS draft_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER NOT NULL REFERENCES attempts(id),
            problem_id TEXT NOT NULL REFERENCES problems(id),
            answer_raw TEXT NOT NULL,
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(attempt_id, problem_id)
        )
    """)

    # Quiz sessions (stub for Phase 5)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id TEXT NOT NULL REFERENCES assignments(id),
            section_id TEXT REFERENCES sections(id),
            created_by TEXT REFERENCES instructors(id),
            qr_url TEXT,
            status TEXT DEFAULT 'pending',
            opens_at TEXT,
            closes_at TEXT,
            time_limit_minutes INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()

    print(f"✓ Database initialized at {DB_PATH}")
