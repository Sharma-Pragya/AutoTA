"""Variant pool drawing logic for AutoTA.

This module handles the logic for drawing variants from the pool,
with exclusion of previously-seen variants for retry functionality.
"""

import json
from typing import Dict, List, Set
from autota.web.db import get_db_connection


def get_prior_variant_ids(student_id: str, assignment_id: str) -> Set[str]:
    """Get all variant IDs this student has seen before in prior attempts.

    Args:
        student_id: Student ID
        assignment_id: Assignment ID

    Returns:
        Set of variant_id strings to exclude
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT variant_id
        FROM variant_assignments
        WHERE student_id = ? AND problem_id LIKE ?
    """, (student_id, f"{assignment_id}%"))

    rows = cursor.fetchall()
    conn.close()

    return {row[0] for row in rows if row[0]}


def get_problem_groups(assignment_id: str) -> Dict[str, List[str]]:
    """Group problems by parent label.

    Problems with the same parent_label share a single variant draw.
    For example, Q1a and Q1b both use the same K-map variant.

    Args:
        assignment_id: Assignment ID

    Returns:
        Dict mapping parent_label to list of problem_ids
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT parent_label, id
        FROM problems
        WHERE assignment_id = ?
        ORDER BY display_order
    """, (assignment_id,))

    rows = cursor.fetchall()
    conn.close()

    groups = {}
    for parent_label, problem_id in rows:
        if parent_label not in groups:
            groups[parent_label] = []
        groups[parent_label].append(problem_id)

    return groups


def draw_variant_from_pool(problem_id: str, exclude_ids: Set[str]) -> dict | None:
    """Draw a random variant from the pool for a problem, excluding certain IDs.

    Args:
        problem_id: Problem ID to draw variant for
        exclude_ids: Set of variant_ids to exclude

    Returns:
        Variant pool row as dict, or None if pool exhausted
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Build exclusion list for SQL
    if exclude_ids:
        placeholders = ','.join('?' * len(exclude_ids))
        query = f"""
            SELECT id, problem_id, parameters_json, parameter_hash,
                   problem_text, minterms, dont_cares, solution_json
            FROM variant_pool
            WHERE problem_id = ? AND id NOT IN ({placeholders})
            ORDER BY RANDOM()
            LIMIT 1
        """
        params = [problem_id] + list(exclude_ids)
    else:
        query = """
            SELECT id, problem_id, parameters_json, parameter_hash,
                   problem_text, minterms, dont_cares, solution_json
            FROM variant_pool
            WHERE problem_id = ?
            ORDER BY RANDOM()
            LIMIT 1
        """
        params = [problem_id]

    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "problem_id": row[1],
        "parameters_json": row[2],
        "parameter_hash": row[3],
        "problem_text": row[4],
        "minterms": row[5],
        "dont_cares": row[6],
        "solution_json": row[7]
    }


def generate_fallback_variant(problem_id: str) -> dict:
    """Generate a fresh variant if pool is exhausted.

    Uses TemplateGenerator to create a new variant on-the-fly.

    Args:
        problem_id: Problem ID to generate variant for

    Returns:
        Variant data dict
    """
    from autota.template_generator import TemplateGenerator
    from autota.models import ProblemSpec
    import hashlib
    import uuid

    # Determine problem parameters based on problem_id
    has_dont_cares = problem_id in ["hw5_1a", "hw5_3a"]

    spec = ProblemSpec(
        problem_type="kmap_simplification",
        topic=f"Problem {problem_id} (fallback)",
        description="K-map simplification",
        num_variants=1,
        parameters={
            "num_variables": 4,
            "num_minterms": [6, 10],
            "num_dont_cares": [0, 3] if has_dont_cares else [0, 0],
            "variables": ["A", "B", "C", "D"]
        },
        answer_format="boolean_expression",
        difficulty="medium"
    )

    generator = TemplateGenerator()
    batch = generator.generate(spec)
    variant = batch.variants[0]

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

    # Format minterms and dont_cares
    minterms = params_obj.get("minterms", [])
    dont_cares = params_obj.get("dont_cares", [])
    minterms_str = f"m({','.join(map(str, sorted(minterms)))})" if minterms else None
    dont_cares_str = f"d({','.join(map(str, sorted(dont_cares)))})" if dont_cares else None

    # Store in pool for future use
    conn = get_db_connection()
    cursor = conn.cursor()
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
            'fallback',
            1
        ))
        conn.commit()
    except Exception:
        # Already exists, that's fine
        pass
    finally:
        conn.close()

    return {
        "id": str(variant.variant_id),
        "problem_id": problem_id,
        "parameters_json": json.dumps(parameters),
        "parameter_hash": param_hash,
        "problem_text": variant_dict.get("problem_text"),
        "minterms": minterms_str,
        "dont_cares": dont_cares_str,
        "solution_json": json.dumps(solution)
    }


def draw_variants(student_id: str, assignment_id: str, attempt_id: int) -> Dict[str, dict]:
    """Draw one variant per independent problem group from the pool.

    Rules:
    1. For each parent group (e.g. Q1 with sub-parts a, b, c):
       - All sub-parts share ONE variant draw from the parent's pool
    2. Exclude any variant_ids this student has seen in prior attempts
    3. If pool exhausted, fall back to TemplateGenerator for fresh variant

    Args:
        student_id: Student ID
        assignment_id: Assignment ID
        attempt_id: Attempt ID (for linking variant assignments)

    Returns:
        Dict mapping problem_id to variant_pool row dict
    """
    # Get all variant IDs this student has seen before
    exclude_ids = get_prior_variant_ids(student_id, assignment_id)

    # Get problem groups (problems sharing the same parent variant)
    groups = get_problem_groups(assignment_id)

    # Draw variants for each group
    result = {}

    for parent_label, problem_ids in groups.items():
        # Find the first problem in this group that needs a variant
        # (typically the 'a' sub-problem for K-map groups)
        primary_problem = problem_ids[0]

        # Check if this is a variant-based problem (K-map) or static problem
        # K-map problems: hw5_1a, hw5_2, hw5_3a
        # Static problems: hw5_1b, hw5_3b, hw5_3c
        if primary_problem in ["hw5_1a", "hw5_2", "hw5_3a"]:
            # Draw from pool
            variant = draw_variant_from_pool(primary_problem, exclude_ids)

            if not variant:
                # Pool exhausted, generate fallback
                variant = generate_fallback_variant(primary_problem)

            # All problems in this group share the same variant
            for problem_id in problem_ids:
                result[problem_id] = variant
        else:
            # Static problems don't need variants from pool
            # They will be handled by the existing variant_assignments logic
            pass

    return result
