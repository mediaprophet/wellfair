/**
 * WellFair Multi-Condition Accumulator (Stage C4)
 * =================================================
 * Merges implication results from multiple ruleset evaluations.
 * Implements Hickam's Dictum: all conditions accumulate, none suppressed.
 *
 * Merge rules:
 *   1. Same anatomyUri from multiple rulesets → keep the HIGHEST severity
 *   2. All unique anatomyUris from all rulesets are included (no dropping)
 *   3. Each result tracks which rulesets triggered it (for Explainer)
 *   4. Severity is ranked: high > medium > low
 *
 * Usage:
 *   import { Accumulator } from './accumulator.js';
 *   const acc = new Accumulator();
 *   acc.add(resultsFromRuleset1);
 *   acc.add(resultsFromRuleset2);
 *   const merged = acc.merge();
 */

export const SEVERITY_RANK = { high: 3, medium: 2, low: 1 };

/**
 * @typedef {Object} Implication
 * @property {string}   anatomyUri     - Full FMA URI
 * @property {string}   severity       - "high" | "medium" | "low"
 * @property {string}   rulesetUrl     - Source ruleset URL
 * @property {string}   [rulesetMeta]  - Raw TTL provenance text
 */

/**
 * @typedef {Object} MergedImplication
 * @property {string}   anatomyUri     - Full FMA URI
 * @property {string}   severity       - Highest severity across all rulesets
 * @property {string[]} sources        - All rulesetUrls that triggered this URI
 * @property {string[]} metadataTtls   - Provenance TTL strings from all sources
 */

export class Accumulator {
  constructor() {
    /** @type {Map<string, MergedImplication>} */
    this._byUri = new Map();
  }

  /**
   * Add an array of implications from one ruleset evaluation.
   * @param {Implication[]} implications
   */
  add(implications) {
    for (const impl of implications) {
      const existing = this._byUri.get(impl.anatomyUri);

      if (!existing) {
        this._byUri.set(impl.anatomyUri, {
          anatomyUri:   impl.anatomyUri,
          severity:     impl.severity,
          sources:      [impl.rulesetUrl],
          metadataTtls: impl.rulesetMeta ? [impl.rulesetMeta] : [],
        });
      } else {
        // Escalate severity if this source reports higher
        if ((SEVERITY_RANK[impl.severity] ?? 0) > (SEVERITY_RANK[existing.severity] ?? 0)) {
          existing.severity = impl.severity;
        }

        // Accumulate all sources (Hickam — no suppression)
        if (!existing.sources.includes(impl.rulesetUrl)) {
          existing.sources.push(impl.rulesetUrl);
        }
        if (impl.rulesetMeta && !existing.metadataTtls.includes(impl.rulesetMeta)) {
          existing.metadataTtls.push(impl.rulesetMeta);
        }
      }
    }
    return this;
  }

  /**
   * Return the merged implication list, sorted by severity descending.
   * @returns {MergedImplication[]}
   */
  merge() {
    return [...this._byUri.values()].sort((a, b) => {
      const rankDiff = (SEVERITY_RANK[b.severity] ?? 0) - (SEVERITY_RANK[a.severity] ?? 0);
      if (rankDiff !== 0) return rankDiff;
      // Secondary sort: alphabetical by URI for stable ordering
      return a.anatomyUri.localeCompare(b.anatomyUri);
    });
  }

  /**
   * Check if any implications have been accumulated.
   * @returns {boolean}
   */
  isEmpty() {
    return this._byUri.size === 0;
  }

  /**
   * Clear all accumulated state (for reuse across sessions).
   */
  reset() {
    this._byUri.clear();
    return this;
  }

  /**
   * Return count of unique anatomical URIs implicated.
   * @returns {number}
   */
  get size() {
    return this._byUri.size;
  }
}


/**
 * One-shot helper: merge multiple implication arrays without instantiating Accumulator.
 * @param  {...Implication[]} arrays
 * @returns {MergedImplication[]}
 */
export function mergeImplications(...arrays) {
  const acc = new Accumulator();
  for (const arr of arrays) acc.add(arr);
  return acc.merge();
}


/**
 * Extract a deduplicated list of all FMA URIs from a merged result,
 * grouped by severity band. Used by the visualizer bridge.
 *
 * @param {MergedImplication[]} merged
 * @returns {{ high: string[], medium: string[], low: string[] }}
 */
export function groupBySeverity(merged) {
  const bands = { high: [], medium: [], low: [] };
  for (const impl of merged) {
    const band = bands[impl.severity];
    if (band) band.push(impl.anatomyUri);
  }
  return bands;
}
