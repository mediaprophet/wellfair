# WellFair — Distributed Analytics & Social Research Commons
## Implementation Plan — DA / RC Epic

> Branch: `release/v0.0.7` (DA vault-side), `release/v0.0.8` (DA coordinator + economic layer), `release/v0.0.9` (RC Research Creator App)
> Drafted: 2026-05-31
> Estimated sessions: 14–18 total across three phases

---

## Background & motivation

This epic builds a **Privacy-Preserving Distributed Analytics Engine** on top of the existing
Wellfair stack. The core insight: Wellfair already holds exactly the kind of high-fidelity,
temporally-anchored evidence that social researchers cannot collect via traditional surveys
(government forms, shelter intake, etc.) because vulnerable populations avoid them. By turning
the vault into a voluntary, privacy-safe research node, we bridge a structural gap in social
policy evidence — without centralising any raw data.

The economic complement is a **Social Bounty System**: research organisations fund bounties;
device vaults that match criteria earn micro-payouts via Lightning; the financial chain is
decoupled from the data chain via blind claim tokens.

The **Research Creator App** is a standalone no-code tool (parallel to `expert-authoring-tool/`)
where researchers formulate studies as signed `StudyCredential` tokens without needing to write
SHACL or N3 directly.

---

## Architectural critique of the source proposal

Several mechanisms described in the design conversation are correct directionally but need
translation into what the Wellfair stack can actually do:

| Proposal | Assessment | Decision |
|----------|------------|----------|
| SPARQL queries broadcast to devices | SPARQL is too heavy for device-side evaluation | Use N3/JSON-encoded rule specs instead — matches existing arch |
| Secure Multi-Party Computation (SMPC) | Academic-grade complexity; overkill for v1 | Use LDP + trusted coordinator + Nym anonymity. SMPC deferred to Phase 3+ |
| Full ZKP of contribution | Requires trusted setup; complex in browser JS | HMAC blind claim ticket for v1; full ZKP later |
| "SPARQL shape" SHACL output | SHACL shapes for filtering, N3 rules for logic | Correct — extend existing `access-profiles.ttl` |
| Proof-of-Provenance via OTS | Already implemented in `vault-sanctuary-evidence.js` | Direct reuse — check IDB records have OTS proofs anchored before study date |
| Sybil resistance via web-of-trust | Hand-wavy in proposal | VC-7 Verified Directory provides foundation; hardware attestation is Phase 3+ |

---

## What already exists (direct reuse)

| Component | File | Reuse |
|-----------|------|-------|
| Nym anonymous routing | `docs/js/vault-nym.js` | Route study credential inbound + response outbound |
| Background job scheduler | `docs/js/vault-scheduler.js` | Periodic study credential polling + contribution jobs |
| OpenTimestamps proof | `docs/js/vault-sanctuary-evidence.js` | Proof-of-Provenance: check existing .ots before submission |
| VP generation | `docs/js/vault-sanctuary-evidence.js` | Reuse `generateVP()` for contribution packaging |
| Ed25519 signing | `docs/js/vault-did.js` + `vault-crypto.js` | Sign contribution payloads |
| Lightning wallet | `docs/js/vault-wallet.js` | Payout redemption endpoint |
| IDB infrastructure | `docs/js/vault-idb.js` | Add new stores in v10 |
| SHACL shapes | `docs/profiles/access-profiles.ttl` | Extend with analytics vocabulary |
| Rule compiler (Python) | `expert-authoring-tool/rule-compiler/compile_ruleset.py` | Adapt for N3 study rule compilation in RC app |

---

## New components overview

```
docs/js/
  vault-analytics.js      DA-1/2  Study credential parser, local N3 evaluator, consent controller
  vault-dp.js             DA-3    Local Differential Privacy: Randomized Response, ε-budget

research-creator/         RC-1→5  Standalone Research Creator App (no-code study builder)
  index.html
  js/rc-builder.js        Visual query builder — event/condition node editor
  js/rc-compiler.js       N3 + SHACL rule compiler (extends rule-compiler/ concepts)
  js/rc-credential.js     StudyCredential signer + Nym broadcast
  js/rc-escrow.js         Bounty escrow UI + Lightning payment request

coordinator/              DA-6→9  Aggregator infrastructure (Node.js; run by institutions)
  server.js               Nym listener + response collector + k-anonymity engine
  aggregator.js           Statistical combination + output guardrails
  token-issuer.js         Blind claim ticket generation + redemption
```

---

## Privacy model (canonical)

### Local Differential Privacy (LDP)
The device applies noise **before** data leaves the vault. For binary queries the mechanism is
Randomized Response (Warner 1965): flip coin p₁; if heads → answer truthfully; if tails → flip
coin p₂ → answer randomly. The researcher strips noise from the aggregate.

Epsilon (ε) budget is tracked per-device per-category in IDB `wf-dp-budget`. Each study
participation costs a configurable ε slice. When budget is exhausted the device silently declines
further queries in that category until the budget resets (rolling 90-day window by default).

### K-Anonymity at output
The coordinator aggregator refuses to publish statistics where the sub-population count
k < configurable floor (default k=15). The researcher must broaden parameters or wait.

### Decoupled blind payout (v1 — HMAC approach)
1. Device submits LDP-noised payload via fresh Nym circuit
2. Coordinator verifies shape validity (not content) + issues HMAC blind claim token:
   `token = HMAC-SHA256(aggregator_secret, submission_id ‖ study_id ‖ device_epoch_slot)`
3. Token stored in IDB `wf-bounties`; submission_id and device identity are never stored together
4. Hours/days later: device presents token over a fresh, unrelated Nym circuit to payout node
5. Payout node verifies HMAC → initiates Lightning push to rotated wallet address

*Full ZKP (Groth16 or similar) deferred to Phase 3 — the HMAC approach already prevents
the aggregator from linking token issuance to specific payloads.*

---

## IDB version roadmap (analytics additions)

| IDB version | When | New stores |
|-------------|------|------------|
| v9 | current (WASM biometrics) | wf-biometrics |
| v10 | DA-1 | + wf-studies, wf-bounties, wf-dp-budget |

`wf-studies` — received StudyCredential tokens (keyPath: `id`)
`wf-bounties` — contribution records + claim tokens (keyPath: `id`)
`wf-dp-budget` — per-category epsilon budget state (keyPath: `category`)

---

## SHACL / namespace additions (`access-profiles.ttl`)

```turtle
## Analytics vocabulary

wf:StudyCredential  a rdfs:Class ; rdfs:label "Research study token"@en .
wf:StudyQuery       a rdfs:Class ; rdfs:label "Embedded N3 evaluation rules"@en .
wf:BountyEscrow     a rdfs:Class ; rdfs:label "Economic parameters of a study"@en .
wf:ContributionToken a rdfs:Class ; rdfs:label "Blind claim ticket for payout"@en .
wf:DataWeight       a rdfs:Class ; rdfs:label "Semantic soundness weight"@en .

wf:studyId          a rdf:Property ; rdfs:domain wf:StudyCredential ; rdfs:range xsd:string .
wf:studyIssuer      a rdf:Property ; rdfs:domain wf:StudyCredential ; rdfs:range xsd:string .
wf:studyExpiry      a rdf:Property ; rdfs:domain wf:StudyCredential ; rdfs:range xsd:dateTime .
wf:studyQuery       a rdf:Property ; rdfs:domain wf:StudyCredential ; rdfs:range wf:StudyQuery .
wf:studyEscrow      a rdf:Property ; rdfs:domain wf:StudyCredential ; rdfs:range wf:BountyEscrow .
wf:epsilonBudget    a rdf:Property ; rdfs:domain wf:StudyQuery ; rdfs:range xsd:decimal .
wf:kFloor           a rdf:Property ; rdfs:domain wf:StudyCredential ; rdfs:range xsd:integer .
wf:dataCategories   a rdf:Property ; rdfs:domain wf:StudyQuery .

wf:payoutSats       a rdf:Property ; rdfs:domain wf:BountyEscrow ; rdfs:range xsd:integer .
wf:escrowLightningAddr a rdf:Property ; rdfs:domain wf:BountyEscrow ; rdfs:range xsd:string .
wf:targetSampleSize a rdf:Property ; rdfs:domain wf:BountyEscrow ; rdfs:range xsd:integer .
```

---

## StudyCredential JSON-LD format (canonical)

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://wellfare.social/ns/vault#"
  ],
  "@type": ["VerifiableCredential", "wf:StudyCredential"],
  "id": "urn:uuid:<study-id>",
  "issuer": "<did:key of research institution>",
  "issuanceDate": "<ISO8601>",
  "expirationDate": "<ISO8601>",
  "credentialSubject": {
    "wf:studyTitle": "Family Separation & Housing Stability Study",
    "wf:studyOrg":   "Melbourne Social Policy Institute",
    "wf:kFloor":     15,
    "wf:studyQuery": {
      "wf:epsilonCost": 0.5,
      "wf:dataCategories": ["wf:housingStatus", "wf:separationEvent"],
      "wf:n3Rules": "<N3 rules as escaped string — evaluated locally>",
      "wf:shapeRef":  "urn:uuid:<shacl-shape-id>"
    },
    "wf:studyEscrow": {
      "wf:payoutSats": 20000,
      "wf:escrowLightningAddr": "<LNURL or BOLT12 address>",
      "wf:targetSampleSize": 200,
      "wf:coordinatorNymAddr": "<Nym address of aggregator>"
    }
  },
  "proof": {
    "type": "Ed25519Signature2020",
    "verificationMethod": "<did:key>#z6Mk...",
    "proofValue": "<base64url Ed25519 sig>"
  }
}
```

---

## Data weight taxonomy (semantic soundness)

| Weight | Label | Evidence type | Example |
|--------|-------|---------------|---------|
| 0.1 | Self-asserted | User fills questionnaire manually | "I have experienced homelessness" toggle |
| 0.4 | Device-synthesised | Local AI parses a document; hash anchored | PDF eviction notice processed on-device |
| 0.6 | OTS-anchored | Record has an OpenTimestamps `.ots` proof predating study | Sanctuary entry committed to Bitcoin before study date |
| 1.0 | Bilaterally ratified | Mutual-signature interaction from VC-11 or VC-8 | Signed VP receipt from a call + data-sharing session |

The weight affects bounty payout fraction: `payout = payoutSats × weight`.

---

## Phase 1 — Vault-side analytics engine (v0.0.7)

### DA-1 — SHACL shapes + IDB v10 + vault-analytics.js skeleton

**Session scope:** 1 session
**Depends on:** nothing (IDB v9 already exists)
**Read first:** `docs/js/vault-idb.js` (v9 layout), `docs/profiles/access-profiles.ttl`, `docs/js/vault-scheduler.js` (registerJobHandler)

**IDB changes (vault-idb.js):**
- Bump `_openDB` to version 10
- Add constants: `_ST_STUDIES = 'wf-studies'`, `_ST_BOUNTIES = 'wf-bounties'`, `_ST_DP_BUDGET = 'wf-dp-budget'`
- Add stores in `onupgradeneeded` with appropriate keyPaths + indices

**SHACL shapes (access-profiles.ttl):**
Add the analytics vocabulary block listed above.

**vault-analytics.js — skeleton (no logic yet):**
```js
// Public API stubs — implementation follows in DA-2
async function initAnalytics()             // called from vault.html after unlock
async function pollStudyCredentials()      // job handler: fetch new credentials via Nym
async function evaluateStudy(studyId)      // job handler: run local N3 rules
async function submitContribution(studyId) // job handler: LDP-noise + Nym send + token store
async function getActiveStudies()          // returns array of wf-studies records with status
async function getContributions()          // returns array of wf-bounties records
async function setAnalyticsConsent(prefs)  // persists per-category consent to IDB wf-sc
async function getAnalyticsConsent()       // returns current consent prefs
```

Register job handlers with vault-scheduler.js:
```js
// In initAnalytics():
registerJobHandler('analytics.poll',     { estimateFn: () => 5000,  runFn: pollStudyCredentials });
registerJobHandler('analytics.evaluate', { estimateFn: () => 2000,  runFn: evaluateStudy });
registerJobHandler('analytics.submit',   { estimateFn: () => 10000, runFn: submitContribution });
```

**Acceptance criteria:**
- [ ] IDB v10 opens; wf-studies, wf-bounties, wf-dp-budget stores created
- [ ] vault-analytics.js loads without error; all stubs defined
- [ ] Job handlers registered; scheduler can enqueue analytics.poll job
- [ ] SHACL shapes added to TTL without breaking existing shape validation

---

### DA-2 — Study credential parser + local N3 rule evaluator

**Session scope:** 1–2 sessions
**Depends on:** DA-1
**Read first:** `docs/js/vault-analytics.js` (DA-1 stubs), `docs/js/vault-nym.js` (nymAdapter.onMessage), `docs/js/vault-crypto.js` (Ed25519 verify)

**`pollStudyCredentials()` implementation:**
1. Call `nymAdapter.receive()` or check a Gun namespace `wf/studies/<vaultDid>` for pending credentials
2. Parse incoming JSON-LD as `StudyCredential`
3. Verify `proof.proofValue` against `issuer` did:key using Ed25519
4. Check `expirationDate` > now
5. Check `wf:dataCategories` against user consent prefs (from `getAnalyticsConsent()`)
6. Check local ε-budget: `_ST_DP_BUDGET[category].remaining >= wf:epsilonCost`
7. If all pass: store in `wf-studies` with `status: 'pending'`; enqueue `analytics.evaluate` job
8. If any fail: store with `status: 'declined'` + reason (for transparency UI)

**`evaluateStudy()` implementation:**
The `wf:n3Rules` string embedded in the credential contains JSON-encoded rules (not full N3 syntax,
to avoid a parser dependency). Format:

```json
{
  "rules": [
    {
      "id": "rule_separation_before_housing",
      "require": [
        { "store": "wf-s", "field": "type", "value": "wf:SeparationEvent" },
        { "store": "wf-s", "field": "ts", "rel": "before", "ref": "rule_housing_change" }
      ]
    },
    {
      "id": "rule_housing_change",
      "require": [
        { "store": "wf-s", "field": "type", "value": "wf:HousingStatusChange" },
        { "store": "wf-s", "field": "housingStatus", "value": "wf:Homeless" }
      ]
    },
    { "id": "rule_within_90_days", "maxDeltaDays": 90, "between": ["rule_separation_before_housing", "rule_housing_change"] }
  ],
  "response": "binary"
}
```

The evaluator reads relevant IDB stores, applies the rules, returns `true/false` (or a count).
Proof-of-Provenance check: for any matched records, verify that at least one has an OTS proof
pre-dating the study's `issuanceDate`. If so, `provenanceWeight = 0.6`; if bilaterally ratified,
`provenanceWeight = 1.0`; otherwise `provenanceWeight = 0.4` or `0.1`.

If evaluation returns true: update `wf-studies[studyId].status = 'eligible'`; store `provenanceWeight`.
Enqueue `analytics.submit` job (only after explicit user consent step — see DA-4).

**Acceptance criteria:**
- [ ] `pollStudyCredentials()` verifies Ed25519 signature on incoming credential
- [ ] Credential stored with correct status based on consent + budget checks
- [ ] `evaluateStudy()` correctly evaluates JSON-encoded rules against IDB data
- [ ] Provenance weight computed and stored
- [ ] False-negative on rules: status = 'no_match'; false-negative = silent, no submission

---

### DA-3 — vault-dp.js — Local Differential Privacy module

**Session scope:** 1 session
**Depends on:** DA-1 (IDB wf-dp-budget)
**Read first:** `docs/js/vault-analytics.js`, `docs/js/vault-idb.js`

**vault-dp.js — public API:**
```js
// Randomized Response for binary questions (ε = ln((p/(1-p)) * (p₂/(1-p₂)))  — standard formula)
// p1 = probability of answering truthfully (default: 0.75 → ε ≈ 1.1)
function randomizedResponse(truthValue, p1 = 0.75, p2 = 0.5)
// Returns: boolean (noisy response)

// Laplace mechanism for integer/count responses
function laplaceMechanism(trueValue, sensitivity, epsilon)
// Returns: number (noisy value)

// Categorical response (generalised RR for non-binary answers)
function categoricalResponse(trueCategory, allCategories, epsilon)
// Returns: string (noisy category label)

// Budget management
async function checkBudget(category, epsilonCost)
// Returns: true if remaining budget >= cost; false if depleted

async function consumeBudget(category, epsilonCost)
// Deducts cost from wf-dp-budget[category]; records consumption timestamp

async function getBudgetState()
// Returns: { [category]: { total, remaining, lastReset } }

async function resetExpiredBudgets()
// Resets categories where lastReset > 90 days ago (rolling window)
```

**ε budget defaults:**
```js
const DEFAULT_EPSILON_TOTAL = 3.0;   // per category per 90-day window
const BUDGET_WINDOW_DAYS    = 90;
```

**Integration in `submitContribution()`:**
```js
const raw    = await evaluateStudy(studyId);          // true/false
const budget = await checkBudget(category, epsilonCost);
if (!budget) return;                                   // silent decline
const noisy  = randomizedResponse(raw, 0.75, 0.5);    // add LDP noise
await consumeBudget(category, epsilonCost);
// ... then Nym-route noisy response
```

**Acceptance criteria:**
- [ ] `randomizedResponse(true)` returns false ~25% of the time (statistical test over 1000 runs)
- [ ] `laplaceMechanism` adds noise proportional to sensitivity/epsilon
- [ ] `checkBudget()` returns false after budget depleted
- [ ] Budget state persists across page reloads (IDB wf-dp-budget)
- [ ] `resetExpiredBudgets()` resets category when 90-day window expires

---

### DA-4 — vault.html Research panel + consent UI

**Session scope:** 1 session
**Depends on:** DA-2, DA-3
**Read first:** `docs/vault.html` (existing panel structure — search for `step-` IDs), `docs/js/vault-analytics.js`

**vault.html panel additions:**
- New nav step `step-research` with nav label "Research"
- **Master consent toggle** (stored in IDB wf-sc via `setAnalyticsConsent()`):
  - "Contribute anonymously to social research" master switch (off by default)
  - Per-category toggles (show only when master is on): housing, health, financial, relationships, location
  - "Privacy budget" meter per category (shows remaining ε as a percentage bar)
- **Active study cards** (pulled from `getActiveStudies()`):
  - Each card: sponsor name, study title, data categories touched, payout amount
  - Status badge: Eligible / Evaluating / Contributed / Declined / No match
  - "View details" expander: N3 rules in human-readable form, k-floor, expiry date
  - For `eligible` studies: "Contribute anonymously" button + "Decline this study" button
  - Privacy summary: "Your answer will have random noise added before leaving your device. A minimum of [k] participants is required before any results are published."
- **Contribution history** (wf-bounties): date, study title, payout status (pending/claimed/paid)
- **Budget indicator** in panel header: "Privacy budget: [X]% remaining this period"

**Notification banner** (shown in owner workspace header when new eligible study arrives):
```
📊 New research opportunity from [Org]: [Title] — [Xk sats] — Tap to review
```

**Acceptance criteria:**
- [ ] Research panel renders in vault.html owner workspace
- [ ] Master toggle persists; per-category toggles only visible when master is on
- [ ] Active studies load from IDB wf-studies
- [ ] Eligible study → "Contribute" button triggers `submitContribution()` job
- [ ] ε budget meter shows correct remaining value per category
- [ ] Contribution history entries visible

---

### DA-5 — Nym-routed submission + blind claim token receipt

**Session scope:** 1 session
**Depends on:** DA-2, DA-3, DA-4
**Read first:** `docs/js/vault-nym.js` (nymAdapter.send), `docs/js/vault-did.js` (generateDid), `docs/js/vault-crypto.js` (toB64)

**`submitContribution()` implementation (full):**

```js
async function submitContribution(studyId) {
  const study    = await _dbGet(_ST_STUDIES, studyId);
  const result   = study.evaluationResult; // boolean or count
  const noisy    = randomizedResponse(result, 0.75, 0.5);
  const weight   = study.provenanceWeight;
  const slotKey  = _epochSlot();           // 6-hour bucket — prevents exact-time correlation

  // Build payload
  const payload = {
    studyId,
    response:  noisy,
    weight,
    slotKey,
    // No device ID, no timestamp, no location
  };

  // Encrypt payload to coordinator's public key (from study credential)
  const coordinatorPubKey = study.credentialSubject['wf:studyEscrow']['wf:coordinatorPublicKey'];
  const encrypted         = await _encryptToRecipient(payload, coordinatorPubKey);

  // Route via fresh Nym circuit
  await nymAdapter.send(study.credentialSubject['wf:studyEscrow']['wf:coordinatorNymAddr'], encrypted);

  // Await blind claim token from coordinator (arrives via Nym onMessage callback)
  // Token stored in wf-bounties when received
  await _dbPut(_ST_BOUNTIES, {
    id:       'bounty-' + studyId + '-' + Date.now(),
    studyId,
    status:   'submitted',
    submittedAt: Date.now(),
    slotKey,
    claimToken: null, // filled when coordinator responds
    payoutSats: Math.round(study.credentialSubject['wf:studyEscrow']['wf:payoutSats'] * weight),
  });

  // Update study status
  await _dbPut(_ST_STUDIES, { ...study, status: 'contributed' });
}
```

**Claim token receipt handler** (in `initAnalytics()` — registers a Nym message handler):
```js
nymAdapter.onMessage((msg) => {
  if (msg.type === 'analytics.claim_token') {
    // Store token in wf-bounties; update status to 'token_received'
    // Do NOT attempt payout immediately — decouple by scheduling analytics.redeem job
    // with a randomised delay of 2–72 hours
    enqueueJob('analytics.redeem', { studyId: msg.studyId, token: msg.token },
               JOB_TRIGGER.ALWAYS, 2);
  }
});
```

**`redeemContribution()` job handler:**
```js
async function redeemContribution({ studyId, token }) {
  // Open a fresh Nym circuit (new ephemeral did:key)
  // POST token to coordinator payout node
  // Receive Lightning invoice; pay via vault-wallet.js walletPay(invoice)
  // Update wf-bounties status = 'paid'
}
```

**Acceptance criteria:**
- [ ] `submitContribution()` sends LDP-noised payload via Nym (not Gun)
- [ ] No device identifier in payload
- [ ] Claim token stored in wf-bounties on receipt
- [ ] `analytics.redeem` job enqueued with random delay
- [ ] On redemption: Lightning invoice received + paid; bounty status = 'paid'
- [ ] Payout visible in contribution history UI (DA-4)

---

## Phase 2 — Coordinator infrastructure (v0.0.8)

*This phase runs on a server operated by trusted institutions, not the Wellfair dev team.
The codebase ships a reference implementation in `coordinator/`.*

### DA-6 — Study credential format specification + coordinator mock

**Session scope:** 1 session
**Depends on:** DA-1 (StudyCredential JSON-LD format is locked)

**`coordinator/` directory structure:**
```
coordinator/
  README.md         Setup + deployment guide for academic/NGO operators
  server.js         Main entry point (Node.js / Deno)
  aggregator.js     Response collection + k-anonymity engine
  token-issuer.js   Blind claim ticket generation + HMAC signing
  config.example.js Coordinator configuration (Nym address, secret, k-floor, etc.)
  mock/
    mock-server.js  Lightweight in-memory mock — runs locally for vault dev/testing
    sample-study.json  Example StudyCredential for testing
```

**`mock/mock-server.js`**: A simple HTTP server (Node.js built-in `http`) that:
- Accepts POST `/submit` with encrypted payload (but in mock mode, just logs it)
- Returns a mock claim token: `{ type: 'analytics.claim_token', studyId, token: <HMAC> }`
- Runs on `http://localhost:4000` for local testing

**`mock/sample-study.json`**: A pre-signed StudyCredential (for local testing — issuer is a
self-generated test did:key). Vault dev flow: load this via `nymAdapter` mock → device evaluates.

**Acceptance criteria:**
- [ ] `coordinator/mock/mock-server.js` runs with `node mock-server.js`
- [ ] vault.html correctly parses `sample-study.json` (load via devtools console injection for testing)
- [ ] Mock server returns valid claim token structure
- [ ] Study appears in Research panel with correct payout amount

---

### DA-7 — Aggregator k-anonymity engine

**Session scope:** 1 session
**Depends on:** DA-6

**`coordinator/aggregator.js`:**
```js
class Aggregator {
  constructor({ kFloor = 15, epsilonEstimate }) { ... }

  receive(studyId, encryptedPayload)
  // Decrypts payload; adds to in-memory pending pool
  // Returns: { accepted: bool, reason }

  canPublish(studyId)
  // Returns true when pool size >= kFloor for this studyId

  publishStats(studyId)
  // Strips noise from aggregate (applies LDP correction formula)
  // Returns: { studyId, n, trueEstimate, confidenceInterval, publishedAt }
  // Writes result to output file / database

  enforceKAnonymity(studyId)
  // If sub-group count < kFloor: returns null (refuse to publish)
  // L-diversity check: if all responses in a sub-group are identical → suppress
}
```

**LDP noise correction**: For Randomized Response with p1=0.75, p2=0.5:
`trueEstimate = (observedYesRate - p2) / (p1 - p2)`

**Output format** (published to open data commons):
```json
{
  "studyId": "...",
  "studyTitle": "...",
  "publishedAt": "...",
  "n": 87,
  "result": {
    "trueEstimate": 0.423,
    "confidenceInterval": [0.31, 0.54],
    "ldpCorrected": true
  },
  "kFloor": 15,
  "methodology": "LDP-RR-p1=0.75"
}
```

**Acceptance criteria:**
- [ ] `receive()` rejects duplicate submission_ids (Sybil guard)
- [ ] `canPublish()` returns false when n < kFloor
- [ ] `publishStats()` applies LDP correction formula correctly (unit tested)
- [ ] Published output matches canonical format above

---

### DA-8 — Nym listener + report publishing back to vault

**Session scope:** 1 session
**Depends on:** DA-7

The aggregator publishes results back to the Nym network using a known channel address
(`wf/studies/<studyId>/results`). Vaults poll this channel via `nymAdapter.onMessage`.

**vault-analytics.js additions:**
```js
async function pollStudyResults()
// Job handler: check for published results on studies where status = 'contributed'
// If result found: store in wf-studies[studyId].result
// Enqueue analytics.notify job

async function notifyUserOfResult(studyId)
// Generates a human-readable insight from the published stat
// E.g.: "A study you contributed to found that 42% of participants experienced X"
// Stored in a notification queue; shown in Research panel
```

**Reciprocal data transparency**: When a result is received, vault-analytics.js can optionally
cross-reference the published statistic against the user's own situation:
```
"Based on a study of 87 anonymous participants matching your profile:
 42% experienced housing instability within 90 days of family separation.
 Local resources that may help: [list from vault-mock or local data]"
```

**Acceptance criteria:**
- [ ] Published result stored in wf-studies record
- [ ] Human-readable insight generated and shown in Research panel
- [ ] Cross-reference suggestion displayed where relevant

---

### DA-9 — Blind claim token: full HMAC flow

**Session scope:** 1 session
**Depends on:** DA-7, DA-8

**`coordinator/token-issuer.js`:**
```js
function issueToken(studyId, slotKey, coordinatorSecret)
// token = HMAC-SHA256(coordinatorSecret, studyId ‖ slotKey)
// Returns token string

function verifyToken(token, studyId, slotKey, coordinatorSecret)
// Returns boolean

async function processRedemption(token, studyId, slotKey, lightningAddr)
// 1. verifyToken()
// 2. Check token not already redeemed (store in coordinator redeemed-set)
// 3. Generate Lightning invoice for payoutSats; push to device
// 4. Record redemption
```

**Device-side `redeemContribution()` (complete implementation):**
```js
async function redeemContribution({ studyId, token }) {
  const bounty   = await _getBountyByStudy(studyId);
  const lnInvoice = await _presentTokenToCoordinator(token, studyId, bounty.slotKey);
  if (lnInvoice) {
    await walletPay(lnInvoice);
    await _dbPut(_ST_BOUNTIES, { ...bounty, status: 'paid', paidAt: Date.now() });
  }
}

async function _presentTokenToCoordinator(token, studyId, slotKey) {
  // Fresh Nym circuit (new did:key, new routing path)
  // POST { token, studyId, slotKey, lightningAddr: await walletGetReceiveAddr() }
  // Response: { invoice: <BOLT11> } or { error }
}
```

**Acceptance criteria:**
- [ ] `issueToken()` + `verifyToken()` round-trip passes
- [ ] Redeemed tokens are rejected on second presentation (double-spend prevention)
- [ ] Device redeems via fresh Nym circuit; Lightning invoice received + paid
- [ ] Full flow works against `mock-server.js`

---

## Phase 3 — Economic layer enhancements (v0.0.8/v0.0.9)

### DA-10 — Lightning payout integration (vault-wallet.js extension)

**Session scope:** 1 session
**Depends on:** DA-9, existing `vault-wallet.js`
**Read first:** `docs/js/vault-wallet.js` (walletInit, walletPay patterns)

**vault-wallet.js additions:**
```js
async function walletGetReceiveAddr()
// Returns a fresh LNURL or BOLT12 offer for receiving payments
// Rotates address each call (privacy: unlinks payout events)

async function walletPay(bolt11Invoice)
// Pays invoice via WebLN; records in wf-txlog with type = 'analytics_payout'

async function getAnalyticsPayoutHistory()
// Returns wf-txlog entries where type = 'analytics_payout'
// Used by Research panel contribution history
```

**UI update (Research panel, DA-4 extension):**
- Contribution history cards: show Lightning payment amount + status (pending → paid)
- Wallet not configured → show install prompt for WebLN wallet (Alby, Zeus)

**Acceptance criteria:**
- [ ] `walletGetReceiveAddr()` returns valid address each call
- [ ] `walletPay()` executes payment + logs to wf-txlog
- [ ] Research panel shows paid amount in contribution history

---

### DA-11 — Social equity scoring UI

**Session scope:** 1 session
**Depends on:** DA-10

Social equity score is a local-only aggregate, never transmitted. Three components:

| Component | Calculation | Display |
|-----------|-------------|---------|
| Financial equity | Sum of analytics_payout wf-txlog entries (Sats earned) | "X sats earned via research contributions" |
| Contribution count | wf-bounties records with status=paid | "Contributed to X studies" |
| Informational equity | Count of study results received in wf-studies | "Accessed X published research insights" |

**vault.html Research panel addition:**
- "My contributions" section at top of Research panel
- Three stat cards: Sats earned, Studies contributed, Research insights received
- Small "impact" blurb: "Your anonymous data helped [n] studies reach their publication threshold."

**Acceptance criteria:**
- [ ] All three equity metrics computed correctly from local IDB
- [ ] Metrics update after new contribution or payout
- [ ] No network call made for equity scoring — local-only

---

### DA-12 — Reciprocal transparency + contextual insights

**Session scope:** 1 session
**Depends on:** DA-8 (results in wf-studies), DA-11

When a study result arrives, vault-analytics.js compares the published statistic to the user's
own IDB data and generates a contextual insight, stored in IDB and surfaced in the Research panel.

**Insight generation:**
```js
async function generateInsight(studyId, publishedResult) {
  // Pull relevant IDB data (e.g., housing status, separation events)
  // Cross-reference with publishedResult.trueEstimate
  // Compose natural-language insight string
  // Look up relevant vault-mock.js resources (emergency contacts, voucher programs)
  // Return { insight: string, resources: [...] }
}
```

Example output in UI:
```
A study you contributed to (Family Separation & Housing Study) published results:
42% of 87 participants experienced housing instability within 90 days.
Based on your situation, these local resources may help:
  • [Emergency housing voucher program — contact details from vault]
  • [Legal aid housing service — from vault contacts]
```

**Acceptance criteria:**
- [ ] Insight generated for each received result
- [ ] Relevant vault resources surfaced where available
- [ ] Insights visible in Research panel, ordered by recency

---

## Research Creator App (v0.0.9+)

### RC-1 — App scaffold

**Session scope:** 1 session
**Depends on:** DA-1 (StudyCredential format locked)

**`research-creator/` directory:**
```
research-creator/
  index.html          App shell — nav: Builder / Credentials / Broadcast / Docs
  css/rc.css          Standalone styles (dark theme, researcher-focused)
  js/
    rc-builder.js     Visual query builder (DA-2)
    rc-compiler.js    N3 + SHACL rule compiler (DA-3)
    rc-credential.js  StudyCredential signer + Nym broadcast (DA-4)
    rc-escrow.js      Bounty escrow UI + Lightning payment request (DA-5)
    rc-did.js         Institution did:key management (generate/import/export)
  docs/
    guide.md          Researcher onboarding guide
    example-study.json Pre-built example credential (housing study)
```

**Dev server:** Same Python server from project root:
`http://localhost:3000/../research-creator/` or serve `research-creator/` separately on port 3001.

**Acceptance criteria:**
- [ ] `research-creator/index.html` loads without errors
- [ ] Nav sections render: Builder, Credentials, Broadcast, Docs
- [ ] `rc-did.js`: generates institution did:key; exports/imports JSON keystore

---

### RC-2 — Visual query builder

**Session scope:** 2 sessions
**Depends on:** RC-1

**rc-builder.js — the node editor:**

The UI presents a canvas with three areas:
1. **Variable palette** (left): draggable event types drawn from `wf:` namespace
   (`wf:SeparationEvent`, `wf:HousingStatusChange`, `wf:MedicalAppointment`, etc.)
2. **Canvas** (centre): drop zones; connect nodes with arrows representing temporal relationships
3. **Constraint panel** (right): for selected edge, configure temporal constraints (within N days, before/after, etc.)

Under the hood, each node maps to a JSON rule spec (as defined in DA-2):
```json
{ "id": "node1", "store": "wf-s", "field": "type", "value": "wf:SeparationEvent" }
```
Each edge maps to a temporal constraint:
```json
{ "id": "edge1", "type": "before", "maxDeltaDays": 90, "from": "node1", "to": "node2" }
```

**Response type selector**: Binary (yes/no), Count (integer), Category (multiple choice)

**LDP settings**: Slider for epsilon cost (shows plain-English privacy impact description)
e.g. "ε=0.5: Strong privacy — researcher gets accurate aggregate from ≥50 participants.
      ε=2.0: Moderate privacy — accurate from ≥15 participants, but individual responses are less noisy."

**Human-readable preview** (auto-generated from rule spec):
"This study looks for participants who experienced a [housing status change to: Homeless] within [90] days of a [Separation event]. Your answer is private: random noise is added before leaving your device."

**Acceptance criteria:**
- [ ] Drag event nodes from palette to canvas
- [ ] Connect nodes with temporal edges; configure maxDeltaDays
- [ ] JSON rule spec correctly generated from canvas state
- [ ] Human-readable preview rendered in real-time
- [ ] Response type and ε-cost configurable

---

### RC-3 — N3/SHACL rule compiler

**Session scope:** 1 session
**Depends on:** RC-2, existing `expert-authoring-tool/rule-compiler/compile_ruleset.py`

**rc-compiler.js:**
```js
function compileRules(nodeGraph)
// Takes the rc-builder.js node graph JSON
// Returns: { n3Rules: <JSON string>, shapeRef: <URI>, humanSummary: <string> }

function validateRules(n3Rules)
// Dry-run against wf: vocabulary — checks all field names, store names, relation types
// Returns: { valid: bool, errors: [...] }

function estimateEpsilon(n3Rules, responseType)
// Estimates required ε for statistical accuracy at k=15
// Returns: { recommendedEpsilon, minSampleForAccuracy }
```

The `n3Rules` JSON format is the same spec consumed by `vault-analytics.js evaluateStudy()` —
this is the shared contract between the RC app and the vault engine.

**SHACL shape generation** (for the StudyCredential's `wf:shapeRef`):
Compile a minimal SHACL shape document (Turtle string) from the rule graph.
This shape is used by vault devices for fast pre-filtering before running the full rule evaluation.

**Integration with expert-authoring-tool/rule-compiler/:**
The existing `compile_ruleset.py` compiles medical knowledge rules. `rc-compiler.js` is the
browser-side equivalent for analytics queries. Consider exposing `compile_ruleset.py` as a
local Flask endpoint for the RC app to call optionally (for researchers who want full N3 syntax).

**Acceptance criteria:**
- [ ] `compileRules()` produces valid JSON rule spec from rc-builder graph
- [ ] `validateRules()` rejects unknown field names / stores
- [ ] `estimateEpsilon()` returns plausible sample-size estimates
- [ ] SHACL shape output is valid Turtle

---

### RC-4 — StudyCredential signer + Nym broadcast

**Session scope:** 1 session
**Depends on:** RC-3, RC-1 (rc-did.js)

**rc-credential.js:**
```js
async function buildCredential(builderConfig, escrowConfig, institutionDid)
// Assembles full StudyCredential JSON-LD from:
//   builderConfig: { n3Rules, shapeRef, epsilonCost, dataCategories, humanSummary }
//   escrowConfig:  { payoutSats, targetSampleSize, kFloor, coordinatorNymAddr, expiryDays }
//   institutionDid: { id, privateKey }
// Generates: { credential: JSON-LD, id: urn:uuid }

async function signCredential(credential, privateKey)
// Ed25519 sign over canonical JSON representation
// Returns: credential with proof block

async function broadcastCredential(signedCredential, nymAddr)
// Send via Nym to the coordinator's address
// Coordinator relays to vaults via the wf/studies Nym channel

async function saveCredential(signedCredential)
// Stores in browser localStorage (RC app is stateless, no IDB)

function listSavedCredentials()
// Returns saved credentials from localStorage
```

**Acceptance criteria:**
- [ ] `buildCredential()` produces valid JSON-LD matching canonical format
- [ ] `signCredential()` produces verifiable Ed25519 proof
- [ ] Saved credentials visible in "Credentials" nav section
- [ ] Broadcast sends credential to configured Nym address

---

### RC-5 — Escrow funding UI + Lightning payment

**Session scope:** 1 session
**Depends on:** RC-4

**rc-escrow.js:**
The RC app does not manage Lightning directly — it generates a BOLT12 offer / LNURL that the
researcher pays using their own Lightning wallet. The coordinator generates the escrow address.

```js
async function requestEscrowAddress(studyId, payoutSats, targetSampleSize, coordinatorNymAddr)
// Sends escrow setup request to coordinator via Nym
// Coordinator responds with LNURL or BOLT12 address for the researcher to pay

function generateEscrowQR(lightningAddr, amountSats)
// Renders QR code for the researcher to scan with their Lightning wallet

async function verifyEscrowFunding(studyId, coordinatorNymAddr)
// Asks coordinator to confirm the escrow has been funded
// Returns: { funded: bool, amountSats, remainingSlots }
```

**RC app funding flow UI:**
1. "Fund Escrow" button on the Credentials screen (after signing)
2. Shows BOLT12 / LNURL QR + amount in sats
3. "Verify funding" button — polls coordinator for confirmation
4. On funded: "Broadcast study" button activates

**Acceptance criteria:**
- [ ] QR code rendered for escrow Lightning address
- [ ] Funding verification polls coordinator and shows confirmed/pending
- [ ] "Broadcast study" only active after coordinator confirms funding

---

## Progress Tracker

| Session | Date | Milestone | Status | Handover |
|---------|------|-----------|--------|----------|
| 1 | | DA-1: SHACL + IDB v10 + vault-analytics.js skeleton | not started | |
| 2 | | DA-2: Study credential parser + N3 rule evaluator | not started | |
| 3 | | DA-3: vault-dp.js — Local Differential Privacy | not started | |
| 4 | | DA-4: vault.html Research panel + consent UI | not started | |
| 5 | | DA-5: Nym submission + blind claim token receipt | not started | |
| 6 | | DA-6: Coordinator mock + sample study credential | not started | |
| 7 | | DA-7: Aggregator k-anonymity engine | not started | |
| 8 | | DA-8: Nym result publishing + vault result receipt | not started | |
| 9 | | DA-9: Blind claim token HMAC full flow | not started | |
| 10 | | DA-10: Lightning payout integration | not started | |
| 11 | | DA-11: Social equity scoring UI | not started | |
| 12 | | DA-12: Reciprocal transparency + contextual insights | not started | |
| 13 | | RC-1: Research Creator App scaffold | not started | |
| 14–15 | | RC-2: Visual query builder | not started | |
| 16 | | RC-3: N3/SHACL rule compiler | not started | |
| 17 | | RC-4: StudyCredential signer + broadcast | not started | |
| 18 | | RC-5: Escrow funding UI + Lightning | not started | |

---

## Handover template

```markdown
# WellFair — Session Handover DA-{n} / RC-{n} ({YYYY-MM-DD})

## Milestone covered

## Completed this session
<!-- Specific: function names, line ranges, file paths -->

## Files modified
| File | Change summary | Key functions added |
|------|---------------|---------------------|

## IDB state
IDB version: v10
Stores: wf-s, wf-sc, wf-meds, wf-ml, wf-pc, wf-dl, wf-contacts, wf-relationships, wf-agreements,
        wf-jobs, wf-events, wf-telemetry, wf-wallet, wf-txlog, wf-biometrics,
        wf-studies, wf-bounties, wf-dp-budget

## What to do next

## Decisions made

## Blocked / deferred

## Acceptance criteria met
- [ ] ...
```
