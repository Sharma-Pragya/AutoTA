# AutoTA Phase 2 — Web UI Implementation Spec

## For Claude Code

Read this entire file before writing any code. Then read:
1. `ARCHITECTURE.md` — the system design (you are building Layer 2)
2. `docs/ui-prototype.jsx` — the visual reference (a working React prototype of every screen)
3. `autota/` — the existing Phase 1 codebase (you wire into this, do not rewrite it)

---

## What You Are Building

A web application where students:
1. Verify their identity (name check against DB)
2. View an exam/assignment with multiple questions (some with sub-parts)
3. Answer each question in structured input fields
4. Check answer format client-side before submitting
5. Navigate freely between questions via a collapsible menu
6. Sign an academic integrity attestation
7. Review all answers and submit
8. Get graded by the existing Layer 3 verifiers (deterministic, instant)

The backend serves pre-generated problem variants (from Phase 1) to authenticated students. It grades submissions using the existing `autota.verify` module. It tracks attempts in SQLite.

---

## Tech Stack

### Backend
- **FastAPI** (Python) — lives in `autota/web/`
- **SQLite** via `sqlite3` stdlib (no ORM for now) — DB file at `data/autota.db` (gitignored)
- **Uvicorn** as the ASGI server
- Imports and uses existing `autota.verify`, `autota.models`, `autota.template_generator` directly

### Frontend
- **React 18** with Vite — lives in `frontend/`
- **No component library** — plain CSS/Tailwind, matching the prototype styling exactly
- Communicates with backend via `fetch()` to `/api/` endpoints
- The prototype in `docs/ui-prototype.jsx` is the EXACT visual spec. Match it pixel-for-pixel: colors, fonts, spacing, layout, component structure. Use IBM Plex Sans + IBM Plex Mono from Google Fonts.

### Dev Setup
- `pip install fastapi uvicorn` (add to pyproject.toml dependencies)
- `cd frontend && npm create vite@latest . -- --template react && npm install`
- Backend runs on `:8000`, frontend on `:5173` with Vite proxy to backend
- Single `./dev.sh` script that starts both

---

## Directory Structure (new files only)

```
AutoTA/
├── autota/
│   └── web/
│       ├── __init__.py
│       ├── app.py              # FastAPI app, CORS, lifespan
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── auth.py         # POST /api/verify-name
│       │   ├── assignment.py   # GET /api/assignment/{student_id}
│       │   ├── submit.py       # POST /api/submit
│       │   └── quiz.py         # Quiz session endpoints (stub for now)
│       ├── db.py               # SQLite setup, migrations, queries
│       └── seed.py             # CLI command to seed DB with students + variants
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main app (adapt from prototype)
│   │   ├── screens/
│   │   │   ├── NameCheck.jsx
│   │   │   ├── Landing.jsx
│   │   │   ├── Question.jsx
│   │   │   ├── MainPage.jsx
│   │   │   ├── Attestation.jsx
│   │   │   └── Review.jsx
│   │   ├── components/
│   │   │   ├── MenuDropdown.jsx
│   │   │   └── FormatChecker.jsx
│   │   ├── api.js              # fetch wrappers
│   │   └── styles.js           # Style objects (extract from prototype)
│   ├── index.html
│   ├── vite.config.js          # proxy /api to :8000
│   └── package.json
├── data/                       # gitignored
│   └── autota.db
├── docs/
│   └── ui-prototype.jsx        # Visual reference
├── dev.sh                      # Starts backend + frontend
└── seed.sh                     # Seeds DB with sample data
```

---

## Database Schema (SQLite)

```sql
-- Students enrolled in a course section
CREATE TABLE students (
    id TEXT PRIMARY KEY,              -- e.g. "UID123456789"
    name TEXT NOT NULL,               -- full name for verification
    email TEXT UNIQUE NOT NULL,       -- UCLA email
    section TEXT                      -- e.g. "1A"
);

-- An assignment or exam (maps to a spec YAML)
CREATE TABLE assignments (
    id TEXT PRIMARY KEY,              -- e.g. "hw5"
    title TEXT NOT NULL,              -- "Homework 5 — Karnaugh Map Simplification"
    course TEXT NOT NULL,             -- "ECE M16"
    spec_path TEXT NOT NULL,          -- path to YAML spec
    instructions TEXT,                -- JSON array of instruction strings
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

-- A problem within an assignment (supports sub-parts)
CREATE TABLE problems (
    id TEXT PRIMARY KEY,              -- e.g. "hw5_1a"
    assignment_id TEXT NOT NULL REFERENCES assignments(id),
    parent_label TEXT NOT NULL,       -- e.g. "1"
    sub_label TEXT,                   -- e.g. "a" or NULL if standalone
    display_order INTEGER NOT NULL,   -- ordering within assignment
    text TEXT NOT NULL,               -- problem statement
    minterms TEXT,                    -- JSON or NULL
    dont_cares TEXT,                  -- JSON or NULL
    hint TEXT,
    answer_format TEXT NOT NULL,      -- "boolean_expression", "value", "number"
    placeholder TEXT                  -- input placeholder text
);

-- A specific variant assigned to a student for a problem
CREATE TABLE variant_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL REFERENCES students(id),
    problem_id TEXT NOT NULL REFERENCES problems(id),
    variant_id TEXT NOT NULL,         -- UUID from ProblemVariant
    variant_json TEXT NOT NULL,       -- full ProblemVariant JSON (minus solution for student view)
    solution_json TEXT NOT NULL,      -- solution JSON (never sent to frontend)
    attempt_number INTEGER NOT NULL DEFAULT 1,
    assigned_at TEXT DEFAULT (datetime('now')),
    UNIQUE(student_id, problem_id, attempt_number)
);

-- Student submissions and grades
CREATE TABLE submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL REFERENCES students(id),
    problem_id TEXT NOT NULL REFERENCES problems(id),
    variant_assignment_id INTEGER NOT NULL REFERENCES variant_assignments(id),
    answer TEXT NOT NULL,
    score REAL,                       -- 0.0 to 1.0
    correct INTEGER,                  -- 0 or 1
    feedback TEXT,
    graded_at TEXT,
    submitted_at TEXT DEFAULT (datetime('now')),
    attestation_signed INTEGER DEFAULT 0  -- 1 if student signed attestation
);

-- Attempt tracking for retry system (Phase 4, schema ready now)
CREATE TABLE attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL REFERENCES students(id),
    assignment_id TEXT NOT NULL REFERENCES assignments(id),
    attempt_number INTEGER NOT NULL DEFAULT 1,
    started_at TEXT DEFAULT (datetime('now')),
    submitted_at TEXT,
    total_score REAL,
    UNIQUE(student_id, assignment_id, attempt_number)
);
```

---

## API Endpoints

### `POST /api/verify-name`

Verifies student identity. Called on the name check screen.

**Request:**
```json
{
  "student_id": "UID123456789",
  "name": "Pragya Sharma"
}
```

**Response (200):**
```json
{
  "verified": true,
  "student_name": "Pragya Sharma",
  "student_id": "UID123456789"
}
```

**Response (403):**
```json
{
  "verified": false,
  "error": "Name does not match our records for this assignment."
}
```

**How student_id is determined:** For Phase 2 MVP, it's passed as a URL parameter: `http://localhost:5173/?sid=UID123456789`. In production this would come from UCLA SSO / Google OAuth. The frontend reads `sid` from the URL and uses it for all API calls.

### `GET /api/assignment/{student_id}`

Returns the full assignment for a student, including their assigned variants (without solutions), attempt number, and problem structure.

**Response (200):**
```json
{
  "assignment": {
    "id": "hw5",
    "title": "Homework 5 — Karnaugh Map Simplification",
    "course": "ECE M16",
    "course_name": "Logic Design of Digital Systems",
    "quarter": "Spring 2026",
    "instructor": "Prof. Mani Srivastava",
    "instructions": ["..."]
  },
  "student": {
    "id": "UID123456789",
    "name": "Pragya Sharma",
    "attempt_number": 2
  },
  "problems": [
    {
      "id": "hw5_1a",
      "parent_label": "1",
      "sub_label": "a",
      "display_order": 1,
      "text": "Simplify the Boolean function F(A,B,C,D) defined by:",
      "minterms": "m(2, 5, 6, 7, 10, 12, 13, 15)",
      "dont_cares": "d(1, 3)",
      "hint": "Look for groupings that wrap around the K-map edges.",
      "answer_format": "boolean_expression",
      "placeholder": null
    }
  ],
  "existing_answers": {
    "hw5_1a": "A'B + CD",
    "hw5_1b": ""
  }
}
```

**Key behavior:**
- If the student has a prior incomplete attempt (started but not submitted), return their saved answers in `existing_answers`
- If this is a retry attempt, the variant_assignments will be different (new variants)
- Solutions are NEVER included in this response

### `POST /api/save-answer`

Auto-saves a single answer as the student types (debounced on frontend, every 3 seconds of inactivity). Does NOT grade.

**Request:**
```json
{
  "student_id": "UID123456789",
  "problem_id": "hw5_1a",
  "answer": "A'B + CD"
}
```

**Response (200):**
```json
{ "saved": true }
```

### `POST /api/check-format`

Client-side format validation is primary (see prototype), but this endpoint provides server-side validation as backup.

**Request:**
```json
{
  "answer": "A'B + CD",
  "answer_format": "boolean_expression"
}
```

**Response (200):**
```json
{
  "valid": true,
  "message": "Format OK — valid Boolean expression."
}
```

### `POST /api/submit`

Submits all answers for grading. This is the final submit — triggers Layer 3 grading.

**Request:**
```json
{
  "student_id": "UID123456789",
  "assignment_id": "hw5",
  "attestation_signed": true,
  "answers": {
    "hw5_1a": "A'B + CD",
    "hw5_1b": "1",
    "hw5_2": "B' + C'D",
    "hw5_3a": "D + A'C",
    "hw5_3b": "5",
    "hw5_3c": "A'C'D' + ACD'"
  }
}
```

**Response (200):**
```json
{
  "submitted": true,
  "timestamp": "2026-03-01T12:00:00Z",
  "results": {
    "hw5_1a": { "correct": true, "score": 1.0, "feedback": "Correct! ..." },
    "hw5_1b": { "correct": true, "score": 1.0, "feedback": "Correct." },
    "hw5_2": { "correct": false, "score": 0.75, "feedback": "Incorrect. 4/16 rows wrong..." }
  },
  "total_score": 0.875
}
```

**Grading logic:**
- For each answer, look up the student's variant_assignment for that problem
- Reconstruct a `ProblemVariant` object from the stored variant JSON + solution JSON
- Call `verifier.grade(variant, student_answer)` using the existing `autota.verify.registry.get_verifier()`
- Store the `GradeResult` in the `submissions` table
- For answer_format "value" and "number": exact match against solution
- For answer_format "boolean_expression": use `BooleanVerifier.grade()` (truth table evaluation)

### `GET /api/results/{student_id}/{assignment_id}`

Returns grading results after submission.

**Response (200):** Same shape as the `POST /api/submit` response.

---

## Seeding Script

`autota/web/seed.py` (also accessible via `python -m autota.web.seed` or `./seed.sh`):

1. Creates the SQLite DB and tables if they don't exist
2. Inserts sample students:
   ```
   UID123456789, "Pragya Sharma", "pragya@ucla.edu", "1A"
   UID987654321, "Jane Bruin", "jbruin@ucla.edu", "1A"
   UID111222333, "Joe Bruin", "joebruin@ucla.edu", "1B"
   ```
3. Creates a sample assignment "hw5" with the 6 problems matching the prototype (Q1a, Q1b, Q2, Q3a, Q3b, Q3c)
4. Runs `TemplateGenerator` to generate variants for each K-map problem
5. Assigns variants to each student (each student gets different variants)
6. Creates attempt records (Pragya on attempt 2, others on attempt 1)

This lets you test the full flow immediately after seeding.

---

## Frontend Implementation Notes

### Adapting the Prototype

The prototype in `docs/ui-prototype.jsx` is a single-file React component with all screens, state management, and styles. To implement:

1. **Split into screen components** matching the directory structure above
2. **Replace hardcoded data** with `fetch()` calls to the API
3. **Keep the styles exactly as-is** — extract the `S` object into `styles.js`
4. **Keep the format validator** — it runs client-side for instant feedback. The server-side `/api/check-format` is a fallback.

### State Management

- Use React Context or simple prop drilling (the prototype uses prop drilling, which is fine for this scale)
- `studentId` comes from URL param `?sid=...`
- After name verification, store `studentName` and `attemptNumber` in state
- `answers` object: `{ [problem_id]: string }` — auto-saved to backend on debounced changes
- On page load, `GET /api/assignment/{sid}` returns existing answers if any (resume support)

### Key Behaviors to Preserve

1. **Name check screen**: First screen. Input must match DB name (case-insensitive). Wrong name = error + Begin button disabled. Correct = green banner + Begin enabled.
2. **Landing page**: Shows student name, attempt number, course info, instructions. Begin button bottom-right.
3. **Question page**: Student name + attempt displayed above problem label. Collapsible menu in top-right header. Back button on Q2+ goes to previous question. Back on Q1 goes to Main Page.
4. **Menu dropdown**: Collapsible by parent question. Q1 ▶ expands to show a, b. Q2 is flat (no sub-parts). Status dots: ○ none, ◐ partial (amber), ● all done (green). Current question's parent auto-expands.
5. **Check Format**: Client-side validation. Different validators for boolean_expression, value, number.
6. **Last question → Attestation**: Not Review. The attestation screen gates the review.
7. **Attestation**: Dynamic student name. Checkbox required. Links to `https://studentconduct.ucla.edu/2026-individual-student-code`. Must be checked to proceed.
8. **Review page**: Shows all answers with format validation status. Click any row to jump back. Two-step submit confirmation.
9. **Submitted screen**: Shows all answers as recorded. No further action possible.

### Auto-save

Debounce answer saves: when the student types in an answer box, wait 3 seconds after they stop typing, then `POST /api/save-answer`. Show a subtle "Saving..." / "Saved ✓" indicator near the answer box. This prevents data loss if the browser crashes.

### Responsive

The prototype is designed for desktop but should work on tablets and phones (for QR quiz mode in Phase 5). Use the existing max-width constraints (620px for narrow cards, 760px for wide cards). The answer textarea and buttons should stack vertically on narrow screens.

---

## Vite Config

```js
// frontend/vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

---

## Dev Script

```bash
#!/bin/bash
# dev.sh — starts backend and frontend

# Start FastAPI backend
echo "Starting backend on :8000..."
cd "$(dirname "$0")"
uvicorn autota.web.app:app --reload --port 8000 &
BACKEND_PID=$!

# Start React frontend
echo "Starting frontend on :5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
echo "AutoTA running: backend :8000, frontend :5173"
wait
```

---

## What NOT to Build (out of scope for Phase 2)

- Google OAuth / UCLA SSO (use URL param `?sid=` for now)
- QR quiz mode (stub the endpoint, don't implement)
- Retry loop / new variant generation on retry (Phase 4)
- LLM-assisted grading Tier 2 (Phase 3)
- Human review queue Tier 3 (Phase 3)
- Analytics dashboard
- Discord bot integration
- Timer / time-limited sessions

---

## Testing

1. After building, run `./seed.sh` to populate the DB
2. Open `http://localhost:5173/?sid=UID123456789`
3. Type "Pragya Sharma" on name check → should verify
4. Click through all screens, answer questions, check format, submit
5. Verify that grading results are correct (use known K-map solutions)
6. Open `http://localhost:5173/?sid=UID987654321` → should show different variants
7. Run existing `pytest` — all 79 Phase 1 tests must still pass (you did not break anything)

---

## Build Order

1. Set up `frontend/` with Vite + React. Get a hello world rendering.
2. Set up `autota/web/app.py` with FastAPI. Get `/api/health` returning `{"ok": true}`.
3. Implement `db.py` with schema creation.
4. Implement `seed.py` — seed students, assignment, problems, variants.
5. Implement `GET /api/assignment/{student_id}` — return assignment + problems.
6. Build frontend screens one at a time: NameCheck → Landing → Question → MainPage → Attestation → Review.
7. Wire auto-save (`POST /api/save-answer`).
8. Implement `POST /api/submit` with Layer 3 grading integration.
9. Test full flow end-to-end.
10. Run `pytest` to confirm Phase 1 tests still pass.
