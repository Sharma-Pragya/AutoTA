"""Registry for mapping problem types to verifier classes."""

from typing import Dict, Type
from autota.verify.base import Verifier


# Global registry mapping problem_type strings to verifier classes
_VERIFIER_REGISTRY: Dict[str, Type[Verifier]] = {}


def register_verifier(verifier_class: Type[Verifier]) -> Type[Verifier]:
    """Register a verifier class in the global registry.

    Can be used as a decorator:
        @register_verifier
        class MyVerifier(Verifier):
            ...

    Args:
        verifier_class: The verifier class to register

    Returns:
        The same verifier class (for decorator usage)

    Raises:
        ValueError: If a verifier for this problem type is already registered
    """
    instance = verifier_class()
    problem_type = instance.problem_type

    if problem_type in _VERIFIER_REGISTRY:
        raise ValueError(
            f"Verifier for problem type '{problem_type}' is already registered: "
            f"{_VERIFIER_REGISTRY[problem_type].__name__}"
        )

    _VERIFIER_REGISTRY[problem_type] = verifier_class
    return verifier_class


def get_verifier(problem_type: str) -> Verifier:
    """Get a verifier instance for the given problem type.

    Args:
        problem_type: The problem type string (e.g., 'kmap_simplification')

    Returns:
        An instance of the appropriate verifier class

    Raises:
        KeyError: If no verifier is registered for this problem type
    """
    if problem_type not in _VERIFIER_REGISTRY:
        raise KeyError(
            f"No verifier registered for problem type '{problem_type}'. "
            f"Available types: {list(_VERIFIER_REGISTRY.keys())}"
        )

    return _VERIFIER_REGISTRY[problem_type]()


def list_registered_types() -> list[str]:
    """List all registered problem types.

    Returns:
        List of problem type strings
    """
    return list(_VERIFIER_REGISTRY.keys())
