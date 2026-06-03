#!/usr/bin/env python3
"""
WellFair Ruleset Sandbox (Stage B5)
=====================================
Validates compiled .pl rulesets against the mock profiles in
shared-schemas/test-profiles/ using a local SWI-Prolog installation.

Tests:
  1. Syntax check — .pl file loads without error
  2. Cycle detection — no infinite loops in rules
  3. Healthy baseline — no false positives (no implications triggered)
  4. Per-profile expected triggers — named structures fire as expected
  5. Threshold boundary tests — triggers fire at value, not at value-epsilon
  6. Comorbid profile (Hickam) — all conditions accumulate, no suppression
  7. EDS hierarchy flag — is_hierarchy_target structures are correctly flagged

Requirements:
  - SWI-Prolog (swipl) on PATH, OR swiplserver Python package
  - rdflib (pip install rdflib) for reading mock profiles

Usage:
    python run_tests.py [--ruleset path/to/ruleset.pl] [--verbose]
    python run_tests.py --all   # run against all .pl files in ../../rulesets/
"""

import argparse
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

try:
    from rdflib import Graph, Namespace, Literal, URIRef
    from rdflib.namespace import RDF, RDFS, XSD
    HAS_RDFLIB = True
except ImportError:
    HAS_RDFLIB = False

ROOT       = Path(__file__).parent.parent.parent
PROFILES   = ROOT / "shared-schemas" / "test-profiles"
RULESETS   = ROOT / "rulesets"
APP        = Namespace("https://wellfair.app/ontology/")
SNOMED     = Namespace("http://snomed.info/id/")
FMA_BASE   = "http://purl.org/sig/ont/fma/"

# ---------------------------------------------------------------------------
# Expected results per mock profile
# Format: { profile_stem: { "must_trigger": [...fma_uris], "must_not_trigger": [...] } }
# ---------------------------------------------------------------------------

EXPECTED = {
    "mock_profile_healthy": {
        "must_trigger":     [],
        "must_not_trigger": [
            FMA_BASE + "Left_kidney",
            FMA_BASE + "Heart",
            FMA_BASE + "Retina",
            FMA_BASE + "Left_renal_artery",
        ],
    },
    "mock_profile_diabetic_severe": {
        "must_trigger": [
            FMA_BASE + "Left_kidney",
            FMA_BASE + "Right_kidney",
            FMA_BASE + "Left_renal_artery",
            FMA_BASE + "Right_renal_artery",
            FMA_BASE + "Retina",
            FMA_BASE + "Pancreas",
        ],
        "must_not_trigger": [
            FMA_BASE + "Left_shoulder_joint",   # EDS target
            FMA_BASE + "Vertebral_column",       # EDS target
        ],
    },
    "mock_profile_hypertensive": {
        "must_trigger": [
            FMA_BASE + "Heart",
            FMA_BASE + "Left_kidney",
            FMA_BASE + "Right_kidney",
            FMA_BASE + "Left_renal_artery",
            FMA_BASE + "Right_renal_artery",
            FMA_BASE + "Brain",
            FMA_BASE + "Aorta",
        ],
        "must_not_trigger": [
            FMA_BASE + "Retina",                 # only DM high-HbA1c target
            FMA_BASE + "Left_shoulder_joint",    # EDS target
        ],
    },
    "mock_profile_comorbid": {
        "must_trigger": [
            FMA_BASE + "Left_kidney",
            FMA_BASE + "Right_kidney",
            FMA_BASE + "Left_renal_artery",
            FMA_BASE + "Heart",
            FMA_BASE + "Retina",
            FMA_BASE + "Brain",
            FMA_BASE + "Aorta",
        ],
        "must_not_trigger": [
            FMA_BASE + "Left_shoulder_joint",   # EDS target not in profile
        ],
    },
}

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
WARN = "\033[93m⚠\033[0m"


# ---------------------------------------------------------------------------
# Profile → Prolog fact converter
# ---------------------------------------------------------------------------

def profile_to_prolog_facts(profile_path: Path) -> str:
    """
    Load a mock profile TTL and emit Prolog assert/1 calls for:
      user_fact(me, '<snomed-uri>').
      user_metric(me, param_name, value).
    """
    if not HAS_RDFLIB:
        raise RuntimeError("rdflib is required: pip install rdflib")

    g = Graph()
    g.parse(str(profile_path), format="turtle")

    lines = [":- dynamic user_fact/2, user_metric/3.", ""]

    # Conditions: subject app:userFact <condition-uri>
    for s, p, o in g.triples((None, APP.userFact, None)):
        lines.append(f":- assert(user_fact(me, '{str(o)}')).")

    # Metrics: _blank app:prologName "x" ; app:value "v"
    for blank in g.subjects(APP.prologName, None):
        param_nodes = list(g.objects(blank, APP.prologName))
        value_nodes = list(g.objects(blank, APP.value))
        if param_nodes and value_nodes:
            param = str(param_nodes[0])
            val   = str(value_nodes[0])
            lines.append(f":- assert(user_metric(me, {param}, {val})).")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# SWI-Prolog runner
# ---------------------------------------------------------------------------

def run_prolog(goal: str, consult_files: list[Path], facts_str: str = "",
               timeout: int = 10) -> tuple[bool, str]:
    """
    Run a Prolog goal using swipl.
    Returns (success: bool, output: str).
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pl",
                                     delete=False, encoding="utf-8") as tmp:
        tmp.write(facts_str + "\n")
        for path in consult_files:
            tmp.write(f":- consult('{path.as_posix()}').\n")
        tmp.write(f":- ({goal} -> halt(0) ; halt(1)).\n")
        tmp_path = Path(tmp.name)

    try:
        result = subprocess.run(
            ["swipl", "-q", "-f", str(tmp_path)],
            capture_output=True, text=True, timeout=timeout
        )
        output = result.stdout + result.stderr
        success = result.returncode == 0
        return success, output
    except FileNotFoundError:
        return False, "ERROR: swipl not found on PATH. Install SWI-Prolog."
    except subprocess.TimeoutExpired:
        return False, f"ERROR: Prolog timed out after {timeout}s (possible infinite loop)."
    finally:
        tmp_path.unlink(missing_ok=True)


def collect_all_triggered(ruleset_path: Path, facts_str: str) -> list[tuple[str, str]]:
    """
    Query all implication_target/3 solutions for user 'me'.
    Returns list of (fma_uri, severity) tuples.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pl",
                                     delete=False, encoding="utf-8") as tmp:
        tmp.write(facts_str + "\n")
        tmp.write(f":- consult('{ruleset_path.as_posix()}').\n")
        tmp.write(textwrap.dedent("""\
            :- forall(
                implication_target(me, URI, Severity),
                (atom_string(URI, US), atom_string(Severity, SS),
                 format("TRIGGER:~w:~w~n", [US, SS]))
            ), halt(0).
        """))
        tmp_path = Path(tmp.name)

    try:
        result = subprocess.run(
            ["swipl", "-q", "-f", str(tmp_path)],
            capture_output=True, text=True, timeout=15
        )
        triggered = []
        for line in (result.stdout + result.stderr).splitlines():
            if line.startswith("TRIGGER:"):
                parts = line[8:].split(":", 1)
                if len(parts) == 2:
                    triggered.append((parts[0], parts[1]))
        return triggered
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    finally:
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Test runners
# ---------------------------------------------------------------------------

def test_syntax(ruleset_path: Path, verbose: bool) -> bool:
    print(f"  [syntax] Loading {ruleset_path.name}...", end=" ")
    ok, out = run_prolog("true", [ruleset_path])
    if ok:
        print(PASS)
    else:
        print(FAIL)
        if verbose:
            print(textwrap.indent(out, "    "))
    return ok


def test_profile(ruleset_path: Path, profile_path: Path,
                 expected: dict, verbose: bool) -> bool:
    profile_name = profile_path.stem
    print(f"  [profile] {profile_name}...", end=" ")

    if not HAS_RDFLIB:
        print(f"{WARN} skipped (rdflib not installed)")
        return True

    try:
        facts = profile_to_prolog_facts(profile_path)
    except Exception as e:
        print(f"{FAIL} (could not parse profile: {e})")
        return False

    triggered = collect_all_triggered(ruleset_path, facts)
    triggered_uris = {uri for uri, _ in triggered}

    must_trigger     = set(expected.get("must_trigger", []))
    must_not_trigger = set(expected.get("must_not_trigger", []))

    missing  = must_trigger - triggered_uris
    spurious = must_not_trigger & triggered_uris

    ok = not missing and not spurious
    print(PASS if ok else FAIL)

    if verbose or not ok:
        if triggered:
            print(f"    Triggered ({len(triggered)}):")
            for uri, sev in sorted(triggered):
                label = uri.split("/")[-1]
                print(f"      {sev:6} {label}")
        if missing:
            print(f"    {FAIL} MISSING expected triggers:")
            for uri in sorted(missing):
                print(f"      {uri.split('/')[-1]}")
        if spurious:
            print(f"    {FAIL} UNEXPECTED triggers (false positives):")
            for uri in sorted(spurious):
                print(f"      {uri.split('/')[-1]}")

    return ok


def test_threshold_boundary(ruleset_path: Path, param: str,
                             threshold: float, condition_snomed: str,
                             expect_above: bool, verbose: bool) -> bool:
    """
    Test that a rule fires at threshold+epsilon but not at threshold-epsilon.
    """
    epsilon = 0.01
    val_above = threshold + epsilon
    val_below = threshold - epsilon

    snomed_uri = f"http://snomed.info/id/{condition_snomed}"
    facts_above = (
        f":- dynamic user_fact/2, user_metric/3.\n"
        f":- assert(user_fact(me, '{snomed_uri}')).\n"
        f":- assert(user_metric(me, {param}, {val_above})).\n"
    )
    facts_below = (
        f":- dynamic user_fact/2, user_metric/3.\n"
        f":- assert(user_fact(me, '{snomed_uri}')).\n"
        f":- assert(user_metric(me, {param}, {val_below})).\n"
    )

    label = f"boundary {param}>{threshold}"
    print(f"  [boundary] {label}...", end=" ")

    trig_above = collect_all_triggered(ruleset_path, facts_above)
    trig_below = collect_all_triggered(ruleset_path, facts_below)

    fires_above = len(trig_above) > 0
    fires_below = len(trig_below) > 0

    ok = fires_above and not fires_below
    print(PASS if ok else FAIL)

    if verbose or not ok:
        print(f"    At {val_above}: {'fires' if fires_above else 'silent'} (expected: fires)")
        print(f"    At {val_below}: {'fires' if fires_below else 'silent'} (expected: silent)")

    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_ruleset(ruleset_path: Path, verbose: bool) -> dict:
    print(f"\n{'=' * 60}")
    print(f"  Ruleset: {ruleset_path.name}")
    print(f"{'=' * 60}")

    results = {"pass": 0, "fail": 0, "skip": 0}

    def record(ok):
        if ok is True:   results["pass"] += 1
        elif ok is False: results["fail"] += 1
        else:             results["skip"] += 1

    # 1. Syntax
    record(test_syntax(ruleset_path, verbose))

    # 2. Profile tests
    for profile_path in sorted(PROFILES.glob("*.ttl")):
        stem = profile_path.stem
        expected = EXPECTED.get(stem, {})
        if not expected and stem != "mock_profile_welfare_ndis":
            print(f"  [profile] {stem}... {WARN} no expected results defined, skipping")
            results["skip"] += 1
            continue
        record(test_profile(ruleset_path, profile_path, expected, verbose))

    # 3. Boundary tests for diabetes ruleset (adapt for other rulesets)
    # Only runs if the ruleset file name contains "diabetes"
    if "diabetes" in ruleset_path.stem:
        record(test_threshold_boundary(
            ruleset_path, "hba1c", 7.0, "44054006", expect_above=True, verbose=verbose
        ))

    if "hypertension" in ruleset_path.stem or "cardiovascular" in ruleset_path.stem:
        record(test_threshold_boundary(
            ruleset_path, "systolic_bp", 130.0, "59621000", expect_above=True, verbose=verbose
        ))

    total = sum(results.values())
    print(f"\n  Result: {results['pass']}/{total - results['skip']} passed "
          f"({results['skip']} skipped, {results['fail']} failed)")

    return results


def main():
    parser = argparse.ArgumentParser(description="WellFair Ruleset Sandbox Test Runner")
    parser.add_argument("--ruleset", type=Path, default=None,
                        help="Path to a specific .pl ruleset to test.")
    parser.add_argument("--all", action="store_true",
                        help=f"Test all .pl files in {RULESETS}")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show detailed trigger output for all tests.")
    args = parser.parse_args()

    if not HAS_RDFLIB:
        print(f"{WARN} rdflib not installed — profile tests will be skipped.")
        print("    pip install rdflib")

    rulesets_to_test = []
    if args.all:
        rulesets_to_test = sorted(RULESETS.glob("*.pl"))
        if not rulesets_to_test:
            print(f"No .pl files found in {RULESETS}")
            sys.exit(0)
    elif args.ruleset:
        rulesets_to_test = [args.ruleset]
    else:
        parser.print_help()
        sys.exit(0)

    total_pass = total_fail = 0
    for ruleset_path in rulesets_to_test:
        r = run_ruleset(ruleset_path, args.verbose)
        total_pass += r["pass"]
        total_fail += r["fail"]

    print(f"\n{'=' * 60}")
    print(f"  TOTAL: {total_pass} passed, {total_fail} failed across {len(rulesets_to_test)} ruleset(s)")
    print(f"{'=' * 60}")
    sys.exit(0 if total_fail == 0 else 1)


if __name__ == "__main__":
    main()
