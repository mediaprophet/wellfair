# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
"""
WellFair Extension Framework.

Extensions are optional capabilities that download on first use and
release memory via teardown().  Extensions with requires_daemon=True
cannot run inside Stlite/Pyodide — they need a local process.

Usage:
    from extensions import registry
    registry.activate("n3_reasoner")
    result = registry.get("n3_reasoner").reason(rules_path, data_ttl)
"""
from extensions.registry import ExtensionRegistry

registry = ExtensionRegistry()

__all__ = ["registry"]
