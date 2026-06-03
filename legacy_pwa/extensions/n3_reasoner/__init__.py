# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
"""
N3Logic Reasoner extension — EYE (Euler YAP Engine).

EYE implements N3Logic as defined by Tim Berners-Lee.  It is the correct
tool for causal/clinical reasoning: "given these interwoven symptoms,
what patterns emerge?"  This is NOT OWL entailment.

EYE binary (~15MB) is downloaded on first use from GitHub releases.
Runs as a subprocess — no persistent daemon.

N3 rule files live in extensions/n3_reasoner/rules/.
"""
from __future__ import annotations
import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from extensions.base import ExtensionBase, ExtensionMeta

_RULES_DIR = Path(__file__).parent / "rules"
_BIN_DIR = Path(__file__).parent / "bin"

# EYE release URLs per platform
_EYE_VERSION = "v10.17.0"
_EYE_RELEASES: dict[str, str] = {
    "linux":   f"https://github.com/eyereasoner/eye/releases/download/{_EYE_VERSION}/eye-linux-x86_64",
    "darwin":  f"https://github.com/eyereasoner/eye/releases/download/{_EYE_VERSION}/eye-macos-x86_64",
    "win32":   f"https://github.com/eyereasoner/eye/releases/download/{_EYE_VERSION}/eye-windows-x86_64.exe",
    "windows": f"https://github.com/eyereasoner/eye/releases/download/{_EYE_VERSION}/eye-windows-x86_64.exe",
}


def _eye_binary_path() -> Path:
    sys = platform.system().lower()
    ext = ".exe" if sys == "windows" else ""
    return _BIN_DIR / f"eye{ext}"


class N3ReasonerExtension(ExtensionBase):
    def __init__(self) -> None:
        self._eye_path: Path | None = None

    @property
    def meta(self) -> ExtensionMeta:
        return ExtensionMeta(
            name="n3_reasoner",
            description="N3Logic causal reasoning via EYE (Euler YAP Engine). Downloads ~15MB binary.",
            version=_EYE_VERSION,
            download_size_mb=15.0,
            requires_daemon=False,
            homepage="https://github.com/eyereasoner/eye",
        )

    def is_available(self) -> bool:
        # Also accept a system-installed `eye`
        return _eye_binary_path().exists() or shutil.which("eye") is not None

    def download(self) -> None:
        from urllib.request import urlretrieve
        sys = platform.system().lower()
        url = _EYE_RELEASES.get(sys)
        if not url:
            raise RuntimeError(f"No EYE binary available for platform: {sys}")
        _BIN_DIR.mkdir(parents=True, exist_ok=True)
        dest = _eye_binary_path()
        print(f"[n3_reasoner] Downloading EYE {_EYE_VERSION} from {url} …")
        urlretrieve(url, dest)
        if sys != "windows":
            dest.chmod(0o755)
        print(f"[n3_reasoner] EYE installed at {dest}")

    def load(self) -> None:
        path = _eye_binary_path()
        if path.exists():
            self._eye_path = path
        elif shutil.which("eye"):
            self._eye_path = Path(shutil.which("eye"))
        else:
            raise RuntimeError("EYE binary not found. Call download() first.")

    def health_check(self) -> bool:
        if not self._eye_path:
            return False
        try:
            result = subprocess.run(
                [str(self._eye_path), "--version"],
                capture_output=True, timeout=5,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def teardown(self) -> None:
        self._eye_path = None

    def reason(
        self,
        data_ttl: str,
        rule_names: list[str] | None = None,
        extra_rules_ttl: str | None = None,
        query_ttl: str | None = None,
        timeout: int = 30,
    ) -> str:
        """
        Run N3Logic forward-chaining inference.

        data_ttl:       RDF data in Turtle/N3 format
        rule_names:     Names of rule files in rules/ to load (e.g. ["adrenal_fatigue"])
                        None = load all rules
        extra_rules_ttl: Additional N3 rules as a string (inline)
        query_ttl:      N3 query/filter (passed as --query to EYE)
        timeout:        Subprocess timeout in seconds

        Returns: inferred N3 triples as a string
        """
        if not self._eye_path:
            raise RuntimeError("N3ReasonerExtension not loaded")

        rule_files = []
        if rule_names is None:
            rule_files = sorted(_RULES_DIR.glob("*.n3"))
        else:
            for name in rule_names:
                p = _RULES_DIR / f"{name}.n3"
                if p.exists():
                    rule_files.append(p)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            data_file = tmp / "data.n3"
            data_file.write_text(data_ttl, encoding="utf-8")

            cmd = [str(self._eye_path), "--nope", str(data_file)]
            cmd += [str(r) for r in rule_files]

            if extra_rules_ttl:
                extra_file = tmp / "extra_rules.n3"
                extra_file.write_text(extra_rules_ttl, encoding="utf-8")
                cmd.append(str(extra_file))

            if query_ttl:
                query_file = tmp / "query.n3"
                query_file.write_text(query_ttl, encoding="utf-8")
                cmd += ["--query", str(query_file)]
            else:
                cmd.append("--pass-only-new")

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            if result.returncode != 0:
                raise RuntimeError(f"EYE error:\n{result.stderr}")
            return result.stdout

    def get_patterns(self, data_ttl: str) -> list[str]:
        """
        High-level helper: returns list of detected health pattern URIs.
        Loads all clinical rules and extracts health:pattern assertions.
        """
        n3_out = self.reason(data_ttl)
        patterns = []
        for line in n3_out.splitlines():
            if "health:pattern" in line:
                # crude extraction — proper parsing via rdflib
                parts = line.split("health:pattern")
                if len(parts) > 1:
                    patterns.append(parts[1].strip().rstrip(" .;"))
        return patterns
