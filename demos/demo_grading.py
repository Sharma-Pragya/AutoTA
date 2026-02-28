#!/usr/bin/env python3
"""
Demo: AutoTA Grading System (Layer 3)

This demonstrates the complete grading pipeline that can be used
to auto-grade student submissions for Boolean expression problems.

NO API KEY NEEDED - completely deterministic grading.
"""

from uuid import uuid4
from autota.models import ProblemVariant
from autota.verify.boolean import BooleanVerifier

print("="*70)
print("AutoTA Grading System Demo - Layer 3")
print("="*70)
print()

# Simulate a homework assignment
print("📚 HOMEWORK ASSIGNMENT")
print("-" * 70)
print("Problem: Simplify F(A,B,C,D) for minterms m(0,2,5,7)")
print("         Express as minimal sum-of-products.")
print()

# Create the problem variant (this would come from Layer 1 generation)
homework_variant = ProblemVariant(
    variant_id=uuid4(),
    problem_text="Simplify F(A,B,C,D) for minterms m(0,2,5,7)",
    parameters={
        "minterms": [0, 2, 5, 7],
        "dont_cares": [],
        "variables": ["A", "B", "C", "D"]
    },
    solution={"expression": "A'B'D' + A'BD"},  # Correct answer
    answer_format="boolean_expression"
)

# Simulate student submissions
students = [
    ("Alice", "A'B'D' + A'BD"),       # Correct minimal form
    ("Bob", "A'(B'D' + BD)"),         # Correct but factored
    ("Charlie", "A'B + A'D"),         # Wrong!
    ("Diana", "AB"),                  # Completely wrong
    ("Eve", "A'B'D' + A'BD + AC"),    # Has extra term
]

verifier = BooleanVerifier()

print("👨‍🎓 STUDENT SUBMISSIONS")
print("-" * 70)
print()

results = []

for name, answer in students:
    print(f"Student: {name}")
    print(f"Answer:  {answer}")

    # Grade the submission
    grade = verifier.grade(homework_variant, answer)

    # Display result
    status = "✅ PASS" if grade.correct else "❌ FAIL"
    score = f"{grade.partial_credit:.0%}"

    print(f"Result:  {status} - Score: {score}")
    print(f"Feedback: {grade.feedback[:100]}...")  # Truncate for display
    print()

    results.append({
        "name": name,
        "answer": answer,
        "score": grade.partial_credit,
        "correct": grade.correct
    })

# Show gradebook
print("="*70)
print("📊 GRADEBOOK SUMMARY")
print("="*70)
print()
print(f"{'Student':<15} {'Score':<10} {'Status'}")
print("-" * 70)

for result in results:
    status = "✅ Pass" if result['correct'] else "❌ Fail"
    score = f"{result['score']:.0%}"
    print(f"{result['name']:<15} {score:<10} {status}")

print()

# Statistics
passed = sum(1 for r in results if r['correct'])
failed = sum(1 for r in results if not r['correct'])
avg_score = sum(r['score'] for r in results) / len(results)

print(f"Class Statistics:")
print(f"  Passed: {passed}/{len(results)} ({passed/len(results):.0%})")
print(f"  Failed: {failed}/{len(results)} ({failed/len(results):.0%})")
print(f"  Average Score: {avg_score:.0%}")
print()

# Show detailed feedback for a failing student
print("="*70)
print("📝 DETAILED FEEDBACK (for Charlie)")
print("="*70)
print()

charlie_result = verifier.grade(homework_variant, "A'B + A'D")
print(f"Answer: A'B + A'D")
print(f"Score: {charlie_result.partial_credit:.0%}")
print(f"\n{charlie_result.feedback}")
print()

print("="*70)
print("✅ GRADING DEMO COMPLETE")
print("="*70)
print()
print("Key Features Demonstrated:")
print("  ✓ Instant deterministic grading (no LLM needed)")
print("  ✓ Partial credit calculation")
print("  ✓ Detailed error feedback with specific rows")
print("  ✓ Accepts functionally equivalent answers")
print("  ✓ Batch grading multiple students")
print()
print("This same verifier is used for:")
print("  1. Verifying LLM-generated solutions (Layer 1)")
print("  2. Grading student submissions (Layer 3)")
print()
print("Next: Integrate with web UI (Phase 2) for complete workflow")
print("="*70)
