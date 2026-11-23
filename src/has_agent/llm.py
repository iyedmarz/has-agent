"""Thin wrapper around a local Ollama server (chat + embeddings)."""

from __future__ import annotations

from typing import Callable

import ollama

from has_agent.config import Settings


class LocalLLM:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = ollama.Client(host=settings.ollama_host)

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embed(model=self.settings.embed_model, input=texts)
        return [list(v) for v in response["embeddings"]]

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.1,
        json_mode: bool = False,
        on_token: Callable[[str], None] | None = None,
    ) -> str:
        options = {"temperature": temperature, "num_ctx": self.settings.num_ctx}
        kwargs = dict(
            model=self.settings.llm_model,
            messages=messages,
            options=options,
        )
        if json_mode:
            kwargs["format"] = "json"
        if on_token is None:
            response = self.client.chat(**kwargs)
            return response["message"]["content"]
        parts: list[str] = []
        for chunk in self.client.chat(stream=True, **kwargs):
            token = chunk["message"]["content"]
            if token:
                parts.append(token)
                on_token(token)
        return "".join(parts)

    def installed_models(self) -> list[str]:
        response = self.client.list()
        names = []
        for model in response["models"]:
            name = getattr(model, "model", None) or model.get("model") or model.get("name")
            if name:
                names.append(name)
        return names
