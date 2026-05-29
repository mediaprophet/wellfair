# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Local LLM extension — Ollama-backed inference for PDF parsing and
unstructured health text extraction.

Requires Ollama daemon running at localhost:11434 (https://ollama.com).
Model weights are pulled via `ollama pull <model>` on first use.

This extension CANNOT run inside Stlite/Pyodide (requires_daemon=True).
"""
from __future__ import annotations
import json
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen
from extensions.base import ExtensionBase, ExtensionMeta

_OLLAMA_BASE = "http://localhost:11434"

# Model registry — ordered by RAM requirement ascending
MODELS: dict[str, dict] = {
    "qwen2.5:1.5b": {
        "description": "Lightweight triage and tagging",
        "ram_gb": 1.0,
        "use_cases": ["tagging", "classification"],
    },
    "llama3.2:3b": {
        "description": "Symptom pattern matching and summarisation",
        "ram_gb": 2.0,
        "use_cases": ["symptom_extraction", "summarisation"],
    },
    "phi3.5": {
        "description": "PDF and clinical note extraction (structured output)",
        "ram_gb": 2.2,
        "use_cases": ["pdf_parsing", "structured_extraction"],
    },
}

_DEFAULT_MODEL = "llama3.2:3b"


class LocalLLMExtension(ExtensionBase):
    def __init__(self, model: str = _DEFAULT_MODEL) -> None:
        self.model = model
        self._available_models: list[str] = []

    @property
    def meta(self) -> ExtensionMeta:
        return ExtensionMeta(
            name="local_llm",
            description="Local LLM via Ollama for PDF parsing and health text extraction. Requires Ollama daemon.",
            version="1.0.0",
            download_size_mb=MODELS.get(self.model, {}).get("ram_gb", 2.0) * 1024,
            requires_daemon=True,
            homepage="https://ollama.com",
        )

    def is_available(self) -> bool:
        try:
            with urlopen(f"{_OLLAMA_BASE}/api/tags", timeout=2) as resp:
                data = json.loads(resp.read())
                self._available_models = [m["name"] for m in data.get("models", [])]
                return any(self.model in m for m in self._available_models)
        except (URLError, OSError):
            return False

    def download(self) -> None:
        """Pull the model via Ollama API."""
        payload = json.dumps({"name": self.model}).encode()
        req = Request(
            f"{_OLLAMA_BASE}/api/pull",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        print(f"[local_llm] Pulling {self.model} via Ollama (this may take a while)…")
        try:
            with urlopen(req, timeout=300) as resp:
                for line in resp:
                    status = json.loads(line).get("status", "")
                    if status:
                        print(f"  {status}", end="\r")
            print(f"\n[local_llm] {self.model} ready.")
        except URLError as e:
            raise RuntimeError(
                f"Ollama not reachable at {_OLLAMA_BASE}. "
                f"Install Ollama from https://ollama.com and start the daemon.\n{e}"
            ) from e

    def load(self) -> None:
        pass  # Ollama manages model loading lazily on first inference

    def health_check(self) -> bool:
        return self.is_available()

    def teardown(self) -> None:
        # Unload model from GPU/RAM via Ollama keep_alive=0
        try:
            payload = json.dumps({"model": self.model, "keep_alive": 0}).encode()
            req = Request(
                f"{_OLLAMA_BASE}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urlopen(req, timeout=5)
        except (URLError, OSError):
            pass

    def generate(self, prompt: str, system: str = "", temperature: float = 0.1) -> str:
        """Run a completion. Returns the assistant response text."""
        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": temperature},
        }).encode()
        req = Request(
            f"{_OLLAMA_BASE}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                return data.get("response", "")
        except URLError as e:
            raise RuntimeError(f"Ollama inference failed: {e}") from e

    def extract_health_data(self, text: str) -> dict:
        """
        Extract structured health observations from free text or PDF content.
        Returns dict suitable for feeding to rdf_transformer.
        """
        system = (
            "You are a clinical data extraction assistant. "
            "Extract health observations from the text and return ONLY valid JSON "
            "with keys: heart_rate, sleep_hours, stress_score, medications, "
            "diagnoses, notes. Use null for missing values."
        )
        response = self.generate(text[:4000], system=system, temperature=0.0)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"notes": response, "extraction_failed": True}

    def summarise_patterns(self, patterns: list[str], context: str = "") -> str:
        """
        Convert N3Logic pattern URIs into a plain-language welfare summary.
        """
        pattern_labels = "\n".join(f"- {p}" for p in patterns)
        prompt = (
            f"The following health patterns were detected:\n{pattern_labels}\n"
            f"Context: {context}\n\n"
            "Write a brief, compassionate welfare summary (2-3 sentences) "
            "explaining what these patterns may indicate and suggesting next steps. "
            "Do not diagnose. Do not use clinical jargon."
        )
        return self.generate(prompt, temperature=0.3)
