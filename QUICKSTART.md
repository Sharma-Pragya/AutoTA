# AutoTA Quick Start Guide

This guide will get you up and running with AutoTA in 5 minutes.

## Prerequisites

- Python 3.9 or higher
- An Anthropic API key (get one at https://console.anthropic.com/)

## Setup

### 1. Clone and Install

```bash
git clone https://github.com/yourusername/autota.git
cd autota
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### 2. Configure API Key

```bash
cp .env.example .env
# Edit .env and add your API key:
# ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Verify Installation

```bash
# Run tests
pytest

# Check CLI
autota --help
autota list-types
```

Expected output:
```
Registered Problem Types

  • kmap_simplification
```

## Generate Your First Problem Variants

AutoTA comes with an example K-map simplification spec. Let's use it:

```bash
autota generate --spec specs/example_kmap.yaml --num 3
```

You should see:
```
AutoTA Problem Generator
Spec: specs/example_kmap.yaml
Output: output

Generating 3 variants...
Generated 3 variants from API
Verifying variants...
Verified: 3, Failed: 0
Writing 3 verified variants to output/example_kmap
Report written to output/example_kmap/report.json

Success! All 3 variants verified.
```

## Explore the Output

```bash
ls output/example_kmap/
```

You'll see:
- `{variant-id-1}.json` - First problem variant
- `{variant-id-2}.json` - Second problem variant
- `{variant-id-3}.json` - Third problem variant
- `report.json` - Summary report

### Example Variant File

```json
{
  "variant_id": "a1b2c3d4-...",
  "problem_text": "Simplify the Boolean function F(A,B,C,D) defined by the following minterms: m(0,2,5,7,8,10,13,15). Express your answer as a minimal sum-of-products.",
  "parameters": {
    "minterms": [0, 2, 5, 7, 8, 10, 13, 15],
    "dont_cares": [],
    "variables": ["A", "B", "C", "D"]
  },
  "solution": {
    "expression": "B'D' + BD",
    "method": "kmap"
  },
  "answer_format": "boolean_expression"
}
```

## Re-verify Existing Variants

If you want to test the verifier independently:

```bash
autota verify --input output/example_kmap/ --type kmap_simplification
```

## Create Your Own Problem Spec

Create a new file `specs/my_problem.yaml`:

```yaml
problem_type: kmap_simplification
topic: "3-Variable K-Map Practice"
description: "Simplify Boolean functions with 3 variables"
num_variants: 10
parameters:
  num_variables: 3
  num_minterms: [3, 6]  # 3 to 6 minterms
  num_dont_cares: [0, 2]  # 0 to 2 don't-cares
  variables: ["A", "B", "C"]
answer_format: "boolean_expression"
difficulty: "easy"
```

Generate variants:

```bash
autota generate --spec specs/my_problem.yaml
```

## What Each File Does

- **specs/** - Problem specifications (YAML)
- **autota/models.py** - Data structures (ProblemSpec, ProblemVariant, etc.)
- **autota/verify/** - Verifiers (deterministic checkers, no LLMs)
- **autota/generator.py** - Claude API integration
- **autota/orchestrator.py** - Coordinates generation + verification
- **autota/cli.py** - Command-line interface
- **output/** - Generated variants (gitignored)
- **materials/** - Reference materials (gitignored)

## Common Issues

### "ANTHROPIC_API_KEY not found"
Make sure you've created `.env` and added your API key.

### Tests failing
Make sure you're in the virtual environment:
```bash
source venv/bin/activate
```

### Import errors
Reinstall in editable mode:
```bash
pip install -e .
```

## Next Steps

1. **Scale up**: Try generating 50+ variants
2. **Customize specs**: Modify parameters for different problem types
3. **Add verifiers**: Create new problem types (see README.md)
4. **Integrate with your LMS**: Use the JSON output in your grading system

## Need Help?

- Check the full README.md for detailed documentation
- Run tests: `pytest tests/ -v`
- Open an issue on GitHub

## Example: Full Workflow

```bash
# 1. Create a spec
cat > specs/hw5_kmaps.yaml << 'EOF'
problem_type: kmap_simplification
topic: "Homework 5 - Karnaugh Maps"
description: "Simplify 4-variable Boolean functions"
num_variants: 70  # One for each student
parameters:
  num_variables: 4
  num_minterms: [6, 12]
  num_dont_cares: [0, 4]
  require_edge_wrap: true
  variables: ["A", "B", "C", "D"]
answer_format: "boolean_expression"
difficulty: "medium"
EOF

# 2. Generate variants
autota generate --spec specs/hw5_kmaps.yaml

# 3. Check the report
cat output/hw5_kmaps/report.json

# 4. Distribute variants to students
# Each student gets a unique variant from output/hw5_kmaps/

# 5. Grade student answers
# Use the solution.expression field to verify correctness
```

That's it! You now have 70 unique, verified K-map problems. 🎉

---

**Pro tip**: Start small (5 variants) to test your spec, then scale up to your full class size once you're confident in the parameters.
