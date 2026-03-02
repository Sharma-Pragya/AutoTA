# AutoTA Phase 2 - Progress Report

## ✅ Completed (Tasks 1-5 of 10)

### 1. Frontend Setup ✓
- Created `frontend/` with Vite + React
- Configured Vite proxy to backend (port 8000)
- Added Google Fonts (IBM Plex Sans + Mono)
- Hello world rendering successfully

**Files:**
- `frontend/vite.config.js` - Proxy configuration
- `frontend/index.html` - Font links
- `frontend/src/App.jsx` - Basic app component

### 2. Backend Setup ✓
- FastAPI app with CORS middleware
- Health endpoint: `GET /api/health` → `{"ok": true}`
- Lifespan manager for database initialization
- Running on port 8000

**Files:**
- `autota/web/app.py` - Main FastAPI application
- `autota/web/__init__.py`
- `autota/web/routes/__init__.py`

### 3. Database Schema ✓
- SQLite database at `data/autota.db` (gitignored)
- 6 tables created:
  - `students` - Student records
  - `assignments` - Assignment metadata
  - `problems` - Problem definitions
  - `variant_assignments` - Student-specific variants
  - `submissions` - Student answers
  - `attempts` - Attempt tracking

**Files:**
- `autota/web/db.py` - Database initialization and connection
- `.gitignore` - Added `data/` directory

### 4. Database Seeding ✓
- Seeding script creates:
  - 3 sample students (Pragya, Jane, Joe)
  - Assignment "hw5" with 6 problems
  - 9 variant assignments (3 students × 3 K-map problems)
  - Uses TemplateGenerator for variant creation
  - Attempt records (Pragya on attempt 2, others on 1)

**Files:**
- `autota/web/seed.py` - Seeding logic
- `seed.sh` - Convenience script

**Usage:**
```bash
./seed.sh
# or
python autota/web/seed.py
```

### 5. Assignment Endpoint ✓
- `GET /api/assignment/{student_id}`
- Returns:
  - Assignment metadata
  - Student info with attempt number
  - 6 problems with student-specific variants
  - Existing answers (empty on first load)
  - Solutions NOT included (stored separately)

**Files:**
- `autota/web/routes/assignment.py`

**Routes Implemented:**
- ✅ `POST /api/verify-name` - Name verification
- ✅ `GET /api/assignment/{student_id}` - Get assignment data
- 🔲 `POST /api/save-answer` - Auto-save (stub)
- 🔲 `POST /api/submit` - Submit for grading (stub)

---

## 📊 Verification Results

All backend tests passing:

```
✓ Health endpoint works
✓ Name verification (correct) works
✓ Name verification (wrong) works
✓ Assignment endpoint returns correct data
✓ Different students get different variants
✓ Problem structure is correct
✓ Database has 3 students, 1 assignment, 6 problems, 9 variants
```

---

## 🚀 How to Test Current Progress

### Start Backend
```bash
uvicorn autota.web.app:app --reload --port 8000
```

### Test Endpoints
```bash
# Health check
curl http://localhost:8000/api/health

# Verify name
curl -X POST http://localhost:8000/api/verify-name \
  -H "Content-Type: application/json" \
  -d '{"student_id": "UID123456789", "name": "Pragya Sharma"}'

# Get assignment
curl http://localhost:8000/api/assignment/UID123456789 | python -m json.tool
```

### Start Frontend (placeholder)
```bash
cd frontend
npm run dev
# Visit: http://localhost:5173
```

---

## 🔨 Remaining Tasks (6-10)

### 6. Build Frontend Screens
- Split `docs/ui-prototype.jsx` into components
- Create screens: NameCheck, Landing, Question, MainPage, Attestation, Review
- Extract styles to `styles.js`
- Wire API calls to backend
- Match prototype pixel-for-pixel

### 7. Auto-save Functionality
- Implement `POST /api/save-answer` endpoint
- Add debounced auto-save to frontend (3 sec)
- Show "Saving..." / "Saved ✓" indicator

### 8. Submit & Grading
- Implement `POST /api/submit` endpoint
- Integrate with Layer 3 verifiers (`autota.verify`)
- Grade using `BooleanVerifier.grade()` for expressions
- Store results in `submissions` table
- Return grading results to frontend

### 9. End-to-End Testing
- Run `./seed.sh`
- Test with `?sid=UID123456789`
- Complete full workflow:
  - Name verification
  - Answer questions
  - Check format
  - Submit
  - Verify correct grading
- Test with different students

### 10. Verify Phase 1 Tests
- Run `pytest` to ensure all 79 Phase 1 tests still pass
- Confirm no existing functionality broken

---

## 📁 New Files Created

```
frontend/
├── index.html           ✅ Fonts added
├── vite.config.js       ✅ Proxy configured
├── src/
│   ├── App.jsx          ✅ Hello world
│   └── index.css        ✅ Reset styles

autota/web/
├── __init__.py          ✅
├── app.py               ✅ FastAPI app
├── db.py                ✅ Database operations
├── seed.py              ✅ Seeding script
└── routes/
    ├── __init__.py      ✅
    ├── auth.py          ✅ Name verification
    ├── assignment.py    ✅ Get assignment
    └── submit.py        🔲 Auto-save stub

data/
└── autota.db            ✅ SQLite database (gitignored)

seed.sh                  ✅ Seeding convenience script
```

---

## 🎯 Next Steps

You can choose to:

**Option A:** Continue building tasks #6-10 automatically
- I'll build all frontend screens, auto-save, grading, and testing
- This will be a long response but will complete Phase 2

**Option B:** Build incrementally
- Do task #6 (frontend screens) next
- Then you can test the UI before I add grading

**Option C:** Start testing now
- Start both servers manually
- Test the backend endpoints
- I'll build the rest after you verify

**Option D:** Create dev.sh first
- Single script to start both backend + frontend
- Makes testing easier
- Then continue with remaining tasks

Let me know which you prefer!

---

## 💡 Dependencies Added

Updated `pyproject.toml`:
```toml
dependencies = [
    "anthropic>=0.18.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
    "typer>=0.9.0",
    "python-dotenv>=1.0.0",
    "rich>=13.0.0",
    "fastapi>=0.104.0",      # ← NEW
    "uvicorn[standard]>=0.24.0",  # ← NEW
]
```

Frontend packages installed:
```
react, react-dom, vite, @vitejs/plugin-react
(206 total packages, 0 vulnerabilities)
```
