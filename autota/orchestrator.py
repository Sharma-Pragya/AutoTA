"""Orchestrates the generation, verification, and output pipeline."""

import json
from pathlib import Path
from typing import Dict, List, Optional
import yaml
from autota.models import ProblemSpec, ProblemVariant, VerificationResult
from autota.generator import VariantGenerator
from autota.verify.registry import get_verifier


class Orchestrator:
    """Coordinates problem generation, verification, and output."""

    def __init__(
        self, api_key: Optional[str] = None, max_retries: int = 2, output_dir: str = "output"
    ):
        """Initialize the orchestrator.

        Args:
            api_key: Anthropic API key (optional, loads from env if not provided)
            max_retries: Maximum number of retry attempts for failed variants
            output_dir: Base directory for output files
        """
        # Generator is optional - only needed for LLM-based generation
        self.generator = None
        try:
            self.generator = VariantGenerator(api_key=api_key)
        except ValueError:
            # API key not available - can still verify existing variants
            pass
        self.max_retries = max_retries
        self.output_dir = Path(output_dir)

    def run(self, spec_path: str, num_variants: Optional[int] = None) -> Dict:
        """Run the full pipeline: load spec, generate, verify, output.

        Args:
            spec_path: Path to YAML spec file
            num_variants: Override number of variants to generate

        Returns:
            Summary report dictionary with statistics
        """
        if self.generator is None:
            raise ValueError(
                "Cannot generate variants: API key not configured. "
                "Use 'autota generate-template' for generation without API key."
            )

        # Load spec
        spec = self._load_spec(spec_path)

        # Determine output directory for this spec
        spec_name = Path(spec_path).stem
        spec_output_dir = self.output_dir / spec_name
        spec_output_dir.mkdir(parents=True, exist_ok=True)

        # Generate variants
        print(f"Generating {num_variants or spec.num_variants} variants...")
        batch = self.generator.generate(spec, num_variants)
        print(f"Generated {batch.num_generated} variants from API")

        # Get verifier
        verifier = get_verifier(spec.problem_type)

        # Verify variants
        print(f"Verifying variants...")
        verified = []
        failed = []

        for variant in batch.variants:
            result = verifier.verify(variant)
            if result.passed:
                verified.append((variant, result))
            else:
                failed.append((variant, result))

        print(f"Verified: {len(verified)}, Failed: {len(failed)}")

        # Retry failed variants if enabled
        if failed and self.max_retries > 0:
            print(f"Retrying {len(failed)} failed variants...")
            verified_retries, still_failed = self._retry_failed(
                spec, failed, verifier, self.max_retries
            )
            verified.extend(verified_retries)
            failed = still_failed

        # Write verified variants to disk
        print(f"Writing {len(verified)} verified variants to {spec_output_dir}")
        for variant, result in verified:
            self._write_variant(variant, spec_output_dir)

        # Write summary report
        report = {
            "spec_file": spec_path,
            "problem_type": spec.problem_type,
            "topic": spec.topic,
            "total_requested": num_variants or spec.num_variants,
            "total_generated": batch.num_generated,
            "verified_count": len(verified),
            "failed_count": len(failed),
            "success_rate": len(verified) / batch.num_generated if batch.num_generated > 0 else 0,
            "model_used": batch.model_used,
            "failed_variants": [
                {
                    "variant_id": str(result.variant_id),
                    "error": result.error_message,
                    "details": result.details,
                }
                for _, result in failed
            ],
        }

        report_path = spec_output_dir / "report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"Report written to {report_path}")
        return report

    def verify_existing(self, input_dir: str, problem_type: str) -> Dict:
        """Re-verify already generated variants.

        Args:
            input_dir: Directory containing variant JSON files
            problem_type: Problem type to use for verification

        Returns:
            Summary report dictionary
        """
        input_path = Path(input_dir)
        verifier = get_verifier(problem_type)

        verified = []
        failed = []

        # Load all JSON files
        for json_file in input_path.glob("*.json"):
            if json_file.name == "report.json":
                continue

            with open(json_file) as f:
                variant_dict = json.load(f)

            variant = ProblemVariant(**variant_dict)
            result = verifier.verify(variant)

            if result.passed:
                verified.append((variant, result))
            else:
                failed.append((variant, result))

        print(f"Re-verification complete: {len(verified)} passed, {len(failed)} failed")

        return {
            "input_dir": input_dir,
            "problem_type": problem_type,
            "total_variants": len(verified) + len(failed),
            "verified_count": len(verified),
            "failed_count": len(failed),
            "success_rate": len(verified) / (len(verified) + len(failed))
            if (len(verified) + len(failed)) > 0
            else 0,
        }

    def _load_spec(self, spec_path: str) -> ProblemSpec:
        """Load problem spec from YAML file.

        Args:
            spec_path: Path to YAML file

        Returns:
            ProblemSpec object
        """
        with open(spec_path) as f:
            data = yaml.safe_load(f)

        return ProblemSpec(**data)

    def _write_variant(self, variant: ProblemVariant, output_dir: Path):
        """Write a variant to a JSON file.

        Args:
            variant: ProblemVariant to write
            output_dir: Directory to write to
        """
        file_path = output_dir / f"{variant.variant_id}.json"
        with open(file_path, "w") as f:
            json.dump(variant.model_dump(), f, indent=2, default=str)

    def _retry_failed(
        self,
        spec: ProblemSpec,
        failed: List[tuple],
        verifier,
        max_retries: int,
    ) -> tuple:
        """Retry generating variants for failed cases.

        Args:
            spec: Problem spec
            failed: List of (variant, result) tuples that failed
            verifier: Verifier instance
            max_retries: Maximum retry attempts

        Returns:
            Tuple of (verified_list, still_failed_list)
        """
        # TODO: Implement retry logic with error feedback to Claude
        # For now, just return empty verified and original failed
        print(f"Retry logic not yet implemented - skipping retries")
        return [], failed
