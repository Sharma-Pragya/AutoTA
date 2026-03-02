"""
Backfill variant_pool from existing variant_assignments.

This script:
1. Reads all rows from variant_assignments
2. For each unique (problem_id, variant_json) combination:
   - Parses the variant_json
   - Computes a SHA256 hash of the canonical parameters
   - Inserts into variant_pool with existing variant_id
3. Preserves all existing variants for reuse
"""

import sqlite3
import json
import hashlib
from pathlib import Path


def compute_parameter_hash(parameters: dict) -> str:
    """Compute SHA256 hash of canonical parameter representation."""
    # Sort keys for canonical representation
    canonical = json.dumps(parameters, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode()).hexdigest()


def backfill_variant_pool():
    """Backfill variant_pool table from existing variant_assignments."""
    db_path = Path(__file__).parent.parent / "data" / "autota.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all existing variant assignments
    cursor.execute("""
        SELECT DISTINCT variant_id, problem_id, variant_json, solution_json
        FROM variant_assignments
        WHERE variant_id IS NOT NULL
    """)

    variants = cursor.fetchall()
    print(f"Found {len(variants)} unique variant assignments")

    inserted = 0
    skipped = 0

    for variant_id, problem_id, variant_json, solution_json in variants:
        try:
            # Parse the variant JSON
            variant_data = json.loads(variant_json)
            solution_data = json.loads(solution_json) if solution_json else {}

            # Extract parameters (minterms, dont_cares, num_vars)
            # The variant_json has a nested "parameters" object
            params_obj = variant_data.get("parameters", {})
            parameters = {
                "num_vars": len(params_obj.get("variables", [])),
                "minterms": params_obj.get("minterms", []),
                "dont_cares": params_obj.get("dont_cares", [])
            }

            # Compute parameter hash
            param_hash = compute_parameter_hash(parameters)

            # Extract problem text and minterm/dont_care strings
            problem_text = variant_data.get("problem_text")
            # Format minterms and dont_cares as strings
            minterms = params_obj.get("minterms", [])
            dont_cares = params_obj.get("dont_cares", [])
            minterms_str = f"m({','.join(map(str, sorted(minterms)))})" if minterms else None
            dont_cares_str = f"d({','.join(map(str, sorted(dont_cares)))})" if dont_cares else None

            # Try to insert into variant_pool
            try:
                cursor.execute("""
                    INSERT INTO variant_pool (
                        id, problem_id, parameters_json, parameter_hash,
                        problem_text, minterms, dont_cares, solution_json,
                        generated_by, verified, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    variant_id,
                    problem_id,
                    json.dumps(parameters),
                    param_hash,
                    problem_text,
                    minterms_str,
                    dont_cares_str,
                    solution_json,
                    'template',  # All existing variants were template-generated
                    1  # Assume verified since they were used
                ))
                inserted += 1
            except sqlite3.IntegrityError:
                # Variant already exists (duplicate variant_id or problem_id+hash)
                skipped += 1

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON for variant {variant_id}: {e}")
            continue
        except Exception as e:
            print(f"Error processing variant {variant_id}: {e}")
            continue

    conn.commit()
    print(f"\nBackfill complete:")
    print(f"  Inserted: {inserted}")
    print(f"  Skipped (duplicates): {skipped}")
    print(f"  Total variants in pool: {inserted + skipped}")

    # Verify the pool
    cursor.execute("SELECT COUNT(*) FROM variant_pool")
    pool_count = cursor.fetchone()[0]
    print(f"\nVariant pool now contains {pool_count} variants")

    conn.close()


if __name__ == "__main__":
    backfill_variant_pool()
