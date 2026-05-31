/**
 * WellFair Capability Definitions
 * ==================================
 * Maps feature names to required capability tokens.
 * Both the JavaScript layer and the Python/Streamlit layer use this mapping
 * (via the window.wellfairPackageState bridge) to gate UI sections.
 *
 * A feature is available when ALL its required capability tokens are present
 * in the active capability set.
 */

// Canonical capability tokens — each provided by exactly one package
export const CAP = Object.freeze({
  CORE_RDF:         "core:rdf",
  CORE_SPARQL:      "core:sparql",
  REASONING_PROLOG: "reasoning:prolog",
  REASONING_N3:     "reasoning:n3",       // EYE — server-side only
  LLM_INFERENCE:    "llm:inference",
  LLM_EXTRACTION:   "llm:extraction",
  LLM_EXPLANATION:  "llm:explanation",
});

// Feature → required capability tokens.
// An empty array means the feature requires no optional packages.
export const FEATURE_REQUIREMENTS = Object.freeze({
  // Base features — no extra packages
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

  // Needs RDF/SPARQL — bundled in wellfare-core, always available
  "pathology":               [CAP.CORE_SPARQL],
  "sparql-query":            [CAP.CORE_SPARQL],

  // Needs Prolog WASM (~8 MB, on-demand download)
  "differential-diagnosis":  [CAP.CORE_SPARQL, CAP.REASONING_PROLOG],
  "welfare-eligibility":     [CAP.CORE_SPARQL, CAP.REASONING_PROLOG],
  "anatomy-3d-reasoning":    [CAP.CORE_SPARQL, CAP.REASONING_PROLOG],

  // Needs LLM (~5 MB runtime + ~1.3 GB model, on-demand)
  "document-ingestion":      [CAP.LLM_EXTRACTION],
  "paper-extraction":        [CAP.LLM_EXTRACTION],
  "explanation-sidebar":     [CAP.LLM_EXPLANATION],

  // Needs both Prolog and LLM
  "study-vault":             [CAP.LLM_EXTRACTION, CAP.REASONING_PROLOG],

  // Server-side only (local Streamlit desktop install)
  "n3-patterns":             [CAP.REASONING_N3],
});

// Navigation section key → feature key.
// Used by the sidebar to determine which items to show or dim.
export const NAV_SECTION_FEATURES = Object.freeze({
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
  "packages":          "profile-view",  // always accessible
});
