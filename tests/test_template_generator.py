"""Tests for template-based problem generator."""

import pytest
from autota.template_generator import TemplateGenerator
from autota.models import ProblemSpec
from autota.verify.boolean import BooleanVerifier


class TestTemplateGenerator:
    """Test the template-based generator."""

    def test_generator_creation(self):
        """Test creating a template generator."""
        gen = TemplateGenerator()
        assert gen is not None

    def test_generator_with_seed(self):
        """Test that seeded generator produces reproducible results."""
        spec = ProblemSpec(
            problem_type="kmap_simplification",
            topic="Test",
            description="Test",
            num_variants=5,
            parameters={
                "num_variables": 3,
                "num_minterms": [3, 5],
                "num_dont_cares": [0, 2],
                "variables": ["A", "B", "C"]
            },
            answer_format="boolean_expression"
        )

        # Generate with same seed twice
        gen1 = TemplateGenerator(seed=42)
        batch1 = gen1.generate(spec)

        gen2 = TemplateGenerator(seed=42)
        batch2 = gen2.generate(spec)

        # Should produce same minterms
        assert len(batch1.variants) == len(batch2.variants)
        for v1, v2 in zip(batch1.variants, batch2.variants):
            assert v1.parameters["minterms"] == v2.parameters["minterms"]

    def test_generate_kmap_variants(self):
        """Test generating K-map variants."""
        spec = ProblemSpec(
            problem_type="kmap_simplification",
            topic="K-Map Test",
            description="Test K-map generation",
            num_variants=5,
            parameters={
                "num_variables": 4,
                "num_minterms": [6, 10],
                "num_dont_cares": [0, 3],
                "variables": ["A", "B", "C", "D"]
            },
            answer_format="boolean_expression"
        )

        gen = TemplateGenerator()
        batch = gen.generate(spec)

        assert batch.num_requested == 5
        assert batch.num_generated == 5
        assert len(batch.variants) == 5
        assert batch.model_used == "template_generator"

    def test_variants_have_unique_parameters(self):
        """Test that each variant has unique parameters."""
        spec = ProblemSpec(
            problem_type="kmap_simplification",
            topic="Uniqueness Test",
            description="Test uniqueness",
            num_variants=10,
            parameters={
                "num_variables": 4,
                "num_minterms": [5, 8],
                "num_dont_cares": [0, 2],
                "variables": ["A", "B", "C", "D"]
            },
            answer_format="boolean_expression"
        )

        gen = TemplateGenerator(seed=123)
        batch = gen.generate(spec)

        # Check uniqueness
        param_sets = set()
        for variant in batch.variants:
            minterms = tuple(sorted(variant.parameters["minterms"]))
            dont_cares = tuple(sorted(variant.parameters["dont_cares"]))
            param_sig = (minterms, dont_cares)

            assert param_sig not in param_sets, "Duplicate parameters found!"
            param_sets.add(param_sig)

    def test_solutions_are_verified(self):
        """Test that all generated solutions verify correctly."""
        spec = ProblemSpec(
            problem_type="kmap_simplification",
            topic="Verification Test",
            description="Test solution verification",
            num_variants=10,
            parameters={
                "num_variables": 4,
                "num_minterms": [4, 8],
                "num_dont_cares": [0, 3],
                "variables": ["A", "B", "C", "D"]
            },
            answer_format="boolean_expression"
        )

        gen = TemplateGenerator(seed=456)
        batch = gen.generate(spec)

        verifier = BooleanVerifier()

        # Verify each generated variant
        for variant in batch.variants:
            result = verifier.verify(variant)
            assert result.passed, f"Generated solution failed verification: {result.error_message}"

    def test_respects_minterm_range(self):
        """Test that generator respects minterm count constraints."""
        spec = ProblemSpec(
            problem_type="kmap_simplification",
            topic="Range Test",
            description="Test minterm range",
            num_variants=20,
            parameters={
                "num_variables": 4,
                "num_minterms": [6, 8],  # Specific range
                "num_dont_cares": [0, 0],  # No don't-cares
                "variables": ["A", "B", "C", "D"]
            },
            answer_format="boolean_expression"
        )

        gen = TemplateGenerator(seed=789)
        batch = gen.generate(spec)

        for variant in batch.variants:
            num_minterms = len(variant.parameters["minterms"])
            assert 6 <= num_minterms <= 8, f"Minterm count {num_minterms} outside range [6, 8]"

    def test_respects_dont_care_range(self):
        """Test that generator respects don't-care count constraints."""
        spec = ProblemSpec(
            problem_type="kmap_simplification",
            topic="Don't-Care Test",
            description="Test don't-care range",
            num_variants=15,
            parameters={
                "num_variables": 4,
                "num_minterms": [6, 8],
                "num_dont_cares": [1, 3],  # Must have 1-3 don't-cares
                "variables": ["A", "B", "C", "D"]
            },
            answer_format="boolean_expression"
        )

        gen = TemplateGenerator(seed=101)
        batch = gen.generate(spec)

        for variant in batch.variants:
            num_dont_cares = len(variant.parameters["dont_cares"])
            assert 1 <= num_dont_cares <= 3, f"Don't-care count {num_dont_cares} outside range [1, 3]"

    def test_problem_text_format(self):
        """Test that problem text is properly formatted."""
        spec = ProblemSpec(
            problem_type="kmap_simplification",
            topic="Format Test",
            description="Test text format",
            num_variants=5,
            parameters={
                "num_variables": 3,
                "num_minterms": [3, 5],
                "num_dont_cares": [0, 2],
                "variables": ["A", "B", "C"]
            },
            answer_format="boolean_expression"
        )

        gen = TemplateGenerator(seed=202)
        batch = gen.generate(spec)

        for variant in batch.variants:
            text = variant.problem_text

            # Should contain variable list
            assert "A,B,C" in text or "(A,B,C)" in text

            # Should mention minterms
            assert "minterm" in text.lower()

            # Should have instruction to simplify
            assert "simplify" in text.lower() or "Simplify" in text

    def test_metadata_included(self):
        """Test that variants include proper metadata."""
        spec = ProblemSpec(
            problem_type="kmap_simplification",
            topic="Metadata Test",
            description="Test metadata",
            num_variants=5,
            parameters={
                "num_variables": 4,
                "num_minterms": [6, 8],
                "num_dont_cares": [0, 2],
                "variables": ["A", "B", "C", "D"]
            },
            answer_format="boolean_expression",
            difficulty="medium"
        )

        gen = TemplateGenerator(seed=303)
        batch = gen.generate(spec)

        for variant in batch.variants:
            assert variant.metadata is not None
            assert variant.metadata["generator"] == "template"
            assert variant.metadata["difficulty"] == "medium"
            assert variant.metadata["num_variables"] == 4
            assert "has_dont_cares" in variant.metadata

    def test_solution_includes_details(self):
        """Test that solutions include algorithmic details."""
        spec = ProblemSpec(
            problem_type="kmap_simplification",
            topic="Solution Details Test",
            description="Test solution details",
            num_variants=5,
            parameters={
                "num_variables": 4,
                "num_minterms": [6, 8],
                "num_dont_cares": [0, 2],
                "variables": ["A", "B", "C", "D"]
            },
            answer_format="boolean_expression"
        )

        gen = TemplateGenerator(seed=404)
        batch = gen.generate(spec)

        for variant in batch.variants:
            solution = variant.solution
            assert "expression" in solution
            assert "method" in solution
            assert solution["method"] == "kmap"
            assert "num_terms" in solution
            assert "num_literals" in solution

    def test_2_variable_generation(self):
        """Test generating 2-variable problems."""
        spec = ProblemSpec(
            problem_type="kmap_simplification",
            topic="2-Var Test",
            description="Test 2-variable generation",
            num_variants=4,
            parameters={
                "num_variables": 2,
                "num_minterms": [1, 3],
                "num_dont_cares": [0, 1],
                "variables": ["A", "B"]
            },
            answer_format="boolean_expression"
        )

        gen = TemplateGenerator(seed=505)
        batch = gen.generate(spec)

        assert len(batch.variants) == 4

        verifier = BooleanVerifier()
        for variant in batch.variants:
            result = verifier.verify(variant)
            assert result.passed

    def test_3_variable_generation(self):
        """Test generating 3-variable problems."""
        spec = ProblemSpec(
            problem_type="kmap_simplification",
            topic="3-Var Test",
            description="Test 3-variable generation",
            num_variants=8,
            parameters={
                "num_variables": 3,
                "num_minterms": [3, 6],
                "num_dont_cares": [0, 2],
                "variables": ["A", "B", "C"]
            },
            answer_format="boolean_expression"
        )

        gen = TemplateGenerator(seed=606)
        batch = gen.generate(spec)

        assert len(batch.variants) == 8

        verifier = BooleanVerifier()
        for variant in batch.variants:
            result = verifier.verify(variant)
            assert result.passed

    def test_5_variable_generation(self):
        """Test generating 5-variable problems."""
        spec = ProblemSpec(
            problem_type="kmap_simplification",
            topic="5-Var Test",
            description="Test 5-variable generation",
            num_variants=5,
            parameters={
                "num_variables": 5,
                "num_minterms": [8, 12],
                "num_dont_cares": [0, 4],
                "variables": ["A", "B", "C", "D", "E"]
            },
            answer_format="boolean_expression"
        )

        gen = TemplateGenerator(seed=707)
        batch = gen.generate(spec)

        assert len(batch.variants) == 5

        verifier = BooleanVerifier()
        for variant in batch.variants:
            result = verifier.verify(variant)
            assert result.passed

    def test_unsupported_problem_type(self):
        """Test that unsupported problem types raise error."""
        spec = ProblemSpec(
            problem_type="unsupported_type",
            topic="Error Test",
            description="Test error handling",
            num_variants=1,
            parameters={},
            answer_format="text"
        )

        gen = TemplateGenerator()

        with pytest.raises(ValueError, match="does not support"):
            gen.generate(spec)

    def test_large_batch_generation(self):
        """Test generating a large batch of variants."""
        spec = ProblemSpec(
            problem_type="kmap_simplification",
            topic="Large Batch Test",
            description="Test large batch",
            num_variants=50,  # Simulate classroom size
            parameters={
                "num_variables": 4,
                "num_minterms": [6, 10],
                "num_dont_cares": [0, 3],
                "variables": ["A", "B", "C", "D"]
            },
            answer_format="boolean_expression"
        )

        gen = TemplateGenerator(seed=808)
        batch = gen.generate(spec)

        # Should generate all 50
        assert batch.num_generated == 50
        assert len(batch.variants) == 50

        # Spot check a few
        verifier = BooleanVerifier()
        for i in [0, 10, 25, 49]:
            result = verifier.verify(batch.variants[i])
            assert result.passed


def test_generate_from_template_function(tmp_path):
    """Test the convenience function for generating from spec file."""
    from autota.template_generator import generate_from_template
    import yaml

    # Create a temp spec file
    spec_data = {
        "problem_type": "kmap_simplification",
        "topic": "Test Topic",
        "description": "Test Description",
        "num_variants": 5,
        "parameters": {
            "num_variables": 4,
            "num_minterms": [6, 8],
            "num_dont_cares": [0, 2],
            "variables": ["A", "B", "C", "D"]
        },
        "answer_format": "boolean_expression"
    }

    spec_file = tmp_path / "test_spec.yaml"
    with open(spec_file, "w") as f:
        yaml.dump(spec_data, f)

    # Generate from file
    batch = generate_from_template(str(spec_file), seed=999)

    assert batch.num_generated == 5
    assert len(batch.variants) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
