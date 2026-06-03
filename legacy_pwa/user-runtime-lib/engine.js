/**
 * WellFair Informatics Engine (Stage C2 / C3 orchestration)
 * ===========================================================
 * Main thread entry point. Coordinates:
 *   1. SPARQL → Prolog fact extraction from local oxigraph store
 *   2. Web Worker lifecycle (wasm-worker.js)
 *   3. Multi-condition accumulation (accumulator.js)
 *   4. Explainer card building (explainer.js)
 *   5. Emitting structured results to the visualizer bridge
 *
 * Usage:
 *   import { InformaticsEngine } from './engine.js';
 *   const engine = new InformaticsEngine({ sparqlEndpoint, onResult, onProgress, onError });
 *   await engine.init();
 *   const results = await engine.evaluate({
 *     rulesetUrls: ["https://.../study_diabetes.pl"],
 *     userGraphTurtle: "<turtle string of user's health data>",
 *   });
 */

import { Accumulator }          from "./accumulator.js";
import { buildExplanationCard } from "./explainer.js";

// ---------------------------------------------------------------------------
// SPARQL query templates
// These run against the local oxigraph store via wellfare-core WASM.
// They extract user_fact and user_metric assertions from the user's RDF graph.
// ---------------------------------------------------------------------------

const SPARQL_EXTRACT_CONDITIONS = `
PREFIX app: <https://wellfair.app/ontology/>
PREFIX snomed: <http://snomed.info/id/>
PREFIX hp: <http://purl.obolibrary.org/obo/HP_>

SELECT DISTINCT ?conditionUri WHERE {
  ?subject app:userFact ?conditionUri .
}
`;

const SPARQL_EXTRACT_METRICS = `
PREFIX app: <https://wellfair.app/ontology/>

SELECT ?paramName ?value WHERE {
  ?metric app:prologName ?paramName ;
          app:value      ?value .
}
`;

// ---------------------------------------------------------------------------
// Fact list builder (SPARQL results → Prolog fact format)
// ---------------------------------------------------------------------------

/**
 * Convert SPARQL JSON results into the FactList format expected by wasm-worker.
 * @param {object} conditionsJson - SPARQL results for conditions query
 * @param {object} metricsJson    - SPARQL results for metrics query
 * @returns {Array<{kind: string, uri?: string, param?: string, value?: number}>}
 */
function buildFactList(conditionsJson, metricsJson) {
  const facts = [];

  // Conditions → user_fact/2
  for (const row of (conditionsJson?.results?.bindings ?? [])) {
    const uri = row.conditionUri?.value;
    if (uri) facts.push({ kind: "fact", uri });
  }

  // Metrics → user_metric/3
  for (const row of (metricsJson?.results?.bindings ?? [])) {
    const param = row.paramName?.value;
    const value = parseFloat(row.value?.value);
    if (param && !isNaN(value)) {
      facts.push({ kind: "metric", param, value });
    }
  }

  return facts;
}

// ---------------------------------------------------------------------------
// Engine class
// ---------------------------------------------------------------------------

export class InformaticsEngine {
  /**
   * @param {object} opts
   * @param {function(string): Promise<string>} opts.sparqlQuery
   *   Function that executes a SPARQL SELECT against the local store
   *   and returns SPARQL JSON results as a string.
   *   Typically wraps wellfare-core's query_health_graph() WASM export.
   * @param {function(MergedResult): void} opts.onResult
   *   Called when all rulesets have been evaluated and results merged.
   * @param {function(string): void} [opts.onProgress]
   *   Called with a human-readable progress stage string.
   * @param {function(string): void} [opts.onError]
   *   Called with an error message string.
   */
  constructor({ sparqlQuery, onResult, onProgress, onError }) {
    this._sparqlQuery  = sparqlQuery;
    this._onResult     = onResult;
    this._onProgress   = onProgress   ?? (() => {});
    this._onError      = onError       ?? console.error;

    this._worker       = null;
    this._workerReady  = false;
    this._pending      = new Map();   // evaluationId → { resolve, reject, accumulator }
    this._evalCounter  = 0;
  }

  // -------------------------------------------------------------------------
  // Initialisation
  // -------------------------------------------------------------------------

  /**
   * Start the WASM Web Worker and wait for it to signal ready.
   * @returns {Promise<void>}
   */
  init() {
    return new Promise((resolve, reject) => {
      this._worker = new Worker(
        new URL("./wasm-worker.js", import.meta.url),
        { type: "module" }
      );

      this._worker.onmessage = (event) => this._handleWorkerMessage(event.data);
      this._worker.onerror   = (err)   => reject(new Error(`Worker error: ${err.message}`));

      // Resolve once worker signals ready
      this._readyResolve = resolve;
      this._readyReject  = reject;

      // Worker auto-inits on start; send explicit init in case it didn't
      this._worker.postMessage({ type: "init" });

      // Timeout if WASM never loads
      setTimeout(() => {
        if (!this._workerReady) {
          reject(new Error("WASM worker did not become ready within 30 seconds."));
        }
      }, 30_000);
    });
  }

  // -------------------------------------------------------------------------
  // Main evaluation entry point
  // -------------------------------------------------------------------------

  /**
   * Evaluate a user's circumstances against one or more rulesets.
   *
   * @param {object} opts
   * @param {string[]}  opts.rulesetUrls       - URLs of .pl rulesets to evaluate against
   * @param {string}    opts.userGraphTurtle   - Turtle string of the user's private RDF graph
   * @returns {Promise<EvaluationResult>}
   */
  async evaluate({ rulesetUrls, userGraphTurtle }) {
    if (!this._workerReady) {
      throw new Error("Engine not initialised. Call init() first.");
    }

    this._onProgress("Preparing user data...");

    // Step 1: Load user's graph into local triple store and extract facts
    const userFacts = await this._extractFacts(userGraphTurtle);

    if (userFacts.length === 0) {
      this._onError("No conditions or metrics found in user profile.");
      return { merged: [], explanations: new Map() };
    }

    this._onProgress(`Evaluating against ${rulesetUrls.length} ruleset(s)...`);

    // Step 2: Evaluate each ruleset in sequence (could parallelise if WASM supports it)
    const accumulator  = new Accumulator();
    const evalPromises = rulesetUrls.map(rulesetUrl =>
      this._evaluateRuleset(rulesetUrl, userFacts, accumulator)
    );

    await Promise.allSettled(evalPromises);

    this._onProgress("Merging results...");

    // Step 3: Merge and return
    const merged = accumulator.merge();

    // Step 4: Pre-build explanation cards for all triggered structures
    const explanations = new Map();
    for (const impl of merged) {
      explanations.set(impl.anatomyUri, buildExplanationCard(impl));
    }

    const result = { merged, explanations };
    this._onResult(result);
    return result;
  }

  // -------------------------------------------------------------------------
  // SPARQL fact extraction (C2)
  // -------------------------------------------------------------------------

  async _extractFacts(userGraphTurtle) {
    // Load the user's graph into the local oxigraph store via wellfare-core
    // This uses the existing store.rs interface: load_turtle() then query()
    try {
      // The sparqlQuery function is expected to handle loading if needed
      // In practice this calls wellfare-core's load_and_query() or similar
      const condJson = JSON.parse(await this._sparqlQuery(SPARQL_EXTRACT_CONDITIONS));
      const metJson  = JSON.parse(await this._sparqlQuery(SPARQL_EXTRACT_METRICS));
      return buildFactList(condJson, metJson);
    } catch (err) {
      this._onError(`SPARQL extraction failed: ${err.message}`);
      return [];
    }
  }

  // -------------------------------------------------------------------------
  // Single ruleset evaluation via Web Worker
  // -------------------------------------------------------------------------

  _evaluateRuleset(rulesetUrl, userFacts, accumulator) {
    return new Promise((resolve, reject) => {
      const evaluationId = `eval_${++this._evalCounter}`;

      this._pending.set(evaluationId, {
        resolve: (implications) => {
          accumulator.add(implications);
          resolve(implications);
        },
        reject,
      });

      this._worker.postMessage({
        type: "evaluate",
        evaluationId,
        rulesetUrl,
        userFacts,
      });
    });
  }

  // -------------------------------------------------------------------------
  // Worker message handler
  // -------------------------------------------------------------------------

  _handleWorkerMessage(msg) {
    switch (msg.type) {
      case "ready":
        this._workerReady = true;
        this._readyResolve?.();
        break;

      case "result": {
        const pending = this._pending.get(msg.evaluationId);
        if (pending) {
          this._pending.delete(msg.evaluationId);
          pending.resolve(msg.implications ?? []);
        }
        break;
      }

      case "error": {
        const pending = this._pending.get(msg.evaluationId);
        if (pending) {
          this._pending.delete(msg.evaluationId);
          this._onError(`Evaluation error: ${msg.message}`);
          pending.reject(new Error(msg.message));
        } else {
          this._onError(`Worker error: ${msg.message}`);
        }
        break;
      }

      case "progress":
        this._onProgress(msg.stage);
        break;

      default:
        break;
    }
  }

  // -------------------------------------------------------------------------
  // Cleanup
  // -------------------------------------------------------------------------

  destroy() {
    this._worker?.terminate();
    this._worker      = null;
    this._workerReady = false;
    this._pending.clear();
  }

  /**
   * Get an explanation card for a specific anatomy URI from the last evaluation.
   * Returns null if the URI was not implicated.
   *
   * @param {Map<string, ExplanationCard>} explanations - from evaluate() result
   * @param {string} anatomyUri
   * @returns {ExplanationCard|null}
   */
  static getExplanation(explanations, anatomyUri) {
    return explanations.get(anatomyUri) ?? null;
  }
}
