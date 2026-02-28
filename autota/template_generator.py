"""
Template-based problem generator.

Generates problem variants without using LLMs by:
1. Randomly selecting parameters within constraints
2. Using Quine-McCluskey to find solutions algorithmically
3. Using templates for problem text

This enables unlimited problem generation at $0 cost.
"""

import random
from typing import List, Dict, Any, Optional
from uuid import uuid4
from autota.models import ProblemSpec, ProblemVariant, GenerationBatch
from autota.solver.quine_mccluskey import QuineMcCluskySolver


class TemplateGenerator:
    """Generate problem variants using templates and algorithmic solving.

    Unlike the LLM-based generator, this:
    - Costs $0 (no API calls)
    - Works offline
    - Generates instantly
    - Produces deterministic, verified solutions
    - Has less variety in problem text

    Best for: development, testing, practice problems, bulk generation
    """

    def __init__(self, seed: Optional[int] = None):
        """Initialize the template generator.

        Args:
            seed: Random seed for reproducibility (optional)
        """
        if seed is not None:
            random.seed(seed)

    def generate(self, spec: ProblemSpec) -> GenerationBatch:
        """Generate problem variants from a spec using templates.

        Args:
            spec: Problem specification

        Returns:
            GenerationBatch with generated variants

        Raises:
            ValueError: If problem type is not supported
        """
        # Route to appropriate generator based on problem type
        if spec.problem_type == "kmap_simplification":
            return self._generate_kmap_variants(spec)
        elif spec.problem_type == "boolean_expression":
            return self._generate_boolean_variants(spec)
        else:
            raise ValueError(
                f"Template generator does not support problem type '{spec.problem_type}'. "
                f"Supported types: kmap_simplification, boolean_expression"
            )

    def _generate_kmap_variants(self, spec: ProblemSpec) -> GenerationBatch:
        """Generate K-map simplification variants.

        Args:
            spec: Problem specification

        Returns:
            GenerationBatch with K-map variants
        """
        variants = []
        used_parameter_sets = set()  # Avoid duplicates

        # Extract constraints from spec
        num_variables = spec.parameters.get("num_variables", 4)
        num_minterms_range = spec.parameters.get("num_minterms", [6, 10])
        num_dont_cares_range = spec.parameters.get("num_dont_cares", [0, 3])
        variables = spec.parameters.get("variables", self._default_variables(num_variables))
        require_edge_wrap = spec.parameters.get("require_edge_wrap", False)

        attempts = 0
        max_attempts = spec.num_variants * 10  # Prevent infinite loops

        while len(variants) < spec.num_variants and attempts < max_attempts:
            attempts += 1

            # Generate random parameters
            num_minterms = random.randint(num_minterms_range[0], num_minterms_range[1])
            num_dont_cares = random.randint(num_dont_cares_range[0], num_dont_cares_range[1])

            # Select random minterms
            max_value = 2 ** num_variables - 1
            all_values = list(range(max_value + 1))

            # Sample minterms
            minterms = random.sample(all_values, min(num_minterms, len(all_values)))

            # Sample don't-cares from remaining values
            remaining = [v for v in all_values if v not in minterms]
            dont_cares = random.sample(remaining, min(num_dont_cares, len(remaining)))

            # Create parameter signature for uniqueness check
            param_sig = (tuple(sorted(minterms)), tuple(sorted(dont_cares)))
            if param_sig in used_parameter_sets:
                continue

            # Check edge wrap requirement if needed
            if require_edge_wrap:
                if not self._has_edge_wrap_potential(minterms, num_variables):
                    continue

            # Solve using Quine-McCluskey
            try:
                solver = QuineMcCluskySolver(
                    minterms=minterms,
                    variables=variables,
                    dont_cares=dont_cares if dont_cares else None
                )
                solution_expr = solver.solve()
                solution_details = solver.get_solution_details()
            except Exception as e:
                # Skip if solver fails (shouldn't happen, but be safe)
                continue

            # Generate problem text from template
            problem_text = self._kmap_problem_template(
                variables=variables,
                minterms=minterms,
                dont_cares=dont_cares,
                difficulty=spec.difficulty
            )

            # Create variant
            variant = ProblemVariant(
                variant_id=uuid4(),
                problem_text=problem_text,
                parameters={
                    "minterms": minterms,
                    "dont_cares": dont_cares,
                    "variables": variables,
                },
                solution={
                    "expression": solution_expr,
                    "method": "kmap",
                    "num_terms": solution_details["num_terms"],
                    "num_literals": solution_details["total_literals"],
                },
                answer_format=spec.answer_format,
                metadata={
                    "difficulty": spec.difficulty,
                    "num_variables": num_variables,
                    "has_dont_cares": len(dont_cares) > 0,
                    "generator": "template",
                },
            )

            variants.append(variant)
            used_parameter_sets.add(param_sig)

        return GenerationBatch(
            variants=variants,
            num_requested=spec.num_variants,
            num_generated=len(variants),
            model_used="template_generator",
        )

    def _generate_boolean_variants(self, spec: ProblemSpec) -> GenerationBatch:
        """Generate Boolean expression evaluation variants.

        Args:
            spec: Problem specification

        Returns:
            GenerationBatch with Boolean expression variants
        """
        # Similar to K-map but for direct expression evaluation
        # Could ask: "Evaluate expression X for inputs A=1, B=0"
        # For now, redirect to K-map generation
        return self._generate_kmap_variants(spec)

    def _kmap_problem_template(
        self,
        variables: List[str],
        minterms: List[int],
        dont_cares: List[int],
        difficulty: str
    ) -> str:
        """Generate problem text for K-map simplification.

        Args:
            variables: List of variable names
            minterms: List of minterm indices
            dont_cares: List of don't-care indices
            difficulty: Difficulty level

        Returns:
            Problem text string
        """
        var_str = ",".join(variables)

        # Sort minterms for consistent display
        sorted_minterms = sorted(minterms)

        # Format minterm list
        if len(sorted_minterms) <= 8:
            minterm_str = ",".join(map(str, sorted_minterms))
        else:
            # For long lists, show first few and last few
            first_few = ",".join(map(str, sorted_minterms[:4]))
            last_few = ",".join(map(str, sorted_minterms[-4:]))
            minterm_str = f"{first_few},...,{last_few}"

        # Base template
        if not dont_cares:
            template = (
                f"Simplify the Boolean function F({var_str}) defined by the following minterms:\n"
                f"m({minterm_str})\n\n"
                f"Express your answer as a minimal sum-of-products (SOP) expression."
            )
        else:
            sorted_dont_cares = sorted(dont_cares)
            dc_str = ",".join(map(str, sorted_dont_cares))

            template = (
                f"Simplify the Boolean function F({var_str}) defined by:\n"
                f"Minterms: m({minterm_str})\n"
                f"Don't-cares: d({dc_str})\n\n"
                f"Express your answer as a minimal sum-of-products (SOP) expression.\n"
                f"You may use the don't-care conditions to simplify the expression."
            )

        # Add difficulty-specific hints
        if difficulty == "easy":
            template += "\n\nHint: Look for adjacent groupings in the K-map."
        elif difficulty == "hard":
            template += "\n\nNote: Pay attention to wraparound groupings at the edges."

        return template

    def _has_edge_wrap_potential(self, minterms: List[int], num_variables: int) -> bool:
        """Check if minterms have potential for edge wraparound groupings.

        Edge wrap occurs when grouping wraps around the K-map edges.
        This happens when minterms differ only in the MSB or LSB.

        Args:
            minterms: List of minterm indices
            num_variables: Number of variables

        Returns:
            True if edge wrap is possible
        """
        if len(minterms) < 2:
            return False

        # Check for pairs that differ only in MSB (top/bottom wrap)
        # or in specific bit positions (left/right wrap)
        for i, m1 in enumerate(minterms):
            for m2 in minterms[i + 1:]:
                # XOR to find differing bits
                diff = m1 ^ m2

                # Check if difference is a power of 2 (single bit)
                if diff != 0 and (diff & (diff - 1)) == 0:
                    # Single bit difference - could be edge wrap
                    # Also check if they're at opposite edges
                    max_val = 2 ** num_variables - 1
                    if m1 == 0 or m2 == 0 or m1 == max_val or m2 == max_val:
                        return True

        return False

    def _default_variables(self, num_variables: int) -> List[str]:
        """Get default variable names for given number of variables.

        Args:
            num_variables: Number of variables

        Returns:
            List of variable names (A, B, C, ...)
        """
        return [chr(ord('A') + i) for i in range(num_variables)]


def generate_from_template(
    spec_path: str,
    num_variants: Optional[int] = None,
    seed: Optional[int] = None
) -> GenerationBatch:
    """Convenience function to generate variants from a spec file.

    Args:
        spec_path: Path to YAML spec file
        num_variants: Override number of variants (optional)
        seed: Random seed for reproducibility (optional)

    Returns:
        GenerationBatch with generated variants
    """
    import yaml
    from pathlib import Path

    # Load spec
    with open(spec_path) as f:
        spec_data = yaml.safe_load(f)

    spec = ProblemSpec(**spec_data)

    # Override num_variants if provided
    if num_variants is not None:
        spec.num_variants = num_variants

    # Generate
    generator = TemplateGenerator(seed=seed)
    return generator.generate(spec)
