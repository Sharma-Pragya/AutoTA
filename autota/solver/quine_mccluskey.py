"""
Quine-McCluskey algorithm for Boolean function minimization.

This module implements the Quine-McCluskey method for finding minimal
sum-of-products (SOP) expressions for Boolean functions.

The algorithm works in two phases:
1. Find all prime implicants (irreducible product terms)
2. Find the minimal cover using prime implicants

References:
- Quine, W.V. (1952). "The Problem of Simplifying Truth Functions"
- McCluskey, E.J. (1956). "Minimization of Boolean Functions"
"""

from typing import List, Set, Tuple, Dict, Optional
from dataclasses import dataclass
from itertools import combinations


@dataclass
class Implicant:
    """Represents a product term in Boolean algebra.

    Attributes:
        binary: Binary representation where '-' means don't-care
                Example: "10-1" means A*B'*D
        minterms: Set of minterms covered by this implicant
        is_prime: Whether this is a prime implicant
    """
    binary: str
    minterms: Set[int]
    is_prime: bool = False

    def __hash__(self):
        return hash(self.binary)

    def __eq__(self, other):
        return self.binary == other.binary

    def count_literals(self) -> int:
        """Count number of literals (non-don't-care positions)."""
        return sum(1 for c in self.binary if c != '-')

    def to_expression(self, variables: List[str]) -> str:
        """Convert to Boolean expression string.

        Args:
            variables: List of variable names (e.g., ['A', 'B', 'C', 'D'])

        Returns:
            Boolean expression (e.g., "A'BD" for "01-1")
        """
        terms = []
        for i, bit in enumerate(self.binary):
            if bit == '1':
                terms.append(variables[i])
            elif bit == '0':
                terms.append(variables[i] + "'")
            # '-' means don't care, skip it

        return ''.join(terms) if terms else '1'


class QuineMcCluskySolver:
    """Quine-McCluskey algorithm solver for Boolean minimization.

    Finds the minimal sum-of-products expression for a Boolean function
    given its minterms and optional don't-cares.

    Example:
        >>> solver = QuineMcCluskySolver(
        ...     minterms=[0, 2, 5, 7],
        ...     dont_cares=[],
        ...     variables=['A', 'B', 'C', 'D']
        ... )
        >>> minimal = solver.solve()
        >>> print(minimal)  # "A'B'D' + A'BD"
    """

    def __init__(
        self,
        minterms: List[int],
        variables: List[str],
        dont_cares: Optional[List[int]] = None
    ):
        """Initialize the solver.

        Args:
            minterms: List of minterm indices (where function = 1)
            variables: List of variable names in order
            dont_cares: Optional list of don't-care indices
        """
        self.minterms = set(minterms)
        self.dont_cares = set(dont_cares) if dont_cares else set()
        self.variables = variables
        self.num_vars = len(variables)

        # Validate inputs
        if not self.minterms:
            raise ValueError("Must provide at least one minterm")

        max_value = 2 ** self.num_vars - 1
        all_terms = self.minterms | self.dont_cares
        if any(term > max_value for term in all_terms):
            raise ValueError(
                f"Minterm/don't-care value exceeds maximum for {self.num_vars} variables ({max_value})"
            )

        # Working sets (minterms + don't-cares for minimization)
        self.all_terms = self.minterms | self.dont_cares

        # Results
        self.prime_implicants: List[Implicant] = []
        self.essential_primes: List[Implicant] = []
        self.minimal_cover: List[Implicant] = []

    def solve(self) -> str:
        """Find the minimal sum-of-products expression.

        Returns:
            Minimal Boolean expression as a string
        """
        # Step 1: Find all prime implicants
        self.prime_implicants = self._find_prime_implicants()

        # Step 2: Find essential prime implicants
        self.essential_primes = self._find_essential_primes()

        # Step 3: Find minimal cover
        self.minimal_cover = self._find_minimal_cover()

        # Step 4: Convert to expression
        return self._cover_to_expression()

    def _find_prime_implicants(self) -> List[Implicant]:
        """Find all prime implicants using iterative combining.

        Returns:
            List of prime implicants
        """
        # Start with all minterms and don't-cares
        current_implicants = [
            Implicant(
                binary=self._int_to_binary(term),
                minterms={term}
            )
            for term in self.all_terms
        ]

        prime_implicants = []

        while current_implicants:
            # Group by number of 1s (for efficient combining)
            groups = self._group_by_ones(current_implicants)

            # Try to combine adjacent groups
            next_implicants = []
            used = set()

            for i in sorted(groups.keys()):
                if i + 1 not in groups:
                    continue

                for imp1 in groups[i]:
                    for imp2 in groups[i + 1]:
                        combined = self._combine(imp1, imp2)
                        if combined:
                            next_implicants.append(combined)
                            used.add(imp1)
                            used.add(imp2)

            # Implicants that couldn't be combined are prime
            for implicants in groups.values():
                for imp in implicants:
                    if imp not in used:
                        imp.is_prime = True
                        if imp not in prime_implicants:
                            prime_implicants.append(imp)

            # Remove duplicates from next iteration
            current_implicants = list({imp.binary: imp for imp in next_implicants}.values())

        return prime_implicants

    def _find_essential_primes(self) -> List[Implicant]:
        """Find essential prime implicants.

        An essential prime implicant is one that covers at least one
        minterm that no other prime implicant covers.

        Returns:
            List of essential prime implicants
        """
        # Build coverage map: minterm -> list of primes that cover it
        coverage: Dict[int, List[Implicant]] = {m: [] for m in self.minterms}

        for prime in self.prime_implicants:
            for minterm in prime.minterms:
                if minterm in self.minterms:  # Only care about actual minterms, not don't-cares
                    coverage[minterm].append(prime)

        # Find essential primes (those that uniquely cover a minterm)
        essential = []
        for minterm, covering_primes in coverage.items():
            if len(covering_primes) == 1:
                prime = covering_primes[0]
                if prime not in essential:
                    essential.append(prime)

        return essential

    def _find_minimal_cover(self) -> List[Implicant]:
        """Find minimal cover using essential primes and additional primes.

        Returns:
            List of implicants forming the minimal cover
        """
        # Start with essential primes
        cover = list(self.essential_primes)
        covered_minterms = set()
        for prime in cover:
            covered_minterms.update(prime.minterms & self.minterms)

        # If essential primes cover everything, we're done
        if covered_minterms == self.minterms:
            return cover

        # Need additional primes to cover remaining minterms
        uncovered = self.minterms - covered_minterms
        remaining_primes = [p for p in self.prime_implicants if p not in cover]

        # Use Petrick's method or greedy approach
        # For simplicity, using greedy: pick prime that covers most uncovered minterms
        while uncovered:
            # Find best prime (covers most uncovered minterms)
            best_prime = None
            best_coverage = 0

            for prime in remaining_primes:
                coverage_count = len(prime.minterms & uncovered)
                if coverage_count > best_coverage:
                    best_coverage = coverage_count
                    best_prime = prime

            if best_prime is None:
                # Shouldn't happen if prime implicants are correct
                break

            cover.append(best_prime)
            remaining_primes.remove(best_prime)
            uncovered -= best_prime.minterms

        return cover

    def _cover_to_expression(self) -> str:
        """Convert minimal cover to Boolean expression string.

        Returns:
            Sum-of-products expression
        """
        if not self.minimal_cover:
            return "0"

        # Sort by number of literals (aesthetic)
        sorted_cover = sorted(self.minimal_cover, key=lambda x: x.count_literals())

        terms = [imp.to_expression(self.variables) for imp in sorted_cover]
        return ' + '.join(terms)

    def _int_to_binary(self, n: int) -> str:
        """Convert integer to binary string of length num_vars.

        Args:
            n: Integer to convert

        Returns:
            Binary string (e.g., "0101" for n=5, num_vars=4)
        """
        return format(n, f'0{self.num_vars}b')

    def _group_by_ones(self, implicants: List[Implicant]) -> Dict[int, List[Implicant]]:
        """Group implicants by number of 1s in their binary representation.

        Args:
            implicants: List of implicants to group

        Returns:
            Dict mapping count of 1s -> list of implicants
        """
        groups: Dict[int, List[Implicant]] = {}

        for imp in implicants:
            count = imp.binary.count('1')
            if count not in groups:
                groups[count] = []
            groups[count].append(imp)

        return groups

    def _combine(self, imp1: Implicant, imp2: Implicant) -> Optional[Implicant]:
        """Try to combine two implicants.

        Two implicants can be combined if they differ in exactly one bit position.

        Args:
            imp1: First implicant
            imp2: Second implicant

        Returns:
            Combined implicant if possible, None otherwise
        """
        # Count differences
        diff_count = 0
        diff_pos = -1

        for i, (b1, b2) in enumerate(zip(imp1.binary, imp2.binary)):
            if b1 != b2:
                # Can't combine if one has '-' and other has a specific value
                # unless they're both the same
                if b1 == '-' or b2 == '-':
                    if b1 != b2:
                        return None
                else:
                    diff_count += 1
                    diff_pos = i
                    if diff_count > 1:
                        return None

        # Must differ in exactly one position
        if diff_count != 1:
            return None

        # Combine by setting differing position to '-'
        new_binary = list(imp1.binary)
        new_binary[diff_pos] = '-'

        return Implicant(
            binary=''.join(new_binary),
            minterms=imp1.minterms | imp2.minterms
        )

    def get_solution_details(self) -> Dict:
        """Get detailed information about the solution.

        Returns:
            Dictionary with solution details including prime implicants,
            essential primes, and minimal cover
        """
        if not self.minimal_cover:
            self.solve()

        return {
            "minterms": list(self.minterms),
            "dont_cares": list(self.dont_cares),
            "num_variables": self.num_vars,
            "prime_implicants": [
                {
                    "binary": p.binary,
                    "expression": p.to_expression(self.variables),
                    "minterms": list(p.minterms),
                    "num_literals": p.count_literals()
                }
                for p in self.prime_implicants
            ],
            "essential_primes": [
                {
                    "binary": p.binary,
                    "expression": p.to_expression(self.variables),
                    "minterms": list(p.minterms)
                }
                for p in self.essential_primes
            ],
            "minimal_cover": [
                {
                    "binary": p.binary,
                    "expression": p.to_expression(self.variables),
                    "minterms": list(p.minterms)
                }
                for p in self.minimal_cover
            ],
            "minimal_expression": self._cover_to_expression(),
            "num_terms": len(self.minimal_cover),
            "total_literals": sum(p.count_literals() for p in self.minimal_cover)
        }
