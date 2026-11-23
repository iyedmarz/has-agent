"""Tiny evaluation harness: retrieval hit@k / MRR, and optional answer checks.

questions file format (JSON list):
[
  {
    "question": "...",
    "expected_sources": ["part of a PDF file name"],
    "expected_keywords": ["words that must appear in a correct answer"]
  }
]
"""

from __future__ import annotations

import json
from pathlib import Path

from has_agent.agent import HASAgent
from has_agent.textutils import normalize


def _matches(hit_source: str, expected: list[str]) -> bool:
    source = normalize(hit_source)
    return any(normalize(e) in source for e in expected)


def run_eval(agent: HASAgent, questions_path: Path, with_answers: bool, k: int) -> dict:
    cases = json.loads(questions_path.read_text(encoding="utf-8"))
    rows = []
    for case in cases:
        hits = agent.retriever.search(case["question"], k=k)
        rank = next(
            (i for i, h in enumerate(hits, 1) if _matches(h.source, case["expected_sources"])),
            None,
        )
        row = {"question": case["question"], "rank": rank}
        if with_answers:
            answer = agent.ask(case["question"], top_k=k)
            keywords = case.get("expected_keywords", [])
            body = normalize(answer.text)
            found = [kw for kw in keywords if normalize(kw) in body]
            row["keyword_recall"] = len(found) / len(keywords) if keywords else None
            row["verdict"] = answer.verdict
        rows.append(row)

    n = len(rows)
    hit_rate = sum(1 for r in rows if r["rank"]) / n if n else 0.0
    mrr = sum(1 / r["rank"] for r in rows if r["rank"]) / n if n else 0.0
    summary = {"questions": n, f"hit@{k}": round(hit_rate, 3), "mrr": round(mrr, 3)}
    if with_answers:
        recalls = [r["keyword_recall"] for r in rows if r.get("keyword_recall") is not None]
        grounded = sum(1 for r in rows if r.get("verdict") == "supported")
        summary["keyword_recall"] = round(sum(recalls) / len(recalls), 3) if recalls else None
        summary["grounded_rate"] = round(grounded / n, 3) if n else 0.0
    return {"summary": summary, "rows": rows}
