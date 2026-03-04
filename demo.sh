#!/bin/bash
# demo.sh — AutoTA demo setup script
# Resets the quiz session, starts both servers, and prints all demo links.
#
# Usage: ./demo.sh
# Stop:  Ctrl+C

set -e

DB=data/autota.db
QUIZ_CODE=QZ5A3F

# Resolve Python: prefer local venv, fall back to system python3
if [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
    UVICORN=".venv/bin/uvicorn"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
    UVICORN="$(python3 -m site --user-base 2>/dev/null)/bin/uvicorn"
    # Simplest fallback: just use python -m uvicorn
    UVICORN_CMD="$PYTHON -m uvicorn"
else
    echo "Python not found. Run ./setup.sh first."
    exit 1
fi
UVICORN_CMD="${UVICORN_CMD:-$UVICORN}"

# ── Colors ────────────────────────────────────────────────────────────────────
BOLD=$(tput bold)
RESET=$(tput sgr0)
GREEN=$(tput setaf 2)
BLUE=$(tput setaf 4)
YELLOW=$(tput setaf 3)
CYAN=$(tput setaf 6)
RED=$(tput setaf 1)

# ── Helpers ───────────────────────────────────────────────────────────────────
step() { echo ""; echo "${BOLD}${BLUE}▶ $1${RESET}"; }
ok()   { echo "  ${GREEN}✓${RESET} $1"; }
info() { echo "  ${CYAN}$1${RESET}"; }
warn() { echo "  ${YELLOW}⚠ $1${RESET}"; }
fail() { echo "  ${RED}✗ $1${RESET}"; exit 1; }
link() { echo "  ${BOLD}${CYAN}$1${RESET}  ${YELLOW}$2${RESET}"; }

# ── 0. Preflight checks ───────────────────────────────────────────────────────
echo ""
echo "${BOLD}╔══════════════════════════════════════════════════╗${RESET}"
echo "${BOLD}║         AutoTA — Demo Setup                      ║${RESET}"
echo "${BOLD}╚══════════════════════════════════════════════════╝${RESET}"

step "Checking prerequisites"

[ -f "$DB" ] || fail "Database not found at $DB. Run: ./setup.sh"
ok "Database exists"

$PYTHON -c "import fastapi" 2>/dev/null || fail "FastAPI not found. Run: ./setup.sh"
ok "FastAPI available"

[ -d "frontend/node_modules" ] || fail "Frontend deps missing. Run: cd frontend && npm install"
ok "Node modules present"

# ── 1. Reset quiz session + homework attempts ─────────────────────────────────
step "Resetting quiz session ($QUIZ_CODE → pending) and homework attempts"

$PYTHON -c "
import sqlite3
conn = sqlite3.connect('$DB')
conn.row_factory = sqlite3.Row

# Reset quiz
row = conn.execute(\"SELECT id, status FROM quiz_sessions WHERE code='$QUIZ_CODE'\").fetchone()
if not row:
    print('  Quiz session $QUIZ_CODE not found — run: python migrations/seed_quiz.py')
    exit(1)

conn.execute('DELETE FROM quiz_submissions WHERE quiz_session_id = ?', (row['id'],))
conn.execute('DELETE FROM quiz_participants WHERE quiz_session_id = ?', (row['id'],))
conn.execute(\"UPDATE quiz_sessions SET status='pending', started_at=NULL, closed_at=NULL WHERE id=?\", (row['id'],))

# Reset hw5 attempts for demo student (keep only attempt 1, clear its submission/score)
DEMO_STUDENT = 'UID123456789'
extra_attempts = conn.execute(
    \"SELECT id FROM attempts WHERE student_id=? AND assignment_id='hw5' AND attempt_number > 1\",
    (DEMO_STUDENT,)
).fetchall()
for a in extra_attempts:
    conn.execute('DELETE FROM submissions WHERE variant_assignment_id IN (SELECT id FROM variant_assignments WHERE attempt_id=?)', (a['id'],))
    conn.execute('DELETE FROM variant_assignments WHERE attempt_id=?', (a['id'],))
    conn.execute('DELETE FROM attempt_results WHERE attempt_id=?', (a['id'],))
    conn.execute('DELETE FROM attempts WHERE id=?', (a['id'],))

# Reset attempt 1 back to in_progress with no score
a1 = conn.execute(
    \"SELECT id FROM attempts WHERE student_id=? AND assignment_id='hw5' AND attempt_number=1\",
    (DEMO_STUDENT,)
).fetchone()
if a1:
    conn.execute('DELETE FROM submissions WHERE variant_assignment_id IN (SELECT id FROM variant_assignments WHERE attempt_id=?)', (a1['id'],))
    conn.execute('DELETE FROM attempt_results WHERE attempt_id=?', (a1['id'],))
    conn.execute(\"UPDATE attempts SET status='in_progress', submitted_at=NULL, total_score=NULL WHERE id=?\", (a1['id'],))

conn.commit()
conn.close()
print('ok')
" | grep -q ok && ok "Quiz reset to pending; hw5 attempts cleared for demo student" || fail "Could not reset quiz session. Run: python migrations/seed_quiz.py"

# ── 2. Kill any existing servers on our ports ─────────────────────────────────
step "Freeing ports 8000 and 5173"

lsof -ti:8000 | xargs kill -9 2>/dev/null && ok "Killed existing process on :8000" || ok "Port 8000 is free"
lsof -ti:5173 | xargs kill -9 2>/dev/null && ok "Killed existing process on :5173" || ok "Port 5173 is free"
sleep 1

# ── 3. Start backend ──────────────────────────────────────────────────────────
step "Starting backend (FastAPI on :8000)"

$UVICORN_CMD autota.web.app:app --port 8000 --log-level warning > /tmp/autota-backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > /tmp/autota-backend.pid

# Wait for backend to be ready
for i in $(seq 1 15); do
    curl -s http://localhost:8000/docs > /dev/null 2>&1 && break
    sleep 0.5
done
curl -s http://localhost:8000/docs > /dev/null 2>&1 && ok "Backend is up (pid $BACKEND_PID)" || fail "Backend failed to start. Check /tmp/autota-backend.log"

# ── 4. Start frontend ─────────────────────────────────────────────────────────
step "Starting frontend (Vite on :5173)"

(cd frontend && npm run dev --silent > /tmp/autota-frontend.log 2>&1) &
FRONTEND_PID=$!
echo $FRONTEND_PID > /tmp/autota-frontend.pid

# Wait for Vite to be ready
for i in $(seq 1 20); do
    curl -s http://localhost:5173 > /dev/null 2>&1 && break
    sleep 0.5
done
curl -s http://localhost:5173 > /dev/null 2>&1 && ok "Frontend is up (pid $FRONTEND_PID)" || fail "Frontend failed to start. Check /tmp/autota-frontend.log"

# ── 5. Open browser tabs ──────────────────────────────────────────────────────
step "Opening demo tabs in browser"

STUDENT_HW="http://localhost:5173/?sid=UID123456789"
INSTRUCTOR="http://localhost:5173/instructor"
INSTRUCTOR_QUIZ="http://localhost:5173/instructor/quiz/$QUIZ_CODE"
STUDENT_QUIZ="http://localhost:5173/quiz/$QUIZ_CODE?sid=UID123456789"
API_DOCS="http://localhost:8000/docs"

open "$STUDENT_HW"       && ok "Student homework UI"
sleep 0.3
open "$INSTRUCTOR"        && ok "Instructor dashboard"
sleep 0.3
open "$INSTRUCTOR_QUIZ"   && ok "Instructor quiz control"
sleep 0.3
open "$STUDENT_QUIZ"      && ok "Student quiz UI"

# ── 6. Demo guide ─────────────────────────────────────────────────────────────
echo ""
echo "${BOLD}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo "${BOLD}║                   DEMO LINKS                                ║${RESET}"
echo "${BOLD}╠══════════════════════════════════════════════════════════════╣${RESET}"
echo "${BOLD}║${RESET}"
link "║  1. Student Homework" "$STUDENT_HW"
link "║     → Name: Pragya Sharma" ""
echo "${BOLD}║${RESET}"
link "║  2. Instructor Dashboard" "$INSTRUCTOR"
link "║     → Gradebook, CSV export, per-student drill-down" ""
echo "${BOLD}║${RESET}"
link "║  3. Instructor Quiz Control" "$INSTRUCTOR_QUIZ"
link "║     → QR code, Start Quiz, live stats, Close Quiz" ""
echo "${BOLD}║${RESET}"
link "║  4. Student Quiz (phone/second tab)" "$STUDENT_QUIZ"
link "║     → Joins after instructor hits Start" ""
echo "${BOLD}║${RESET}"
link "║  5. API Docs (bonus)" "$API_DOCS"
echo "${BOLD}║${RESET}"
echo "${BOLD}╠══════════════════════════════════════════════════════════════╣${RESET}"
echo "${BOLD}║  DEMO FLOW                                                   ║${RESET}"
echo "${BOLD}╠══════════════════════════════════════════════════════════════╣${RESET}"
echo "${BOLD}║${RESET}"
echo "${BOLD}║${RESET}  ${BOLD}A. Homework${RESET} (tab 1)"
echo "${BOLD}║${RESET}     • Verify name → Pragya Sharma"
echo "${BOLD}║${RESET}     • Show K-map question with minterms"
echo "${BOLD}║${RESET}     • Submit wrong answer → instant feedback"
echo "${BOLD}║${RESET}     • Retry with new variant"
echo "${BOLD}║${RESET}"
echo "${BOLD}║${RESET}  ${BOLD}B. Instructor Dashboard${RESET} (tab 2)"
echo "${BOLD}║${RESET}     • Summary cards: 30 students, 8 assignments"
echo "${BOLD}║${RESET}     • Gradebook matrix → click a student"
echo "${BOLD}║${RESET}     • Export CSV (BruinLearn-compatible)"
echo "${BOLD}║${RESET}"
echo "${BOLD}║${RESET}  ${BOLD}C. In-Class Quiz${RESET} (tabs 3 + 4 side by side)"
echo "${BOLD}║${RESET}     • Tab 3: Show QR code + code $QUIZ_CODE"
echo "${BOLD}║${RESET}     • Tab 4: Student is waiting for quiz to start"
echo "${BOLD}║${RESET}     • Tab 3: Click START QUIZ"
echo "${BOLD}║${RESET}     • Tab 4: Quiz goes live — enter A'B', submit"
echo "${BOLD}║${RESET}     • Tab 4: Try again — best score kept"
echo "${BOLD}║${RESET}     • Tab 3: Watch live stats update (3s polling)"
echo "${BOLD}║${RESET}     • Tab 3: Click CLOSE QUIZ → grades written"
echo "${BOLD}║${RESET}     • Tab 2: Refresh gradebook → score appears"
echo "${BOLD}║${RESET}"
echo "${BOLD}╠══════════════════════════════════════════════════════════════╣${RESET}"
echo "${BOLD}║  Press Ctrl+C to stop both servers                          ║${RESET}"
echo "${BOLD}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""

# ── 7. Wait and clean up on Ctrl+C ───────────────────────────────────────────
cleanup() {
    echo ""
    echo "${BOLD}Stopping servers...${RESET}"
    kill $BACKEND_PID 2>/dev/null && ok "Backend stopped"
    # Kill the npm process group
    pkill -f "vite" 2>/dev/null && ok "Frontend stopped"
    echo "${BOLD}Done. Thanks for the demo!${RESET}"
    echo ""
    exit 0
}

trap cleanup INT TERM

# Keep script alive
while true; do sleep 1; done
