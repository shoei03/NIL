#!/usr/bin/env python3
"""
Similarity Calculator

Implements N-gram and LCS similarity calculation using the same algorithms as NIL.
"""

from typing import List, Set


class SimilarityCalculator:
    """Calculate similarity between token sequences using NIL's algorithms."""

    def __init__(self, gram_size: int = 5):
        """
        Initialize the calculator.

        Args:
            gram_size: Size of N-grams (default: 5, same as NIL)
        """
        self.gram_size = gram_size

    def calc_ngram_similarity(self, tokens_a: List[int], tokens_b: List[int]) -> int:
        """
        Calculate N-gram similarity between two token sequences.

        This implements the same algorithm as NIL's NGramBasedFiltration:
        similarity = intersection * 100 / min(size_a, size_b)

        Args:
            tokens_a: First token sequence
            tokens_b: Second token sequence

        Returns:
            Similarity percentage (0-100)
        """
        if not tokens_a or not tokens_b:
            return 0

        ngrams_a = self._create_ngrams(tokens_a)
        ngrams_b = self._create_ngrams(tokens_b)

        if not ngrams_a or not ngrams_b:
            return 0

        intersection = len(ngrams_a & ngrams_b)
        min_size = min(len(ngrams_a), len(ngrams_b))

        return (intersection * 100) // min_size if min_size > 0 else 0

    def calc_lcs_similarity(self, tokens_a: List[int], tokens_b: List[int]) -> int:
        """
        Calculate LCS similarity between two token sequences.

        This implements the same algorithm as NIL's LCSBasedVerification:
        similarity = lcs_length * 100 / min(len(a), len(b))

        Uses Hunt-Szymanski algorithm for O(N log N) complexity.

        Args:
            tokens_a: First token sequence
            tokens_b: Second token sequence

        Returns:
            Similarity percentage (0-100)
        """
        if not tokens_a or not tokens_b:
            return 0

        lcs_length = self._hunt_szymanski_lcs(tokens_a, tokens_b)
        min_len = min(len(tokens_a), len(tokens_b))

        return (lcs_length * 100) // min_len if min_len > 0 else 0

    def _create_ngrams(self, tokens: List[int]) -> Set[int]:
        """
        Create a distinct set of N-gram hashes from token sequence.

        This implements the same logic as NIL's TokenSequence.toNgrams():
        - Extract N-grams of size gram_size
        - Hash each N-gram using Python's hash()
        - Return distinct set

        Args:
            tokens: Token sequence

        Returns:
            Set of N-gram hashes
        """
        if len(tokens) < self.gram_size:
            return set()

        ngrams = set()
        for i in range(len(tokens) - self.gram_size + 1):
            ngram = tuple(tokens[i : i + self.gram_size])
            ngrams.add(hash(ngram))

        return ngrams

    def _hunt_szymanski_lcs(self, a: List[int], b: List[int]) -> int:
        """
        Calculate LCS length using Hunt-Szymanski algorithm.

        This is a Python port of NIL's HuntSzymanskiLCS implementation.
        Time complexity: O(N log N)

        Reference: https://dl.acm.org/doi/10.1145/359581.359603

        Args:
            a: First token sequence
            b: Second token sequence

        Returns:
            Length of LCS
        """
        # Optimize by using shorter sequence first
        if len(a) < len(b):
            shorter, longer = a, b
        else:
            shorter, longer = b, a

        n, m = len(shorter), len(longer)

        if n == 0 or m == 0:
            return 0

        # Build inverted index: token -> list of positions in longer sequence
        inverted_indices = {}
        for i in range(m - 1, -1, -1):
            token = longer[i]
            if token not in inverted_indices:
                inverted_indices[token] = []
            inverted_indices[token].append(i)

        # Initialize LCS array
        # lcs[k] = smallest index in longer sequence where LCS of length k ends
        lcs = [float("inf")] * (n + 1)
        lcs[0] = -1

        # Process each token in shorter sequence
        for token in shorter:
            if token not in inverted_indices:
                continue

            # Process positions in reverse order (from inverted_indices)
            for pos in inverted_indices[token]:
                # Binary search to find the right position to update
                left, right = 0, n
                while left < right:
                    mid = (left + right + 1) // 2
                    if lcs[mid] < pos:
                        left = mid
                    else:
                        right = mid - 1

                # Update if we found a longer LCS
                if lcs[left] < pos < lcs[left + 1]:
                    lcs[left + 1] = pos

        # Find the longest LCS length
        for k in range(n, -1, -1):
            if lcs[k] != float("inf"):
                return k

        return 0


def main():
    """Test the similarity calculator."""
    calc = SimilarityCalculator(gram_size=5)

    # Test case 1: Identical sequences
    tokens1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    tokens2 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    print("Test 1 - Identical sequences:")
    print(f"  N-gram similarity: {calc.calc_ngram_similarity(tokens1, tokens2)}%")
    print(f"  LCS similarity: {calc.calc_lcs_similarity(tokens1, tokens2)}%")

    # Test case 2: Partially similar sequences
    tokens3 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    tokens4 = [1, 2, 3, 99, 5, 6, 7, 88, 9, 10]
    print("\nTest 2 - Partially similar:")
    print(f"  N-gram similarity: {calc.calc_ngram_similarity(tokens3, tokens4)}%")
    print(f"  LCS similarity: {calc.calc_lcs_similarity(tokens3, tokens4)}%")

    # Test case 3: Different sequences
    tokens5 = [1, 2, 3, 4, 5]
    tokens6 = [10, 20, 30, 40, 50]
    print("\nTest 3 - Different sequences:")
    print(f"  N-gram similarity: {calc.calc_ngram_similarity(tokens5, tokens6)}%")
    print(f"  LCS similarity: {calc.calc_lcs_similarity(tokens5, tokens6)}%")


if __name__ == "__main__":
    main()
