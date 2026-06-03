/**
 * WellFair WASM Worker (Stage C3)
 * ================================
 * Runs inside a Web Worker — never on the main UI thread.
 * Manages the SWI-Prolog WASM lifecycle: initialisation, rule loading,
 * fact assertion, query execution, teardown, and memory release.
 *
 * Message protocol (from main thread → worker):
 *   { type: "init" }
 *   { type: "evaluate", rulesetUrl: string, userFacts: FactList, evaluationId: string }
 *   { type: "cancel", evaluationId: string }
 *
 * Message protocol (worker → main thread):
 *   { type: "ready" }
 *   { type: "result", evaluationId, implications: ImplicationList, proofTrace: TraceList }
 *   { type: "error",  evaluationId, message: string }
 *   { type: "progress", evaluationId, stage: string }
 *
 * FactList:  Array<{ kind: "fact"|"metric", uri?: string, param?: string, value?: number }>
 * ImplicationList: Array<{ anatomyUri: string, severity: string, rulesetUrl: string }>
 * TraceList: Array<{ implId: string, conditionUri: string, param?: string, value?: number }>
 */

// ---------------------------------------------------------------------------
// SWI-Prolog WASM initialisation
// The actual import path depends on how swipl-wasm is bundled.
// Replace with the correct CDN or local path for your build.
// ---------------------------------------------------------------------------
let prologReady = false;
let Prolog       = null;

const INIT_TIMEOUT_MS    = 30_000;
const QUERY_TIMEOUT_MS   = 8_000;   // per ruleset evaluation
const SIGNATURE_VERIFY   = false;   // set true when Ed25519 signing is wired up (Stage B6/E3)

// In-memory cache: rulesetUrl → { pl: string, ttl: string, cachedAt: number }
const rulesetCache = new Map();
const CACHE_TTL_MS = 60 * 60 * 1000; // 1 hour

// ---------------------------------------------------------------------------
// Utility
// ---------------------------------------------------------------------------

function post(msg) {
  self.postMessage(msg);
}

function postProgress(evaluationId, stage) {
  post({ type: "progress", evaluationId, stage });
}

function postError(evaluationId, message) {
  post({ type: "error", evaluationId, message });
}

// ---------------------------------------------------------------------------
// WASM initialisation
// ---------------------------------------------------------------------------

async function initProlog() {
  try {
    // Resolve the swipl.js blob URL from OPFS via PackageManager.
    // The worker receives the blob URL in the "init" message payload.
    // Falls back to a CDN URL if the package manager hasn't passed one yet.
    const jsUrl = self._swiplJsUrl
      || "https://cdn.jsdelivr.net/npm/swipl-wasm@4.1.14/dist/swipl/swipl.js";

    const module = await import(/* @vite-ignore */ jsUrl);
    Prolog = await module.default({
      // Point the WASM binary loader at the OPFS blob URL if available
      locateFile: (filename) => {
        if (filename.endsWith(".wasm") && self._swiplWasmUrl) {
          return self._swiplWasmUrl;
        }
        // CDN fallback for the .wasm binary
        return `https://cdn.jsdelivr.net/npm/swipl-wasm@4.1.14/dist/swipl/${filename}`;
      },
    });
    prologReady = true;
    post({ type: "ready" });
  } catch (err) {
    post({ type: "error", evaluationId: null, message: `Prolog WASM init failed: ${err.message}` });
  }
}

// ---------------------------------------------------------------------------
// Ruleset fetching and caching
// ---------------------------------------------------------------------------

async function fetchRuleset(rulesetUrl) {
  const cached = rulesetCache.get(rulesetUrl);
  if (cached && (Date.now() - cached.cachedAt) < CACHE_TTL_MS) {
    return cached;
  }

  const plUrl  = rulesetUrl.endsWith(".pl") ? rulesetUrl : rulesetUrl + ".pl";
  const ttlUrl = rulesetUrl.endsWith(".pl")
    ? rulesetUrl.replace(/\.pl$/, ".ttl")
    : rulesetUrl + ".ttl";

  const [plResp, ttlResp] = await Promise.all([
    fetch(plUrl),
    fetch(ttlUrl),
  ]);

  if (!plResp.ok)  throw new Error(`Failed to fetch Prolog rules: ${plUrl} (${plResp.status})`);
  if (!ttlResp.ok) throw new Error(`Failed to fetch ruleset metadata: ${ttlUrl} (${ttlResp.status})`);

  const pl  = await plResp.text();
  const ttl = await ttlResp.text();

  if (SIGNATURE_VERIFY) {
    await verifySignature(pl, ttl, rulesetUrl);  // Stage E3 — throws on failure
  }

  const entry = { pl, ttl, cachedAt: Date.now() };
  rulesetCache.set(rulesetUrl, entry);
  return entry;
}

// Placeholder — wired up in Stage E3
async function verifySignature(_pl, _ttl, _url) {
  // TODO: fetch .sig file, fetch expert public key from WebID, verify Ed25519
  console.warn("[wasm-worker] Signature verification not yet implemented.");
}

// ---------------------------------------------------------------------------
// Fact assertion
// ---------------------------------------------------------------------------

/**
 * Assert user facts into the Prolog engine.
 * Returns a list of retract calls needed to clean up afterward.
 *
 * FactList schema:
 *   { kind: "fact",   uri: "<full-uri>" }
 *   { kind: "metric", param: "hba1c",  value: 7.4 }
 */
function assertFacts(facts) {
  const retracts = [];

  for (const f of facts) {
    if (f.kind === "fact") {
      const goal = `assert(user_fact(me, '${f.uri}'))`;
      Prolog.call(goal);
      retracts.push(`retract(user_fact(me, '${f.uri}'))`);
    } else if (f.kind === "metric") {
      const goal = `assert(user_metric(me, ${f.param}, ${f.value}))`;
      Prolog.call(goal);
      retracts.push(`retract(user_metric(me, ${f.param}, ${f.value}))`);
    }
  }

  return retracts;
}

function retractFacts(retracts) {
  for (const goal of retracts) {
    try { Prolog.call(goal); } catch (_) { /* already retracted */ }
  }
}

// ---------------------------------------------------------------------------
// Query execution with timeout
// ---------------------------------------------------------------------------

function queryWithTimeout(query, timeoutMs) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new Error(`Query timed out after ${timeoutMs}ms — possible infinite loop in ruleset`));
    }, timeoutMs);

    try {
      const results = [];
      const q = Prolog.query(query);

      // Collect all solutions
      let solution = q.next();
      while (solution.value !== false) {
        results.push(solution.value);
        solution = q.next();
      }
      q.close();

      clearTimeout(timer);
      resolve(results);
    } catch (err) {
      clearTimeout(timer);
      reject(err);
    }
  });
}

// ---------------------------------------------------------------------------
// Main evaluation
// ---------------------------------------------------------------------------

async function evaluate({ rulesetUrl, userFacts, evaluationId }) {
  if (!prologReady) {
    return postError(evaluationId, "Prolog WASM is not initialised.");
  }

  postProgress(evaluationId, "fetching_ruleset");

  let ruleset;
  try {
    ruleset = await fetchRuleset(rulesetUrl);
  } catch (err) {
    return postError(evaluationId, `Ruleset fetch failed: ${err.message}`);
  }

  postProgress(evaluationId, "loading_rules");

  // Write the .pl content to the WASM virtual filesystem then consult it
  const plPath = `/tmp/${evaluationId}.pl`;
  try {
    Prolog.FS.writeFile(plPath, ruleset.pl);
    Prolog.call(`consult('${plPath}')`);
  } catch (err) {
    return postError(evaluationId, `Ruleset load failed: ${err.message}`);
  }

  postProgress(evaluationId, "asserting_facts");

  const retracts = assertFacts(userFacts);

  postProgress(evaluationId, "querying");

  let rawResults;
  try {
    rawResults = await queryWithTimeout(
      "implication_target(me, URI, Severity)",
      QUERY_TIMEOUT_MS
    );
  } catch (err) {
    retractFacts(retracts);
    return postError(evaluationId, err.message);
  }

  // Clean up — retract all asserted facts
  retractFacts(retracts);

  // Unload the ruleset from WASM FS to free memory
  try {
    Prolog.FS.unlink(plPath);
  } catch (_) {}

  // Build structured implication list
  const implications = rawResults.map(sol => ({
    anatomyUri:  sol.URI,
    severity:    sol.Severity,
    rulesetUrl,
    // Embed raw TTL reference for Explainer module (Stage C5)
    rulesetMeta: ruleset.ttl,
  }));

  // Build lightweight proof trace (for Explainer)
  // Full proof trace requires Prolog's built-in proof recording — simplified here
  const proofTrace = rawResults.map(sol => ({
    anatomyUri:  sol.URI,
    severity:    sol.Severity,
    rulesetUrl,
  }));

  post({
    type: "result",
    evaluationId,
    implications,
    proofTrace,
  });
}

// ---------------------------------------------------------------------------
// Message handler
// ---------------------------------------------------------------------------

self.onmessage = async function (event) {
  const msg = event.data;

  switch (msg.type) {
    case "init":
      // Accept blob URLs from PackageManager so we can load from OPFS
      if (msg.swiplJsUrl)   self._swiplJsUrl   = msg.swiplJsUrl;
      if (msg.swiplWasmUrl) self._swiplWasmUrl = msg.swiplWasmUrl;
      await initProlog();
      break;

    case "evaluate":
      await evaluate(msg);
      break;

    case "cancel":
      // Future: abort in-flight query via AbortController
      postError(msg.evaluationId, "Evaluation cancelled by user.");
      break;

    default:
      console.warn("[wasm-worker] Unknown message type:", msg.type);
  }
};

// Auto-init when worker starts
initProlog();
