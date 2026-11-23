"""Page-aware chunking. Each chunk keeps its page number for precise citations."""

from __future__ import annotations

import re


def clean_text(text: str) -> str:
    text = text.replace("­", "")          # soft hyphens
    text = re.sub(r"-\n(?=\w)", "", text)       # words hyphenated across lines
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _hard_split(paragraph: str, max_chars: int, overlap: int) -> list[str]:
    pieces: list[str] = []
    start = 0
    while start < len(paragraph):
        end = min(start + max_chars, len(paragraph))
        if end < len(paragraph):
            cut = paragraph.rfind(". ", start + max_chars // 2, end)
            if cut != -1:
                end = cut + 1
        piece = paragraph[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= len(paragraph):
            break
        start = max(end - overlap, start + 1)
    return pieces


def split_text(text: str, max_chars: int = 1200, overlap: int = 150) -> list[str]:
    """Greedy paragraph packing; oversized paragraphs are split on sentence ends."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buffer = ""
    for paragraph in paragraphs:
        pieces = (
            _hard_split(paragraph, max_chars, overlap)
            if len(paragraph) > max_chars
            else [paragraph]
        )
        for piece in pieces:
            if buffer and len(buffer) + 2 + len(piece) > max_chars:
                chunks.append(buffer)
                buffer = piece
            else:
                buffer = f"{buffer}\n\n{piece}" if buffer else piece
    if buffer:
        chunks.append(buffer)
    return chunks
