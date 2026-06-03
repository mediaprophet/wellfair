'use strict';

// ── Sentinel VM + N3 Logic rule engine ───────────────────────────────────────
//
// Backed by wellfare-core WASM (W6 / A6).  Falls back gracefully when WASM is
// not loaded yet — all functions return null rather than throwing.
//
// Routing lanes (qualiaDB PermissiveRoutingLane):
//   0 = PassthroughStandard       — local telemetry, simple threshold flags
//   1 = EnforcePermissiveCommons  — cooperative obligation gates (µ-units)
//   2 = EnforceBilateralMicroCommons — N3Logic clinical rules (identity required)
//   3 = SpatiotemporalAmbiguous   — GeoSPARQL / NPU path (future)

const LANE_NAMES = ['Passthrough', 'PermissiveCommons', 'BilateralMicroCommons', 'Spatiotemporal'];

// ── SentinelCompiler ──────────────────────────────────────────────────────────
// Wraps the WASM compile_query_to_json export for query routing classification.
// Used by vault.html to determine which lane a query belongs to before executing.

class SentinelCompiler {
    /**
     * Classify a SPARQL/N3/GeoSPARQL query string and return routing metadata.
     * @param {string} query
     * @returns {{routing_tier: number, validation_mask: number, lane_name: string}|null}
     */
    static async classify(query) {
        const wasm = await window.vaultWasm?.load();
        if (!wasm || !wasm.compile_query_to_json) return null;
        try {
            const result = JSON.parse(wasm.compile_query_to_json(query));
            return {
                routing_tier:    result.routing_tier    ?? 0,
                validation_mask: result.validation_mask ?? 0,
                lane_name:       LANE_NAMES[result.routing_tier ?? 0] ?? 'Unknown',
            };
        } catch { return null; }
    }

    /**
     * Legacy sync interface (returns dummy — use classify() async instead).
     * @deprecated  Use SentinelCompiler.classify(query) instead.
     */
    static compileConstraint(subject, predicate, expectedObject) {
        console.warn('[Sentinel] compileConstraint is deprecated; use classify() async');
        return new BigUint64Array([1n, 2n, 3n]);
    }
}

// ── Sentinel policy constraint evaluation (W6) ────────────────────────────────

/**
 * Evaluate a named policy constraint against a quint (s,p,o,c,m).
 * Constraint names: "cooperative_obligation" | "guardian_identity" | "commercial_block"
 * @param {string} constraintName
 * @param {bigint} s  Subject Lexicon ID
 * @param {bigint} p  Predicate Lexicon ID
 * @param {bigint} o  Object Lexicon ID
 * @param {bigint} c  Context Lexicon ID
 * @param {bigint} m  Metadata/policy bitmask
 * @returns {Promise<{passed: boolean, routingLane: number, laneName: string}|null>}
 */
async function evaluatePolicyConstraint(constraintName, s, p, o, c, m) {
    const wasm = await window.vaultWasm?.load();
    if (!wasm || !wasm.validate_health_quin) return null;
    try {
        const result = JSON.parse(wasm.validate_health_quin(constraintName, s, p, o, c, m));
        return {
            passed:      result.passed,
            routingLane: result.routingLane,
            laneName:    LANE_NAMES[result.routingLane] ?? 'Unknown',
        };
    } catch { return null; }
}

// ── N3 Logic clinical rule evaluation (A6) ────────────────────────────────────

/**
 * Evaluate all 7 N3 clinical rules against a Turtle health document.
 * Returns triggered patterns with confidence + routing lane.
 * @param {string} turtle  Turtle RDF string (from vaultWasm.exportVaultToTurtle())
 * @returns {Promise<Array<{pattern:string, confidence:string, routingLane:number, n3Source:string, recommendedAction?:string}>|null>}
 */
async function evaluateN3Rules(turtle) {
    const wasm = await window.vaultWasm?.load();
    if (!wasm || !wasm.evaluate_n3_rules) return null;
    try {
        return JSON.parse(wasm.evaluate_n3_rules(turtle));
    } catch { return null; }
}

/**
 * Convenience: export all vault health data as Turtle, then run N3 rules.
 * Returns null if WASM is unavailable or vault has no health data.
 * @returns {Promise<Array<{pattern:string,confidence:string,routingLane:number,n3Source:string,recommendedAction?:string}>|null>}
 */
async function evaluateVaultN3Rules() {
    if (!window.vaultWasm) return null;
    const turtle = await window.vaultWasm.exportVaultToTurtle();
    if (!turtle) return null;
    return evaluateN3Rules(turtle);
}

// ── Public API ────────────────────────────────────────────────────────────────

window.SentinelCompiler = SentinelCompiler;
window.vaultSentinel = {
    LANE_NAMES,
    classify:                  SentinelCompiler.classify.bind(SentinelCompiler),
    evaluatePolicyConstraint,
    evaluateN3Rules,
    evaluateVaultN3Rules,
};
