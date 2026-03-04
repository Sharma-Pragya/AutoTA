#!/bin/bash
# setup.sh — one-time setup for AutoTA
# Creates a Python venv, installs all dependencies, sets up the database.
#
# Usage: ./setup.sh

set -e

BOLD=$(tput bold)
RESET=$(tput sgr0)
GREEN=$(tput setaf 2)
BLUE=$(tput setaf 4)
CYAN=$(tput setaf 6)
RED=$(tput setaf 1)

step() { echo ""; echo "${BOLD}${BLUE}▶ $1${RESET}"; }
ok()   { echo "  ${GREEN}✓${RESET} $1"; }
fail() { echo "  ${RED}✗ $1${RESET}"; exit 1; }

echo ""
echo "${BOLD}╔══════════════════════════════════════════════════╗${RESET}"
echo "${BOLD}║         AutoTA — First-Time Setup                ║${RESET}"
echo "${BOLD}╚══════════════════════════════════════════════════╝${RESET}"

# ── 1. Python ─────────────────────────────────────────────────────────────────
step "Finding Python 3.9+"

PYTHON=""
for candidate in python3 python3.12 python3.11 python3.10 python3.9 python; do
    if command -v "$candidate" &>/dev/null; then
        version=$("$candidate" -c 'import sys; print(sys.version_info >= (3,9))' 2>/dev/null)
        if [ "$version" = "True" ]; then
            PYTHON="$candidate"
            break
        fi
    fi
done

[ -n "$PYTHON" ] || fail "Python 3.9+ not found. Install it from https://python.org"
ok "Using $($PYTHON --version)"

# ── 2. Create venv ────────────────────────────────────────────────────────────
step "Creating virtual environment (.venv)"

if [ ! -d ".venv" ]; then
    $PYTHON -m venv .venv
    ok "Created .venv"
else
    ok ".venv already exists — skipping"
fi

VENV_PYTHON=".venv/bin/python"
VENV_PIP=".venv/bin/pip"

# ── 3. Install Python dependencies ───────────────────────────────────────────
step "Installing Python dependencies"

$VENV_PIP install --upgrade pip --quiet
$VENV_PIP install -e ".[dev]" --quiet
ok "Python packages installed"

# ── 4. Frontend dependencies ──────────────────────────────────────────────────
step "Installing frontend dependencies"

command -v node &>/dev/null || fail "Node.js not found. Install it from https://nodejs.org"
command -v npm  &>/dev/null || fail "npm not found."
ok "Node $(node --version), npm $(npm --version)"

(cd frontend && npm install --silent)
ok "npm packages installed"

# ── 5. Database ───────────────────────────────────────────────────────────────
step "Setting up database"

mkdir -p data

if [ -f "data/autota.db" ]; then
    ok "Database already exists — skipping (delete data/autota.db to reset)"
else
    $VENV_PYTHON -c "from autota.web.db import init_db; init_db()"
    ok "Base schema created"

    $VENV_PYTHON migrations/run_004.py
    ok "Migrations applied"

    $VENV_PYTHON autota/web/seed.py
    ok "Seeded 30 students, 8 assignments"

    $VENV_PYTHON migrations/seed_quiz.py
    ok "Seeded quiz session QZ5A3F"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "${BOLD}╔══════════════════════════════════════════════════╗${RESET}"
echo "${BOLD}║  Setup complete! Run the demo with:              ║${RESET}"
echo "${BOLD}║                                                  ║${RESET}"
echo "${BOLD}║    ./demo.sh                                     ║${RESET}"
echo "${BOLD}║                                                  ║${RESET}"
echo "${BOLD}╚══════════════════════════════════════════════════╝${RESET}"
echo ""
