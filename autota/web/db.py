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

    # Students table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            section TEXT
        )
    """)

    # Assignments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            course TEXT NOT NULL,
            spec_path TEXT NOT NULL,
            instructions TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Problems table
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
            placeholder TEXT
        )
    """)

    # Variant assignments table
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
            UNIQUE(student_id, problem_id, attempt_number)
        )
    """)

    # Submissions table
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
            attestation_signed INTEGER DEFAULT 0
        )
    """)

    # Attempts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL REFERENCES students(id),
            assignment_id TEXT NOT NULL REFERENCES assignments(id),
            attempt_number INTEGER NOT NULL DEFAULT 1,
            started_at TEXT DEFAULT (datetime('now')),
            submitted_at TEXT,
            total_score REAL,
            UNIQUE(student_id, assignment_id, attempt_number)
        )
    """)

    conn.commit()
    conn.close()

    print(f"✓ Database initialized at {DB_PATH}")
