"""Local append-only audit trail (JSONL). Nothing is ever sent off the machine."""

from __future__ import annotations

import json
import time

from has_agent.config import Settings


def log_interaction(settings: Settings, record: dict) -> None:
    settings.audit_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **record}
    if not settings.log_questions:
        entry.pop("question", None)
        entry.pop("search_query", None)
    with settings.audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
