# AutoTA - LLM-Powered Parameterized Assessment Generator

AutoTA generates unique, computationally verified problem variants for STEM courses using LLMs. Instead of giving every student the same homework problem (which they can copy or feed to ChatGPT), AutoTA generates N unique variants of each problem with different parameters, each with a verified solution.

**The core principle**: LLMs generate, deterministic code verifies. These two components are intentionally decoupled.

## Current Status

**Phase 1 - CLI Generation + Verification Pipeline** ✅

- ✅ Domain-agnostic architecture with pluggable verifiers
- ✅ Boolean algebra verifier (K-maps, truth tables)
- ✅ Claude API integration for variant generation
- ✅ Comprehensive testing suite
- ✅ CLI interface with rich output

**Target Domain**: Digital logic (UCLA ECE M16) - Boolean algebra, K-maps, truth tables, logic gate analysis

**Future Phases**: Web UI, database storage, student grading, Discord bot integration

## Features

- 🎯 **Unique Problem Variants**: Generate dozens or hundreds of unique variants from a single spec
- ✅ **Computational Verification**: Every solution is verified by deterministic Python code (never LLM-based)
- 🔌 **Pluggable Architecture**: Easy to add new problem types and verifiers
- 🚀 **Production Ready**: Batch generation, retry logic, detailed error reporting
- 📊 **Rich CLI**: Beautiful terminal output with progress tracking and statistics

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/autota.git
cd autota

# Install dependencies
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

### 2. Configuration

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your Anthropic API key
# ANTHROPIC_API_KEY=your-key-here
```

### 3. Generate Problem Variants

```bash
# Generate 5 K-map simplification problems
autota generate --spec specs/example_kmap.yaml --num 5

# Output will be in output/example_kmap/
```

### 4. Verify Existing Variants

```bash
# Re-verify already generated variants
autota verify --input output/example_kmap/ --type kmap_simplification
```

## Architecture

```
┌─────────────────┐
│  Problem Spec   │  YAML file defining problem constraints
│   (YAML)        │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Prompt Builder  │  Constructs prompts for Claude API
└────────┬────────┘
         │
         v
┌─────────────────┐
│   Generator     │  Calls Claude API, parses JSON response
│  (Claude API)   │
└────────┬────────┘
         │
         v
┌─────────────────┐
│   Verifier      │  Deterministic Python verification
│  (No LLMs!)     │  • Boolean algebra (truth tables)
└────────┬────────┘  • Future: circuits, calculus, etc.
         │
         v
┌─────────────────┐
│     Output      │  Verified variants + summary report
│     (JSON)      │
└─────────────────┘
```

## Problem Spec Format

Define problems using YAML:

```yaml
problem_type: kmap_simplification
topic: "Karnaugh Map Simplification"
description: "Simplify a Boolean function using a 4-variable K-map"
num_variants: 5
parameters:
  num_variables: 4
  num_minterms: [6, 10]  # range
  num_dont_cares: [0, 3]  # range
  require_edge_wrap: true
  variables: ["A", "B", "C", "D"]
reference_material: "materials/hw5_kmap.pdf"  # optional
answer_format: "boolean_expression"
difficulty: "medium"
```

## Generated Variant Format

Each variant is a JSON file:

```json
{
  "variant_id": "uuid-here",
  "problem_text": "Simplify F(A,B,C,D) with minterms m(0,2,5,7,8,10,13,15)...",
  "parameters": {
    "minterms": [0, 2, 5, 7, 8, 10, 13, 15],
    "dont_cares": [],
    "variables": ["A", "B", "C", "D"]
  },
  "solution": {
    "expression": "B'D' + BD",
    "method": "kmap"
  },
  "answer_format": "boolean_expression",
  "metadata": {
    "has_edge_wrap": true
  }
}
```

## Adding New Problem Types

1. **Create a verifier** in `autota/verify/`:

```python
from autota.verify.base import Verifier
from autota.verify.registry import register_verifier
from autota.models import ProblemVariant, VerificationResult

@register_verifier
class MyVerifier(Verifier):
    @property
    def problem_type(self) -> str:
        return "my_problem_type"

    def verify(self, variant: ProblemVariant) -> VerificationResult:
        # Deterministic verification logic here
        # NO LLM calls allowed!
        pass
```

2. **Create a spec** in `specs/`:

```yaml
problem_type: my_problem_type
# ... your parameters ...
```

3. **Generate and verify**:

```bash
autota generate --spec specs/my_problem.yaml
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=autota --cov-report=html

# Run specific test file
pytest tests/test_boolean_verifier.py -v
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Format code
black autota/ tests/

# Lint code
ruff check autota/ tests/
```

## Project Structure

```
autota/
├── README.md                    # This file
├── .gitignore
├── .env.example
├── pyproject.toml              # Package configuration
├── specs/                       # Problem specifications
│   └── example_kmap.yaml
├── autota/                      # Main package
│   ├── __init__.py
│   ├── cli.py                  # CLI entry point
│   ├── models.py               # Pydantic models
│   ├── prompt_builder.py       # Prompt construction
│   ├── generator.py            # Claude API integration
│   ├── orchestrator.py         # Pipeline coordination
│   └── verify/                 # Verification modules
│       ├── __init__.py
│       ├── base.py             # Abstract verifier
│       ├── registry.py         # Verifier registry
│       └── boolean.py          # Boolean algebra verifier
├── materials/                  # Gitignored - reference materials
├── output/                     # Gitignored - generated variants
└── tests/                      # Test suite
    ├── test_models.py
    └── test_boolean_verifier.py
```

## Design Principles

1. **Domain-Agnostic Core**: The orchestrator, CLI, models, and generator work for any problem type
2. **Verification is Never LLM-Based**: Verifiers are deterministic Python - no API calls
3. **Fail Loudly**: Failed variants are flagged clearly, never silently passed
4. **Everything is JSON**: Variants, results, reports - all structured data
5. **Pluggable Verifiers**: Add new problem types without modifying core code

## Roadmap

- [x] Phase 1: CLI generation + verification pipeline
- [ ] Phase 2: PDF parsing for reference materials
- [ ] Phase 3: Minimality checking for Boolean expressions
- [ ] Phase 4: Additional verifiers (circuit analysis, truth tables)
- [ ] Phase 5: Student grading system
- [ ] Phase 6: Web UI
- [ ] Phase 7: Discord bot integration
- [ ] Phase 8: Database storage and analytics

## Contributing

Contributions welcome! Key areas:

- New verifiers for different problem types
- Improved verification algorithms
- Better prompt engineering for higher success rates
- Documentation and examples

## License

[Add your license here]

## Citation

If you use AutoTA in your research or teaching, please cite:

```
[Add citation when published]
```

## Contact

[Add contact information]

---

Built with ❤️ for educators who want to maintain academic integrity while leveraging AI to scale personalized learning.
