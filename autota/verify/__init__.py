"""Verification modules for different problem types."""

from autota.verify.base import Verifier
from autota.verify.registry import get_verifier, register_verifier

# Import verifiers to trigger registration
from autota.verify import boolean  # noqa: F401

__all__ = ["Verifier", "get_verifier", "register_verifier"]
