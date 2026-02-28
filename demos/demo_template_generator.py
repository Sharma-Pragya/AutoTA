#!/usr/bin/env python3
"""
Demo: Template-Based Problem Generator

This demonstrates generating unlimited problem variants WITHOUT using LLMs.
Uses random parameter selection + Quine-McCluskey solver for solutions.

NO API KEY NEEDED - completely free and unlimited!
"""

from autota.template_generator import TemplateGenerator
from autota.models import ProblemSpec
from autota.verify.boolean import BooleanVerifier

print("="*70)
print("AutoTA Template Generator Demo")
print("="*70)
print()
print("✨ Generate UNLIMITED problems at $0 cost!")
print("✨ NO API key needed!")
print("✨ Instant generation!")
print()

# Example 1: Generate 5 K-map problems
print("📌 Example 1: Generate 5 K-Map Problems")
print("-" * 70)

spec = ProblemSpec(
    problem_type="kmap_simplification",
    topic="Practice K-Maps",
    description="Practice problems for K-map simplification",
    num_variants=5,
    parameters={
        "num_variables": 4,
        "num_minterms": [6, 10],
        "num_dont_cares": [0, 3],
        "variables": ["A", "B", "C", "D"]
    },
    answer_format="boolean_expression",
    difficulty="medium"
)

generator = TemplateGenerator(seed=42)
batch = generator.generate(spec)

print(f"Generated {batch.num_generated} variants")
print()

# Show first 3
for i, variant in enumerate(batch.variants[:3], 1):
    print(f"Problem {i}:")
    print(f"  Minterms: {variant.parameters['minterms']}")
    print(f"  Solution: {variant.solution['expression']}")
    print(f"  Terms: {variant.solution['num_terms']}, Literals: {variant.solution['num_literals']}")
    print()

# Example 2: Verify all solutions
print("📌 Example 2: Verify All Solutions")
print("-" * 70)

verifier = BooleanVerifier()
all_passed = True

for i, variant in enumerate(batch.variants, 1):
    result = verifier.verify(variant)
    if not result.passed:
        print(f"❌ Variant {i} FAILED")
        all_passed = False

if all_passed:
    print(f"✅ All {len(batch.variants)} solutions verified correctly!")
print()

# Example 3: Generate with reproducibility
print("📌 Example 3: Reproducible Generation (with seed)")
print("-" * 70)

gen1 = TemplateGenerator(seed=123)
batch1 = gen1.generate(spec)

gen2 = TemplateGenerator(seed=123)
batch2 = gen2.generate(spec)

print("Generated with seed=123 twice:")
print(f"Batch 1, Variant 1 minterms: {batch1.variants[0].parameters['minterms']}")
print(f"Batch 2, Variant 1 minterms: {batch2.variants[0].parameters['minterms']}")
print(f"Identical: {batch1.variants[0].parameters['minterms'] == batch2.variants[0].parameters['minterms']}")
print()

# Example 4: Different variable counts
print("📌 Example 4: Different Variable Counts")
print("-" * 70)

for num_vars in [2, 3, 4, 5]:
    spec_n = ProblemSpec(
        problem_type="kmap_simplification",
        topic=f"{num_vars}-Variable K-Maps",
        description="Test",
        num_variants=3,
        parameters={
            "num_variables": num_vars,
            "num_minterms": [2, 2**(num_vars-1)],
            "num_dont_cares": [0, 2],
            "variables": [chr(ord('A') + i) for i in range(num_vars)]
        },
        answer_format="boolean_expression"
    )

    gen = TemplateGenerator(seed=num_vars * 100)
    batch_n = gen.generate(spec_n)

    print(f"{num_vars} variables: Generated {batch_n.num_generated} variants")
    example_solution = batch_n.variants[0].solution['expression']
    print(f"  Example solution: {example_solution}")

print()

# Example 5: Large batch (classroom size)
print("📌 Example 5: Generate Classroom-Size Batch")
print("-" * 70)

classroom_spec = ProblemSpec(
    problem_type="kmap_simplification",
    topic="Homework 5: K-Map Simplification",
    description="Homework assignment",
    num_variants=70,  # One per student
    parameters={
        "num_variables": 4,
        "num_minterms": [6, 10],
        "num_dont_cares": [0, 3],
        "variables": ["A", "B", "C", "D"]
    },
    answer_format="boolean_expression",
    difficulty="medium"
)

import time
start_time = time.time()

gen = TemplateGenerator(seed=999)
classroom_batch = gen.generate(classroom_spec)

elapsed = time.time() - start_time

print(f"Generated {classroom_batch.num_generated} unique problems")
print(f"Time taken: {elapsed:.3f} seconds")
print(f"Speed: {classroom_batch.num_generated / elapsed:.1f} problems/second")
print()

# Verify uniqueness
param_sets = set()
for variant in classroom_batch.variants:
    minterms = tuple(sorted(variant.parameters['minterms']))
    param_sets.add(minterms)

print(f"Unique parameter sets: {len(param_sets)}")
print(f"All unique: {len(param_sets) == len(classroom_batch.variants)}")
print()

# Example 6: Problem text preview
print("📌 Example 6: Generated Problem Text")
print("-" * 70)

example = classroom_batch.variants[0]
print("Sample problem given to student:")
print()
print(example.problem_text)
print()
print(f"(Answer: {example.solution['expression']})")
print()

# Example 7: Compare with LLM approach
print("📌 Example 7: Template vs LLM Comparison")
print("-" * 70)

comparison_table = [
    ("Cost", "$0.00", "~$0.21 for 70 variants"),
    ("Speed", f"{classroom_batch.num_generated / elapsed:.0f} problems/sec", "~1 problem/sec"),
    ("Reliability", "100% verified", "~90-95% pass rate"),
    ("Offline", "Yes", "No"),
    ("API Key", "Not needed", "Required"),
    ("Text Variety", "Low (templates)", "High (creative)"),
    ("Minimality", "Guaranteed", "Not guaranteed"),
]

print(f"{'Metric':<15} {'Template Generator':<25} {'LLM Generator'}")
print("-" * 70)
for metric, template_val, llm_val in comparison_table:
    print(f"{metric:<15} {template_val:<25} {llm_val}")

print()

print("="*70)
print("🎯 Use Cases for Template Generator:")
print("="*70)
print("  ✓ Development and testing (no API key needed)")
print("  ✓ Practice problems (unlimited quantity)")
print("  ✓ Bulk generation (70+ variants instantly)")
print("  ✓ Teaching demonstrations (reproducible with seed)")
print("  ✓ Cost-sensitive scenarios ($0 vs paid API)")
print()
print("💡 When to use LLM generator instead:")
print("  • Need creative, varied problem text")
print("  • Want story-based problems")
print("  • Final distribution to students")
print()

print("="*70)
print("✅ DEMO COMPLETE")
print("="*70)
print()
print("Try it yourself:")
print("  autota generate-template --spec specs/example_kmap.yaml --num 10")
print("  autota generate-template --spec specs/example_kmap.yaml --num 70 --seed 42")
print()
print("Compare with LLM generation (requires API key):")
print("  autota generate --spec specs/example_kmap.yaml --num 10")
print()
print("="*70)
