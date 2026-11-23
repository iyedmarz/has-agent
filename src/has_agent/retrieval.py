"""Hybrid retrieval: dense vectors (bge-m3) + BM25 keywords, merged with RRF.

Why hybrid? Dense search captures meaning ("insuffisance rénale" ~ "atteinte des reins"),
BM25 nails exact terms that matter in medicine (drug names, acronyms, codes).
"""

from __future__ import annotations

from dataclasses import dataclass

from rank_bm25 import BM25Okapi

from has_agent.config import Settings
from has_agent.ingest import get_collection
from has_agent.llm import LocalLLM
from has_agent.textutils import reciprocal_rank_fusion, tokenize


@dataclass
class Hit:
    id: str
    text: str
    source: str
    title: str
    page: int
    score: float


class HybridRetriever:
    def __init__(self, settings: Settings, llm: LocalLLM | None = None):
        self.settings = settings
        self.llm = llm or LocalLLM(settings)
        self.collection = get_collection(settings)
        self._load_corpus()

    def _load_corpus(self) -> None:
        data = self.collection.get(include=["documents", "metadatas"])
        self.ids: list[str] = data["ids"]
        self.docs: dict[str, str] = dict(zip(self.ids, data["documents"]))
        self.metas: dict[str, dict] = dict(zip(self.ids, data["metadatas"]))
        tokenized = [tokenize(self.docs[i]) for i in self.ids]
        self.bm25 = BM25Okapi(tokenized) if tokenized else None

    @property
    def size(self) -> int:
        return len(self.ids)

    def search(self, query: str, k: int | None = None, pool: int = 20) -> list[Hit]:
        k = k or self.settings.top_k
        if not self.ids:
            return []

        dense = self.collection.query(
            query_embeddings=self.llm.embed([query]),
            n_results=min(pool, len(self.ids)),
        )
        dense_ranking = dense["ids"][0]

        sparse_ranking: list[str] = []
        query_tokens = tokenize(query)
        if self.bm25 and query_tokens:
            scores = self.bm25.get_scores(query_tokens)
            order = sorted(range(len(self.ids)), key=lambda i: scores[i], reverse=True)
            sparse_ranking = [self.ids[i] for i in order[:pool] if scores[i] > 0]

        fused = reciprocal_rank_fusion([dense_ranking, sparse_ranking])
        best = sorted(fused, key=fused.get, reverse=True)[:k]
        hits = []
        for chunk_id in best:
            meta = self.metas[chunk_id]
            hits.append(
                Hit(
                    id=chunk_id,
                    text=self.docs[chunk_id],
                    source=meta["source"],
                    title=meta["title"],
                    page=int(meta["page"]),
                    score=fused[chunk_id],
                )
            )
        return hits
