#!/usr/bin/env python3
"""
Quick API test script for AutoTA.

This script tests the full generation pipeline with a small batch.
Run this after setting your ANTHROPIC_API_KEY in .env
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Check for API key
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("❌ Error: ANTHROPIC_API_KEY not found in .env file")
    print("\nPlease add your API key to .env:")
    print("  echo 'ANTHROPIC_API_KEY=sk-ant-your-key-here' > .env")
    print("\nGet an API key at: https://console.anthropic.com/")
    sys.exit(1)

print("✓ API key found")
print(f"✓ Key starts with: {api_key[:15]}...")

# Import AutoTA components
from autota.models import ProblemSpec
from autota.generator import VariantGenerator
from autota.verify.boolean import BooleanVerifier

print("\n" + "="*60)
print("AutoTA API Integration Test")
print("="*60)

# Create a minimal test spec
print("\n📝 Creating test spec...")
spec = ProblemSpec(
    problem_type="kmap_simplification",
    topic="API Test - 3-Variable K-Maps",
    description="Simple 3-variable Boolean functions for API testing",
    num_variants=2,  # Small batch for quick testing
    parameters={
        "num_variables": 3,
        "num_minterms": [3, 5],
        "num_dont_cares": [0, 1],
        "variables": ["A", "B", "C"]
    },
    answer_format="boolean_expression",
    difficulty="easy"
)
print(f"✓ Spec created: {spec.topic}")
print(f"  Requesting {spec.num_variants} variants")

# Generate variants
print("\n🔄 Calling Claude API...")
print("  (This may take 5-10 seconds)")
try:
    generator = VariantGenerator(api_key=api_key)
    batch = generator.generate(spec)
    print(f"✓ API call successful!")
    print(f"  Generated {batch.num_generated} variants")
    print(f"  Model used: {batch.model_used}")
except Exception as e:
    print(f"❌ API call failed: {e}")
    sys.exit(1)

# Verify variants
print("\n🔍 Verifying variants...")
verifier = BooleanVerifier()
verified_count = 0
failed_count = 0

for i, variant in enumerate(batch.variants, 1):
    result = verifier.verify(variant)

    if result.passed:
        verified_count += 1
        print(f"✓ Variant {i} verified")
        print(f"  Minterms: {variant.parameters.get('minterms')}")
        print(f"  Solution: {variant.solution.get('expression')}")
    else:
        failed_count += 1
        print(f"❌ Variant {i} failed verification")
        print(f"  Error: {result.error_message}")

# Summary
print("\n" + "="*60)
print("Test Summary")
print("="*60)
print(f"Total generated: {batch.num_generated}")
print(f"Verified: {verified_count}")
print(f"Failed: {failed_count}")
print(f"Success rate: {verified_count/batch.num_generated*100:.1f}%")

if verified_count == batch.num_generated:
    print("\n🎉 SUCCESS! All variants verified correctly.")
    print("\nYour API integration is working perfectly!")
    print("\nNext steps:")
    print("  1. Try: autota generate --spec specs/example_kmap.yaml --num 5")
    print("  2. Check output in: output/example_kmap/")
    print("  3. Read: API_TESTING_GUIDE.md for more tests")
elif verified_count > 0:
    print("\n⚠️  PARTIAL SUCCESS: Some variants verified.")
    print("\nThis is normal - not all LLM outputs are perfect.")
    print("The system correctly rejected invalid solutions!")
else:
    print("\n❌ FAILURE: No variants verified.")
    print("\nThis might indicate:")
    print("  - API response format issue")
    print("  - Verification logic issue")
    print("  - Check the error messages above")

print("\n" + "="*60)
