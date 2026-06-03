# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Abstract base class for all WellFair extensions."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ExtensionMeta:
    name: str
    description: str
    version: str
    download_size_mb: float
    requires_daemon: bool       # True = cannot run in Stlite/Pyodide
    homepage: str = ""


class ExtensionBase(ABC):
    """
    All extensions implement this interface.

    Lifecycle:
        1. ExtensionRegistry.activate(name)  → calls download() then load()
        2. Use the extension via its public methods
        3. ExtensionRegistry.deactivate(name) → calls teardown()
    """

    @property
    @abstractmethod
    def meta(self) -> ExtensionMeta:
        ...

    def is_available(self) -> bool:
        """Return True if the extension binary/model is already on disk."""
        return False

    @abstractmethod
    def download(self) -> None:
        """Fetch any required binaries or model weights to local storage."""
        ...

    @abstractmethod
    def load(self) -> None:
        """Initialise the extension (start daemon, load weights, etc.)."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if the extension is operational."""
        ...

    @abstractmethod
    def teardown(self) -> None:
        """Release all resources (stop daemon, unload model from memory)."""
        ...
