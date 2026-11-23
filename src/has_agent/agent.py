"""The agent loop: rewrite -> retrieve -> answer with citations -> verify -> audit."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Callable

from has_agent.audit import log_interaction
from has_agent.config import Settings, get_settings
from has_agent.llm import LocalLLM
from has_agent.prompts import ANSWER_TEMPLATE, REWRITE_PROMPT, SYSTEM_PROMPT, VERIFY_PROMPT
from has_agent.retrieval import Hit, HybridRetriever

NOT_FOUND = "Je ne trouve pas cette information dans les documents indexés."


@dataclass
class Answer:
    text: str
    search_query: str
    hits: list[Hit]
    cited: list[int] = field(default_factory=list)       # 1-based source numbers
    verdict: str | None = None                           # supported / partially_supported / unsupported
    unsupported_claims: list[str] = field(default_factory=list)
    seconds: float = 0.0


def format_context(hits: list[Hit]) -> str:
    blocks = [
        f"[{i}] {hit.title} (fichier : {hit.source}, page {hit.page})\n{hit.text}"
        for i, hit in enumerate(hits, start=1)
    ]
    return "\n\n---\n\n".join(blocks)


def extract_citations(text: str, n_sources: int) -> list[int]:
    found = {int(m) for m in re.findall(r"\[(\d+)\]", text)}
    return sorted(n for n in found if 1 <= n <= n_sources)


def parse_verification(raw: str) -> tuple[str, list[str]]:
    try:
        data = json.loads(raw)
        verdict = data.get("verdict", "unknown")
        claims = [str(c) for c in data.get("unsupported_claims", [])]
        return verdict, claims
    except (json.JSONDecodeError, AttributeError):
        return "unknown", []


class HASAgent:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.llm = LocalLLM(self.settings)
        self.retriever = HybridRetriever(self.settings, self.llm)

    def _rewrite(self, question: str, history: list[dict]) -> str:
        if not history:
            return question
        transcript = "\n".join(f"{m['role']}: {m['content']}" for m in history[-6:])
        prompt = REWRITE_PROMPT.format(history=transcript, question=question)
        rewritten = self.llm.chat([{"role": "user", "content": prompt}], temperature=0.0)
        return rewritten.strip().strip('"') or question

    def _verify(self, answer: str, context: str) -> tuple[str, list[str]]:
        prompt = VERIFY_PROMPT.format(context=context, answer=answer)
        raw = self.llm.chat(
            [{"role": "user", "content": prompt}], temperature=0.0, json_mode=True
        )
        return parse_verification(raw)

    def ask(
        self,
        question: str,
        history: list[dict] | None = None,
        top_k: int | None = None,
        verify: bool = True,
        on_token: Callable[[str], None] | None = None,
    ) -> Answer:
        started = time.time()
        history = history or []

        search_query = self._rewrite(question, history)
        hits = self.retriever.search(search_query, k=top_k)

        if not hits:
            return Answer(
                text="L'index est vide. Lancez d'abord : has-agent ingest",
                search_query=search_query,
                hits=[],
                seconds=time.time() - started,
            )

        context = format_context(hits)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += history[-6:]
        messages.append(
            {
                "role": "user",
                "content": ANSWER_TEMPLATE.format(context=context, question=question),
            }
        )
        text = self.llm.chat(messages, on_token=on_token).strip()

        answer = Answer(
            text=text,
            search_query=search_query,
            hits=hits,
            cited=extract_citations(text, len(hits)),
        )
        if verify:
            answer.verdict, answer.unsupported_claims = self._verify(text, context)
        answer.seconds = time.time() - started

        log_interaction(
            self.settings,
            {
                "question": question,
                "search_query": search_query,
                "sources": [h.id for h in hits],
                "cited": answer.cited,
                "verdict": answer.verdict,
                "llm_model": self.settings.llm_model,
                "embed_model": self.settings.embed_model,
                "seconds": round(answer.seconds, 2),
            },
        )
        return answer
