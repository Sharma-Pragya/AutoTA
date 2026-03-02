# Changelog

All notable changes to AutoTA will be documented in this file.

## [Phase 2.1] - 2026-03-01

### Added - Schema Hardening & Multi-Attempt System
- Production-grade database schema with 19 tables and 2 views
- Institutional hierarchy: courses, course_offerings, instructors, sections, enrollments
- Variant pool system with 13+ variants per problem type
- Multi-attempt support with configurable max_attempts per assignment
- Variant exclusion logic: students never see same variant twice on retry
- Weighted scoring system (K-map problems: 2 pts, follow-up: 1 pt)
- Separated grading layer with dedicated grades table
- Draft answers table for mutable auto-save layer
- Attempt state machine: created → in_progress → graded
- POST /api/retry/{student_id}/{assignment_id} endpoint
- Retry UI with "Start New Attempt" button and attempts remaining indicator
- Max attempts reached warning on landing page
- Points display on question screen
- Attempt counter shows "Attempt N of M"

### Changed
- GET /api/assignment now returns attempt.status, max_attempts, points per problem, can_retry, attempts_remaining
- POST /api/submit now uses attempt_id, writes to grades table, computes weighted scores
- POST /api/save-answer now writes to draft_answers table
- variant_assignments table now has attempt_id foreign key
- submissions table now has answer_normalized column
- problems table now has problem_type, points, depends_on_problem_id columns
- assignments table now has offering_id, type, max_attempts, time_limit_minutes, opens_at, closes_at columns
- attempts table now has status, attestation_signed, attestation_signed_at columns

### Database Schema
- Created: variant_pool, draft_answers, grades, attempt_results, quiz_sessions
- Created: courses, course_offerings, instructors, sections, enrollments
- Created views: v_student_attempt_status, v_grade_report
- Migration: migrations/002_schema_hardening.sql
- Backfill: migrations/backfill_variant_pool.py

## [Phase 2] - 2026-02-28

### Added - Web Interface
- React 18 frontend with Vite
- FastAPI backend with SQLite database
- 6 database tables: students, assignments, problems, variant_assignments, submissions, attempts
- Name verification screen with case-insensitive matching
- Landing page with assignment overview
- Question navigation with dropdown menu
- Auto-save with 3-second debounce
- Format validation for Boolean expressions
- Academic integrity attestation
- Review page with answer summary
- Instant grading with Layer 3 verifier integration
- Submission confirmation screen
- 5 API endpoints:
  - POST /api/verify-name
  - GET /api/assignment/{student_id}
  - POST /api/save-answer
  - POST /api/submit
  - GET /api/health
- Database seeding script with 3 test students
- Development server scripts (dev.sh, seed.sh)
- IBM Plex Sans & Mono fonts
- Pixel-perfect UI matching design prototype

### Frontend Components
- NameCheck.jsx - Student identity verification
- Landing.jsx - Assignment overview
- Question.jsx - Problem display with answer input
- MainPage.jsx - Navigation hub
- Attestation.jsx - Academic integrity pledge
- Review.jsx - Submit confirmation
- MenuDropdown.jsx - Question navigation

### Backend Routes
- routes/auth.py - Name verification
- routes/assignment.py - Assignment data retrieval
- routes/submit.py - Answer submission and grading

## [Phase 1] - 2026-02-27

### Added - CLI Generation & Verification Pipeline
- Domain-agnostic architecture with pluggable verifiers
- Boolean algebra verifier using truth table evaluation
- Quine-McCluskey algorithm for minimal SOP expressions
- Template-based variant generator for K-map problems
- Layer 3 grading system with partial credit
- Detailed feedback generation
- CLI commands: generate, verify
- Pydantic models for type safety
- Verifier registry system
- 79 comprehensive tests
- Problem spec YAML format
- JSON output format for variants

### Core Modules
- autota/verify/boolean_verifier.py - Boolean expression verification
- autota/verify/quine_mccluskey.py - Minimal expression solver
- autota/template_generator.py - Variant generation
- autota/models.py - Data models
- autota/cli.py - Command-line interface

### Tests
- 79 passing tests covering:
  - Boolean expression parsing
  - Truth table evaluation
  - Quine-McCluskey algorithm
  - Template generation
  - Grading logic
  - Integration workflows
