"""Pure-Python text helpers (no heavy dependencies, easy to unit-test)."""

from __future__ import annotations

import re
import unicodedata

_STOPWORDS = {
    "le", "la", "les", "de", "des", "du", "un", "une", "et", "ou", "en", "au", "aux",
    "ce", "ces", "cette", "dans", "pour", "par", "sur", "avec", "sans", "est", "sont",
    "que", "qui", "quoi", "se", "sa", "son", "ses", "ne", "pas", "plus", "quel",
    "quelle", "quels", "quelles", "il", "elle", "ils", "elles", "on", "nous", "vous",
}


def normalize(text: str) -> str:
    """Lowercase and strip accents so 'médicament' matches 'medicament'."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"\w+", normalize(text))
    return [t for t in tokens if len(t) > 1 and t not in _STOPWORDS]


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> dict[str, float]:
    """Merge several ranked id lists into one score per id (RRF, Cormack et al.)."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, item_id in enumerate(ranking):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank + 1)
    return scores
