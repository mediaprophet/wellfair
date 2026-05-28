# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# https://www.linkedin.com/in/ubiquitous/
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Template-driven RDF: schema.org + QUDT + PROV-O + optional SNOMED/LOINC/FHIR."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

from src.normalizer import minutes_to_iso_duration, ms_to_aware_datetime
from src.utils import clean_column_name, data_type_from_filename, safe_str

CLINICAL_PREFIXES = frozenset({"snomed", "loinc", "fhir"})


@dataclass
class TransformOptions:
    """Runtime options for RDF generation."""

    clinical_mode: bool = True
    include_provenance: bool = True
    export_label: str = "Samsung Health CSV export"


class OntologyTemplate:
    """Load and expose ontology_template.yaml."""

    def __init__(self, template_path: str | Path):
        self.path = Path(template_path)
        self.reload()

    def reload(self) -> None:
        with self.path.open(encoding="utf-8") as f:
            self.raw = yaml.safe_load(f) or {}
        self.namespaces: dict[str, str] = self.raw.get("namespaces", {})
        self.mappings: dict[str, Any] = self.raw.get("mappings", {})
        self.default_subject = self.raw.get(
            "default_subject_template", "urn:health:{data_type}:{uuid}"
        )
        self.provenance_cfg: dict[str, Any] = self.raw.get("provenance", {})
        self.unit_aliases: dict[str, str] = self.raw.get("unit_aliases", {})
        self.ontology_modes: dict[str, Any] = self.raw.get("ontology_modes", {})
        self.mapping_aliases: dict[str, str] = self.raw.get("mapping_aliases", {})

    def resolve_mapping(self, data_type: str) -> tuple[str, dict[str, Any] | None]:
        """Return canonical data type key and mapping (via aliases)."""
        if data_type in self.mappings:
            return data_type, self.mappings[data_type]
        canonical = self.mapping_aliases.get(data_type)
        if canonical and canonical in self.mappings:
            return canonical, self.mappings[canonical]
        return data_type, None

    def bind_namespaces(self, graph: Graph) -> None:
        for prefix, uri in self.namespaces.items():
            graph.bind(prefix, Namespace(uri), override=True)

    def clinical_references_enabled(self, options: TransformOptions) -> bool:
        if options.clinical_mode:
            return True
        mode = self.ontology_modes.get("clinical", {})
        return bool(mode.get("include_clinical_references", False))


def _expand_subject(template: str, row: dict[str, Any], data_type: str) -> str:
    uuid = (
        safe_str(row.get("uuid"))
        or safe_str(row.get("datauuid"))
        or safe_str(row.get("custom"))
        or "unknown"
    )
    return template.format(
        data_type=data_type.split(".")[-1] if "." in data_type else data_type,
        uuid=uuid,
    )


def resolve_uri(term: str, ns_map: dict[str, Namespace]) -> URIRef:
    """
    Resolve prefixed CURIE (schema:Person), bare local with health default,
    or full http(s) URI.
    """
    term = str(term).strip()
    if term.startswith(("http://", "https://", "urn:")):
        return URIRef(term)
    if ":" not in term:
        if "health" in ns_map:
            return URIRef(str(ns_map["health"]) + term)
        raise ValueError(f"Cannot resolve bare term: {term}")
    prefix, local = term.split(":", 1)
    if prefix not in ns_map:
        raise KeyError(f"Unknown namespace prefix: {prefix}")
    base = str(ns_map[prefix])
    if base.endswith("#") or base.endswith("/"):
        return URIRef(base + local)
    return URIRef(f"{base}{local}")


def resolve_unit_uri(
    unit: str,
    ns_map: dict[str, Namespace],
    unit_aliases: dict[str, str],
) -> URIRef | None:
    """Map qudt-unit:Kilogram, qudt:KGM, or KGM alias to QUDT vocab unit URI."""
    if not unit:
        return None
    unit = str(unit).strip()

    if unit.startswith(("http://", "https://")):
        return URIRef(unit)

    if ":" in unit:
        prefix, local = unit.split(":", 1)
        if prefix in ("qudt-unit", "qudt"):
            vocab = ns_map.get("qudt-unit") or ns_map.get("qudt")
            if vocab:
                return URIRef(str(vocab) + local)
        return resolve_uri(unit, ns_map)

    local = unit_aliases.get(unit.upper(), unit)
    vocab = ns_map.get("qudt-unit")
    if vocab:
        return URIRef(str(vocab) + local)
    return None


def _apply_transform(
    transform: str | None,
    value: Any,
    row: dict[str, Any],
    prop_cfg: dict[str, Any],
) -> Any:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if not transform:
        return value

    if transform == "unix_ms_to_iso_with_offset":
        col = prop_cfg.get("source_column")
        ms = row.get(col) if col else value
        dt = ms_to_aware_datetime(ms, row.get("time_offset"))
        return dt.isoformat() if dt else None

    if transform == "minutes_to_iso_duration":
        return minutes_to_iso_duration(value)

    return value


def _literal_for_value(value: Any, prop_cfg: dict[str, Any]) -> Literal | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return Literal(value.isoformat(), datatype=XSD.dateTime)
    if isinstance(value, bool):
        return Literal(value, datatype=XSD.boolean)
    if isinstance(value, int):
        return Literal(value, datatype=XSD.integer)
    if isinstance(value, float):
        return Literal(value, datatype=XSD.decimal)
    return Literal(str(value))


def _add_clinical_reference(
    g: Graph,
    subj: URIRef,
    prop_cfg: dict[str, Any],
    ns_map: dict[str, Namespace],
) -> None:
    """Emit health:semanticReference links to FHIR / SNOMED / LOINC URIs."""
    ref_pred = URIRef(str(ns_map["health"]) + "semanticReference")
    for key in ("fhir_reference", "snomed_reference", "loinc_reference"):
        ref = prop_cfg.get(key)
        if not ref:
            continue
        try:
            target = resolve_uri(str(ref), ns_map)
        except (KeyError, ValueError):
            continue
        g.add((subj, ref_pred, target))
        g.add((target, RDF.type, URIRef(str(ns_map["health"]) + "InteroperabilityLink")))


def _add_provenance(
    g: Graph,
    subj: URIRef,
    template: OntologyTemplate,
    options: TransformOptions,
    ns_map: dict[str, Namespace],
) -> None:
    if not options.include_provenance:
        return
    prov = template.provenance_cfg
    if not prov:
        return

    derived = prov.get("was_derived_from", "urn:health:source:samsung-health-export")
    g.add((subj, URIRef(str(ns_map["prov"]) + "wasDerivedFrom"), URIRef(derived)))
    g.add(
        (
            subj,
            URIRef(str(ns_map["prov"]) + "wasGeneratedBy"),
            URIRef(f"urn:health:agent:{prov.get('generator', 'health-to-solid')}"),
        ),
    )
    label = prov.get("source_label") or options.export_label
    g.add((subj, URIRef(str(ns_map["schema"]) + "description"), Literal(label)))


def _add_type_level_clinical(
    g: Graph,
    subj: URIRef,
    mapping: dict[str, Any],
    ns_map: dict[str, Namespace],
) -> None:
    concept = mapping.get("snomed_concept")
    if concept:
        try:
            concept_uri = resolve_uri(str(concept), ns_map)
            g.add((subj, URIRef(str(ns_map["health"]) + "snomedConcept"), concept_uri))
        except (KeyError, ValueError):
            pass
    loinc = mapping.get("loinc_concept")
    if loinc:
        try:
            loinc_uri = resolve_uri(str(loinc), ns_map)
            g.add((subj, URIRef(str(ns_map["health"]) + "loincConcept"), loinc_uri))
        except (KeyError, ValueError):
            pass


def _add_qudt_value_bundle(
    g: Graph,
    subj: URIRef,
    pred: URIRef,
    lit: Literal,
    unit_uri: URIRef | None,
    ns_map: dict[str, Namespace],
) -> None:
    """Attach value literal and QUDT unit on subject (schema.org + QUDT pattern)."""
    g.add((subj, pred, lit))
    if unit_uri is None:
        return
    qudt_unit_pred = URIRef(str(ns_map.get("qudt", Namespace("http://qudt.org/schema/qudt/"))) + "unit")
    g.add((subj, qudt_unit_pred, unit_uri))
    if "schema" in ns_map:
        g.add((subj, URIRef(str(ns_map["schema"]) + "unitCode"), Literal(str(unit_uri).split("/")[-1])))


def rows_from_dataframe(df: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for _, series in df.iterrows():
        row = {clean_column_name(k): v for k, v in series.items()}
        rows.append(row)
    return rows


def graph_for_data_type(
    template: OntologyTemplate,
    data_type: str,
    df: pd.DataFrame,
    options: TransformOptions | None = None,
) -> Graph:
    """Build RDF graph for one data type using template mapping."""
    options = options or TransformOptions()
    _canonical, mapping = template.resolve_mapping(data_type)
    if not mapping:
        return Graph()

    g = Graph()
    template.bind_namespaces(g)
    ns_map = {p: Namespace(u) for p, u in template.namespaces.items()}
    clinical = template.clinical_references_enabled(options)

    rdf_type = mapping.get("rdf_type", "schema:Thing")
    type_uri = resolve_uri(str(rdf_type), ns_map)
    also_type = mapping.get("schema_also_type")
    subject_tpl = mapping.get("subject") or template.default_subject
    props: dict[str, Any] = mapping.get("properties", {})

    for row in rows_from_dataframe(df):
        subj_str = _expand_subject(subject_tpl, row, data_type)
        subj = URIRef(subj_str)
        g.add((subj, RDF.type, type_uri))
        if also_type:
            g.add((subj, RDF.type, resolve_uri(str(also_type), ns_map)))

        label = mapping.get("label")
        if label:
            g.add((subj, URIRef(str(ns_map["schema"]) + "name"), Literal(label)))

        if clinical:
            _add_type_level_clinical(g, subj, mapping, ns_map)

        _add_provenance(g, subj, template, options, ns_map)

        for col_key, prop_cfg in props.items():
            if isinstance(prop_cfg, str):
                prop_cfg = {"predicate": prop_cfg}
            pred_s = prop_cfg.get("predicate")
            if not pred_s:
                continue

            col = clean_column_name(col_key)
            raw = row.get(col)
            if raw is None or (isinstance(raw, float) and pd.isna(raw)):
                continue

            transform = prop_cfg.get("transform")
            value = _apply_transform(
                transform, raw, row, {**prop_cfg, "source_column": col}
            )
            if value is None:
                continue

            lit = _literal_for_value(value, prop_cfg)
            if lit is None:
                continue

            pred = resolve_uri(str(pred_s), ns_map)
            unit_uri = resolve_unit_uri(
                prop_cfg.get("unit", ""),
                ns_map,
                template.unit_aliases,
            )
            _add_qudt_value_bundle(g, subj, pred, lit, unit_uri, ns_map)

            if clinical:
                _add_clinical_reference(g, subj, prop_cfg, ns_map)

    return g


def transform_export(
    normalized: dict[str, Any],
    template_path: str | Path,
    progress: bool = False,
    options: TransformOptions | None = None,
) -> dict[str, Graph]:
    """Transform all normalized dataframes into per-data-type graphs."""
    template = OntologyTemplate(template_path)
    options = options or TransformOptions()
    graphs: dict[str, Graph] = {}

    items = list(normalized.get("dataframes", {}).items())
    iterator = items
    if progress:
        from tqdm import tqdm

        iterator = tqdm(items, desc="RDF transform")

    for filename, df in iterator:
        data_type = data_type_from_filename(filename)
        g = graph_for_data_type(template, data_type, df, options)
        if len(g):
            graphs[data_type] = g

    return graphs


def merge_graphs(graphs: dict[str, Graph]) -> Graph:
    merged = Graph()
    for g in graphs.values():
        for t in g:
            merged.add(t)
    return merged


def graph_to_jsonld(graph: Graph, indent: int = 2) -> str:
    """Serialize graph to JSON-LD string."""
    try:
        data = json.loads(graph.serialize(format="json-ld"))
        return json.dumps(data, indent=indent, default=str)
    except Exception:
        return json.dumps({"@context": {}, "@graph": []}, indent=indent)


def count_clinical_triples(graph: Graph) -> dict[str, int]:
    """Count triples touching SNOMED / LOINC / FHIR / QUDT namespaces."""
    counts = {"snomed": 0, "loinc": 0, "fhir": 0, "qudt": 0, "health_ref": 0}
    markers = {
        "snomed": "snomed.info",
        "loinc": "loinc.org",
        "fhir": "hl7.org/fhir",
        "qudt": "qudt.org",
    }
    health_sem = "semanticReference"
    for s, p, o in graph:
        for key, fragment in markers.items():
            if fragment in str(s) or fragment in str(o) or fragment in str(p):
                counts[key] += 1
        if health_sem in str(p):
            counts["health_ref"] += 1
    return counts


def load_template(template_path: str | Path) -> OntologyTemplate:
    return OntologyTemplate(template_path)
