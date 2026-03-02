"""Database seeding script for AutoTA."""

import json
import hashlib
from autota.web.db import get_db_connection, init_db
from autota.template_generator import TemplateGenerator
from autota.models import ProblemSpec


def seed_students(conn):
    """Insert sample students."""
    cursor = conn.cursor()

    students = [
        ("UID123456789", "Pragya Sharma", "pragya@ucla.edu", "1A"),
        ("UID987654321", "Jane Bruin", "jbruin@ucla.edu", "1A"),
        ("UID111222333", "Joe Bruin", "joebruin@ucla.edu", "1B"),
    ]

    for student_id, name, email, section in students:
        cursor.execute(
            "INSERT OR REPLACE INTO students (id, name, email, section) VALUES (?, ?, ?, ?)",
            (student_id, name, email, section)
        )

    conn.commit()
    print(f"✓ Seeded {len(students)} students")


def seed_institutional_data(conn):
    """Seed courses, course_offerings, instructors, sections, enrollments."""
    cursor = conn.cursor()

    # Insert course
    cursor.execute(
        "INSERT OR REPLACE INTO courses (id, name, department) VALUES (?, ?, ?)",
        ("ECE_M16", "Digital Design", "ECE")
    )

    # Insert course offering
    cursor.execute(
        "INSERT OR REPLACE INTO course_offerings (id, course_id, quarter, year) VALUES (?, ?, ?, ?)",
        ("ECE_M16_SP26", "ECE_M16", "Spring", 2026)
    )

    # Insert instructor
    cursor.execute(
        "INSERT OR REPLACE INTO instructors (id, name, email, role) VALUES (?, ?, ?, ?)",
        ("msrivastava", "Mani Srivastava", "mani@cs.ucla.edu", "instructor")
    )

    # Insert section
    cursor.execute(
        "INSERT OR REPLACE INTO sections (id, offering_id, label, instructor_id) VALUES (?, ?, ?, ?)",
        ("ECE_M16_SP26_1A", "ECE_M16_SP26", "1A", "msrivastava")
    )

    conn.commit()
    print("✓ Seeded institutional hierarchy (courses, offerings, instructors, sections)")


def seed_enrollments(conn):
    """Enroll all students in section 1A."""
    cursor = conn.cursor()

    students = [
        ("UID123456789", "ECE_M16_SP26_1A"),
        ("UID987654321", "ECE_M16_SP26_1A"),
        ("UID111222333", "ECE_M16_SP26_1A"),
    ]

    for student_id, section_id in students:
        cursor.execute(
            "INSERT OR IGNORE INTO enrollments (student_id, section_id) VALUES (?, ?)",
            (student_id, section_id)
        )

    conn.commit()
    print(f"✓ Enrolled {len(students)} students in section 1A")


def seed_assignment(conn):
    """Create assignment hw5."""
    cursor = conn.cursor()

    instructions = json.dumps([
        "Each problem presents a Boolean function as a set of minterms. Simplify using a K-map.",
        "Express all answers as minimal sum-of-products (SOP) expressions.",
        "Use standard notation: AND (implicit), OR (+), NOT (').",
        "Don't-care conditions may be used to further simplify your expression.",
        "Use \"Check Format\" to validate your syntax before moving on.",
    ])

    cursor.execute(
        """INSERT OR REPLACE INTO assignments
           (id, title, course, spec_path, instructions, is_active,
            offering_id, type, max_attempts)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "hw5",
            "Homework 5 — Karnaugh Map Simplification",
            "ECE M16",
            "specs/example_kmap.yaml",
            instructions,
            1,
            "ECE_M16_SP26",  # New: offering_id
            "homework",      # New: type
            3                # New: max_attempts
        )
    )

    conn.commit()
    print("✓ Seeded assignment: hw5")


def seed_problems(conn):
    """Create the 6 problems for hw5."""
    cursor = conn.cursor()

    problems = [
        {
            "id": "hw5_1a",
            "assignment_id": "hw5",
            "parent_label": "1",
            "sub_label": "a",
            "display_order": 1,
            "text": "Simplify the Boolean function F(A,B,C,D) defined by the minterms and don't-cares below.",
            "hint": "Look for groupings that wrap around the K-map edges.",
            "answer_format": "boolean_expression",
            "placeholder": None,
            "has_variants": True,
            "points": 2.0,  # New: K-map problems worth 2 points
        },
        {
            "id": "hw5_1b",
            "assignment_id": "hw5",
            "parent_label": "1",
            "sub_label": "b",
            "display_order": 2,
            "text": "Using your simplified expression from part (a), determine the output F when A=1, B=0, C=1, D=1.",
            "hint": "Substitute the values into your SOP expression from part (a).",
            "answer_format": "value",
            "placeholder": "0 or 1",
            "has_variants": False,
            "points": 1.0,  # New: follow-up problems worth 1 point
        },
        {
            "id": "hw5_2",
            "assignment_id": "hw5",
            "parent_label": "2",
            "sub_label": None,
            "display_order": 3,
            "text": "Simplify the Boolean function F(A,B,C,D) defined by the minterms below.",
            "hint": "Try grouping the largest possible power-of-2 blocks first.",
            "answer_format": "boolean_expression",
            "placeholder": None,
            "has_variants": True,
            "points": 2.0,  # New: K-map problem worth 2 points
        },
        {
            "id": "hw5_3a",
            "assignment_id": "hw5",
            "parent_label": "3",
            "sub_label": "a",
            "display_order": 4,
            "text": "Simplify the Boolean function F(A,B,C,D) defined by the minterms and don't-cares below.",
            "hint": "Don't-cares can help form larger groups. Check all four edges.",
            "answer_format": "boolean_expression",
            "placeholder": None,
            "has_variants": True,
            "points": 2.0,  # New: K-map problem worth 2 points
        },
        {
            "id": "hw5_3b",
            "assignment_id": "hw5",
            "parent_label": "3",
            "sub_label": "b",
            "display_order": 5,
            "text": "How many literal appearances are in your minimal SOP expression from part (a)?",
            "hint": "Count each variable appearance (complemented or not) in every product term.",
            "answer_format": "number",
            "placeholder": "e.g. 6",
            "has_variants": False,
            "points": 1.0,  # New: follow-up problem worth 1 point
        },
        {
            "id": "hw5_3c",
            "assignment_id": "hw5",
            "parent_label": "3",
            "sub_label": "c",
            "display_order": 6,
            "text": "Write the complement F'(A,B,C,D) as a minimal sum-of-products expression.",
            "hint": "The minterms of F' are the non-minterm, non-don't-care rows from part (a).",
            "answer_format": "boolean_expression",
            "placeholder": None,
            "has_variants": False,
            "points": 1.0,  # New: follow-up problem worth 1 point
        },
    ]

    for p in problems:
        cursor.execute(
            """INSERT OR REPLACE INTO problems
               (id, assignment_id, parent_label, sub_label, display_order, text,
                minterms, dont_cares, hint, answer_format, placeholder,
                problem_type, points)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                p["id"],
                p["assignment_id"],
                p["parent_label"],
                p["sub_label"],
                p["display_order"],
                p["text"],
                None,  # Will be set per-student variant
                None,
                p["hint"],
                p["answer_format"],
                p["placeholder"],
                "kmap_simplification",  # New: problem_type
                p.get("points", 1.0),   # New: points (default 1.0)
            )
        )

    conn.commit()
    print(f"✓ Seeded {len(problems)} problems")
    return problems


def generate_and_assign_variants(conn, problems, students):
    """Generate problem variants and assign to students."""
    cursor = conn.cursor()

    # Problems that need variants (K-map problems)
    variant_problems = ["hw5_1a", "hw5_2", "hw5_3a"]

    generator = TemplateGenerator()

    for problem_id in variant_problems:
        # Create a spec for this problem
        spec = ProblemSpec(
            problem_type="kmap_simplification",
            topic=f"Problem {problem_id}",
            description="K-map simplification",
            num_variants=len(students),  # One variant per student
            parameters={
                "num_variables": 4,
                "num_minterms": [6, 10],
                "num_dont_cares": [0, 3] if problem_id in ["hw5_1a", "hw5_3a"] else [0, 0],
                "variables": ["A", "B", "C", "D"]
            },
            answer_format="boolean_expression",
            difficulty="medium"
        )

        # Generate variants
        batch = generator.generate(spec)

        # Assign to each student
        for student_idx, (student_id, _, _, _) in enumerate(students):
            variant = batch.variants[student_idx]

            # Determine attempt number (Pragya on attempt 2, others on 1)
            attempt_number = 2 if student_id == "UID123456789" else 1

            # Prepare variant JSON (without solution for student view)
            variant_dict = variant.model_dump()
            solution = variant_dict.pop("solution")

            # Store variant assignment
            cursor.execute(
                """INSERT OR REPLACE INTO variant_assignments
                   (student_id, problem_id, variant_id, variant_json, solution_json, attempt_number)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    student_id,
                    problem_id,
                    str(variant.variant_id),
                    json.dumps(variant_dict),
                    json.dumps(solution),
                    attempt_number
                )
            )

        print(f"✓ Generated and assigned {len(students)} variants for {problem_id}")

    conn.commit()


def seed_variant_pool(conn):
    """Generate and populate variant_pool with 10 variants per K-map problem."""
    cursor = conn.cursor()

    variant_problems = ["hw5_1a", "hw5_2", "hw5_3a"]
    generator = TemplateGenerator()

    total_generated = 0

    for problem_id in variant_problems:
        # Create a spec for this problem
        spec = ProblemSpec(
            problem_type="kmap_simplification",
            topic=f"Problem {problem_id}",
            description="K-map simplification",
            num_variants=10,  # Generate 10 variants per problem
            parameters={
                "num_variables": 4,
                "num_minterms": [6, 10],
                "num_dont_cares": [0, 3] if problem_id in ["hw5_1a", "hw5_3a"] else [0, 0],
                "variables": ["A", "B", "C", "D"]
            },
            answer_format="boolean_expression",
            difficulty="medium"
        )

        # Generate variants
        batch = generator.generate(spec)

        for variant in batch.variants:
            variant_dict = variant.model_dump()
            solution = variant_dict.pop("solution")
            params_obj = variant_dict.get("parameters", {})

            # Compute parameter hash
            parameters = {
                "num_vars": len(params_obj.get("variables", [])),
                "minterms": params_obj.get("minterms", []),
                "dont_cares": params_obj.get("dont_cares", [])
            }
            canonical = json.dumps(parameters, sort_keys=True, separators=(',', ':'))
            param_hash = hashlib.sha256(canonical.encode()).hexdigest()

            # Format minterms and dont_cares as strings
            minterms = params_obj.get("minterms", [])
            dont_cares = params_obj.get("dont_cares", [])
            minterms_str = f"m({','.join(map(str, sorted(minterms)))})" if minterms else None
            dont_cares_str = f"d({','.join(map(str, sorted(dont_cares)))})" if dont_cares else None

            # Insert into variant_pool
            try:
                cursor.execute("""
                    INSERT INTO variant_pool (
                        id, problem_id, parameters_json, parameter_hash,
                        problem_text, minterms, dont_cares, solution_json,
                        generated_by, verified
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(variant.variant_id),
                    problem_id,
                    json.dumps(parameters),
                    param_hash,
                    variant_dict.get("problem_text"),
                    minterms_str,
                    dont_cares_str,
                    json.dumps(solution),
                    'template',
                    1
                ))
                total_generated += 1
            except Exception:
                # Skip duplicates
                pass

    conn.commit()
    print(f"✓ Generated {total_generated} variants for variant pool")


def seed_attempts(conn, students):
    """Create attempt records for students."""
    cursor = conn.cursor()

    for student_id, _, _, _ in students:
        attempt_number = 2 if student_id == "UID123456789" else 1
        # Set status based on whether it's been submitted
        # For now, all attempts are in_progress
        status = "in_progress"

        cursor.execute(
            """INSERT OR REPLACE INTO attempts
               (student_id, assignment_id, attempt_number, status)
               VALUES (?, ?, ?, ?)""",
            (student_id, "hw5", attempt_number, status)
        )

    conn.commit()
    print(f"✓ Seeded attempt records for {len(students)} students")


def main():
    """Run the complete seeding process."""
    print("\n=== AutoTA Database Seeding ===\n")

    # Initialize database
    init_db()

    # Get connection
    conn = get_db_connection()

    # Seed data
    students = [
        ("UID123456789", "Pragya Sharma", "pragya@ucla.edu", "1A"),
        ("UID987654321", "Jane Bruin", "jbruin@ucla.edu", "1A"),
        ("UID111222333", "Joe Bruin", "joebruin@ucla.edu", "1B"),
    ]

    seed_institutional_data(conn)
    seed_students(conn)
    seed_enrollments(conn)
    seed_assignment(conn)
    problems = seed_problems(conn)
    generate_and_assign_variants(conn, problems, students)
    seed_variant_pool(conn)
    seed_attempts(conn, students)

    conn.close()

    print("\n✓ Database seeding complete!\n")
    print("You can now start the server and visit:")
    print("  http://localhost:5173/?sid=UID123456789")
    print("  http://localhost:5173/?sid=UID987654321")
    print("  http://localhost:5173/?sid=UID111222333")
    print()


if __name__ == "__main__":
    main()
