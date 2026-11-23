"""Central configuration, overridable with environment variables.

Privacy by design: the agent refuses to talk to a non-local Ollama server
unless HAS_ALLOW_REMOTE=1 is set explicitly.
"""

from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    ollama_host: str
    llm_model: str
    embed_model: str
    pdf_dir: Path
    index_dir: Path
    audit_path: Path
    collection: str
    chunk_chars: int
    chunk_overlap: int
    top_k: int
    num_ctx: int
    log_questions: bool


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_settings() -> Settings:
    data = Path(os.getenv("HAS_DATA_DIR", ROOT / "data"))
    settings = Settings(
        ollama_host=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"),
        llm_model=os.getenv("HAS_LLM_MODEL", "qwen3.5:4b"),
        embed_model=os.getenv("HAS_EMBED_MODEL", "bge-m3"),
        pdf_dir=Path(os.getenv("HAS_PDF_DIR", data / "pdfs")),
        index_dir=Path(os.getenv("HAS_INDEX_DIR", data / "index")),
        audit_path=Path(os.getenv("HAS_AUDIT_PATH", data / "audit.jsonl")),
        collection="has_documents",
        chunk_chars=int(os.getenv("HAS_CHUNK_CHARS", "1200")),
        chunk_overlap=int(os.getenv("HAS_CHUNK_OVERLAP", "150")),
        top_k=int(os.getenv("HAS_TOP_K", "6")),
        num_ctx=int(os.getenv("HAS_NUM_CTX", "8192")),
        log_questions=_env_bool("HAS_AUDIT_LOG_QUESTIONS", True),
    )
    assert_local(settings.ollama_host)
    return settings


def assert_local(host: str) -> None:
    """Raise if the LLM endpoint is not on the local machine / private network."""
    if _env_bool("HAS_ALLOW_REMOTE", False):
        return
    hostname = urlparse(host if "://" in host else f"http://{host}").hostname or ""
    if hostname in {"localhost", "host.docker.internal"}:
        return
    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        raise RuntimeError(
            f"Refusing non-local LLM host '{hostname}'. "
            "Set HAS_ALLOW_REMOTE=1 only if you really intend this."
        ) from None
    if not (ip.is_loopback or ip.is_private):
        raise RuntimeError(
            f"Refusing public LLM host '{hostname}'. Medical data must stay local."
        )
