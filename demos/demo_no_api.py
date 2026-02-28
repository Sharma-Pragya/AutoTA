#!/usr/bin/env python3
"""
Demo: What AutoTA can do WITHOUT an API key

This demonstrates the verification engine, which is the core
of AutoTA and works completely offline with no costs.
"""

from uuid import uuid4
from autota.models import ProblemVariant
from autota.verify.boolean import BooleanVerifier

print("="*70)
print("AutoTA Demo - NO API KEY NEEDED")
print("="*70)
print()

# Initialize verifier
verifier = BooleanVerifier()

print("✅ Use Case 1: Verify a Boolean Expression")
print("-" * 70)

variant1 = ProblemVariant(
    variant_id=uuid4(),
    problem_text="Simplify F(A,B,C) where F=1 for minterms [0,2,4,6]",
    parameters={
        "minterms": [0, 2, 4, 6],
        "dont_cares": [],
        "variables": ["A", "B", "C"]
    },
    solution={"expression": "C'"},  # Minimal solution
    answer_format="boolean_expression"
)

result1 = verifier.verify(variant1)
print(f"Problem: {variant1.problem_text}")
print(f"Minterms: {variant1.parameters['minterms']}")
print(f"Proposed Solution: {variant1.solution['expression']}")
print(f"Verification: {'✅ CORRECT' if result1.passed else '❌ INCORRECT'}")
print()

print("✅ Use Case 2: Detect Incorrect Solutions")
print("-" * 70)

variant2 = ProblemVariant(
    variant_id=uuid4(),
    problem_text="Simplify F(A,B) where F=1 for minterms [1,3]",
    parameters={
        "minterms": [1, 3],
        "dont_cares": [],
        "variables": ["A", "B"]
    },
    solution={"expression": "A"},  # WRONG! Should be "B"
    answer_format="boolean_expression"
)

result2 = verifier.verify(variant2)
print(f"Problem: {variant2.problem_text}")
print(f"Minterms: {variant2.parameters['minterms']}")
print(f"Proposed Solution: {variant2.solution['expression']}")
print(f"Verification: {'✅ CORRECT' if result2.passed else '❌ INCORRECT'}")
if not result2.passed:
    print(f"Error: {result2.error_message}")
print()

print("✅ Use Case 3: Grade Student Answers")
print("-" * 70)

# Teacher's problem
problem_minterms = [0, 2, 5, 7]
problem_vars = ["A", "B", "C", "D"]

# Three students submit different answers
student_answers = [
    ("Alice", "A'B'D' + A'BD"),      # Correct minimal form
    ("Bob", "A'(B'D' + BD)"),        # Correct but factored
    ("Charlie", "AB"),                # Wrong
]

print(f"Problem: Simplify F(A,B,C,D) for minterms {problem_minterms}")
print()

for name, answer in student_answers:
    student_variant = ProblemVariant(
        variant_id=uuid4(),
        problem_text="Student submission",
        parameters={
            "minterms": problem_minterms,
            "dont_cares": [],
            "variables": problem_vars
        },
        solution={"expression": answer},
        answer_format="boolean_expression"
    )

    result = verifier.verify(student_variant)
    status = "✅ CORRECT" if result.passed else "❌ INCORRECT"
    print(f"{name:8} → {answer:20} {status}")

print()

print("✅ Use Case 4: Verify Complex Expressions")
print("-" * 70)

variant4 = ProblemVariant(
    variant_id=uuid4(),
    problem_text="Complex expression with parentheses",
    parameters={
        "minterms": [1, 3, 5, 7, 9, 11, 13, 15],
        "dont_cares": [],
        "variables": ["A", "B", "C", "D"]
    },
    solution={"expression": "(A+B+C)D"},  # All rows where D=1
    answer_format="boolean_expression"
)

result4 = verifier.verify(variant4)
print(f"Expression: {variant4.solution['expression']}")
print(f"Covers minterms: {variant4.parameters['minterms']}")
print(f"Verification: {'✅ CORRECT' if result4.passed else '❌ INCORRECT'}")
print()

print("✅ Use Case 5: Handle Don't-Cares")
print("-" * 70)

variant5 = ProblemVariant(
    variant_id=uuid4(),
    problem_text="Problem with don't-cares",
    parameters={
        "minterms": [0, 2, 8, 10],
        "dont_cares": [1, 3, 9, 11],
        "variables": ["A", "B", "C", "D"]
    },
    solution={"expression": "B'D'"},  # Can use don't-cares for simplification
    answer_format="boolean_expression"
)

result5 = verifier.verify(variant5)
print(f"Minterms: {variant5.parameters['minterms']}")
print(f"Don't-cares: {variant5.parameters['dont_cares']}")
print(f"Solution: {variant5.solution['expression']}")
print(f"Verification: {'✅ CORRECT' if result5.passed else '❌ INCORRECT'}")
print()

print("="*70)
print("Summary: What Works Without API Key")
print("="*70)
print("""
✅ Verify any Boolean expression against minterms
✅ Grade student answers (check correctness)
✅ Detect incorrect solutions
✅ Handle don't-care conditions
✅ Support 2, 3, 4+ variable problems
✅ Parse complex expressions (parentheses, negations, etc.)
✅ Generate detailed error reports

❌ Cannot generate NEW problem text (needs LLM)
❌ Cannot create creative problem variations (needs LLM)

💡 Solution: Add template-based generator (no LLM needed)
   → Random minterms + algorithmic solver
   → Unlimited free problem generation
""")
print("="*70)
