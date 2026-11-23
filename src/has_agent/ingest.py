"""PDF ingestion: extract text per page, chunk, embed locally, store in ChromaDB."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Callable

import chromadb
from pypdf import PdfReader

from has_agent.chunking import clean_text, split_text
from has_agent.config import Settings
from has_agent.llm import LocalLLM

BATCH = 32
MIN_PAGE_CHARS = 40


def get_collection(settings: Settings, reset: bool = False):
    settings.index_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(settings.index_dir))
    if reset:
        try:
            client.delete_collection(settings.collection)
        except Exception:
            pass
    return client.get_or_create_collection(
        settings.collection, metadata={"hnsw:space": "cosine"}
    )


def file_sha1(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def extract_pages(path: Path) -> tuple[str, list[tuple[int, str]]]:
    reader = PdfReader(str(path))
    title = ""
    if reader.metadata and reader.metadata.title:
        title = str(reader.metadata.title).strip()
    title = title or path.stem.replace("_", " ").replace("-", " ")
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = clean_text(page.extract_text() or "")
        if len(text) >= MIN_PAGE_CHARS:
            pages.append((number, text))
    return title, pages


def ingest(
    settings: Settings,
    reset: bool = False,
    progress: Callable[[str], None] = print,
) -> dict:
    pdfs = sorted(settings.pdf_dir.glob("*.pdf"))
    if not pdfs:
        progress(f"No PDF found in {settings.pdf_dir}. Add HAS documents there first.")
        return {"documents": 0, "chunks": 0, "skipped": 0}

    collection = get_collection(settings, reset=reset)
    llm = LocalLLM(settings)
    stats = {"documents": 0, "chunks": 0, "skipped": 0}

    for pdf in pdfs:
        doc_hash = file_sha1(pdf)
        if collection.get(where={"doc_hash": doc_hash}, limit=1)["ids"]:
            progress(f"= {pdf.name}: already indexed, skipped")
            stats["skipped"] += 1
            continue

        title, pages = extract_pages(pdf)
        ids, texts, metas = [], [], []
        for page_number, page_text in pages:
            for i, chunk in enumerate(
                split_text(page_text, settings.chunk_chars, settings.chunk_overlap)
            ):
                ids.append(f"{doc_hash[:12]}-p{page_number}-c{i}")
                texts.append(chunk)
                metas.append(
                    {
                        "source": pdf.name,
                        "title": title,
                        "page": page_number,
                        "doc_hash": doc_hash,
                    }
                )
        if not texts:
            progress(f"! {pdf.name}: no extractable text (scanned PDF? needs OCR)")
            continue

        for start in range(0, len(texts), BATCH):
            end = start + BATCH
            collection.add(
                ids=ids[start:end],
                documents=texts[start:end],
                metadatas=metas[start:end],
                embeddings=llm.embed(texts[start:end]),
            )
        stats["documents"] += 1
        stats["chunks"] += len(texts)
        progress(f"+ {pdf.name}: {len(pages)} pages, {len(texts)} chunks")

    return stats
