# AutoTA Phase 2.3 — Quiz Mode

## Context

Phases 2.0-2.2 are complete: student web UI, production schema (19 tables), variant pool, retry system, and instructor dashboard with grade management + CSV export.

Now we add **in-class quiz mode** — a synchronous, timed, mobile-first assessment tool. The instructor projects a QR code, 200 students scan on their phones, answer 1-2 K-map problems in 10 minutes with **unlimited retries** (instant score feedback after each submit, best score kept), and the instructor watches live results on a dashboard.

Read these files first:
1. `PHASE2.2_INSTRUCTOR_DASHBOARD.md` — what exists
2. `docs/quiz-prototype.jsx` — **interactive prototype — MATCH THIS EXACTLY**
3. `autota/web/routes/` — existing backend routes
4. `autota/core/variant_draw.py` — variant assignment logic

---

## Key Differences from Homework Mode

| | Homework | Quiz |
|---|---|---|
| Timing | Async, days/weeks | Synchronous, 10 min |
| Device | Laptop | Phone (mobile-first) |
| Timer | Soft deadline | Server-enforced countdown |
| Retries | Fixed (e.g. 3 max) | **Unlimited until timer expires** |
| Score feedback | After final submit | **Instant after each submit** |
| Score recording | Best of N attempts | **Best score when quiz closes** |
| Attestation | Required | None (in-class) |
| Entry method | Direct URL with SID | QR code / short code |
| Instructor view | Post-hoc dashboard | **Live updating dashboard** |
| Variants | Pre-drawn from pool | Drawn once at quiz join |

---

## The Quiz Lifecycle

```
PENDING ──[instructor clicks Start]──> ACTIVE ──[timer expires OR instructor clicks End]──> CLOSED ──[instructor clicks Show Solutions]──> REVIEW
```

### States

**PENDING**: Quiz is created, QR code and short code are displayed. Students can join (hit the entry URL) but can't see problems yet. Instructor projects this screen.

**ACTIVE**: Timer is counting down. Students see problems and can submit answers. Each submit returns instant scores. Students can edit and resubmit unlimited times. Server tracks all attempts and keeps the best score per problem. Instructor sees live submission count, score distribution, and retry stats.

**CLOSED**: Timer expired or instructor manually ended the quiz. No more submissions accepted. Server returns 403 for any new submissions. Instructor sees final stats. "Show Solutions →" button appears.

**REVIEW**: Instructor projects the review screen showing each problem, the correct answer, and common wrong answers with counts. This is for the in-class walkthrough.

---

## Student Flow (Mobile)

### Entry Screen
- URL: `/quiz/{code}` or `/quiz?code={code}` or `/q/{code}`
- Shows quiz title, course name
- If code is in URL, auto-join
- If no code, show input field for manual entry
- **No attestation, no name check** — just join
- Student identified by `?sid=` URL param (or session, or cookie — same as homework mode for now)

### Waiting Screen (status = PENDING)
- "Waiting for quiz to start..."
- Shows quiz title and code
- **Polls server every 2 seconds** for status change to ACTIVE
- When ACTIVE detected, transitions to answering view

### Answering View (status = ACTIVE)
- **Timer bar** (sticky top): quiz title + attempt number (if retrying) on left, countdown on right
  - Bar is UCLA blue normally, turns red when ≤60 seconds remain
- **Best score banner** (shown only after first submit): "Current best: X%" in green banner
  - Reminds students their best score is kept
- **Progress dots**: one per problem, showing Q1/Q2
  - Blue = current, green checkmark = perfect on this problem, light blue = answered, gray = empty
- **Problem card**: label + points, problem text, minterms box (blue background), don't-cares if applicable
  - If problem already perfect (from previous attempt): green "✅ You already got this one right!" banner
  - If problem has a previous score < 100%: yellow "Previous best: X% — Try to improve!" banner
- **Answer input**: large textarea, monospace font, mobile-friendly sizing
- **Check Format button**: validates Boolean expression syntax (balanced parens, valid chars A-D, ', +, etc.)
- **Next →** / **Submit Quiz** (or **Resubmit** on retries): submit button is green
- **← Previous** link for going back

### Submit Confirmation Modal
- "Submit quiz?" / "Resubmit?"
- Shows N of M answered
- Warning if unanswered questions
- Green note: "✓ You'll see your score and can retry if time remains."
- "Go Back" / "Submit" buttons

### Result View (after each submit)
- Shows emoji based on score (🎉 ≥80%, 📊 50-79%, 💪 <50%)
- **This attempt score**: large number, color-coded
- **Best score note** (if best > this attempt): "✓ Best score: X%"
- **Per-problem breakdown**: problem label, score cell, feedback text
  - Shows "Best: X%" if previous attempt was better for that problem
- **If score < 100%**: "You can fix your answers and resubmit!" + blue "✏️ Edit & Resubmit" button + "Best score is recorded · X:XX remaining"
- **If perfect 100%**: "🎉 Perfect score! You can relax — your best score has been recorded."
- Timer still visible and counting

### Time's Up Screen (status = CLOSED)
- "⏰ Quiz Closed"
- Best score badge: large score + attempt count
- Per-problem best scores
- "Your instructor will review the solutions now."

---

## Instructor Flow (Desktop)

### Creating a Quiz (CLI for now)
```bash
python -m autota quiz create \
  --title "Quiz 3 — K-Map Simplification" \
  --time-limit 600 \
  --assignment-id quiz3
```
This creates a `quiz_sessions` row with a generated short code and status = PENDING.

### Pending Screen (`/instructor/quiz/{code}`)
- Dark header with "AutoTA · ECE M16 · Quiz Control"
- Centered card with:
  - Quiz title, problem count, time limit, "Unlimited retries", enrolled count
  - **QR code** (generated server-side or client-side using a library) pointing to `/quiz/{code}`
  - **Short code** displayed large in monospace (e.g. "QZ-5A3F")
  - **URL** shown below code: `autota.app/q/QZ5A3F`
  - "How it works" info box explaining the flow
  - Big green **"▶ Start Quiz (10 min)"** button

### Active Screen (LIVE)
- Header: dark (turns red when ≤60s), shows "● LIVE", large countdown timer, red "End Quiz" button
- **Live stats row** (4 cards):
  - Submitted: X/200 with progress bar
  - Retries: count + "X% retried"
  - Avg Best: percentage + "First: X%" subtext (shows improvement from retries)
  - Still Working: count of students who haven't submitted at all
- **Live score distribution** (left panel): 10-bin histogram using best scores, bars animate up as submissions come in
- **Recent Activity** (right panel): scrollable feed of recent submissions with "RETRY" badge in purple for resubmissions
- **Haven't Submitted Yet** panel: name chips for students who haven't submitted, so TAs can check on them
- **Polls every 3 seconds** for updated stats

### Closed Screen
- Shows final stats: submitted count, avg best score, avg first score, median, retry count + "X% improved"
- Final score distribution histogram
- **"Show Solutions →"** button

### Review Screen (projected for class)
- For each problem:
  - Problem text with minterms
  - **Correct answer** in large green box
  - **% correct** (using best scores)
  - **Common wrong answers** table: answer in red monospace + student count

---

## Database Changes

### New table: `quiz_sessions`

```sql
CREATE TABLE quiz_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id TEXT NOT NULL REFERENCES assignments(id),
    code TEXT NOT NULL UNIQUE,           -- Short code e.g. "QZ5A3F"
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'closed', 'review')),
    time_limit_seconds INTEGER NOT NULL DEFAULT 600,
    started_at TEXT,                      -- Set when instructor clicks Start
    closed_at TEXT,                       -- Set when timer expires or instructor clicks End
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    created_by TEXT                       -- Instructor ID
);
```

### New table: `quiz_submissions`

Tracks every submit (for retry history). Different from homework `submissions` because quizzes allow unlimited rapid resubmission.

```sql
CREATE TABLE quiz_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_session_id INTEGER NOT NULL REFERENCES quiz_sessions(id),
    student_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL DEFAULT 1,  -- 1, 2, 3... increments per student
    answers_json TEXT NOT NULL,                  -- JSON: {"quiz3_1": "B'D' + BD", "quiz3_2": "A'B + BC'"}
    scores_json TEXT,                            -- JSON: {"quiz3_1": {"score": 1.0, "correct": true, "feedback": "..."}, ...}
    total_score REAL,                            -- 0.0 to 1.0
    total_points_earned REAL,
    is_best INTEGER NOT NULL DEFAULT 0,          -- 1 if this is the student's current best attempt
    submitted_at TEXT NOT NULL DEFAULT (datetime('now')),
    graded_at TEXT,
    UNIQUE(quiz_session_id, student_id, attempt_number)
);
CREATE INDEX idx_quiz_sub_session_student ON quiz_submissions(quiz_session_id, student_id);
```

### New table: `quiz_participants`

Tracks who joined the quiz (even if they didn't submit).

```sql
CREATE TABLE quiz_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_session_id INTEGER NOT NULL REFERENCES quiz_sessions(id),
    student_id TEXT NOT NULL,
    joined_at TEXT NOT NULL DEFAULT (datetime('now')),
    variant_assignments_json TEXT,  -- JSON mapping problem_id → variant_pool_id (drawn at join)
    UNIQUE(quiz_session_id, student_id)
);
```

### Migration: `migrations/004_quiz_mode.sql`

Contains the 3 tables above + indexes.

### Variant Assignment for Quizzes

When a student joins a quiz, draw variants for all problems in the assignment from the variant pool (same logic as `variant_draw.py`). Store the mapping in `quiz_participants.variant_assignments_json`. Each student gets a unique combination.

---

## API Endpoints

### Quiz Management (Instructor)

**`POST /api/instructor/quiz/create`**
Create a new quiz session. Generates a random 6-char alphanumeric code.
```json
{ "assignment_id": "quiz3", "time_limit_seconds": 600 }
→ { "quiz_session_id": 1, "code": "QZ5A3F", "status": "pending" }
```

**`POST /api/instructor/quiz/{code}/start`**
Set status to "active", record `started_at = now()`.
```json
→ { "status": "active", "started_at": "...", "expires_at": "..." }
```

**`POST /api/instructor/quiz/{code}/close`**
Set status to "closed", record `closed_at = now()`. Called by timer expiry OR manual close.

**`POST /api/instructor/quiz/{code}/review`**
Set status to "review". Returns solutions data for the review screen.

**`GET /api/instructor/quiz/{code}/live`**
Polled every 3 seconds during active quiz. Returns:
```json
{
  "status": "active",
  "time_remaining_seconds": 342,
  "total_enrolled": 200,
  "submitted_count": 156,
  "retry_count": 68,
  "not_submitted_count": 44,
  "avg_best_score": 0.73,
  "avg_first_score": 0.58,
  "score_distribution": [2, 5, 8, 12, 18, 22, 28, 32, 20, 9],
  "recent_submissions": [
    { "name": "Alex Chen", "score": 0.85, "is_retry": true, "submitted_at": "..." }
  ],
  "not_submitted": [
    { "name": "Carmen Rivera", "uid": "UID100000002" }
  ]
}
```

**`GET /api/instructor/quiz/{code}/results`**
Final results after close. Includes per-problem breakdown, common errors, score stats.
```json
{
  "status": "closed",
  "submitted_count": 184,
  "avg_best_score": 0.76,
  "avg_first_score": 0.61,
  "median_best_score": 0.80,
  "retry_count": 98,
  "improvement_rate": 0.72,
  "problems": [
    {
      "id": "quiz3_1", "label": "Q1", "points": 10,
      "text": "...", "minterms": "...", "dont_cares": "...",
      "correct_answer": "B'D' + BD",
      "pct_correct": 0.68,
      "common_errors": [
        { "answer": "AB + CD", "count": 23 },
        { "answer": "A'B", "count": 15 }
      ]
    }
  ]
}
```

### Quiz Student Endpoints

**`POST /api/quiz/{code}/join`**
Student joins the quiz. Draws variants. Returns quiz info + status.
```json
{ "student_id": "UID123456789" }
→ {
  "quiz_session_id": 1,
  "status": "active",
  "time_remaining_seconds": 580,
  "problems": [
    { "id": "quiz3_1", "label": "Q1", "points": 10, "text": "...", "minterms": "m(0,2,5,7,...)", "dont_cares": "d(1,6)" }
  ]
}
```
If status is "pending", return problems but with `time_remaining_seconds: null` — client shows waiting screen.
If status is "closed" or "review", return 403.

**`GET /api/quiz/{code}/status`**
Polled by student every 2 seconds when waiting. Returns `{ "status": "pending"|"active"|"closed"|"review", "time_remaining_seconds": N }`.

**`POST /api/quiz/{code}/submit`**
Submit answers. Server grades instantly and returns results.
```json
{
  "student_id": "UID123456789",
  "answers": { "quiz3_1": "B'D' + BD", "quiz3_2": "A'B + BC'" }
}
→ {
  "attempt_number": 2,
  "scores": {
    "quiz3_1": { "score": 1.0, "correct": true, "feedback": "Correct!" },
    "quiz3_2": { "score": 0.35, "correct": false, "feedback": "Partially correct. 10/16 rows match." }
  },
  "total_score": 0.675,
  "best_scores": {
    "quiz3_1": 1.0,
    "quiz3_2": 0.5
  },
  "best_total_score": 0.75,
  "time_remaining_seconds": 245
}
```
**Critical**: server MUST check time remaining. If `closed_at` is set or `now() > started_at + time_limit_seconds`, return 403 `{ "error": "quiz_closed" }`.

---

## Timer Implementation

The timer is **server-authoritative**:
1. `quiz_sessions.started_at` + `time_limit_seconds` = expiry time
2. Every API call checks: `if now() > expiry → auto-close quiz`
3. Client displays countdown based on `time_remaining_seconds` from server
4. Client polls `/status` periodically to stay in sync
5. Server never trusts client-side time

**Auto-close**: a background check on every quiz endpoint request — if the quiz should be closed, close it automatically. No background worker needed for SQLite.

---

## QR Code Generation

Generate a QR code pointing to `/quiz/{code}?sid={from_url}` (or just `/quiz/{code}` if no SID available).

Options:
- **Client-side**: Use `qrcode` npm package to generate in the React component. Simpler, no server-side dependency.
- **Server-side**: Generate as SVG or PNG at `/api/quiz/{code}/qr`. More reliable for projection.

Recommend client-side (`qrcode.react` or `qr-code-styling`) for simplicity.

---

## Frontend Structure

```
frontend/src/
├── quiz/
│   ├── QuizApp.jsx            # Quiz layout + screen routing
│   ├── screens/
│   │   ├── QuizEntry.jsx      # Code entry / auto-join
│   │   ├── QuizWaiting.jsx    # Waiting for start (polls status)
│   │   ├── QuizActive.jsx     # Timer + problems + answer input
│   │   ├── QuizResult.jsx     # Post-submit score + retry button
│   │   └── QuizClosed.jsx     # Time's up, best score shown
│   ├── components/
│   │   ├── TimerBar.jsx       # Sticky countdown
│   │   ├── ProgressDots.jsx   # Problem navigation dots
│   │   ├── MintermBox.jsx     # Styled minterms display
│   │   ├── FormatChecker.jsx  # Boolean expression validator
│   │   └── ConfirmModal.jsx   # Submit confirmation
│   └── quizApi.js             # Quiz API wrappers
├── instructor/
│   ├── screens/
│   │   ├── QuizPending.jsx    # QR code + Start button
│   │   ├── QuizLive.jsx       # Live dashboard (polls /live)
│   │   ├── QuizClosed.jsx     # Final stats + Show Solutions button
│   │   └── QuizReview.jsx     # Solutions + common errors
```

### Routing

- `/quiz/{code}` → `QuizApp` (student quiz flow)
- `/q/{code}` → redirect to `/quiz/{code}`
- `/instructor/quiz/{code}` → instructor quiz control
- Existing routes (`/`, `/instructor`) unchanged

---

## Grading During Quiz

Use the existing grading pipeline:
1. Student submits → `POST /api/quiz/{code}/submit`
2. Server calls `grade_answer(problem, student_answer)` using existing `BooleanExpressionVerifier`
3. Scores stored in `quiz_submissions.scores_json`
4. Best score per student per problem tracked via `is_best` flag
5. When quiz closes, optionally copy best scores to the main `grades`/`attempt_results` tables for the instructor dashboard

### Writing Quiz Results to Main Grade Tables

After a quiz closes, the best `quiz_submission` for each student should be written into the standard grading pipeline:
1. Create an `attempt` row (status = "graded")
2. Create `submission` rows for each problem
3. Create `grade` rows from the quiz scores
4. Create `attempt_results` row with the aggregate

This way quiz scores appear in the instructor dashboard alongside homework scores, and can be exported to BruinLearn.

---

## Mobile-First CSS Considerations

The student quiz UI must work on phones:
- Max-width: 100vw, no horizontal scroll
- Touch targets: minimum 44px height for buttons
- Font sizes: 16px+ for inputs (prevents iOS zoom)
- No hover-dependent interactions
- Timer bar sticky at top
- Answer input fills available width
- Confirmation modal centered and sized for small screens

---

## What NOT to Build (Phase 2.3)

- Real authentication (still URL params)
- Quiz creation UI (use CLI)
- Quiz editing after creation
- Partial submissions (auto-save drafts)
- Student-to-student cheating detection
- WebSocket live updates (polling is fine for 3-5s intervals)
- Multiple quiz sessions simultaneously
- Quiz analytics over time

---

## Testing

1. Run migration: `sqlite3 data/autota.db < migrations/004_quiz_mode.sql`
2. Create a quiz via CLI
3. **Student flow**: Open `/quiz/{code}` on phone-width browser
   - Join → see waiting screen → (start quiz) → answer → submit → see scores → retry → resubmit → time expires → see final score
4. **Instructor flow**: Open `/instructor/quiz/{code}`
   - See QR code + Start button → Start → watch live stats update → End Quiz → see final stats → Show Solutions
5. **Timer enforcement**: Submit after quiz closes → should get 403
6. **Best score tracking**: Submit twice, verify best score is kept per problem
7. **Integration**: After quiz closes, verify scores appear in instructor dashboard
8. **Existing features**: homework UI still works, instructor dashboard still works, all 79 tests pass

---

## Build Order

1. Create `migrations/004_quiz_mode.sql` and run it
2. Add quiz CLI command for creating sessions
3. Implement quiz student endpoints: join, status, submit (with grading + best-score tracking)
4. Implement quiz instructor endpoints: create, start, close, review, live, results
5. Build student QuizApp: entry → waiting → active → result → closed screens
6. Build instructor quiz screens: pending → live → closed → review
7. Add QR code generation (client-side library)
8. Add quiz routing to App.jsx (`/quiz/{code}`, `/instructor/quiz/{code}`)
9. Implement quiz-close → write to main grade tables
10. Seed a test quiz with problems from the variant pool
11. Test full flow end-to-end on mobile-width viewport
12. Run `pytest`
