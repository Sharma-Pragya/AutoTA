"""Command-line interface for AutoTA."""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from autota.orchestrator import Orchestrator

app = typer.Typer(
    name="autota",
    help="AutoTA - LLM-powered parameterized assessment generator for STEM courses",
)
console = Console()


@app.command()
def generate_template(
    spec: str = typer.Option(
        ..., "--spec", "-s", help="Path to problem spec YAML file"
    ),
    num: Optional[int] = typer.Option(
        None, "--num", "-n", help="Number of variants to generate (overrides spec)"
    ),
    output: str = typer.Option(
        "output", "--output", "-o", help="Output directory for generated variants"
    ),
    seed: Optional[int] = typer.Option(
        None, "--seed", help="Random seed for reproducibility"
    ),
):
    """Generate problem variants using templates (NO API KEY NEEDED).

    This command generates problems using algorithmic methods instead of LLMs:
    - Random parameter selection within spec constraints
    - Quine-McCluskey algorithm for finding solutions
    - Template-based problem text

    Benefits:
    - $0 cost (no API calls)
    - Unlimited generation
    - Instant results
    - Deterministic with seed

    Example:
        autota generate-template --spec specs/example_kmap.yaml --num 70
        autota generate-template --spec specs/example_kmap.yaml --num 10 --seed 42
    """
    from autota.template_generator import TemplateGenerator
    from autota.verify.boolean import BooleanVerifier
    from autota.models import ProblemSpec
    import yaml
    import json
    from pathlib import Path

    console.print(f"\n[bold cyan]AutoTA Template Generator[/bold cyan]")
    console.print(f"Spec: {spec}")
    console.print(f"Output: {output}")
    if seed is not None:
        console.print(f"Seed: {seed}")
    console.print()

    try:
        # Load spec
        with open(spec) as f:
            spec_data = yaml.safe_load(f)

        problem_spec = ProblemSpec(**spec_data)

        # Override num_variants if provided
        if num is not None:
            problem_spec.num_variants = num

        console.print(f"Generating {problem_spec.num_variants} variants...")

        # Generate
        generator = TemplateGenerator(seed=seed)
        batch = generator.generate(problem_spec)

        console.print(f"✓ Generated {batch.num_generated} variants")

        # Verify all
        console.print(f"Verifying variants...")
        verifier = BooleanVerifier()

        verified = []
        failed = []

        for variant in batch.variants:
            result = verifier.verify(variant)
            if result.passed:
                verified.append((variant, result))
            else:
                failed.append((variant, result))

        console.print(f"✓ Verified: {len(verified)}, Failed: {len(failed)}")

        # Write to output
        spec_name = Path(spec).stem
        spec_output_dir = Path(output) / spec_name
        spec_output_dir.mkdir(parents=True, exist_ok=True)

        console.print(f"Writing {len(verified)} variants to {spec_output_dir}...")

        for variant, _ in verified:
            variant_file = spec_output_dir / f"{variant.variant_id}.json"
            with open(variant_file, "w") as f:
                json.dump(variant.model_dump(), f, indent=2, default=str)

        # Write report
        report = {
            "spec_file": spec,
            "problem_type": problem_spec.problem_type,
            "topic": problem_spec.topic,
            "total_requested": problem_spec.num_variants,
            "total_generated": batch.num_generated,
            "verified_count": len(verified),
            "failed_count": len(failed),
            "success_rate": len(verified) / batch.num_generated if batch.num_generated > 0 else 0,
            "generator": "template",
            "seed": seed,
        }

        report_path = spec_output_dir / "report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        console.print(f"✓ Report written to {report_path}")
        console.print()

        # Display summary
        table = Table(title="Generation Summary", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="dim")
        table.add_column("Value", justify="right")

        table.add_row("Requested", str(problem_spec.num_variants))
        table.add_row("Generated", str(batch.num_generated))
        table.add_row("Verified", str(len(verified)), style="green")
        table.add_row("Failed", str(len(failed)), style="red" if len(failed) > 0 else "dim")
        table.add_row("Success Rate", f"{report['success_rate']:.1%}")
        table.add_row("Generator", "Template (no API)")

        console.print(table)
        console.print()

        if len(verified) == batch.num_generated:
            console.print(f"[bold green]✓ Success! All {len(verified)} variants generated and verified.[/bold green]")
        else:
            console.print(f"[yellow]⚠ Warning: {len(failed)} variants failed verification[/yellow]")

        console.print()

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def generate(
    spec: str = typer.Option(
        ..., "--spec", "-s", help="Path to problem spec YAML file"
    ),
    num: Optional[int] = typer.Option(
        None, "--num", "-n", help="Number of variants to generate (overrides spec)"
    ),
    output: str = typer.Option(
        "output", "--output", "-o", help="Output directory for generated variants"
    ),
    api_key: Optional[str] = typer.Option(
        None, "--api-key", help="Anthropic API key (overrides .env)"
    ),
    max_retries: int = typer.Option(
        2, "--max-retries", help="Maximum retry attempts for failed variants"
    ),
):
    """Generate problem variants from a spec file.

    This command:
    1. Loads the problem spec from YAML
    2. Calls Claude API to generate variants
    3. Verifies each variant using deterministic code
    4. Retries failed variants (optional)
    5. Writes verified variants and a report to the output directory
    """
    console.print(f"\n[bold cyan]AutoTA Problem Generator[/bold cyan]")
    console.print(f"Spec: {spec}")
    console.print(f"Output: {output}\n")

    try:
        orchestrator = Orchestrator(
            api_key=api_key, max_retries=max_retries, output_dir=output
        )
        report = orchestrator.run(spec, num_variants=num)

        # Display summary
        _display_report(report)

        if report["failed_count"] > 0:
            console.print(
                f"\n[yellow]Warning: {report['failed_count']} variants failed verification[/yellow]"
            )
            console.print(
                "See the report.json file for details on failed variants."
            )
        else:
            console.print(
                f"\n[bold green]Success! All {report['verified_count']} variants verified.[/bold green]"
            )

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def verify(
    input: str = typer.Option(
        ..., "--input", "-i", help="Directory containing variant JSON files"
    ),
    problem_type: str = typer.Option(
        ..., "--type", "-t", help="Problem type for verification"
    ),
):
    """Re-verify already generated variants.

    This is useful for:
    - Testing verifiers independently
    - Re-checking variants after verifier updates
    - Debugging verification failures
    """
    console.print(f"\n[bold cyan]AutoTA Verifier[/bold cyan]")
    console.print(f"Input: {input}")
    console.print(f"Problem type: {problem_type}\n")

    try:
        orchestrator = Orchestrator()
        report = orchestrator.verify_existing(input, problem_type)

        _display_verification_report(report)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def list_types():
    """List all registered problem types and their verifiers."""
    from autota.verify.registry import list_registered_types

    console.print("\n[bold cyan]Registered Problem Types[/bold cyan]\n")

    types = list_registered_types()
    if not types:
        console.print("[yellow]No problem types registered yet.[/yellow]")
        console.print("Register verifiers using the @register_verifier decorator.")
    else:
        for problem_type in sorted(types):
            console.print(f"  • {problem_type}")

    console.print()


@app.command()
def solve(
    minterms: str = typer.Option(
        ..., "--minterms", "-m", help="Comma-separated list of minterms (e.g., '0,2,5,7')"
    ),
    variables: str = typer.Option(
        ..., "--vars", "-v", help="Comma-separated list of variables (e.g., 'A,B,C,D')"
    ),
    dont_cares: Optional[str] = typer.Option(
        None, "--dont-cares", "-d", help="Comma-separated list of don't-cares (optional)"
    ),
    show_details: bool = typer.Option(
        False, "--details", help="Show detailed solution steps"
    ),
):
    """Find the minimal sum-of-products expression using Quine-McCluskey algorithm.

    This command uses the Quine-McCluskey algorithm to find the minimal
    Boolean expression for given minterms.

    Example:
        autota solve -m "0,2,5,7" -v "A,B,C,D"
        autota solve -m "0,2,8,10" -d "1,3,9,11" -v "A,B,C,D" --details
    """
    from autota.solver.quine_mccluskey import QuineMcCluskySolver

    console.print(f"\n[bold cyan]AutoTA Quine-McCluskey Solver[/bold cyan]\n")

    try:
        # Parse inputs
        minterm_list = [int(x.strip()) for x in minterms.split(",")]
        var_list = [x.strip() for x in variables.split(",")]
        dont_care_list = []
        if dont_cares:
            dont_care_list = [int(x.strip()) for x in dont_cares.split(",")]

        # Create solver
        solver = QuineMcCluskySolver(
            minterms=minterm_list,
            variables=var_list,
            dont_cares=dont_care_list
        )

        # Solve
        minimal_expr = solver.solve()

        # Display basic result
        console.print(f"[bold green]Minimal Expression:[/bold green] {minimal_expr}\n")

        # Show details if requested
        if show_details:
            details = solver.get_solution_details()

            # Prime implicants table
            table = Table(title="Prime Implicants", show_header=True, header_style="bold cyan")
            table.add_column("Binary", style="dim")
            table.add_column("Expression")
            table.add_column("Covers Minterms")
            table.add_column("Literals", justify="right")

            for pi in details["prime_implicants"]:
                table.add_row(
                    pi["binary"],
                    pi["expression"],
                    str(pi["minterms"]),
                    str(pi["num_literals"])
                )

            console.print(table)
            console.print()

            # Essential primes
            if details["essential_primes"]:
                console.print("[bold]Essential Prime Implicants:[/bold]")
                for epi in details["essential_primes"]:
                    console.print(f"  • {epi['expression']} (covers {epi['minterms']})")
                console.print()

            # Statistics
            console.print(f"[bold]Solution Statistics:[/bold]")
            console.print(f"  Number of terms: {details['num_terms']}")
            console.print(f"  Total literals: {details['total_literals']}")
            console.print()

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def grade(
    problem_type: str = typer.Option(
        ..., "--type", "-t", help="Problem type (e.g., kmap_simplification)"
    ),
    minterms: str = typer.Option(
        ..., "--minterms", "-m", help="Comma-separated list of minterms (e.g., '0,2,5,7')"
    ),
    variables: str = typer.Option(
        ..., "--vars", "-v", help="Comma-separated list of variables (e.g., 'A,B,C,D')"
    ),
    answer: str = typer.Option(
        ..., "--answer", "-a", help="Student's Boolean expression answer"
    ),
    dont_cares: Optional[str] = typer.Option(
        None, "--dont-cares", "-d", help="Comma-separated list of don't-cares (optional)"
    ),
):
    """Grade a student's answer for a Boolean expression problem.

    This command allows you to grade student submissions without needing
    pre-generated problem variants.

    Example:
        autota grade -t kmap_simplification -m "1,3" -v "A,B" -a "B"
    """
    from autota.verify.registry import get_verifier
    from autota.models import ProblemVariant
    from uuid import uuid4

    console.print(f"\n[bold cyan]AutoTA Grader[/bold cyan]")
    console.print(f"Problem Type: {problem_type}\n")

    try:
        # Parse inputs
        minterm_list = [int(x.strip()) for x in minterms.split(",")]
        var_list = [x.strip() for x in variables.split(",")]
        dont_care_list = []
        if dont_cares:
            dont_care_list = [int(x.strip()) for x in dont_cares.split(",")]

        # Create a temporary variant
        variant = ProblemVariant(
            variant_id=uuid4(),
            problem_text=f"Problem with minterms {minterm_list}",
            parameters={
                "minterms": minterm_list,
                "dont_cares": dont_care_list,
                "variables": var_list,
            },
            solution={"expression": ""},  # Not needed for grading
            answer_format="boolean_expression",
        )

        # Get verifier and grade
        verifier = get_verifier(problem_type)
        result = verifier.grade(variant, answer)

        # Display result
        table = Table(title="Grading Result", show_header=True, header_style="bold cyan")
        table.add_column("Field", style="dim")
        table.add_column("Value")

        table.add_row("Student Answer", answer)
        table.add_row(
            "Result",
            "✅ CORRECT" if result.correct else "❌ INCORRECT",
            style="green" if result.correct else "red",
        )
        table.add_row("Score", f"{result.partial_credit:.1%}")

        console.print(table)
        console.print(f"\n[bold]Feedback:[/bold]\n{result.feedback}\n")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


def _display_report(report: dict):
    """Display generation report in a formatted table."""
    table = Table(title="Generation Report", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")

    table.add_row("Problem Type", report["problem_type"])
    table.add_row("Topic", report["topic"])
    table.add_row("Requested", str(report["total_requested"]))
    table.add_row("Generated", str(report["total_generated"]))
    table.add_row("Verified", str(report["verified_count"]), style="green")
    table.add_row("Failed", str(report["failed_count"]), style="red" if report["failed_count"] > 0 else "dim")
    table.add_row("Success Rate", f"{report['success_rate']:.1%}")

    console.print(table)


def _display_verification_report(report: dict):
    """Display verification report in a formatted table."""
    table = Table(title="Verification Report", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")

    table.add_row("Input Directory", report["input_dir"])
    table.add_row("Problem Type", report["problem_type"])
    table.add_row("Total Variants", str(report["total_variants"]))
    table.add_row("Verified", str(report["verified_count"]), style="green")
    table.add_row("Failed", str(report["failed_count"]), style="red" if report["failed_count"] > 0 else "dim")
    table.add_row("Success Rate", f"{report['success_rate']:.1%}")

    console.print(table)


if __name__ == "__main__":
    app()
