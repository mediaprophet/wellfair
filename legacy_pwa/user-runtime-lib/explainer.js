/**
 * WellFair Explainer Module (Stage C5)
 * ======================================
 * Translates a merged implication entry into a plain-English explanation
 * for display in the 3D viewer's click-to-explain sidebar.
 *
 * Inputs per explanation request:
 *   - The MergedImplication for the clicked anatomical URI
 *   - The parsed ruleset TTL metadata (mechanism summaries, citations)
 *   - Optionally: the local LLM for rewriting mechanism summaries
 *
 * Output:
 *   ExplanationCard — structured object rendered by the sidebar UI
 *
 * The study citation is ALWAYS verbatim from the signed .ttl metadata.
 * The mechanism summary MAY be lightly rewritten by the local LLM for
 * readability, but the source text is preserved separately.
 */

// FMA URI → human-readable anatomical name (local fallback dictionary)
// The resolver should prefer rdfs:label from anatomy-mappings.ttl when available.
const FMA_LABELS = {
  "http://purl.org/sig/ont/fma/Heart":                "Heart",
  "http://purl.org/sig/ont/fma/Left_kidney":          "Left Kidney",
  "http://purl.org/sig/ont/fma/Right_kidney":         "Right Kidney",
  "http://purl.org/sig/ont/fma/Left_renal_artery":    "Left Renal Artery",
  "http://purl.org/sig/ont/fma/Right_renal_artery":   "Right Renal Artery",
  "http://purl.org/sig/ont/fma/Retina":               "Retina",
  "http://purl.org/sig/ont/fma/Pancreas":             "Pancreas",
  "http://purl.org/sig/ont/fma/Brain":                "Brain",
  "http://purl.org/sig/ont/fma/Cerebral_cortex":      "Cerebral Cortex",
  "http://purl.org/sig/ont/fma/Aorta":                "Aorta",
  "http://purl.org/sig/ont/fma/Left_coronary_artery": "Left Coronary Artery",
  "http://purl.org/sig/ont/fma/Right_coronary_artery":"Right Coronary Artery",
  "http://purl.org/sig/ont/fma/Spinal_cord":          "Spinal Cord",
  "http://purl.org/sig/ont/fma/Vertebral_column":     "Vertebral Column",
  "http://purl.org/sig/ont/fma/Left_shoulder_joint":  "Left Shoulder Joint",
  "http://purl.org/sig/ont/fma/Right_shoulder_joint": "Right Shoulder Joint",
  "http://purl.org/sig/ont/fma/Left_hip_joint":       "Left Hip Joint",
  "http://purl.org/sig/ont/fma/Right_hip_joint":      "Right Hip Joint",
  "http://purl.org/sig/ont/fma/Left_knee_joint":      "Left Knee Joint",
  "http://purl.org/sig/ont/fma/Right_knee_joint":     "Right Knee Joint",
  "http://purl.org/sig/ont/fma/Left_ankle_joint":     "Left Ankle Joint",
  "http://purl.org/sig/ont/fma/Right_ankle_joint":    "Right Ankle Joint",
  "http://purl.org/sig/ont/fma/Left_wrist_joint":     "Left Wrist Joint",
  "http://purl.org/sig/ont/fma/Right_wrist_joint":    "Right Wrist Joint",
  "http://purl.org/sig/ont/fma/Pelvic_diaphragm":     "Pelvic Floor",
  "http://purl.org/sig/ont/fma/Thyroid_gland":        "Thyroid Gland",
  "http://purl.org/sig/ont/fma/Left_adrenal_gland":   "Left Adrenal Gland",
  "http://purl.org/sig/ont/fma/Right_adrenal_gland":  "Right Adrenal Gland",
  "http://purl.org/sig/ont/fma/Left_lung":            "Left Lung",
  "http://purl.org/sig/ont/fma/Right_lung":           "Right Lung",
  "http://purl.org/sig/ont/fma/Cardiovascular_system":"Cardiovascular System",
  "http://purl.org/sig/ont/fma/Stomach":              "Stomach",
  "http://purl.org/sig/ont/fma/Large_intestine":      "Large Intestine",
  "http://purl.org/sig/ont/fma/Liver":                "Liver",
  "http://purl.org/sig/ont/fma/Gallbladder":          "Gallbladder",
  "http://purl.org/sig/ont/fma/Lymph_node":           "Lymph Node",
};

const SEVERITY_LABELS = {
  high:   { label: "High Implication",   color: "#ff4444", icon: "⚠" },
  medium: { label: "Medium Implication", color: "#ffaa00", icon: "◈" },
  low:    { label: "Low Implication",    color: "#ffffaa", icon: "◇" },
};

const DISCLAIMER =
  "This is an automated evaluation against published research, not a clinical " +
  "diagnosis or medical advice. Discuss any findings with a qualified health professional.";


/**
 * Minimal TTL parser — extracts key literal values from a ruleset .ttl string.
 * A full RDF parser (N3.js) should be used in production.
 * This handles the specific output format of compile_ruleset.py.
 *
 * @param {string} ttlText
 * @param {string} anatomyUri - Full FMA URI to find implications for
 * @returns {Array<{title, doi, year, journal, authors, mechanism, citation}>}
 */
function extractFromTtl(ttlText, anatomyUri) {
  const results = [];
  const fmaShort = anatomyUri.split("/").pop();  // e.g. "Left_renal_artery"

  // Match ClinicalImplication blocks that reference this FMA URI
  const implBlockRe = new RegExp(
    `cond:[^\\s]+\\s[\\s\\S]*?app:impliesPathologyIn\\s+<${escapeRegex(anatomyUri)}>` +
    `[\\s\\S]*?app:inRuleset\\s+<([^>]+)>\\s*\\.`,
    "g"
  );

  // Ruleset-level metadata
  const titleMatch      = ttlText.match(/rdfs:label\s+"([^"]+)"\s*;/);
  const doiMatch        = ttlText.match(/dcterms:source\s+<([^>]+)>/);
  const yearMatch       = ttlText.match(/dcterms:created\s+"(\d{4})"/);
  const journalMatch    = ttlText.match(/dcterms:publisher\s+"([^"]+)"/);
  const authorMatches   = [...ttlText.matchAll(/dcterms:creator\s+"([^"]+)"/g)];

  const title   = titleMatch?.[1]   ?? "Unknown Study";
  const doi     = doiMatch?.[1]     ?? null;
  const year    = yearMatch?.[1]    ?? null;
  const journal = journalMatch?.[1] ?? null;
  const authors = authorMatches.map(m => m[1]);

  // Find mechanism summaries for this specific anatomy target
  const mechRe = new RegExp(
    `app:impliesPathologyIn\\s+<${escapeRegex(anatomyUri)}>\\s*;[\\s\\S]*?` +
    `app:mechanismSummary\\s+"([^"]+)"`,
    "g"
  );
  const citRe = new RegExp(
    `app:impliesPathologyIn\\s+<${escapeRegex(anatomyUri)}>\\s*;[\\s\\S]*?` +
    `app:citationFragment\\s+"([^"]+)"`,
    "g"
  );

  const mechanisms  = [...ttlText.matchAll(mechRe)].map(m => m[1]);
  const citations   = [...ttlText.matchAll(citRe)].map(m => m[1]);

  if (mechanisms.length > 0 || doi) {
    results.push({
      title,
      doi,
      year,
      journal,
      authors,
      mechanism: mechanisms[0] ?? null,
      citation:  citations[0]  ?? null,
    });
  }

  return results;
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}


/**
 * @typedef {Object} ExplanationCard
 * @property {string}   anatomyUri
 * @property {string}   anatomyLabel      - Human-readable name
 * @property {string}   severity          - "high" | "medium" | "low"
 * @property {string}   severityLabel
 * @property {string}   severityColor
 * @property {string}   severityIcon
 * @property {Source[]} sources           - One per triggering ruleset
 * @property {string}   disclaimer
 * @property {boolean}  hasMultipleSources
 */

/**
 * @typedef {Object} Source
 * @property {string}   rulesetUrl
 * @property {string}   title
 * @property {string|null} doi
 * @property {string|null} year
 * @property {string|null} journal
 * @property {string[]} authors
 * @property {string|null} mechanism
 * @property {string|null} citation
 * @property {string|null} doiLink
 */


/**
 * Build an ExplanationCard for a clicked mesh's anatomy URI.
 *
 * @param {import('./accumulator.js').MergedImplication} mergedImpl
 * @returns {ExplanationCard}
 */
export function buildExplanationCard(mergedImpl) {
  const { anatomyUri, severity, sources, metadataTtls } = mergedImpl;

  const anatomyLabel  = FMA_LABELS[anatomyUri] ?? anatomyUri.split("/").pop().replace(/_/g, " ");
  const severityMeta  = SEVERITY_LABELS[severity] ?? SEVERITY_LABELS.low;

  const sourceCards = sources.map((rulesetUrl, i) => {
    const ttlText = metadataTtls[i] ?? "";
    const extracted = extractFromTtl(ttlText, anatomyUri);
    const info = extracted[0] ?? {};

    return {
      rulesetUrl,
      title:     info.title   ?? rulesetUrl.split("/").pop(),
      doi:       info.doi     ?? null,
      year:      info.year    ?? null,
      journal:   info.journal ?? null,
      authors:   info.authors ?? [],
      mechanism: info.mechanism ?? null,
      citation:  info.citation  ?? null,
      doiLink:   info.doi ? `https://doi.org/${info.doi.replace(/^https?:\/\/doi\.org\//, "")}` : null,
    };
  });

  return {
    anatomyUri,
    anatomyLabel,
    severity,
    severityLabel: severityMeta.label,
    severityColor: severityMeta.color,
    severityIcon:  severityMeta.icon,
    sources:       sourceCards,
    disclaimer:    DISCLAIMER,
    hasMultipleSources: sourceCards.length > 1,
  };
}


/**
 * Render an ExplanationCard to an HTML string for the sidebar panel.
 * Pure function — no DOM side effects.
 *
 * @param {ExplanationCard} card
 * @param {boolean} [darkMode=true]
 * @returns {string} HTML
 */
export function renderExplanationHtml(card, darkMode = true) {
  const bg      = darkMode ? "rgba(10,5,20,0.92)" : "rgba(255,255,255,0.96)";
  const fg      = darkMode ? "#f8fafc" : "#0f172a";
  const subdued = darkMode ? "#94a3b8"  : "#475569";
  const border  = darkMode ? "rgba(0,240,255,0.2)" : "rgba(15,23,42,0.1)";

  const sourcesHtml = card.sources.map((src, i) => {
    const authLine = src.authors.length
      ? `<div style="color:${subdued};font-size:11px;margin-top:2px">${src.authors.slice(0,3).join(", ")}${src.authors.length > 3 ? " et al." : ""}</div>`
      : "";

    const mechHtml = src.mechanism
      ? `<div style="margin-top:10px;padding:8px 10px;background:${darkMode ? "rgba(0,240,255,0.05)" : "rgba(15,23,42,0.04)"};border-radius:6px;font-size:12px;line-height:1.5;">${src.mechanism}</div>`
      : "";

    const citHtml = src.citation
      ? `<div style="margin-top:8px;font-size:11px;color:${subdued};font-style:italic;border-left:2px solid ${card.severityColor};padding-left:8px;">"${src.citation}"</div>`
      : "";

    const doiHtml = src.doiLink
      ? `<a href="${src.doiLink}" target="_blank" rel="noopener" style="color:${darkMode ? "#00f0ff" : "#0d9488"};font-size:11px;text-decoration:none;display:block;margin-top:6px;">↗ ${src.doi}</a>`
      : "";

    const multi = card.sources.length > 1
      ? `<div style="font-size:10px;color:${subdued};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px">Source ${i + 1}</div>`
      : "";

    return `
      <div style="margin-top:${i > 0 ? "14px" : "0"};padding-top:${i > 0 ? "14px" : "0"};border-top:${i > 0 ? `1px solid ${border}` : "none"}">
        ${multi}
        <div style="font-weight:700;font-size:13px">${src.title}</div>
        <div style="font-size:11px;color:${subdued};margin-top:2px">${[src.journal, src.year].filter(Boolean).join(" · ")}</div>
        ${authLine}
        ${mechHtml}
        ${citHtml}
        ${doiHtml}
      </div>`;
  }).join("");

  return `
    <div style="
      background:${bg};
      color:${fg};
      border:1px solid ${border};
      border-left:3px solid ${card.severityColor};
      border-radius:12px;
      padding:16px 18px;
      font-family:'Outfit',sans-serif;
      max-width:340px;
      box-shadow:0 8px 32px rgba(0,0,0,0.4);
      backdrop-filter:blur(20px);
    ">
      <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:12px">
        <span style="font-size:18px">${card.severityIcon}</span>
        <div>
          <div style="font-weight:800;font-size:15px;letter-spacing:0.02em">${card.anatomyLabel}</div>
          <div style="font-size:11px;color:${card.severityColor};font-weight:700;text-transform:uppercase;letter-spacing:0.1em">${card.severityLabel}</div>
        </div>
      </div>

      ${sourcesHtml}

      <div style="margin-top:14px;padding-top:10px;border-top:1px solid ${border};font-size:10px;color:${subdued};line-height:1.4">
        ${card.disclaimer}
      </div>
    </div>`;
}


/**
 * Build a plain-text version of an ExplanationCard (for accessibility,
 * screen readers, and the non-3D text report output path).
 *
 * @param {ExplanationCard} card
 * @returns {string}
 */
export function renderExplanationText(card) {
  const lines = [
    `${card.anatomyLabel} — ${card.severityLabel}`,
    "=".repeat(50),
  ];

  for (const src of card.sources) {
    lines.push("");
    lines.push(`Study: ${src.title}`);
    if (src.journal || src.year) lines.push(`Source: ${[src.journal, src.year].filter(Boolean).join(", ")}`);
    if (src.authors.length)      lines.push(`Authors: ${src.authors.join(", ")}`);
    if (src.doi)                 lines.push(`DOI: ${src.doi}`);
    if (src.mechanism)           lines.push(`\nMechanism: ${src.mechanism}`);
    if (src.citation)            lines.push(`\n"${src.citation}"`);
  }

  lines.push("");
  lines.push(card.disclaimer);
  return lines.join("\n");
}
