# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
"""
SHACL Validator extension — pure Python via pyshacl.
Always available (no download required), does NOT require a daemon.
Uses RDFS/SHACL shapes, NOT OWL class membership.
"""
from __future__ import annotations
from pathlib import Path
from extensions.base import ExtensionBase, ExtensionMeta

_SHAPES_DIR = Path(__file__).parent / "shapes"


class ShaclValidatorExtension(ExtensionBase):
    def __init__(self) -> None:
        self._pyshacl = None

    @property
    def meta(self) -> ExtensionMeta:
        return ExtensionMeta(
            name="shacl_validator",
            description="SHACL/RDFS shape validation for health data (no OWL). Pure pip, zero download.",
            version="1.0.0",
            download_size_mb=0.0,
            requires_daemon=False,
            homepage="https://github.com/RDFLib/pySHACL",
        )

    def is_available(self) -> bool:
        try:
            import pyshacl  # noqa: F401
            return True
        except ImportError:
            return False

    def download(self) -> None:
        import subprocess, sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyshacl>=0.25"])

    def load(self) -> None:
        import pyshacl
        self._pyshacl = pyshacl

    def health_check(self) -> bool:
        return self._pyshacl is not None

    def teardown(self) -> None:
        self._pyshacl = None

    def validate(self, data_graph_ttl: str, shape_name: str | None = None) -> dict:
        """
        Validate a Turtle graph against SHACL shapes.
        shape_name: filename stem in shapes/ (e.g. "sleep"). None = all shapes.
        Returns {"conforms": bool, "violations": [{"message": str, "path": str}]}
        """
        if self._pyshacl is None:
            raise RuntimeError("ShaclValidatorExtension not loaded")

        from rdflib import Graph
        data_g = Graph()
        data_g.parse(data=data_graph_ttl, format="turtle")

        shape_files = (
            [_SHAPES_DIR / f"{shape_name}.ttl"]
            if shape_name
            else sorted(_SHAPES_DIR.glob("*.ttl"))
        )

        all_violations = []
        conforms_overall = True

        for sf in shape_files:
            if not sf.exists():
                continue
            shapes_g = Graph()
            shapes_g.parse(sf, format="turtle")
            conforms, _, report_text = self._pyshacl.validate(
                data_g,
                shacl_graph=shapes_g,
                ont_graph=None,   # No OWL reasoning
                inference="rdfs", # RDFS only
                abort_on_first=False,
            )
            if not conforms:
                conforms_overall = False
                all_violations.append({"shape_file": sf.name, "report": report_text})

        return {"conforms": conforms_overall, "violations": all_violations}
