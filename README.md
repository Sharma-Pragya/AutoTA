# AutoTA - LLM-Powered Parameterized Assessment Generator

AutoTA generates unique, computationally verified problem variants for STEM courses using LLMs. Instead of giving every student the same homework problem (which they can copy or feed to ChatGPT), AutoTA generates N unique variants of each problem with different parameters, each with a verified solution.

**The core principle**: LLMs generate, deterministic code verifies. These two components are intentionally decoupled.

## Current Status

**Phase 1 - CLI Generation + Verification Pipeline** ✅
- ✅ Domain-agnostic architecture with pluggable verifiers
- ✅ Boolean algebra verifier (K-maps, truth tables, Quine-McCluskey)
- ✅ Template-based variant generation
- ✅ 79 comprehensive tests
- ✅ CLI interface with rich output

**Phase 2 - Web Interface** ✅
- ✅ React frontend with pixel-perfect UI
- ✅ FastAPI backend with SQLite database
- ✅ Student name verification
- ✅ Auto-save with 3-second debounce
- ✅ Format validation for Boolean expressions
- ✅ Academic integrity attestation
- ✅ Instant grading with Layer 3 verifier integration

**Phase 2.1 - Schema Hardening & Multi-Attempt System** ✅
- ✅ Production-grade database schema (19 tables + 2 views)
- ✅ Institutional hierarchy (courses, offerings, sections, enrollments)
- ✅ Variant pool with 13+ variants per problem
- ✅ Multi-attempt support with configurable max_attempts
- ✅ Variant exclusion on retry (never see same variant twice)
- ✅ Weighted scoring (K-map: 2 pts, follow-up: 1 pt)
- ✅ Separated grading layer
- ✅ Draft answers with auto-save
- ✅ Attempt state machine
- ✅ Retry UI with attempts remaining

**Target Domain**: Digital logic (UCLA ECE M16) - Boolean algebra, K-maps, truth tables, logic gate analysis

**Future Phases**: In-class quiz sessions, instructor dashboard, analytics

## Features

- 🎯 **Unique Problem Variants**: Generate dozens or hundreds of unique variants from a single spec
- ✅ **Computational Verification**: Every solution is verified by deterministic Python code (never LLM-based)
- 🔌 **Pluggable Architecture**: Easy to add new problem types and verifiers
- 🚀 **Production Ready**: Batch generation, retry logic, detailed error reporting
- 📊 **Rich CLI**: Beautiful terminal output with progress tracking and statistics

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm

### 1. Installation

```bash
# Install Python dependencies
pip install -e .

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Database Setup

The `data/` directory exists but the database file is not committed to git. You need to create and seed it:

```bash
# Run migrations to create database schema
sqlite3 data/autota.db < migrations/001_initial_schema.sql
sqlite3 data/autota.db < migrations/002_schema_hardening.sql

# Backfill variant pool from existing assignments
python -m migrations.backfill_variant_pool

# Seed database with test data (3 students, 1 assignment, variant pool)
./seed.sh
```

This creates `data/autota.db` with:
- 19 tables + 2 views
- 3 test students (Pragya, Jane, Joe)
- 1 assignment (Homework 5 - K-maps)
- 39 variants in the pool (13 per problem type)

### 3. Run the Web Application

```bash
# Start both backend and frontend
./dev.sh

# Or start separately:
./start-backend.sh  # Backend on :8000
./start-frontend.sh # Frontend on :5173
```

### 4. Access the Application

- Frontend: http://localhost:5173/?sid=UID123456789
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Test Accounts:**
- Pragya Sharma: `sid=UID123456789`
- Jane Bruin: `sid=UID987654321`
- Joe Bruin: `sid=UID111222333`

### CLI Usage (Phase 1)

```bash
# Generate 5 K-map variants using CLI
autota generate --spec specs/example_kmap.yaml --num 5

# Verify existing variants
autota verify --input output/example_kmap/ --type kmap_simplification
```

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

## Problem Spec Format

Define problems using YAML:

```yaml
problem_type: kmap_simplification
topic: "Karnaugh Map Simplification"
description: "Simplify a Boolean function using a 4-variable K-map"
num_variants: 5
parameters:
  num_variables: 4
  num_minterms: [6, 10]  # range
  num_dont_cares: [0, 3]  # range
  require_edge_wrap: true
  variables: ["A", "B", "C", "D"]
reference_material: "materials/hw5_kmap.pdf"  # optional
answer_format: "boolean_expression"
difficulty: "medium"
```

## Generated Variant Format

Each variant is a JSON file:

```json
{
  "variant_id": "uuid-here",
  "problem_text": "Simplify F(A,B,C,D) with minterms m(0,2,5,7,8,10,13,15)...",
  "parameters": {
    "minterms": [0, 2, 5, 7, 8, 10, 13, 15],
    "dont_cares": [],
    "variables": ["A", "B", "C", "D"]
  },
  "solution": {
    "expression": "B'D' + BD",
    "method": "kmap"
  },
  "answer_format": "boolean_expression",
  "metadata": {
    "has_edge_wrap": true
  }
}
```

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
        # Deterministic verification logic here
        # NO LLM calls allowed!
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

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=autota --cov-report=html

# Run specific test file
pytest tests/test_boolean_verifier.py -v
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Format code
black autota/ tests/

# Lint code
ruff check autota/ tests/
```

## Project Structure

```
AutoTA/
├── README.md
├── .gitignore
├── pyproject.toml              # Package configuration
├── dev.sh                      # Start backend + frontend
├── seed.sh                     # Database seeding
├── autota/                     # Main package
│   ├── cli.py                  # Phase 1 CLI
│   ├── models.py               # Pydantic models
│   ├── template_generator.py  # Variant generation
│   ├── verify/                 # Phase 1 — Verification
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── boolean_verifier.py
│   │   └── quine_mccluskey.py
│   └── web/                    # Phase 2 — Web backend
│       ├── app.py              # FastAPI application
│       ├── db.py               # Database utilities
│       ├── seed.py             # Database seeding
│       ├── variant_draw.py     # Phase 2.1 — Variant pool
│       └── routes/
│           ├── auth.py         # Name verification
│           ├── assignment.py   # Assignment retrieval
│           ├── submit.py       # Submission & grading
│           └── retry.py        # Phase 2.1 — Retry
├── frontend/                   # Phase 2 — React UI
│   └── src/
│       ├── screens/            # UI screens
│       ├── components/         # Reusable components
│       ├── api.js              # API client
│       ├── utils.js            # Format validation
│       └── styles.js           # Style constants
├── migrations/
│   ├── 001_initial_schema.sql
│   ├── 002_schema_hardening.sql
│   └── backfill_variant_pool.py
├── specs/
│   ├── PHASE2_SPEC.md
│   └── PHASE2.1_SCHEMA_MIGRATION.md
├── tests/                      # 79 Phase 1 tests
├── docs/
│   ├── phase2/                 # Phase 2 documentation
│   └── ui-prototype.jsx
└── data/                       # Gitignored — SQLite DB
```

## Design Principles

1. **Domain-Agnostic Core**: The orchestrator, CLI, models, and generator work for any problem type
2. **Verification is Never LLM-Based**: Verifiers are deterministic Python - no API calls
3. **Fail Loudly**: Failed variants are flagged clearly, never silently passed
4. **Everything is JSON**: Variants, results, reports - all structured data
5. **Pluggable Verifiers**: Add new problem types without modifying core code

## API Endpoints

### Phase 2
- `POST /api/verify-name` — Verify student identity
- `GET /api/assignment/{student_id}` — Get assignment with variants
- `POST /api/save-answer` — Auto-save draft answer
- `POST /api/submit` — Submit all answers for grading

### Phase 2.1
- `POST /api/retry/{student_id}/{assignment_id}` — Start new attempt
  - Verifies attempt_number < max_attempts
  - Draws fresh variants excluding prior ones
  - Returns new attempt info

## Database Schema (Phase 2.1)

### Core Tables
- `students`, `assignments`, `problems`, `variant_assignments`, `submissions`, `attempts`

### Institutional Hierarchy
- `courses`, `course_offerings`, `instructors`, `sections`, `enrollments`

### Phase 2.1 Extensions
- `variant_pool` — Reusable variant library
- `draft_answers` — Auto-save layer
- `grades` — Separated grading metadata
- `attempt_results` — Aggregate scores
- `quiz_sessions` — Future: in-class quizzes

### Views
- `v_student_attempt_status` — Retry eligibility
- `v_grade_report` — Grade export

## Roadmap

- [x] Phase 1: CLI generation + verification pipeline
- [x] Phase 2: Web UI with instant grading
- [x] Phase 2.1: Schema hardening & multi-attempt
- [ ] Phase 3: In-class quiz sessions with QR codes
- [ ] Phase 4: Instructor dashboard & analytics
- [ ] Phase 5: Additional problem types (circuits, truth tables)
- [ ] Phase 6: LMS integration (Canvas, Gradescope)
- [ ] Phase 7: Advanced analytics & learning insights

## Contributing

Contributions welcome! Key areas:

- New verifiers for different problem types
- Improved verification algorithms
- Better prompt engineering for higher success rates
- Documentation and examples

## License

[Add your license here]

## Citation

If you use AutoTA in your research or teaching, please cite:

```
[Add citation when published]
```

## Contact

[Add contact information]

---

Built with ❤️ for educators who want to maintain academic integrity while leveraging AI to scale personalized learning.
