"""Builds prompts for Claude API to generate problem variants."""

from pathlib import Path
from typing import Optional, Tuple
from autota.models import ProblemSpec


class PromptBuilder:
    """Constructs system and user prompts for problem variant generation."""

    def __init__(self, spec: ProblemSpec):
        """Initialize prompt builder with a problem spec.

        Args:
            spec: Problem specification
        """
        self.spec = spec

    def build_prompts(self) -> Tuple[str, str]:
        """Build system and user prompts for Claude API.

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt()
        return system_prompt, user_prompt

    def _build_system_prompt(self) -> str:
        """Build the system prompt."""
        return """You are a STEM problem generator for university courses. Your task is to generate unique, high-quality problem variants with verified solutions.

CRITICAL REQUIREMENTS:
1. Output ONLY valid JSON - no markdown, no explanations, just the JSON array
2. Each variant must be UNIQUE - different parameters from all others
3. Solutions must be CORRECT - they will be computationally verified
4. Follow the parameter constraints EXACTLY
5. Make problems realistic and educational

Your output will be parsed as JSON and verified by deterministic code. Any deviation from the schema will cause failure."""

    def _build_user_prompt(self) -> str:
        """Build the user prompt with spec details and examples."""
        # Load reference material if provided
        reference_text = ""
        if self.spec.reference_material:
            reference_text = self._load_reference_material(self.spec.reference_material)

        # Build the prompt
        prompt = f"""Generate {self.spec.num_variants} unique variants of the following problem:

PROBLEM TYPE: {self.spec.problem_type}
TOPIC: {self.spec.topic}
DESCRIPTION: {self.spec.description}
DIFFICULTY: {self.spec.difficulty}

PARAMETERS:
{self._format_parameters()}

ANSWER FORMAT: {self.spec.answer_format}
"""

        if reference_text:
            prompt += f"\nREFERENCE MATERIAL:\n{reference_text}\n"

        prompt += """
OUTPUT SCHEMA:
Your response must be a JSON array of variant objects. Each variant must have:
- problem_text (string): The student-facing problem statement
- parameters (object): Specific parameters for this variant (minterms, dont_cares, variables, etc.)
- solution (object): The correct solution with 'expression' and 'method' fields
- answer_format (string): The expected answer format
- metadata (object, optional): Additional info like difficulty, tags, etc.

EXAMPLE OUTPUT:
[
  {
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
    "answer_format": "boolean_expression",
    "metadata": {
      "has_edge_wrap": true
    }
  }
]

IMPORTANT:
- Each variant must have DIFFERENT minterms
- Do NOT reuse parameter sets
- Ensure solutions are minimal (simplified)
- For K-map problems, verify your solution covers all minterms
- Output ONLY the JSON array, nothing else

Generate {self.spec.num_variants} variants now:"""

        return prompt

    def _format_parameters(self) -> str:
        """Format parameters section of prompt."""
        lines = []
        for key, value in self.spec.parameters.items():
            if isinstance(value, list) and len(value) == 2 and all(
                isinstance(x, int) for x in value
            ):
                # Range format
                lines.append(f"  {key}: {value[0]} to {value[1]}")
            else:
                lines.append(f"  {key}: {value}")
        return "\n".join(lines)

    def _load_reference_material(self, path: str) -> str:
        """Load reference material from file.

        Args:
            path: Path to reference material file

        Returns:
            Content of the file, or a note if unavailable
        """
        file_path = Path(path)

        if not file_path.exists():
            return f"[Reference material not found: {path}]"

        # Handle different file types
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            # TODO: Implement PDF parsing
            return f"[PDF parsing not yet implemented: {path}]"
        elif suffix in [".txt", ".md"]:
            try:
                return file_path.read_text(encoding="utf-8")
            except Exception as e:
                return f"[Error reading {path}: {e}]"
        else:
            return f"[Unsupported file type: {suffix}]"
