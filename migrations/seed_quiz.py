"""Seed a test quiz session (quiz3) with 2 K-map problems and variant pool entries."""
import json
import hashlib
import random
import sqlite3
from pathlib import Path
from autota.template_generator import TemplateGenerator
from autota.models import ProblemSpec

random.seed(99)
DB_PATH = Path("data/autota.db")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# ── Assignment ───────────────────────────────────────────────────────────────
instructions = json.dumps([
    "Simplify the Boolean function using a K-map.",
    "Express answers as minimal SOP (sum of products).",
    "Use A, B, C, D as variable names; prime (') for complement; + for OR.",
])
cursor.execute("""
    INSERT OR REPLACE INTO assignments
        (id, title, course, spec_path, instructions, is_active,
         offering_id, type, max_attempts)
    VALUES (?, ?, ?, ?, ?, 1, ?, 'quiz', 1)
""", (
    "quiz3", "Quiz 3 — K-Map Simplification",
    "ECE M16", "specs/quiz3.yaml", instructions, "ECE_M16_SP26",
))

# ── Problems ─────────────────────────────────────────────────────────────────
problems = [
    dict(id="quiz3_1", parent="1", sub=None, order=1,
         text="Simplify the Boolean function F(A,B,C,D) defined by the following minterms. Express your answer as a minimal sum-of-products (SOP).",
         format="boolean_expression", points=10.0, has_variants=True),
    dict(id="quiz3_2", parent="2", sub=None, order=2,
         text="Find the minimal SOP expression for the following function.",
         format="boolean_expression", points=10.0, has_variants=True),
]
for p in problems:
    cursor.execute("""
        INSERT OR REPLACE INTO problems
            (id, assignment_id, parent_label, sub_label, display_order,
             text, hint, answer_format, placeholder, problem_type, points)
        VALUES (?, ?, ?, ?, ?, ?, NULL, ?, NULL, 'kmap_simplification', ?)
    """, (p["id"], "quiz3", p["parent"], p.get("sub"), p["order"],
          p["text"], p["format"], p["points"]))

# ── Variant pool ─────────────────────────────────────────────────────────────
generator = TemplateGenerator()
total_pool = 0
for problem_id in ["quiz3_1", "quiz3_2"]:
    spec = ProblemSpec(
        problem_type="kmap_simplification",
        topic=f"Quiz pool {problem_id}",
        description="K-map simplification",
        num_variants=30,
        parameters={
            "num_variables": 4,
            "num_minterms": [6, 10],
            "num_dont_cares": [0, 3],
            "variables": ["A", "B", "C", "D"],
        },
        answer_format="boolean_expression",
        difficulty="medium",
    )
    batch = generator.generate(spec)
    for v in batch.variants:
        vd = v.model_dump()
        solution = vd.pop("solution")
        params = vd.get("parameters", {})
        minterms = params.get("minterms", [])
        dont_cares = params.get("dont_cares", [])
        canonical_params = {"num_vars": 4, "minterms": sorted(minterms), "dont_cares": sorted(dont_cares)}
        param_hash = hashlib.sha256(json.dumps(canonical_params, sort_keys=True, separators=(',',':')).encode()).hexdigest()
        minterms_str = f"m({','.join(map(str, sorted(minterms)))})" if minterms else None
        dc_str = f"d({','.join(map(str, sorted(dont_cares)))})" if dont_cares else None
        try:
            cursor.execute("""
                INSERT INTO variant_pool
                    (id, problem_id, parameters_json, parameter_hash,
                     problem_text, minterms, dont_cares, solution_json, generated_by, verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'template', 1)
            """, (str(v.variant_id), problem_id, json.dumps(canonical_params),
                  param_hash, vd.get("problem_text"), minterms_str, dc_str, json.dumps(solution)))
            total_pool += 1
        except Exception:
            pass
print(f"✓ Generated {total_pool} pool variants for quiz3")

# ── Quiz session ─────────────────────────────────────────────────────────────
cursor.execute("""
    INSERT OR REPLACE INTO quiz_sessions
        (assignment_id, code, status, time_limit_seconds, created_by, created_at)
    VALUES ('quiz3', 'QZ5A3F', 'pending', 600, 'msrivastava', datetime('now'))
""")
quiz_id = cursor.lastrowid
conn.commit()

cursor.execute("SELECT id, code FROM quiz_sessions WHERE code = 'QZ5A3F'")
row = cursor.fetchone()
print(f"✓ Quiz session: id={row['id']}, code={row['code']}")

conn.close()
print("\nReady:")
print("  Instructor: http://localhost:5173/instructor/quiz/QZ5A3F")
print("  Student:    http://localhost:5173/quiz/QZ5A3F?sid=UID123456789")
