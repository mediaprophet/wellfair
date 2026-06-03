#!/usr/bin/env python3
"""
WellFair Rule Compiler (Stage B2)
==================================
Transforms a validated extraction JSON (from the LLM paper-parser) into:
  1. <ruleset_id>.ttl  — Turtle provenance metadata (source, authorship, implication graph)
  2. <ruleset_id>.pl   — SWI-Prolog Horn clauses ready for consult() in WASM

Usage:
    python compile_ruleset.py <extraction.json> [--output-dir ./rulesets] [--id my_ruleset_id]

The output .pl file is deterministic given the same input JSON — safe to diff and version-control.
The output .ttl file links each Prolog clause back to the source study and FMA targets.
"""

import argparse
import json
import re
import sys
import textwrap
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# URI resolution helpers
# ---------------------------------------------------------------------------

FMA_BASE    = "http://purl.org/sig/ont/fma/"
SNOMED_BASE = "http://snomed.info/id/"
HP_BASE     = "http://purl.obolibrary.org/obo/HP_"
WELFARE_BASE = "https://wellfair.app/welfare/"

OPERATOR_MAP = {
    "greater_than":       ">",
    "less_than":          "<",
    "greater_than_equal": ">=",
    "less_than_equal":    "=<",   # SWI-Prolog uses =< not <=
    "equals":             "=:=",
    "between":            None,   # handled separately
}


def resolve_uri(prefixed: str) -> str:
    """Expand a prefixed URI string to its full IRI."""
    if prefixed == "unresolved":
        raise ValueError("URI is unresolved — expert must fix before compiling.")
    if prefixed.startswith("snomed:"):
        return SNOMED_BASE + prefixed[7:]
    if prefixed.startswith("fma:"):
        return FMA_BASE + prefixed[4:]
    if prefixed.startswith("hp:"):
        return HP_BASE + prefixed[3:]
    if prefixed.startswith("welfare:"):
        return WELFARE_BASE + prefixed[8:]
    # Already a full URI
    if prefixed.startswith("http"):
        return prefixed
    raise ValueError(f"Cannot resolve URI prefix: {prefixed!r}")


def safe_atom(uri: str) -> str:
    """Wrap a URI in single quotes for use as a Prolog atom."""
    return f"'{uri}'"


def slugify(text: str) -> str:
    """Convert text to a safe snake_case identifier."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


# ---------------------------------------------------------------------------
# Prolog clause generation
# ---------------------------------------------------------------------------

def build_trigger_body(triggers: list[dict]) -> list[str]:
    """
    Convert biomarker_triggers list into Prolog body goals.
    All triggers are ANDed (comma-separated in the clause body).
    """
    goals = []
    for t in triggers:
        param = t["prolog_param"]
        op    = t["operator"]
        val   = t["value"]

        if op == "between":
            val_upper = t.get("value_upper")
            if val_upper is None:
                raise ValueError(f"'between' operator requires value_upper for param '{param}'")
            goals.append(f"    user_metric(User, {param}, _V_{param})")
            goals.append(f"    _V_{param} >= {val}")
            goals.append(f"    _V_{param} =< {val_upper}")
        else:
            prolog_op = OPERATOR_MAP.get(op)
            if prolog_op is None:
                raise ValueError(f"Unknown operator: {op!r}")
            # Use a unique variable name per param to avoid conflicts
            var = f"_V_{param}"
            goals.append(f"    user_metric(User, {param}, {var})")
            goals.append(f"    {var} {prolog_op} {val}")

    return goals


def compile_implication_to_clauses(impl: dict, ruleset_id: str, study_doi: str) -> list[str]:
    """
    Generate one or more Prolog clauses for a single logical_implication block.
    Returns a list of clause strings.
    """
    clauses = []
    impl_id         = impl["implication_id"]
    condition_uri   = resolve_uri(impl["condition_indicated"])
    triggers        = impl.get("biomarker_triggers", [])
    structures      = impl.get("affected_anatomical_structures", [])
    entitlements    = impl.get("affected_entitlements", [])
    comorbidities   = impl.get("comorbidity_modifiers", [])

    # -- one clause per affected anatomical structure -----------------------
    for struct in structures:
        fma_raw  = struct["fma_uri"]
        severity = struct["severity_weight"]
        is_hier  = struct.get("is_hierarchy_target", False)

        try:
            fma_uri = resolve_uri(fma_raw)
        except ValueError as e:
            clauses.append(f"% SKIPPED {impl_id} → {fma_raw}: {e}")
            continue

        head = (
            f"implication_target(User, {safe_atom(fma_uri)}, {safe_atom(severity)})"
        )

        body_goals = [f"    user_fact(User, {safe_atom(condition_uri)})"]

        if triggers:
            trigger_goals = build_trigger_body(triggers)
            body_goals.extend(trigger_goals)

        # Hierarchy traversal flag — stored as metadata, not logic
        # (SPARQL resolver handles traversal; Prolog targets exact URIs)
        hier_comment = "  % hierarchy traversal required in SPARQL resolver" if is_hier else ""

        body = ",\n".join(body_goals) + "."

        clause = (
            f"% {impl_id} | source: {study_doi}{hier_comment}\n"
            f"{head} :-\n"
            f"{body}"
        )
        clauses.append(clause)

        # -- comorbidity modifier escalation clauses -------------------------
        for comorbid in comorbidities:
            comorbid_uri = resolve_uri(comorbid["condition_uri"])
            escalated    = comorbid["escalates_to"]
            affected_uris = comorbid.get("affected_uris", [])

            # Only generate escalation clause if this FMA URI is in scope
            if affected_uris and fma_uri not in [resolve_uri(u) for u in affected_uris]:
                continue

            esc_head = (
                f"implication_target(User, {safe_atom(fma_uri)}, {safe_atom(escalated)})"
            )
            esc_body_goals = [
                f"    user_fact(User, {safe_atom(condition_uri)})",
                f"    user_fact(User, {safe_atom(comorbid_uri)})",
            ]
            if triggers:
                esc_body_goals.extend(build_trigger_body(triggers))

            esc_body = ",\n".join(esc_body_goals) + "."
            esc_clause = (
                f"% {impl_id}_comorbid_escalation | comorbidity: {comorbid['condition_uri']}\n"
                f"{esc_head} :-\n"
                f"{esc_body}"
            )
            clauses.append(esc_clause)

    # -- welfare entitlement clauses ----------------------------------------
    for ent in entitlements:
        ent_uri = resolve_uri(ent["entitlement_uri"])
        ent_display = ent["entitlement_display"]

        head = f"entitlement_triggered(User, {safe_atom(ent_uri)})"
        body_goals = [f"    user_fact(User, {safe_atom(condition_uri)})"]
        if triggers:
            body_goals.extend(build_trigger_body(triggers))

        body = ",\n".join(body_goals) + "."
        clause = (
            f"% {impl_id} welfare | '{ent_display}'\n"
            f"{head} :-\n"
            f"{body}"
        )
        clauses.append(clause)

    return clauses


# ---------------------------------------------------------------------------
# Prolog file generation
# ---------------------------------------------------------------------------

def generate_prolog(data: dict, ruleset_id: str) -> str:
    meta      = data["study_metadata"]
    doi       = meta.get("doi_or_url") or "unknown"
    title     = meta.get("title", "Untitled")
    authors   = ", ".join(meta.get("authors") or []) or "Unknown"
    year      = meta.get("publication_year") or "?"
    journal   = meta.get("journal_or_source") or "?"
    domain    = meta.get("domain", "biomedical")

    lines = [
        f"% {'=' * 72}",
        f"% WellFair Ruleset: {ruleset_id}",
        f"% {'=' * 72}",
        f"% Title:   {title}",
        f"% Authors: {authors}",
        f"% Year:    {year}",
        f"% Journal: {journal}",
        f"% Domain:  {domain}",
        f"% Source:  {doi}",
        f"% Generated: {date.today().isoformat()}",
        f"% DO NOT EDIT — generated by WellFair Rule Compiler v1.0",
        f"% {'=' * 72}",
        "",
        ":- discontiguous implication_target/3.",
        ":- discontiguous entitlement_triggered/2.",
        "",
    ]

    for impl in data.get("logical_implications", []):
        try:
            clauses = compile_implication_to_clauses(impl, ruleset_id, doi)
        except ValueError as e:
            lines.append(f"% ERROR in implication '{impl.get('implication_id', '?')}': {e}")
            continue
        lines.append(f"% --- {impl['implication_id']} ---")
        lines.extend(clauses)
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Turtle provenance file generation
# ---------------------------------------------------------------------------

TTL_PREFIXES = """\
@prefix rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:    <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:     <http://www.w3.org/2001/XMLSchema#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix fma:     <http://purl.org/sig/ont/fma/> .
@prefix snomed:  <http://snomed.info/id/> .
@prefix hp:      <http://purl.obolibrary.org/obo/HP_> .
@prefix app:     <https://wellfair.app/ontology/> .
@prefix cond:    <https://wellfair.app/condition/> .
@prefix rs:      <https://wellfair.app/ruleset/> .
"""


def _ttl_str(val: str) -> str:
    escaped = val.replace('"', '\\"')
    return f'"{escaped}"'


def _ttl_uri(uri: str) -> str:
    return f"<{uri}>"


def generate_turtle(data: dict, ruleset_id: str, pl_filename: str) -> str:
    meta    = data["study_metadata"]
    doi     = meta.get("doi_or_url") or ""
    title   = meta.get("title", "Untitled")
    authors = meta.get("authors") or []
    year    = meta.get("publication_year")
    journal = meta.get("journal_or_source") or ""
    domain  = meta.get("domain", "biomedical")

    rs_uri = f"https://wellfair.app/ruleset/{ruleset_id}"

    lines = [TTL_PREFIXES, ""]
    lines.append(f"# {'=' * 70}")
    lines.append(f"# Ruleset: {ruleset_id}")
    lines.append(f"# {'=' * 70}")
    lines.append("")

    # Ruleset resource
    lines.append(f"<{rs_uri}>")
    lines.append(f"    a app:Ruleset ;")
    lines.append(f"    rdfs:label {_ttl_str(title)} ;")
    if doi:
        lines.append(f"    dcterms:source <{doi}> ;")
    if year:
        lines.append(f"    dcterms:created {_ttl_str(str(year))}^^xsd:gYear ;")
    if journal:
        lines.append(f"    dcterms:publisher {_ttl_str(journal)} ;")
    lines.append(f"    app:domain {_ttl_str(domain)} ;")
    lines.append(f"    app:prologFile {_ttl_str(pl_filename)} ;")
    for author in authors:
        lines.append(f"    dcterms:creator {_ttl_str(author)} ;")
    lines.append(f"    dcterms:modified {_ttl_str(date.today().isoformat())}^^xsd:date .")
    lines.append("")

    # One ClinicalImplication resource per (implication_id, structure) pair
    for impl in data.get("logical_implications", []):
        impl_id       = impl["implication_id"]
        condition_raw = impl["condition_indicated"]
        structures    = impl.get("affected_anatomical_structures", [])
        entitlements  = impl.get("affected_entitlements", [])
        citation_frag = impl.get("citation_fragment")

        try:
            condition_uri = resolve_uri(condition_raw)
        except ValueError:
            lines.append(f"# SKIPPED {impl_id}: unresolved condition URI")
            continue

        for struct in structures:
            fma_raw  = struct["fma_uri"]
            severity = struct["severity_weight"]
            mechanism = struct.get("mechanism_summary") or ""
            is_hier  = struct.get("is_hierarchy_target", False)

            try:
                fma_uri = resolve_uri(fma_raw)
            except ValueError:
                lines.append(f"# SKIPPED {impl_id} → {fma_raw}: unresolved FMA URI")
                continue

            impl_res = f"cond:{impl_id}_{slugify(fma_raw)}"
            lines.append(f"{impl_res}")
            lines.append(f"    a app:ClinicalImplication ;")
            lines.append(f"    rdfs:label {_ttl_str(f'{impl_id} → {fma_raw}')} ;")
            lines.append(f"    app:forCondition {_ttl_uri(condition_uri)} ;")
            lines.append(f"    app:impliesPathologyIn {_ttl_uri(fma_uri)} ;")
            lines.append(f"    app:severityWeight {_ttl_str(severity)} ;")
            if mechanism:
                lines.append(f"    app:mechanismSummary {_ttl_str(mechanism)} ;")
            if citation_frag:
                lines.append(f"    app:citationFragment {_ttl_str(citation_frag)} ;")
            if is_hier:
                lines.append(f"    app:requiresHierarchyTraversal true ;")
            lines.append(f"    app:inRuleset <{rs_uri}> .")
            lines.append("")

        for ent in entitlements:
            ent_raw     = ent["entitlement_uri"]
            ent_display = ent["entitlement_display"]
            ent_notes   = ent.get("eligibility_notes") or ""

            try:
                ent_uri = resolve_uri(ent_raw)
            except ValueError:
                lines.append(f"# SKIPPED {impl_id} entitlement {ent_raw}: unresolved URI")
                continue

            impl_res = f"cond:{impl_id}_{slugify(ent_raw)}"
            lines.append(f"{impl_res}")
            lines.append(f"    a app:WelfareImplication ;")
            lines.append(f"    rdfs:label {_ttl_str(ent_display)} ;")
            lines.append(f"    app:forCondition {_ttl_uri(condition_uri)} ;")
            lines.append(f"    app:triggersEntitlement {_ttl_uri(ent_uri)} ;")
            if ent_notes:
                lines.append(f"    app:eligibilityNotes {_ttl_str(ent_notes)} ;")
            lines.append(f"    app:inRuleset <{rs_uri}> .")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Compile a WellFair extraction JSON into .pl + .ttl ruleset files."
    )
    parser.add_argument("extraction_json", type=Path, help="Path to the validated extraction JSON file.")
    parser.add_argument("--output-dir", type=Path, default=Path("../../rulesets"),
                        help="Directory to write output files (default: ../../rulesets)")
    parser.add_argument("--id", dest="ruleset_id", type=str, default=None,
                        help="Ruleset identifier (snake_case). Derived from filename if omitted.")
    args = parser.parse_args()

    # Load and validate JSON
    if not args.extraction_json.exists():
        print(f"ERROR: File not found: {args.extraction_json}", file=sys.stderr)
        sys.exit(1)

    with open(args.extraction_json, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)

    # Check schema version
    if data.get("schema_version") != "1.0":
        print("WARNING: schema_version is not '1.0'. Proceeding anyway.", file=sys.stderr)

    # Determine ruleset ID
    ruleset_id = args.ruleset_id
    if not ruleset_id:
        # Derive from filename: my_extraction.json → my_extraction
        ruleset_id = slugify(args.extraction_json.stem)
    if not re.match(r"^[a-z0-9_]+$", ruleset_id):
        print(f"ERROR: Ruleset ID must be snake_case alphanumeric: {ruleset_id!r}", file=sys.stderr)
        sys.exit(1)

    # Ensure output dir exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    pl_filename  = f"{ruleset_id}.pl"
    ttl_filename = f"{ruleset_id}.ttl"
    pl_path      = args.output_dir / pl_filename
    ttl_path     = args.output_dir / ttl_filename

    # Generate
    print(f"Compiling: {args.extraction_json} → {ruleset_id}.{{pl,ttl}}")

    try:
        prolog_src = generate_prolog(data, ruleset_id)
        turtle_src = generate_turtle(data, ruleset_id, pl_filename)
    except Exception as e:
        print(f"ERROR during compilation: {e}", file=sys.stderr)
        sys.exit(1)

    pl_path.write_text(prolog_src, encoding="utf-8")
    ttl_path.write_text(turtle_src, encoding="utf-8")

    impl_count = len(data.get("logical_implications", []))
    struct_count = sum(
        len(i.get("affected_anatomical_structures", []))
        for i in data.get("logical_implications", [])
    )
    ent_count = sum(
        len(i.get("affected_entitlements", []))
        for i in data.get("logical_implications", [])
    )

    print(f"  Written: {pl_path}")
    print(f"  Written: {ttl_path}")
    print(f"  Implications: {impl_count} | Anatomical targets: {struct_count} | Entitlements: {ent_count}")
    print("Done.")


if __name__ == "__main__":
    main()
