"""
Bridge between Streamlit/Pyodide and the browser-level PackageManager.

In the stlite environment, Python runs inside Pyodide which has access to
browser globals via the `js` module. This module reads window.wellfairPackageState
(a plain JS object written by package-manager.js) so that Streamlit views can
gate features based on installed packages.

In the local Streamlit (desktop) environment, the `js` module is not available.
All features are treated as available so the app functions normally during development.
"""
from __future__ import annotations

_IN_PYODIDE = False
try:
    import js as _js  # type: ignore  # only exists in Pyodide/stlite
    _IN_PYODIDE = True
except ImportError:
    pass


def _get_state() -> dict:
    """Read window.wellfairPackageState from the browser, or return defaults."""
    if not _IN_PYODIDE:
        return {"ready": True, "capabilities": _ALL_CAPS, "packages": {}}
    try:
        state = _js.window.wellfairPackageState
        if state is None:
            return {"ready": False, "capabilities": _BASE_CAPS, "packages": {}}
        return {
            "ready":        bool(state.ready),
            "capabilities": list(state.capabilities),
            "packages":     {},  # accessed per-package below
        }
    except Exception:
        return {"ready": False, "capabilities": _BASE_CAPS, "packages": {}}


# Capabilities always present (oxigraph is bundled in wellfare-core WASM)
_BASE_CAPS = ["core:rdf", "core:sparql"]

# All capabilities — returned in non-Pyodide (desktop) mode so features aren't hidden
_ALL_CAPS = [
    "core:rdf", "core:sparql",
    "reasoning:prolog", "reasoning:n3",
    "llm:inference", "llm:extraction", "llm:explanation",
]

# Feature → required capability tokens (mirrors capabilities.js)
_FEATURE_REQUIREMENTS: dict[str, list[str]] = {
    "profile-view":            [],
    "personal-health":         [],
    "rdf-convert":             [],
    "anatomy-3d":              [],
    "calendar-timeline":       [],
    "life-events":             [],
    "location":                [],
    "social-work":             [],
    "case-management":         [],
    "sanctuary-mode":          [],
    "assessments":             [],
    "mental-health":           [],
    "agent-directory":         [],
    "pathology":               ["core:sparql"],
    "sparql-query":            ["core:sparql"],
    "differential-diagnosis":  ["core:sparql", "reasoning:prolog"],
    "welfare-eligibility":     ["core:sparql", "reasoning:prolog"],
    "anatomy-3d-reasoning":    ["core:sparql", "reasoning:prolog"],
    "document-ingestion":      ["llm:extraction"],
    "paper-extraction":        ["llm:extraction"],
    "explanation-sidebar":     ["llm:explanation"],
    "study-vault":             ["llm:extraction", "reasoning:prolog"],
    "n3-patterns":             ["reasoning:n3"],
}

# Navigation section key → feature key (mirrors capabilities.js)
_NAV_FEATURE_MAP: dict[str, str] = {
    "profile_intake":    "profile-view",
    "personal_health":   "personal-health",
    "calendar_timeline": "calendar-timeline",
    "pathology":         "pathology",
    "anatomy_3d":        "anatomy-3d",
    "mental_health":     "mental-health",
    "life_events":       "life-events",
    "case_management":   "case-management",
    "social_work":       "social-work",
    "assessments":       "assessments",
    "document_ingestion":"document-ingestion",
    "study_vault":       "study-vault",
    "location":          "location",
    "agent_directory":   "agent-directory",
    "sanctuary_mode":    "sanctuary-mode",
    "packages":          "profile-view",
}


def get_capabilities() -> set[str]:
    """Return the set of currently available capability tokens."""
    return set(_get_state().get("capabilities", _BASE_CAPS))


def is_feature_available(feature_id: str) -> bool:
    """True if all capabilities required by feature_id are present."""
    caps = get_capabilities()
    required = _FEATURE_REQUIREMENTS.get(feature_id, [])
    return all(c in caps for c in required)


def is_nav_section_available(section_key: str) -> bool:
    """True if the navigation section's feature requirements are met."""
    feature = _NAV_FEATURE_MAP.get(section_key, "profile-view")
    return is_feature_available(feature)


def missing_caps_for(feature_id: str) -> list[str]:
    """Return capability tokens that are required but not yet installed."""
    caps = get_capabilities()
    required = _FEATURE_REQUIREMENTS.get(feature_id, [])
    return [c for c in required if c not in caps]


def get_package_status(package_id: str) -> str:
    """
    Return the install status string for a package:
    bundled | not-installed | downloading | installed | loaded | error
    """
    if not _IN_PYODIDE:
        return "installed"  # desktop — treat everything as available
    try:
        state = _js.window.wellfairPackageState
        if state is None:
            return "not-installed"
        pkgs = state.packages
        pkg  = getattr(pkgs, package_id.replace("-", "_"), None) or getattr(pkgs, package_id, None)
        if pkg is None:
            return "not-installed"
        return str(pkg.status)
    except Exception:
        return "not-installed"


def trigger_install_ui(package_id: str) -> None:
    """Signal the browser to show the install overlay for a package."""
    if not _IN_PYODIDE:
        return
    try:
        _js.window.wellfairPackages.showInstallUI(package_id)
    except Exception:
        pass
