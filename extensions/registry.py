# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Extension registry — discover, activate, and manage WellFair extensions."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from extensions.base import ExtensionBase


class ExtensionRegistry:
    def __init__(self) -> None:
        self._available: dict[str, type[ExtensionBase]] = {}
        self._active: dict[str, ExtensionBase] = {}
        self._discover()

    def _discover(self) -> None:
        from extensions.shacl_validator import ShaclValidatorExtension
        from extensions.n3_reasoner import N3ReasonerExtension
        from extensions.local_llm import LocalLLMExtension
        self._available = {
            "shacl_validator": ShaclValidatorExtension,
            "n3_reasoner": N3ReasonerExtension,
            "local_llm": LocalLLMExtension,
        }

    def available(self) -> list[dict]:
        """Return metadata for all known extensions with their current status."""
        out = []
        for name, cls in self._available.items():
            inst = cls()
            out.append({
                "name": name,
                "description": inst.meta.description,
                "version": inst.meta.version,
                "download_size_mb": inst.meta.download_size_mb,
                "requires_daemon": inst.meta.requires_daemon,
                "installed": inst.is_available(),
                "active": name in self._active,
            })
        return out

    def activate(self, name: str, **kwargs) -> "ExtensionBase":
        """Download (if needed) and load an extension. Returns the live instance."""
        if name in self._active:
            return self._active[name]
        if name not in self._available:
            raise KeyError(f"Unknown extension: {name!r}. Available: {list(self._available)}")
        inst = self._available[name](**kwargs)
        if not inst.is_available():
            inst.download()
        inst.load()
        if not inst.health_check():
            raise RuntimeError(f"Extension {name!r} failed health check after load")
        self._active[name] = inst
        return inst

    def get(self, name: str) -> "ExtensionBase":
        if name not in self._active:
            raise RuntimeError(f"Extension {name!r} is not active. Call activate() first.")
        return self._active[name]

    def deactivate(self, name: str) -> None:
        if name in self._active:
            self._active.pop(name).teardown()

    def deactivate_all(self) -> None:
        for name in list(self._active):
            self.deactivate(name)
