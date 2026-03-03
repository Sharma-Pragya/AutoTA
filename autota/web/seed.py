"""Database seeding script for AutoTA.

Seeds 8 assignments, ~30 students across sections 1A and 1B,
and realistic randomized submission data for the instructor dashboard.
"""

import json
import random
import hashlib
from autota.web.db import get_db_connection, init_db
from autota.template_generator import TemplateGenerator
from autota.models import ProblemSpec

random.seed(42)  # Reproducible randomness


# ── Student roster (30 students) ──────────────────────────────────────────────

STUDENT_NAMES = [
    "Pragya Sharma", "Jane Bruin", "Joe Bruin",
    "Alice Chen", "Bob Martinez", "Carol Johnson", "David Kim",
    "Emma Wilson", "Frank Lee", "Grace Taylor", "Henry Brown",
    "Isabella Davis", "James Anderson", "Karen Thomas", "Liam Jackson",
    "Mia White", "Noah Harris", "Olivia Martin", "Peter Thompson",
    "Quinn Garcia", "Rachel Martinez", "Samuel Robinson", "Tara Clark",
    "Uma Lewis", "Victor Walker", "Wendy Hall", "Xavier Allen",
    "Yara Young", "Zach Hernandez", "Amy Scott",
]

# Build student records: first 3 are fixed, rest auto-generated
STUDENTS = []
for i, name in enumerate(STUDENT_NAMES):
    uid = f"UID{100000000 + i}"
    # Sections: 1A for first 15, 1B for next 15
    section = "1A" if i < 15 else "1B"
    first = name.split()[0].lower()
    last = name.split()[-1].lower()
    email = f"{first}.{last}@ucla.edu"
    STUDENTS.append((uid, name, email, section))

# Keep backwards-compatible legacy UIDs for first 3
STUDENTS[0] = ("UID123456789", "Pragya Sharma", "pragya@ucla.edu", "1A")
STUDENTS[1] = ("UID987654321", "Jane Bruin", "jbruin@ucla.edu", "1A")
STUDENTS[2] = ("UID111222333", "Joe Bruin", "joebruin@ucla.edu", "1B")


# ── Assignment definitions ─────────────────────────────────────────────────────

ASSIGNMENTS = [
    {
        "id": "hw3",
        "title": "PSET 3 — Boolean Algebra",
        "type": "homework",
        "is_active": 0,
        "max_attempts": 3,
        "closes_at": "2026-02-01T23:59:00Z",
        "total_pts": 8,
        "problems": [
            {"id": "hw3_1", "parent": "1", "sub": None, "order": 1, "text": "Simplify using Boolean algebra: AB + AB' + A'B", "format": "boolean_expression", "points": 2.0},
            {"id": "hw3_2a", "parent": "2", "sub": "a", "order": 2, "text": "Write the canonical SOP for F(A,B,C) = Σm(1,3,5,7)", "format": "boolean_expression", "points": 2.0},
            {"id": "hw3_2b", "parent": "2", "sub": "b", "order": 3, "text": "Simplify the SOP from (a) using Boolean algebra", "format": "boolean_expression", "points": 2.0},
            {"id": "hw3_3", "parent": "3", "sub": None, "order": 4, "text": "How many prime implicants does F(A,B,C) = Σm(0,2,4,6) have?", "format": "number", "points": 2.0},
        ],
    },
    {
        "id": "hw4",
        "title": "PSET 4 — Combinational Logic",
        "type": "homework",
        "is_active": 0,
        "max_attempts": 3,
        "closes_at": "2026-02-15T23:59:00Z",
        "total_pts": 10,
        "problems": [
            {"id": "hw4_1", "parent": "1", "sub": None, "order": 1, "text": "Design a 2-bit comparator. Write the SOP for A > B.", "format": "boolean_expression", "points": 3.0},
            {"id": "hw4_2a", "parent": "2", "sub": "a", "order": 2, "text": "Simplify F(A,B,C,D) = Σm(0,1,4,5,8,9,12,13)", "format": "boolean_expression", "points": 3.0},
            {"id": "hw4_2b", "parent": "2", "sub": "b", "order": 3, "text": "What is the gate count for your simplified expression?", "format": "number", "points": 2.0},
            {"id": "hw4_3", "parent": "3", "sub": None, "order": 4, "text": "Simplify using K-map: F(A,B,C,D) = Σm(3,7,11,15)", "format": "boolean_expression", "points": 2.0},
        ],
    },
    {
        "id": "hw5",
        "title": "PSET 5 — Karnaugh Map Simplification",
        "type": "homework",
        "is_active": 1,
        "max_attempts": 3,
        "closes_at": "2026-03-01T23:59:00Z",
        "total_pts": 10,
        "problems": [
            {"id": "hw5_1a", "parent": "1", "sub": "a", "order": 1, "text": "Simplify the Boolean function F(A,B,C,D) defined by the minterms and don't-cares below.", "format": "boolean_expression", "points": 2.0, "has_variants": True},
            {"id": "hw5_1b", "parent": "1", "sub": "b", "order": 2, "text": "Using your simplified expression from part (a), determine the output F when A=1, B=0, C=1, D=1.", "format": "value", "points": 1.0, "placeholder": "0 or 1"},
            {"id": "hw5_2", "parent": "2", "sub": None, "order": 3, "text": "Simplify the Boolean function F(A,B,C,D) defined by the minterms below.", "format": "boolean_expression", "points": 2.0, "has_variants": True},
            {"id": "hw5_3a", "parent": "3", "sub": "a", "order": 4, "text": "Simplify the Boolean function F(A,B,C,D) defined by the minterms and don't-cares below.", "format": "boolean_expression", "points": 2.0, "has_variants": True},
            {"id": "hw5_3b", "parent": "3", "sub": "b", "order": 5, "text": "How many literal appearances are in your minimal SOP expression from part (a)?", "format": "number", "points": 1.0, "placeholder": "e.g. 6"},
            {"id": "hw5_3c", "parent": "3", "sub": "c", "order": 6, "text": "Write the complement F'(A,B,C,D) as a minimal sum-of-products expression.", "format": "boolean_expression", "points": 2.0},
        ],
    },
    {
        "id": "hw6",
        "title": "PSET 6 — Multi-Level Optimization",
        "type": "homework",
        "is_active": 1,
        "max_attempts": 3,
        "closes_at": "2026-03-15T23:59:00Z",
        "total_pts": 10,
        "problems": [
            {"id": "hw6_1a", "parent": "1", "sub": "a", "order": 1, "text": "Find a minimal two-level AND-OR implementation for F(A,B,C,D) = Σm(0,1,2,5,8,10,12,13)", "format": "boolean_expression", "points": 3.0, "has_variants": True},
            {"id": "hw6_1b", "parent": "1", "sub": "b", "order": 2, "text": "Factor your expression from (a) to reduce literal count.", "format": "boolean_expression", "points": 2.0},
            {"id": "hw6_2", "parent": "2", "sub": None, "order": 3, "text": "Simplify F(A,B,C,D) = Σm(2,3,7,9,11,13) + d(1,10,15) using K-map.", "format": "boolean_expression", "points": 3.0, "has_variants": True},
            {"id": "hw6_3", "parent": "3", "sub": None, "order": 4, "text": "How many gates are needed for a two-level NAND-NAND realization of F = AC + BC + A'B'?", "format": "number", "points": 2.0},
        ],
    },
    {
        "id": "quiz1",
        "title": "Quiz 1 — Gates & Truth Tables",
        "type": "quiz",
        "is_active": 0,
        "max_attempts": 1,
        "closes_at": "2026-01-20T14:50:00Z",
        "total_pts": 20,
        "problems": [
            {"id": "quiz1_1", "parent": "1", "sub": None, "order": 1, "text": "Write the truth table output for F = AB' + A'B", "format": "boolean_expression", "points": 5.0},
            {"id": "quiz1_2", "parent": "2", "sub": None, "order": 2, "text": "Simplify: (A+B)(A+B')", "format": "boolean_expression", "points": 5.0},
            {"id": "quiz1_3", "parent": "3", "sub": None, "order": 3, "text": "How many rows does a 3-variable truth table have?", "format": "number", "points": 5.0},
            {"id": "quiz1_4", "parent": "4", "sub": None, "order": 4, "text": "Express F(A,B,C) = Σm(1,3,5,7) in simplest form", "format": "boolean_expression", "points": 5.0},
        ],
    },
    {
        "id": "quiz2",
        "title": "Quiz 2 — K-Map Speed Round",
        "type": "quiz",
        "is_active": 0,
        "max_attempts": 1,
        "closes_at": "2026-02-10T14:50:00Z",
        "total_pts": 20,
        "problems": [
            {"id": "quiz2_1", "parent": "1", "sub": None, "order": 1, "text": "Simplify F(A,B,C,D) = Σm(0,4,8,12)", "format": "boolean_expression", "points": 5.0},
            {"id": "quiz2_2", "parent": "2", "sub": None, "order": 2, "text": "Simplify F(A,B,C) = Σm(0,2,4,6)", "format": "boolean_expression", "points": 5.0},
            {"id": "quiz2_3", "parent": "3", "sub": None, "order": 3, "text": "Simplify F(A,B,C,D) = Σm(1,3,5,7,9,11,13,15)", "format": "boolean_expression", "points": 5.0},
            {"id": "quiz2_4", "parent": "4", "sub": None, "order": 4, "text": "Find the number of prime implicants in F(A,B,C,D) = Σm(0,2,8,10)", "format": "number", "points": 5.0},
        ],
    },
    {
        "id": "midterm",
        "title": "Midterm Exam",
        "type": "exam",
        "is_active": 0,
        "max_attempts": 1,
        "closes_at": "2026-02-20T13:50:00Z",
        "total_pts": 100,
        "problems": [
            {"id": "midterm_1", "parent": "1", "sub": None, "order": 1, "text": "Boolean Algebra: Prove De Morgan's theorem for three variables", "format": "boolean_expression", "points": 20.0},
            {"id": "midterm_2a", "parent": "2", "sub": "a", "order": 2, "text": "K-Map: Simplify F(A,B,C,D) = Σm(0,1,2,4,5,6,8,9,10,12,13,14) + d(3,7,11,15)", "format": "boolean_expression", "points": 25.0, "has_variants": True},
            {"id": "midterm_2b", "parent": "2", "sub": "b", "order": 3, "text": "What is the gate count (AND+OR, no inverters) for your minimal SOP?", "format": "number", "points": 10.0},
            {"id": "midterm_3", "parent": "3", "sub": None, "order": 4, "text": "Design a 4-bit priority encoder. Write SOP for each output bit.", "format": "boolean_expression", "points": 25.0},
            {"id": "midterm_4", "parent": "4", "sub": None, "order": 5, "text": "Convert F = A(BC + D) to NAND-NAND form", "format": "boolean_expression", "points": 20.0},
        ],
    },
    {
        "id": "da1",
        "title": "Design Assignment 1 — ALU Design",
        "type": "project",
        "is_active": 1,
        "max_attempts": 1,
        "closes_at": "2026-03-20T23:59:00Z",
        "total_pts": 50,
        "problems": [
            {"id": "da1_1", "parent": "1", "sub": None, "order": 1, "text": "Design a 1-bit full adder. Write Boolean expressions for Sum and Carry.", "format": "boolean_expression", "points": 15.0},
            {"id": "da1_2", "parent": "2", "sub": None, "order": 2, "text": "Extend to a 4-bit ripple carry adder. Write expression for carry out C4.", "format": "boolean_expression", "points": 20.0},
            {"id": "da1_3", "parent": "3", "sub": None, "order": 3, "text": "What is the maximum propagation delay in gate delays for the 4-bit RCA?", "format": "number", "points": 15.0},
        ],
    },
]


# ── Seeding functions ──────────────────────────────────────────────────────────

def seed_institutional_data(conn):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO courses (id, name, department) VALUES (?, ?, ?)",
        ("ECE_M16", "Digital Design", "ECE")
    )
    cursor.execute(
        "INSERT OR REPLACE INTO course_offerings (id, course_id, quarter, year) VALUES (?, ?, ?, ?)",
        ("ECE_M16_SP26", "ECE_M16", "Spring", 2026)
    )
    cursor.execute(
        "INSERT OR REPLACE INTO instructors (id, name, email, role) VALUES (?, ?, ?, ?)",
        ("msrivastava", "Mani Srivastava", "mani@cs.ucla.edu", "instructor")
    )
    cursor.execute(
        "INSERT OR REPLACE INTO sections (id, offering_id, label, instructor_id) VALUES (?, ?, ?, ?)",
        ("ECE_M16_SP26_1A", "ECE_M16_SP26", "1A", "msrivastava")
    )
    cursor.execute(
        "INSERT OR REPLACE INTO sections (id, offering_id, label, instructor_id) VALUES (?, ?, ?, ?)",
        ("ECE_M16_SP26_1B", "ECE_M16_SP26", "1B", "msrivastava")
    )
    conn.commit()
    print("✓ Seeded institutional hierarchy")


def seed_students(conn):
    cursor = conn.cursor()
    for student_id, name, email, section in STUDENTS:
        cursor.execute(
            "INSERT OR REPLACE INTO students (id, name, email, section) VALUES (?, ?, ?, ?)",
            (student_id, name, email, section)
        )
    conn.commit()
    print(f"✓ Seeded {len(STUDENTS)} students")


def seed_enrollments(conn):
    cursor = conn.cursor()
    for student_id, _, _, section in STUDENTS:
        section_id = f"ECE_M16_SP26_{section}"
        cursor.execute(
            "INSERT OR IGNORE INTO enrollments (student_id, section_id) VALUES (?, ?)",
            (student_id, section_id)
        )
    conn.commit()
    print(f"✓ Enrolled {len(STUDENTS)} students")


def seed_assignments(conn):
    cursor = conn.cursor()
    instructions = json.dumps([
        "Each problem presents a Boolean function as a set of minterms. Simplify using a K-map.",
        "Express all answers as minimal sum-of-products (SOP) expressions.",
        "Use standard notation: AND (implicit), OR (+), NOT (').",
        "Don't-care conditions may be used to further simplify your expression.",
        "Use \"Check Format\" to validate your syntax before moving on.",
    ])

    for asgn in ASSIGNMENTS:
        cursor.execute(
            """INSERT OR REPLACE INTO assignments
               (id, title, course, spec_path, instructions, is_active,
                offering_id, type, max_attempts, closes_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                asgn["id"],
                asgn["title"],
                "ECE M16",
                f"specs/{asgn['id']}.yaml",
                instructions,
                asgn["is_active"],
                "ECE_M16_SP26",
                asgn["type"],
                asgn["max_attempts"],
                asgn["closes_at"],
            )
        )

    conn.commit()
    print(f"✓ Seeded {len(ASSIGNMENTS)} assignments")


def seed_problems(conn):
    cursor = conn.cursor()
    total = 0
    for asgn in ASSIGNMENTS:
        for p in asgn["problems"]:
            cursor.execute(
                """INSERT OR REPLACE INTO problems
                   (id, assignment_id, parent_label, sub_label, display_order,
                    text, hint, answer_format, placeholder, problem_type, points)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    p["id"],
                    asgn["id"],
                    p["parent"],
                    p.get("sub"),
                    p["order"],
                    p["text"],
                    p.get("hint"),
                    p["format"],
                    p.get("placeholder"),
                    "kmap_simplification",
                    p["points"],
                )
            )
            total += 1
    conn.commit()
    print(f"✓ Seeded {total} problems")


def generate_variants_for_hw5(conn):
    """Generate real K-map variants for hw5 and assign to students."""
    cursor = conn.cursor()
    variant_problem_ids = ["hw5_1a", "hw5_2", "hw5_3a"]
    generator = TemplateGenerator()

    for problem_id in variant_problem_ids:
        spec = ProblemSpec(
            problem_type="kmap_simplification",
            topic=f"Problem {problem_id}",
            description="K-map simplification",
            num_variants=len(STUDENTS),
            parameters={
                "num_variables": 4,
                "num_minterms": [6, 10],
                "num_dont_cares": [0, 3] if problem_id in ["hw5_1a", "hw5_3a"] else [0, 0],
                "variables": ["A", "B", "C", "D"]
            },
            answer_format="boolean_expression",
            difficulty="medium"
        )
        batch = generator.generate(spec)

        for idx, (student_id, _, _, _) in enumerate(STUDENTS):
            variant = batch.variants[idx]
            attempt_number = 2 if student_id == "UID123456789" else 1
            variant_dict = variant.model_dump()
            solution = variant_dict.pop("solution")

            cursor.execute(
                """INSERT OR REPLACE INTO variant_assignments
                   (student_id, problem_id, variant_id, variant_json, solution_json, attempt_number)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    student_id, problem_id, str(variant.variant_id),
                    json.dumps(variant_dict), json.dumps(solution), attempt_number
                )
            )

        print(f"  ✓ Variants assigned for {problem_id}")

    conn.commit()
    print("✓ Generated hw5 variants for all students")


def seed_variant_pool(conn):
    """Generate 10 pool variants per hw5 K-map problem."""
    cursor = conn.cursor()
    generator = TemplateGenerator()
    total = 0

    for problem_id in ["hw5_1a", "hw5_2", "hw5_3a"]:
        spec = ProblemSpec(
            problem_type="kmap_simplification",
            topic=f"Pool for {problem_id}",
            description="K-map simplification",
            num_variants=10,
            parameters={
                "num_variables": 4,
                "num_minterms": [6, 10],
                "num_dont_cares": [0, 3] if problem_id in ["hw5_1a", "hw5_3a"] else [0, 0],
                "variables": ["A", "B", "C", "D"]
            },
            answer_format="boolean_expression",
            difficulty="medium"
        )
        batch = generator.generate(spec)

        for variant in batch.variants:
            variant_dict = variant.model_dump()
            solution = variant_dict.pop("solution")
            params_obj = variant_dict.get("parameters", {})
            minterms = params_obj.get("minterms", [])
            dont_cares = params_obj.get("dont_cares", [])
            parameters = {
                "num_vars": len(params_obj.get("variables", [])),
                "minterms": minterms,
                "dont_cares": dont_cares
            }
            canonical = json.dumps(parameters, sort_keys=True, separators=(',', ':'))
            param_hash = hashlib.sha256(canonical.encode()).hexdigest()
            minterms_str = f"m({','.join(map(str, sorted(minterms)))})" if minterms else None
            dont_cares_str = f"d({','.join(map(str, sorted(dont_cares)))})" if dont_cares else None

            try:
                cursor.execute("""
                    INSERT INTO variant_pool
                        (id, problem_id, parameters_json, parameter_hash,
                         problem_text, minterms, dont_cares, solution_json,
                         generated_by, verified)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(variant.variant_id), problem_id, json.dumps(parameters),
                    param_hash, variant_dict.get("problem_text"),
                    minterms_str, dont_cares_str, json.dumps(solution),
                    'template', 1
                ))
                total += 1
            except Exception:
                pass

    conn.commit()
    print(f"✓ Generated {total} pool variants")


def _random_score(mean=0.75, std=0.18):
    """Generate a realistic right-skewed score in [0.0, 1.0]."""
    s = random.gauss(mean, std)
    return max(0.0, min(1.0, round(s, 2)))


def _score_for_assignment(asgn_type, student_idx):
    """Assign student-specific score tendencies per assignment type."""
    # High performers in first 8, low in last 7, middle the rest
    if student_idx < 8:
        base = 0.88
    elif student_idx >= 23:
        base = 0.58
    else:
        base = 0.74
    # Quizzes are slightly harder, midterm hardest
    if asgn_type == "exam":
        base -= 0.08
    elif asgn_type == "quiz":
        base -= 0.04
    return base


def _submission_status(asgn_id, student_idx):
    """Decide if student submitted: active assignments have ~75% submit rate."""
    active_ids = {"hw5", "hw6", "da1"}
    if asgn_id in active_ids:
        # ~75% of students submitted even for active (they already did it)
        return random.random() < 0.72
    else:
        # Closed assignments: ~90% submitted
        return random.random() < 0.90


def seed_attempt_records(conn):
    """Create attempts and submissions for all students across all assignments."""
    cursor = conn.cursor()

    for asgn in ASSIGNMENTS:
        asgn_id = asgn["id"]
        problems = asgn["problems"]
        total_pts = sum(p["points"] for p in problems)

        for idx, (student_id, _, _, _) in enumerate(STUDENTS):
            # Decide if student submitted
            submitted = _submission_status(asgn_id, idx)
            if not submitted:
                continue

            attempt_number = 1
            # Pragya on attempt 2 for hw5
            if student_id == "UID123456789" and asgn_id == "hw5":
                attempt_number = 2

            base_score = _score_for_assignment(asgn["type"], idx)

            # Insert attempt
            cursor.execute(
                """INSERT OR IGNORE INTO attempts
                   (student_id, assignment_id, attempt_number, status,
                    submitted_at, total_score, attestation_signed, attestation_signed_at)
                   VALUES (?, ?, ?, 'graded', datetime('now', ?), ?, 1, datetime('now', ?))""",
                (
                    student_id, asgn_id, attempt_number,
                    f"-{random.randint(1, 30)} days",
                    round(base_score, 3),
                    f"-{random.randint(1, 30)} days",
                )
            )

            # Get the attempt id
            cursor.execute(
                "SELECT id FROM attempts WHERE student_id = ? AND assignment_id = ? AND attempt_number = ?",
                (student_id, asgn_id, attempt_number)
            )
            attempt_row = cursor.fetchone()
            if not attempt_row:
                continue
            attempt_id = attempt_row["id"]

            points_earned = 0.0
            problems_correct = 0

            for p in problems:
                problem_id = p["id"]
                problem_pts = p["points"]

                # Determine per-problem score with some variance
                p_score = _random_score(base_score, 0.20)
                correct = p_score >= 0.5

                # Need a variant_assignment for kmap problems; for others make a dummy
                # For hw5 kmap problems, variant assignments were already created above
                # For other problems, create a minimal variant_assignment entry
                cursor.execute(
                    "SELECT id FROM variant_assignments WHERE student_id = ? AND problem_id = ? AND attempt_number = ?",
                    (student_id, problem_id, attempt_number)
                )
                va_row = cursor.fetchone()

                if not va_row:
                    # Create a dummy variant_assignment for non-kmap problems
                    dummy_variant = json.dumps({
                        "variant_id": f"dummy-{student_id}-{problem_id}",
                        "problem_text": p["text"],
                        "parameters": {},
                        "answer_format": p["format"],
                        "metadata": {}
                    })
                    dummy_solution = json.dumps({"answer": "correct"})
                    try:
                        cursor.execute(
                            """INSERT OR IGNORE INTO variant_assignments
                               (student_id, problem_id, variant_id, variant_json,
                                solution_json, attempt_number, attempt_id)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (
                                student_id, problem_id,
                                f"dummy-{student_id}-{problem_id}",
                                dummy_variant, dummy_solution,
                                attempt_number, attempt_id
                            )
                        )
                    except Exception:
                        pass
                    cursor.execute(
                        "SELECT id FROM variant_assignments WHERE student_id = ? AND problem_id = ? AND attempt_number = ?",
                        (student_id, problem_id, attempt_number)
                    )
                    va_row = cursor.fetchone()
                    if not va_row:
                        continue

                va_id = va_row["id"]

                # Generate a plausible answer string
                answer = "A'B + CD" if p["format"] == "boolean_expression" else (
                    "1" if p["format"] == "value" else str(random.randint(2, 8))
                )

                # Insert submission
                cursor.execute(
                    """INSERT OR IGNORE INTO submissions
                       (student_id, problem_id, variant_assignment_id, answer,
                        score, correct, feedback, graded_at, attestation_signed)
                       VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), 1)""",
                    (
                        student_id, problem_id, va_id, answer,
                        round(p_score, 3), 1 if correct else 0,
                        "Correct!" if correct else "Incorrect — check your groupings."
                    )
                )
                sub_id = cursor.lastrowid

                # Insert grade
                cursor.execute(
                    """INSERT OR IGNORE INTO grades
                       (submission_id, score, correct, feedback, grading_tier, grading_status, graded_by)
                       VALUES (?, ?, ?, ?, 'deterministic', 'graded', 'autota_verifier')""",
                    (
                        sub_id, round(p_score, 3), 1 if correct else 0,
                        "Correct!" if correct else "Incorrect — check your groupings."
                    )
                )

                points_earned += p_score * problem_pts
                if correct:
                    problems_correct += 1

            # Insert attempt_results
            weighted_score = points_earned / total_pts if total_pts > 0 else 0
            cursor.execute(
                """INSERT OR IGNORE INTO attempt_results
                   (attempt_id, total_score, total_points_earned, total_points_possible,
                    problems_correct, problems_total)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    attempt_id, round(weighted_score, 3),
                    round(points_earned, 3), total_pts,
                    problems_correct, len(problems)
                )
            )

    conn.commit()
    print(f"✓ Seeded attempt/submission records for {len(STUDENTS)} students × {len(ASSIGNMENTS)} assignments")


def main():
    """Run the complete seeding process."""
    print("\n=== AutoTA Database Seeding ===\n")

    init_db()
    conn = get_db_connection()

    seed_institutional_data(conn)
    seed_students(conn)
    seed_enrollments(conn)
    seed_assignments(conn)
    seed_problems(conn)
    generate_variants_for_hw5(conn)
    seed_variant_pool(conn)
    seed_attempt_records(conn)

    conn.close()

    print("\n✓ Database seeding complete!\n")
    print("Student UI (pick any UID):")
    for uid, name, _, section in STUDENTS[:6]:
        print(f"  http://localhost:5173/?sid={uid}  ({name}, {section})")
    print("  ...")
    print("\nInstructor UI:")
    print("  http://localhost:5173/instructor")
    print()


if __name__ == "__main__":
    main()
