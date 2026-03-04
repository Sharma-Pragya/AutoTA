# AutoTA — LLM-Powered Parameterized Assessment Generator

AutoTA generates unique, computationally verified problem variants for STEM courses using LLMs. Instead of giving every student the same homework problem (which they can copy or feed to ChatGPT), AutoTA generates N unique variants of each problem with different parameters, each with a verified solution.

**The core principle**: LLMs generate, deterministic code verifies. These two components are intentionally decoupled.

---

## Current Status

### Phase 1 — CLI Generation + Verification Pipeline ✅
- Domain-agnostic architecture with pluggable verifiers
- Boolean algebra verifier (K-maps, truth tables, Quine-McCluskey)
- Template-based variant generation
- 100 tests (79 Phase 1 + 21 quiz)
- CLI interface with rich output

### Phase 2 — Student Web UI ✅
- React 18 + Vite frontend (IBM Plex Sans/Mono, pixel-perfect prototype match)
- FastAPI backend with SQLite database
- Student name verification
- Question navigation with collapsible menu
- Auto-save with 3-second debounce
- Client-side format validation for Boolean expressions
- Academic integrity attestation
- Instant grading via Layer 3 verifier integration

### Phase 2.1 — Schema Hardening & Multi-Attempt System ✅
- Production-grade database schema (19 tables + 2 views)
- Institutional hierarchy (courses, offerings, sections, enrollments)
- Variant pool with 30+ variants per problem
- Multi-attempt support with configurable max_attempts
- Variant exclusion on retry (never see same variant twice)
- Weighted scoring (K-map: 2 pts, follow-up: 1 pt)
- Separated grading layer
- Draft answers with auto-save
- Attempt state machine with retry UI

### Phase 2.2 — Instructor Dashboard ✅
- Instructor dashboard at `/instructor`
- 5 views: Dashboard, Gradebook, Assignment Detail, Student Drill-Down, Roster
- Summary cards: active assignments, submission rates, class average
- Full gradebook: 30 students × 8 assignments score matrix
- Per-assignment: score distribution histogram, per-problem breakdown, per-student grades
- Per-student: all-assignment history with per-problem answers and feedback
- 30 seeded students across 2 sections, 8 assignments (hw, quiz, exam, project types)

### Phase 2.3 — In-Class Quiz Mode ✅
- Synchronous timed quizzes: instructor projects QR code, students scan on phones
- Server-authoritative timer (never trust client time); auto-closes on expiry
- Unlimited retries: instant score after each submit, best score per problem kept
- Graded by existing BooleanExpressionVerifier pipeline
- On quiz close: best scores written to main grade tables (appear in instructor dashboard)
- Student UI: mobile-first, sticky timer bar, progress dots, per-problem feedback
- Instructor UI: QR code display, live polling dashboard (3s), results review with correct answers
- Client-side QR code generation via `qrcode.react`
- Token-based auth on all instructor endpoints (`AUTOTA_INSTRUCTOR_TOKEN` env var)
- SQLite context manager — no connection leaks under concurrent load
- CSV gradebook export (`GET /api/instructor/gradebook/export`)
- React error boundaries on all quiz and dashboard components
- 21 dedicated quiz tests (timer, auto-close, best-score tracking, grade writeback)

---

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+, npm

### 1. One-time setup

```bash
./setup.sh
```

This creates a `.venv`, installs all Python dependencies, installs frontend npm packages, and seeds the database (30 students, 8 assignments, quiz session `QZ5A3F`).

### 2. Run the demo

```bash
./demo.sh
```

Opens 4 browser tabs automatically (student homework, instructor dashboard, instructor quiz control, student quiz view) with both servers running. Press Ctrl+C to stop.

### 3. Run for development

```bash
./dev.sh
```

**Optional — instructor auth token** (required before deploying):

```bash
export AUTOTA_INSTRUCTOR_TOKEN=your-secret-token
```

Without this, instructor endpoints are unprotected (dev-only convenience). The frontend reads the token from `VITE_INSTRUCTOR_TOKEN` in `frontend/.env.local`, or pass it via URL hash: `/instructor#token=your-secret-token`.

### 4. Access the application

| URL | Description |
|-----|-------------|
| `http://localhost:5173/?sid=UID123456789` | Student homework UI |
| `http://localhost:5173/instructor` | Instructor dashboard |
| `http://localhost:5173/instructor/quiz/QZ5A3F` | Instructor quiz control |
| `http://localhost:5173/quiz/QZ5A3F?sid=UID123456789` | Student quiz UI |
| `http://localhost:8000/docs` | API docs (Swagger) |

**Test accounts:**
- Pragya Sharma: `sid=UID123456789`
- Jane Bruin: `sid=UID987654321`
- Joe Bruin: `sid=UID111222333`

### 5. Reset quiz session for re-testing

```bash
python -c "
import sqlite3
conn = sqlite3.connect('data/autota.db')
conn.execute('DELETE FROM quiz_submissions WHERE quiz_session_id = 1')
conn.execute('DELETE FROM quiz_participants WHERE quiz_session_id = 1')
conn.execute(\"UPDATE quiz_sessions SET status='pending', started_at=NULL, closed_at=NULL WHERE code='QZ5A3F'\")
conn.commit(); conn.close()
print('Reset done')
"
```

---

## CLI Usage (Phase 1)

```bash
# Generate 5 K-map variants
autota generate --spec specs/example_kmap.yaml --num 5

# Verify existing variants
autota verify --input output/example_kmap/ --type kmap_simplification
```

---

## Architecture

```
┌─────────────────┐
│  Problem Spec   │  YAML file defining problem constraints
│   (YAML)        │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Prompt Builder  │  Constructs prompts for Claude API
└────────┬────────┘
         │
         v
┌─────────────────┐
│   Generator     │  Calls Claude API, parses JSON response
│  (Claude API)   │
└────────┬────────┘
         │
         v
┌─────────────────┐
│   Verifier      │  Deterministic Python verification
│  (No LLMs!)     │  • Boolean algebra (truth tables)
└────────┬────────┘  • Future: circuits, calculus, etc.
         │
         v
┌─────────────────┐
│     Output      │  Verified variants + summary report
│     (JSON)      │
└─────────────────┘
```

---

## API Endpoints

### Student
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/verify-name` | Verify student identity |
| `GET` | `/api/assignment/{student_id}` | Get assignment with variants |
| `POST` | `/api/save-answer` | Auto-save draft answer |
| `POST` | `/api/submit` | Submit all answers for grading |
| `POST` | `/api/retry/{student_id}/{assignment_id}` | Start new attempt |

### Quiz (Student)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/quiz/{code}/join` | Join quiz, draw variants |
| `GET` | `/api/quiz/{code}/status` | Poll status + time remaining |
| `POST` | `/api/quiz/{code}/submit` | Submit answers, get instant score |

### Instructor — Dashboard
All instructor endpoints require `X-Instructor-Token` header when `AUTOTA_INSTRUCTOR_TOKEN` is set.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/instructor/dashboard` | Summary cards + assignment table |
| `GET` | `/api/instructor/gradebook` | Full student × assignment matrix |
| `GET` | `/api/instructor/gradebook/export` | Download gradebook as CSV |
| `GET` | `/api/instructor/assignment/{id}` | Score distribution + per-problem breakdown |
| `GET` | `/api/instructor/student/{id}` | Per-student all-assignment history |
| `GET` | `/api/instructor/roster` | Student directory |

### Instructor — Quiz
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/instructor/quiz/create` | Create new quiz session |
| `GET` | `/api/instructor/quiz/{code}/meta` | Quiz metadata |
| `POST` | `/api/instructor/quiz/{code}/start` | Start quiz (starts timer) |
| `POST` | `/api/instructor/quiz/{code}/close` | End quiz + write grades |
| `POST` | `/api/instructor/quiz/{code}/review` | Enter review mode |
| `GET` | `/api/instructor/quiz/{code}/live` | Live stats (poll every 3s) |
| `GET` | `/api/instructor/quiz/{code}/results` | Final results + per-problem breakdown |

---

## Project Structure

```
AutoTA/
├── autota/
│   ├── cli.py                      # Phase 1 CLI
│   ├── models.py                   # Pydantic models
│   ├── template_generator.py       # Variant generation
│   ├── verify/                     # Phase 1 — Verification
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── boolean_verifier.py
│   │   └── quine_mccluskey.py
│   └── web/                        # Phase 2+ — Web backend
│       ├── app.py                  # FastAPI application
│       ├── auth.py                 # Instructor token auth dependency
│       ├── db.py                   # DB init, connection, context manager
│       ├── seed.py                 # Seed 30 students + 8 assignments
│       └── routes/
│           ├── auth.py             # Name verification
│           ├── assignment.py       # Assignment retrieval
│           ├── submit.py           # Submission + grading
│           ├── retry.py            # Phase 2.1 — Retry
│           ├── instructor.py       # Phase 2.2 — Instructor dashboard + CSV export
│           └── quiz.py             # Phase 2.3 — Quiz mode
├── frontend/
│   └── src/
│       ├── App.jsx                 # Path-based routing + error boundaries
│       ├── api.js                  # API client
│       ├── utils.js                # Utilities
│       ├── components/
│       │   └── ErrorBoundary.jsx   # React error boundary
│       ├── screens/                # Student homework screens
│       │   ├── NameCheck.jsx
│       │   ├── Landing.jsx
│       │   ├── Question.jsx
│       │   ├── MainPage.jsx
│       │   ├── Attestation.jsx
│       │   ├── Review.jsx
│       │   └── InstructorDashboard.jsx
│       ├── quiz/                   # Phase 2.3 — Student quiz UI
│       │   ├── QuizApp.jsx
│       │   └── quizApi.js
│       └── instructor/             # Phase 2.3 — Instructor quiz UI
│           └── screens/
│               └── InstructorQuiz.jsx
├── migrations/
│   ├── 002_schema_hardening.sql
│   ├── 004_quiz_mode.sql           # quiz_submissions + quiz_participants
│   ├── run_004.py                  # Safe migration runner (checks existing columns)
│   ├── seed_quiz.py                # Seeds QZ5A3F test session
│   └── backfill_variant_pool.py
├── specs/
│   ├── PHASE2_SPEC.md
│   ├── PHASE2.1_SCHEMA_MIGRATION.md
│   ├── PHASE2.2_INSTRUCTOR_DASHBOARD.md
│   └── PHASE2.3_QUIZ_MODE.md
├── docs/
│   ├── ui-prototype.jsx            # Student UI prototype
│   ├── autota-instructor-prototype-v2.jsx
│   └── autota-quiz-prototype.jsx
├── tests/                          # 100 tests
│   ├── test_quiz.py                # Phase 2.3 — 21 quiz logic tests
│   └── ...                         # Phase 1 tests
├── data/                           # Gitignored — SQLite DB lives here
└── pyproject.toml
```

---

## Database Schema

### Core Tables
`students`, `assignments`, `problems`, `variant_pool`, `variant_assignments`, `submissions`, `grades`, `attempts`, `attempt_results`, `draft_answers`

### Institutional Hierarchy
`courses`, `course_offerings`, `instructors`, `sections`, `enrollments`

### Quiz Mode (Phase 2.3)
`quiz_sessions`, `quiz_submissions`, `quiz_participants`

### Views
- `v_student_attempt_status` — retry eligibility
- `v_grade_report` — grade export

---

## Adding New Problem Types

1. **Create a verifier** in `autota/verify/`:

```python
from autota.verify.base import Verifier
from autota.verify.registry import register_verifier
from autota.models import ProblemVariant, VerificationResult

@register_verifier
class MyVerifier(Verifier):
    @property
    def problem_type(self) -> str:
        return "my_problem_type"

    def verify(self, variant: ProblemVariant) -> VerificationResult:
        # Deterministic verification logic here — no LLM calls
        pass
```

2. **Create a spec** in `specs/`:

```yaml
problem_type: my_problem_type
# ... your parameters ...
```

3. **Generate and verify**:

```bash
autota generate --spec specs/my_problem.yaml
```

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=autota --cov-report=html

# Run specific test file
pytest tests/test_boolean_verifier.py -v
```

---

## Design Principles

1. **Domain-Agnostic Core**: The orchestrator, CLI, models, and generator work for any problem type
2. **Verification is Never LLM-Based**: Verifiers are deterministic Python — no API calls
3. **Fail Loudly**: Failed variants are flagged clearly, never silently passed
4. **Everything is JSON**: Variants, results, reports — all structured data
5. **Pluggable Verifiers**: Add new problem types without modifying core code
6. **Server-Authoritative**: Quiz timers and grading are always computed server-side

---

## Roadmap

- [x] Phase 1: CLI generation + verification pipeline
- [x] Phase 2: Student web UI with instant grading
- [x] Phase 2.1: Schema hardening & multi-attempt system
- [x] Phase 2.2: Instructor dashboard & gradebook
- [x] Phase 2.3: In-class quiz mode with live stats
- [ ] Phase 3: Deployment (serve frontend via FastAPI, production hosting)
- [ ] Phase 4: Additional problem types (circuits, truth tables, FSMs)
- [ ] Phase 5: LMS integration (Canvas, Gradescope CSV export)
- [ ] Phase 6: Advanced analytics & learning insights

---

## License

[Add your license here]
