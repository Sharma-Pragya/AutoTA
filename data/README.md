# Database Directory

This directory contains the SQLite database file for AutoTA.

## Setup

The database file (`autota.db`) is **not committed to git**. You must create it by running the migrations and seed script:

```bash
# From the project root directory:

# 1. Run migrations to create schema
sqlite3 data/autota.db < migrations/001_initial_schema.sql
sqlite3 data/autota.db < migrations/002_schema_hardening.sql

# 2. Backfill variant pool
python -m migrations.backfill_variant_pool

# 3. Seed database with test data
./seed.sh
```

## What Gets Created

After running the setup scripts, you'll have:

- **19 tables**: students, assignments, problems, variant_assignments, submissions, attempts, courses, course_offerings, instructors, sections, enrollments, variant_pool, draft_answers, grades, attempt_results, quiz_sessions, and more
- **2 views**: v_student_attempt_status, v_grade_report
- **3 test students**: Pragya Sharma, Jane Bruin, Joe Bruin
- **1 assignment**: Homework 5 - Karnaugh Map Simplification
- **39 variants**: 13 variants per K-map problem type in the variant pool

## File Structure

```
data/
├── README.md       # This file
├── .gitkeep        # Keeps directory in git
└── autota.db       # SQLite database (NOT in git)
```

## Database Schema

See `migrations/001_initial_schema.sql` and `migrations/002_schema_hardening.sql` for the complete schema definition.

## Backup

To backup the database:

```bash
# Create a backup
cp data/autota.db data/autota.db.backup

# Or export to SQL
sqlite3 data/autota.db .dump > backup.sql
```

## Reset Database

To start fresh:

```bash
# Remove existing database
rm data/autota.db

# Re-run setup (see above)
```
