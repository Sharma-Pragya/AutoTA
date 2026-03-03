"""Run migration 004: add quiz mode tables and extend quiz_sessions."""
import sqlite3
from pathlib import Path

DB_PATH = Path("data/autota.db")
SQL_PATH = Path("migrations/004_quiz_mode.sql")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Add missing columns to quiz_sessions (idempotent)
existing = {row[1] for row in cursor.execute("PRAGMA table_info(quiz_sessions)")}

new_cols = [
    ("code", "TEXT"),
    ("time_limit_seconds", "INTEGER DEFAULT 600"),
    ("started_at", "TEXT"),
    ("closed_at", "TEXT"),
]
for col, col_type in new_cols:
    if col not in existing:
        cursor.execute(f"ALTER TABLE quiz_sessions ADD COLUMN {col} {col_type}")
        print(f"  + Added column quiz_sessions.{col}")
    else:
        print(f"  = Column quiz_sessions.{col} already exists")

# Add UNIQUE constraint workaround: add code index
cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_quiz_sessions_code ON quiz_sessions(code) WHERE code IS NOT NULL")

# Run the SQL file for new tables
sql = SQL_PATH.read_text()
conn.executescript(sql)

conn.commit()
conn.close()
print("✓ Migration 004 complete")
