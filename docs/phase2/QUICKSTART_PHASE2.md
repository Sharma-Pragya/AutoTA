# AutoTA Phase 2 — Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. Seed the Database
```bash
./seed.sh
```

Creates:
- 3 sample students
- 1 assignment (hw5)
- 6 problems
- 9 unique K-map variants

### 2. Start Development Servers
```bash
./dev.sh
```

Starts:
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:5173

### 3. Test the Application
Visit: **http://localhost:5173/?sid=UID123456789**

**Login**: Type "Pragya Sharma" → Click "Check"

---

## 📝 Test Workflow

1. **Name Check**: Enter "Pragya Sharma" → Begin
2. **Landing**: Review instructions → Begin
3. **Q1a**: Type answer (e.g., `A'B + CD`) → Check Format → Next
4. **Q1b**: Type answer (e.g., `1`) → Next
5. **Q2**: Answer → Next
6. **Q3a, Q3b, Q3c**: Answer all
7. **Main Page**: (Click logo or "Main Page" button)
8. **Review & Submit**: (From last question or main page)
9. **Attestation**: Check box → Proceed
10. **Review**: See all answers → Submit All → Confirm
11. **Results**: See instant grading! ✅

---

## 👥 Test Users

| Student ID | Name | Attempt |
|------------|------|---------|
| `UID123456789` | Pragya Sharma | 2 |
| `UID987654321` | Jane Bruin | 1 |
| `UID111222333` | Joe Bruin | 1 |

**Each student gets different K-map variants!**

---

## 🔗 Useful URLs

- **Frontend**: http://localhost:5173/?sid=UID123456789
- **Backend API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

---

## 🛠️ Helpful Commands

### Reseed Database
```bash
rm -f data/autota.db
./seed.sh
```

### Run Phase 1 Tests
```bash
pytest -v
```

### Check Database
```bash
sqlite3 data/autota.db "SELECT * FROM students"
sqlite3 data/autota.db "SELECT COUNT(*) FROM variant_assignments"
```

### Stop Servers
Press `Ctrl+C` in the terminal running `./dev.sh`

---

## 💡 Tips

- **Auto-save**: Answers save automatically after 3 seconds of typing
- **Format Check**: Click "Check Format" to validate syntax before moving on
- **Navigation**: Use the menu (☰) in the top-right to jump between questions
- **Different variants**: Try different student IDs to see unique problems
- **Resume**: Refresh the page → auto-loaded saved answers

---

## 📊 What Gets Graded

| Problem | Type | Grading Method |
|---------|------|----------------|
| Q1a | boolean_expression | Truth table evaluation |
| Q1b | value | Exact match (placeholder) |
| Q2 | boolean_expression | Truth table evaluation |
| Q3a | boolean_expression | Truth table evaluation |
| Q3b | number | Exact match (placeholder) |
| Q3c | boolean_expression | Truth table evaluation |

**K-map problems (Q1a, Q2, Q3a)** are automatically graded using the BooleanVerifier from Phase 1!

---

## 🐛 Troubleshooting

### "Missing Student ID" error
→ Make sure URL has `?sid=UID123456789`

### Backend not starting
→ Check if port 8000 is already in use: `lsof -i :8000`

### Frontend not loading
→ Check if `npm install` was run in `frontend/`

### Name verification fails
→ Make sure database is seeded (`./seed.sh`)
→ Enter exact name: "Pragya Sharma" (case-insensitive)

### No variants showing
→ Check database: `sqlite3 data/autota.db "SELECT COUNT(*) FROM variant_assignments"`
→ Should show 9

---

## 🎯 Expected Behavior

✅ Name check verifies against database
✅ Assignment loads with 6 problems
✅ Each student sees different K-map minterms
✅ Answers auto-save
✅ Format validation works client-side
✅ Menu shows completion status
✅ Attestation required before review
✅ Submit triggers instant grading
✅ Results show score + feedback

---

## 📚 See Full Documentation

- `PHASE2_COMPLETE.md` — Complete implementation details
- `PHASE2_SPEC.md` — Original specification
- `ARCHITECTURE.md` — Overall system design
- `docs/ui-prototype.jsx` — Visual reference

---

**Enjoy testing AutoTA Phase 2!** 🎉
