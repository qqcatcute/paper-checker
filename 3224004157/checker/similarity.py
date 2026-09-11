"""Character-frequency similarity suitable for Chinese and mixed-language text."""

import math
import unicodedata
from collections import Counter
from collections.abc import Mapping

UNIGRAM_WEIGHT = 0.3
BIGRAM_WEIGHT = 0.7


def normalize_text(text: str) -> str:
    """Normalize width/case and retain only Unicode letters and numbers."""
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return "".join(character for character in normalized if character.isalnum())


def cosine_similarity(left: Mapping[str, int], right: Mapping[str, int]) -> float:
    """Compare two non-negative frequency mappings; an empty norm scores zero."""
    vocabulary = set(left) | set(right)
    left_vector = [left.get(feature, 0) for feature in vocabulary]
    right_vector = [right.get(feature, 0) for feature in vocabulary]
    dot = sum(a * b for a, b in zip(left_vector, right_vector))
    left_squared = sum(value * value for value in left_vector)
    right_squared = sum(value * value for value in right_vector)
    if not left_squared or not right_squared:
        return 0.0
    return min(1.0, max(0.0, dot / math.sqrt(left_squared * right_squared)))


def similarity(left: str, right: str) -> float:
    """Return a score in [0, 1] using 30% unigrams and 70% bigrams.

    An empty normalized input scores zero. If either text is a single
    character, only unigram cosine is used because a bigram cannot exist.
    """
    left = normalize_text(left)
    right = normalize_text(right)
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    unigram_score = cosine_similarity(Counter(left), Counter(right))
    if min(len(left), len(right)) == 1:
        return unigram_score
    left_pairs = Counter(left[index : index + 2] for index in range(len(left) - 1))
    right_pairs = Counter(right[index : index + 2] for index in range(len(right) - 1))
    bigram_score = cosine_similarity(left_pairs, right_pairs)
    return min(1.0, max(0.0, UNIGRAM_WEIGHT * unigram_score + BIGRAM_WEIGHT * bigram_score))
