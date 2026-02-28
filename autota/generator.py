"""Claude API integration for generating problem variants."""

import json
import os
from typing import List, Optional
from dotenv import load_dotenv
from anthropic import Anthropic
from autota.models import ProblemSpec, ProblemVariant, GenerationBatch
from autota.prompt_builder import PromptBuilder


class VariantGenerator:
    """Generates problem variants using Claude API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the generator.

        Args:
            api_key: Anthropic API key. If None, loads from environment.
        """
        load_dotenv()
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Set it in .env or pass to constructor."
            )
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-5-20250929"  # Latest Sonnet

    def generate(
        self, spec: ProblemSpec, num_variants: Optional[int] = None
    ) -> GenerationBatch:
        """Generate problem variants based on spec.

        Args:
            spec: Problem specification
            num_variants: Number of variants to generate (overrides spec.num_variants)

        Returns:
            GenerationBatch with generated variants

        Raises:
            ValueError: If generation fails or response is invalid
        """
        num_to_generate = num_variants or spec.num_variants

        # For large batches, split into multiple API calls
        batch_size = 10
        if num_to_generate <= batch_size:
            return self._generate_batch(spec, num_to_generate)
        else:
            # Multiple batches
            all_variants = []
            remaining = num_to_generate

            while remaining > 0:
                current_batch_size = min(batch_size, remaining)
                batch = self._generate_batch(spec, current_batch_size)
                all_variants.extend(batch.variants)
                remaining -= current_batch_size

            return GenerationBatch(
                variants=all_variants,
                num_requested=num_to_generate,
                num_generated=len(all_variants),
                model_used=self.model,
            )

    def _generate_batch(self, spec: ProblemSpec, num_variants: int) -> GenerationBatch:
        """Generate a single batch of variants via API call.

        Args:
            spec: Problem specification
            num_variants: Number of variants for this batch

        Returns:
            GenerationBatch with generated variants
        """
        from datetime import datetime

        # Build prompts
        prompt_builder = PromptBuilder(spec)
        system_prompt, user_prompt = prompt_builder.build_prompts()

        # Adjust user prompt for batch size
        user_prompt = user_prompt.replace(
            f"Generate {spec.num_variants} variants", f"Generate {num_variants} variants"
        )

        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                temperature=1.0,  # Higher temperature for more diversity
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Extract response text
            response_text = response.content[0].text

            # Parse JSON
            variants_data = self._parse_response(response_text)

            # Convert to ProblemVariant objects
            variants = []
            for variant_dict in variants_data:
                variant = ProblemVariant(
                    problem_text=variant_dict["problem_text"],
                    parameters=variant_dict["parameters"],
                    solution=variant_dict["solution"],
                    answer_format=variant_dict["answer_format"],
                    metadata=variant_dict.get("metadata"),
                )
                variants.append(variant)

            return GenerationBatch(
                variants=variants,
                num_requested=num_variants,
                num_generated=len(variants),
                api_call_timestamp=datetime.utcnow().isoformat(),
                model_used=self.model,
            )

        except Exception as e:
            raise ValueError(f"Failed to generate variants: {e}")

    def _parse_response(self, response_text: str) -> List[dict]:
        """Parse Claude's response into variant dictionaries.

        Args:
            response_text: Raw response from Claude

        Returns:
            List of variant dictionaries

        Raises:
            ValueError: If response is not valid JSON
        """
        # Try to extract JSON from response
        # Claude sometimes wraps in markdown code blocks
        text = response_text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Response is not valid JSON: {e}\nResponse: {text[:500]}")

        if not isinstance(data, list):
            raise ValueError(f"Response must be a JSON array, got {type(data)}")

        return data


# Add missing import at the top
from typing import Optional
