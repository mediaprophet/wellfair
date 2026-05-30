# WellFair v0.0.6-dev — Verifiable Communications Ecosystem
## Implementation Plan

> Branch: `release/v0.0.6`  
> Started: 2026-05-30  
> Estimated sessions: 11–14  
> Epic ref: `memory/project_comms_epic.md`

---

## How to use this plan

**At the start of every session**, read in this order:
1. `CLAUDE.md` — project orientation, terminology, architecture (mandatory)
2. This file — find the current milestone row in the Progress Tracker, read that milestone section
3. The handover file written by the previous session (path shown in Progress Tracker)
4. The source files listed under "Read first" for that milestone

**At the end of every session**, write a handover file at:
`instructions/HANDOVER_VC{milestone}_{YYYY-MM-DD}.md`

Follow the Handover Template below exactly. Then update the Progress Tracker table in this file with the session date, handover path, and status. Commit everything before closing.

---

## Mandatory terminology & architecture constraints

- **"Identity credentials"** — never DIDs, never VCs in user-facing text. Technical spec names
  (`did:key`, `did:peer`, W3C VC Data Model) are fine in code/comments.
- **SHACL/RDFS** for data shapes about people. OWL only for policy artefacts (EdgeConstraint, etc.).
- Health namespace: `wf:` → `https://wellfare.social/ns/vault#`
- **No "sovereign"** anywhere — directory is "Verified Directory" in code, "Contacts" or "Directory" in UI.
- Phone is authoritative vault; desktop is always stateless.
- Gun.eco for WebRTC signalling only — health data never touches Gun relay nodes.
- IDB version: currently **v3** (stores: wf-s, wf-sc, wf-meds, wf-ml, wf-pc, wf-dl).
  **VC-7 bumps it to v4.**
- New JS modules go in `docs/js/`; no bundler; plain globals; script load order matters.
- Testing: always use `mcp__Claude_in_Chrome__*` tools against `python -m http.server 3000 --directory docs`.
  The Claude app preview lacks WebCrypto.

---

## Architecture overview for this epic

```
vault.html  ←──── extended with new panels: Directory, Queue (Scheduler), Call UI
  │
  ├── docs/js/vault-directory.js       VC-7  Contact graph, FOAF-inspired, IDB wf-contacts
  ├── docs/js/vault-handshake.js       VC-8  Semantic Handshake — ODRL agreement + did:peer
  ├── docs/js/vault-comms-gate.js      VC-9  Inbound caller gating — Nym+Gun, VC verify
  ├── docs/js/vault-comms-call.js      VC-10 Call session, WebRTC media, link gen, guest cred
  ├── docs/js/vault-cv.js              VC-10 OpenCV placeholder — emotional recognition, pulse
  ├── docs/js/vault-scheduler.js       VC-12 Background job queue engine
  ├── docs/js/vault-transcript.js      VC-13 Raw event log → HTML+RDFa transcript
  ├── docs/js/vault-comms-transcode.js VC-14 Language transcoding — 3-tier progressive
  └── docs/js/vault-package.js         VC-15 Content package + JSON-LD manifest assembly

connector/index.html  ←── extended: new "Calls" nav section, desktop offload worker
  └── (no new JS module — call logic lives in vault-comms-call.js, loaded by both pages)

docs/join.html         VC-10 NEW — lightweight call join page for guest/vault-user topology B
```

**Call topologies:**
- **A**: vault-owner ↔ vault-owner — both use phone(vault.html)+laptop(connector/index.html)
- **B**: vault-owner generates call link → guest or WellFair user opens `docs/join.html?id=<session>`

**Scheduler mental model:** video encoding queue — jobs accumulate during the day; engine runs them
when conditions are met (idle, charging, desktop paired, or manual). Nothing is processed inline
for heavy work. Jobs persist in IDB `wf-jobs` across app restarts.

---

## Session size guidance

Each Claude Code session has a limited context window (typically enough for 1–2 milestones of
focused implementation). Signs you are approaching the limit:
- Responses start summarising rather than implementing
- Tool call results are being compressed/truncated
- You notice prior context being dropped from tool outputs

When approaching the limit: **stop, write the handover, commit, and tell the user to start a new session.**
Do not attempt to rush VC milestones into a single session — incomplete code is worse than a clean stop.

Recommended session scopes (adjust based on actual progress):

| Session | Scope |
|---------|-------|
| 1 | VC-7: SHACL shapes + IDB v4 + vault-directory.js |
| 2 | VC-7 cont.: vault.html Directory panel + wiring |
| 3 | VC-8: vault-handshake.js (QR + Nym flows, ODRL signing) |
| 4 | VC-9: vault-comms-gate.js (dual transport, ring UI) |
| 5 | VC-10a: vault-comms-call.js + docs/join.html |
| 6 | VC-10b: connector/index.html Calls panel + vault-cv.js stub |
| 7 | VC-11: in-call data sharing panel + receipt generation |
| 8 | VC-12a: vault-scheduler.js engine + IDB wf-jobs |
| 9 | VC-12b: Queue UI panel in vault.html + desktop offload protocol |
| 10 | VC-13a: wf-events IDB store + raw event capture during calls |
| 11 | VC-13b: HTML+RDFa transcript generation + revision signing UI |
| 12 | VC-14: vault-comms-transcode.js (3-tier STT + translation) |
| 13 | VC-15: vault-package.js + manifest.jsonld + zip + OTS |
| 14 | Buffer — integration, cross-page wiring, edge cases |

---

## Progress Tracker

| Session | Date | Milestone | Status | Handover file |
|---------|------|-----------|--------|---------------|
| 1 | 2026-05-30 | VC-7a: shapes + IDB + directory.js | complete | instructions/HANDOVER_VC7a_2026-05-30.md |
| 2 | — | VC-7b: vault.html Directory panel | not started | — |
| 3 | — | VC-8: Handshake | not started | — |
| 4 | — | VC-9: Caller Gating | not started | — |
| 5 | — | VC-10a: call.js + join.html | not started | — |
| 6 | — | VC-10b: connector Calls panel + cv stub | not started | — |
| 7 | — | VC-11: Web Connector in-call | not started | — |
| 8 | — | VC-12a: scheduler engine + IDB | not started | — |
| 9 | — | VC-12b: Queue UI + desktop offload | not started | — |
| 10 | — | VC-13a: event log capture | not started | — |
| 11 | — | VC-13b: transcript generation + revision | not started | — |
| 12 | — | VC-14: transcoding | not started | — |
| 13 | — | VC-15: content package | not started | — |
| 14 | — | Buffer / integration | not started | — |

---

## Handover Template

Copy this template verbatim into `instructions/HANDOVER_VC{n}_{YYYY-MM-DD}.md` at session end.
Fill in every section — a sparse handover wastes the next session's context budget.

```markdown
# WellFair — Session Handover VC-{n} ({YYYY-MM-DD})

## Milestone covered
<!-- e.g. "VC-7a: SHACL shapes, IDB v4, vault-directory.js skeleton" -->

## Completed in this session
<!-- Bulleted list of exactly what was built/written. Be specific: function names, line ranges. -->

## Files modified
| File | Change summary | Key functions added |
|------|---------------|---------------------|
| docs/js/vault-idb.js | IDB bumped to v4; added wf-contacts store | _openDB (updated) |
| ... | | |

## IDB state
<!-- Current IDB version number and all store names as of end of session -->
IDB version: v4
Stores: wf-s, wf-sc, wf-meds, wf-ml, wf-pc, wf-dl, wf-contacts, wf-relationships, wf-agreements

## Script load order (vault.html)
<!-- Always include current load order — it changes as modules are added -->
vault-idb.js → vault-crypto.js → vault-did.js → vault-nym.js → vault-mock.js →
vault-directory.js → vault-sanctuary-pins.js → ...

## What to do next (immediate — first thing next session)
<!-- Be specific enough that the next session needs no inference. E.g.: -->
<!-- "Open docs/js/vault-directory.js. The addContact() function is scaffolded but -->
<!--  saveContact() is a stub at line 87. Implement it: encrypt contact record under -->
<!--  the vault AES key, then call _dbPut(_ST_CONTACTS, record)." -->

## Decisions made this session
<!-- Any architectural decisions, deviations from the plan, or things discovered -->

## Blocked / deferred
<!-- Anything that couldn't be done and why -->

## Acceptance criteria met
<!-- Tick off which items from the milestone's acceptance criteria are done -->
- [ ] ...
- [ ] ...
```

---

## Milestone Specifications

### VC-7 — Verified Directory

**Session scope:** 1–2 sessions  
**Depends on:** nothing (IDB already exists)  
**Read first:** `docs/js/vault-idb.js`, `docs/profiles/access-profiles.ttl`, `docs/vault.html` (panel structure, search for `step-` IDs)

**IDB changes (vault-idb.js):**
- Bump `_openDB` to version 4
- Add stores: `wf-contacts` (keyPath: `id`), `wf-relationships` (keyPath: `id`), `wf-agreements` (keyPath: `id`)
- Add constants: `_ST_CONTACTS`, `_ST_RELS`, `_ST_AGREEMENTS`

**SHACL shapes (access-profiles.ttl):**
```turtle
wf:Contact       a rdfs:Class ; rdfs:label "Contact"@en .
wf:Relationship  a rdfs:Class ; rdfs:label "Relationship edge"@en .
wf:UsageAgreement a rdfs:Class ; rdfs:label "Signed usage agreement"@en .

wf:contactDid    a rdf:Property ; rdfs:domain wf:Contact ; rdfs:range xsd:string .
wf:contactWebId  a rdf:Property ; rdfs:domain wf:Contact ; rdfs:range xsd:anyURI .
wf:relationshipType a rdf:Property ; rdfs:domain wf:Relationship .
wf:agreementOdrl a rdf:Property ; rdfs:domain wf:UsageAgreement ; rdfs:range xsd:string .
wf:agreementSig  a rdf:Property ; rdfs:domain wf:UsageAgreement ; rdfs:range xsd:string .
```

**vault-directory.js — public API:**
```js
async function addContact(name, did, webId, notes)     // create + store encrypted contact
async function getContact(id)                          // decrypt + return
async function getAllContacts()                         // return array
async function updateContact(id, fields)
async function deleteContact(id)
async function lookupByDid(did)                        // used by caller gating
async function getRelationship(contactId)              // return relationship + agreement
async function saveRelationship(contactId, peerDid, agreementJsonLd, ourSig, theirSig)
```

Contacts are AES-256-GCM encrypted at rest using the vault key (same pattern as sanctuary entries).

**vault.html panel:**
- New step `step-directory` with nav link "Contacts"
- Contact list (search box, add button, contact cards)
- Contact detail sheet: name, DID, WebID, relationship type, agreement status
- "Initiate handshake" button per contact (wires to VC-8)
- Inbound caller lookup badge during call events (wires to VC-9)

**Acceptance criteria:**
- [ ] IDB v4 opens without error; all 3 new stores created on upgrade
- [ ] Add contact → appears in list → survives page reload
- [ ] Contact data encrypted at rest (raw IDB value is not plaintext)
- [ ] `lookupByDid(did)` returns correct contact or null
- [ ] Directory panel renders in vault.html owner workspace

---

### VC-8 — Semantic Handshake

**Session scope:** 1 session  
**Depends on:** VC-7 (vault-directory.js, IDB wf-agreements)  
**Read first:** `docs/js/vault-directory.js`, `docs/js/vault-did.js`, `docs/profiles/access-profiles.ttl`

**vault-handshake.js — public API:**
```js
async function initiateHandshake(contactId)
// Generates: our did:key, proposed ODRL Permission set (JSON-LD), encodes as QR payload
// OR sends via nymAdapter if contact has Nym address
// Returns: { qrData, nymSent }

async function receiveHandshake(payload)
// Parses incoming handshake proposal
// Returns: { contactName, did, agreement } for user to review

async function acceptHandshake(payload, approved)
// If approved: sign agreement with our Ed25519 key → saveRelationship() → return signed blob
// Sends signed blob back to initiator

async function finaliseHandshake(signedBlob)
// Called on initiator side when counterparty returns signature
// Verifies signature → saveRelationship() on initiator side
```

**Agreement format (ODRL JSON-LD):**
```json
{
  "@context": ["http://www.w3.org/ns/odrl.jsonld", "https://wellfare.social/ns/vault#"],
  "@type": "odrl:Agreement",
  "uid": "urn:uuid:<generated>",
  "wf:initiator": "<did:key of initiator>",
  "wf:counterparty": "<did:key of counterparty>",
  "wf:peerDid": "<did:peer for this relationship>",
  "permission": [{ "action": "odrl:read", "target": "wf:medications" }, ...],
  "wf:initiatorSig": "<base64 Ed25519 sig over canonical JSON>",
  "wf:counterpartySig": "<base64 Ed25519 sig over canonical JSON>"
}
```

**Acceptance criteria:**
- [ ] Initiator side generates valid ODRL JSON-LD + QR payload
- [ ] Receiver side parses payload, shows agreement for review
- [ ] Both sides sign; signatures verifiable with counterparty's did:key
- [ ] `saveRelationship()` called on both sides; IDB wf-agreements has signed record

---

### VC-9 — Inbound Caller Gating

**Session scope:** 1 session  
**Depends on:** VC-7 (lookupByDid), VC-8 (agreement structure)  
**Read first:** `docs/js/vault-nym.js`, `docs/js/vault-directory.js`, `docs/vault.html` (Gun setup)

**vault-comms-gate.js — public API:**
```js
function startGate()
// Listens on Nym (nymAdapter.onMessage) AND Gun (gun.get('wf/calls/<vaultDid>').on(...))
// for inbound {type:"call_request", callerDid, callerVc, sessionId, gunNode}

async function _verifyInbound(msg)
// 1. lookupByDid(msg.callerDid) → contact or null
// 2. If contact: check agreement ODRL permissions satisfy call type
// 3. Verify callerVc signature (Ed25519)
// 4. If all pass: _ringDevice(contact, msg)
// 5. If fail: _holdForVerification(msg) → show verification UI

function _ringDevice(contact, msg)
// Show incoming call overlay: contact name, relationship label, accept/reject buttons

function _holdForVerification(msg)
// Show "Verify identity" step: caller's DID, ask them to provide credential
```

**vault.html UI additions:**
- Incoming call overlay (fixed position, above all panels)
- Verification hold screen (shows caller DID, prompts for credential presentation)

**Acceptance criteria:**
- [ ] Known contact calling → ring overlay shows with name + relationship
- [ ] Unknown caller → held at verification screen
- [ ] Caller with invalid VC signature → rejected silently, no ring
- [ ] Dual transport: gate listens on both Nym and Gun simultaneously

---

### VC-10 — Hypermedia Voice/Video

**Session scope:** 2 sessions (10a: call.js + join.html; 10b: connector Calls panel + cv stub)  
**Depends on:** VC-9  
**Read first:** `docs/connector/index.html` (sidebar nav structure), `docs/js/noise-xx.js`

**vault-comms-call.js — public API:**
```js
async function startCall(contactId)
// Gets relationship did:peer → creates Gun session node → gets getUserMedia
// → creates RTCPeerConnection with audio+video → sends offer over Gun/Nym
// Returns: { sessionId, callLink }  ← callLink = docs/join.html?id=<sessionId>

async function answerCall(sessionId, gunNode)
// Called from gate after user accepts ring
// Gets getUserMedia → creates RTCPeerConnection → sends answer

async function generateGuestLink(sessionId)
// Returns URL: <origin>/join.html?id=<sessionId>&token=<hmac>
// Token is HMAC of sessionId under vault key — validated when guest loads join.html

function endCall()
// Closes RTCPeerConnection, nulls media streams, clears Gun session node

function muteAudio(bool)
function muteVideo(bool)
```

**docs/join.html:**
- Detects `?id=` and `?token=` params
- If `?vault=1` param also present: prompts user to pair their vault phone (opens webconnect QR flow) before joining
- Otherwise: guest mode — name entry → generates ephemeral `did:key` → joins call
- In-call UI: self + remote video tiles, mute/end controls, minimal header

**connector/index.html Calls panel:**
- New nav item "Calls" (icon: phone)
- Initiate call: shows paired contacts, "Start call" button → calls vault's `startCall()` via DataChannel `{type:"initiate_call", contactId}`
- Active call: video tiles, mute/hold/end, call link share button
- Incoming call notification (from vault over DataChannel)

**vault-cv.js (stub only — no implementation):**
```js
// Placeholder for future OpenCV integration
// Emotional recognition via facial landmark analysis
// Pulse-rate estimation via Eulerian Video Magnification (micro-colour amplification)
// All processing fully client-side — no frames leave device
const VaultCV = {
  isAvailable: () => false,  // set to true when OpenCV.js loads
  analyzeFrame: async (videoElement) => null,
};
```

**Acceptance criteria:**
- [ ] vault-comms-call.js: `startCall()` creates RTCPeerConnection with audio+video tracks
- [ ] join.html: loads, guest entry works, joins call P2P
- [ ] join.html: `?vault=1` flow prompts vault pairing
- [ ] connector/index.html: Calls nav item visible; initiate call sends DataChannel message
- [ ] vault-cv.js: stub loads without error; `isAvailable()` returns false

---

### VC-11 — Web Connector (Live Data Sharing)

**Session scope:** 1 session  
**Depends on:** VC-10 (active call session), VC-8 (agreement permissions)  
**Read first:** `docs/js/vault-sanctuary-evidence.js` (generateVP), existing DataChannel message protocol in `instructions/VAULT_CONNECTOR_NEXT_STEPS.md`

**New DataChannel messages:**
```js
// Caller → vault (encrypted)
{type:"data_request", id, sections:["wf:medications","wf:overview"], callSessionId}

// vault → caller (encrypted, signed)
{type:"data_response", id, section, data, sig, callSessionId}

// vault → caller (encrypted)
{type:"data_receipt", id, receiptJsonLd, callSessionId}  // VP receipt blob
```

**In-call data sharing panel (vault.html):**
- Slide-up from bottom of call UI
- Shows requested sections, approve/deny per section
- On approve: serves data + generates VP receipt (reuse `generateVP()` from vault-sanctuary-evidence.js adapted for call context)
- Receipt stored in IDB `wf-s` (or new `wf-receipts` store if cleaner) + made available to VC-15 package builder

**Acceptance criteria:**
- [ ] Caller can request sections via DataChannel
- [ ] Vault shows approval panel with section names
- [ ] Approved section served + Ed25519 signed
- [ ] VP receipt generated + stored in IDB
- [ ] Receipt retrievable by session ID for VC-15

---

### VC-12 — Background Job Scheduler

**Session scope:** 1–2 sessions (12a: engine + IDB; 12b: UI panel + desktop offload)  
**Depends on:** VC-7 (IDB v4 — but can be built in parallel with VC-8–11)  
**Read first:** `docs/js/vault-idb.js`, `docs/vault.html` (existing panel structure)

**IDB changes:**
- Bump to v5 (if VC-7 was v4) or v4 if building in parallel
- Add store: `wf-jobs` (keyPath: `id`)
- Record shape: `{id, type, status, priority, created_at, started_at, completed_at, estimated_ms, actual_ms, trigger_conditions, payload, result_ref, error, retry_count}`

**Trigger condition flags:**
```js
const JOB_TRIGGER = {
  ALWAYS:   0b0001,
  IDLE:     0b0010,
  CHARGING: 0b0100,
  DESKTOP:  0b1000,
  MANUAL:   0b10000,
};
```

**vault-scheduler.js — public API:**
```js
function startScheduler()          // begin tick loop
function stopScheduler()           // halt (e.g. when user closes vault)
async function enqueueJob(type, payload, triggerConditions, priority)
async function cancelJob(id)
async function runJobNow(id)       // manual override — bypasses trigger conditions
function registerJobHandler(type, { estimateFn, runFn })
// estimateFn(payload) → estimated ms
// runFn(job, onProgress) → result
```

**Condition detection:**
```js
async function _checkConditions(triggerConditions)
// IDLE: document.visibilityState === 'hidden' OR requestIdleCallback available
// CHARGING: navigator.getBattery() if available; fallback: 00:00–06:00 local time
// DESKTOP: check if connector DataChannel is live (global _dcChannel !== null)
// ALWAYS: always true
// MANUAL: always false (only runJobNow() bypasses)
```

**Desktop offload (when DESKTOP condition met):**
```js
// vault-scheduler.js sends over DataChannel:
{type:"job_offload", job_id, job_type, payload}

// connector/index.html responds with:
{type:"job_progress", job_id, pct, eta_ms}  // interim updates
{type:"job_result", job_id, result}          // on completion
{type:"job_error", job_id, error}            // on failure
```

**Queue UI panel (vault.html):**
- Nav item "Queue" (icon: clock/stack)
- Job list: status icon, type label, estimated time, progress bar
- Status filter tabs: All / Pending / Running / Done / Failed
- Per-job "Run now" button
- "Run all pending" button
- Scheduler settings: toggle auto-conditions (idle, charging, desktop)
- Header badge: spinner + pending count when scheduler is active

**Acceptance criteria:**
- [ ] `enqueueJob()` writes to IDB wf-jobs
- [ ] Scheduler tick runs; picks up eligible jobs respecting trigger conditions
- [ ] Failed jobs retry up to 3 times with backoff; then status = `failed`
- [ ] Queue UI panel renders all jobs with correct status
- [ ] "Run now" overrides conditions and executes job
- [ ] Desktop offload: `job_offload` message sent over DataChannel when DESKTOP condition met

---

### VC-13 — Event Log & Transcript Engine

**Session scope:** 2 sessions (13a: event capture; 13b: HTML+RDFa generation + revision)  
**Depends on:** VC-10 (call session events), VC-11 (data sharing events), VC-12 (jobs)  
**Read first:** `docs/js/vault-scheduler.js` (job registration), `docs/js/vault-meds-lod.js` (LOD lookup pattern)

**IDB changes:**
- Add store `wf-events` (keyPath: `id`)
- Record: `{id, sessionId, seq, type, actorDid, ts, payload, hash, prevHash}`
- Hash chain: `hash = sha256(JSON.stringify({seq, type, actorDid, ts, payload}) + prevHash)`

**Event types captured:**
```js
'call.start', 'call.end',
'participant.join', 'participant.leave',
'data.request', 'data.approve', 'data.deny', 'data.serve',
'message.text', 'speech.segment',
'call.record.start', 'call.record.stop'
```

**vault-transcript.js — public API:**
```js
async function captureEvent(sessionId, type, actorDid, payload)
// Appends to wf-events; computes hash chain; enqueues transcript.generate job if not already queued

async function generateTranscript(sessionId)
// Job handler for transcript.generate
// Returns: HTML string (the full RDFa document)

async function annotateTranscript(sessionId)
// Job handler for transcript.annotate
// Looks up key terms via vault-meds-lod.js → adds resource= attributes
// Marks ambiguities with wf:Ambiguity

async function saveRevision(sessionId, deltaText, correctedByDid, privateKey)
// Signs delta with Ed25519; stores wf:Revision; updates transcript HTML
```

**HTML+RDFa structure:**
```html
<html prefix="wf: https://wellfare.social/ns/vault# dcterms: http://purl.org/dc/terms/">
<body vocab="https://wellfare.social/ns/vault#" typeof="wf:CommunicationTranscript">
  <!-- wf:hasSegment sections for each event -->
  <!-- wf:AmbiguityLog section -->
  <!-- wf:RevisionHistory section -->
  <!-- wf:DataSharingLog section (receipts) -->
</body>
```

**Acceptance criteria:**
- [ ] `captureEvent()` writes to wf-events with valid hash chain
- [ ] `generateTranscript()` job produces valid HTML+RDFa from events
- [ ] `annotateTranscript()` adds `resource=` for known medication names
- [ ] `wf:Ambiguity` marked for unresolved entities
- [ ] `saveRevision()` produces Ed25519-signed revision; chain is verifiable

---

### VC-14 — Language Transcoding

**Session scope:** 1 session  
**Depends on:** VC-12 (scheduler jobs), VC-13 (wf:SpeechSegment events)  
**Read first:** `docs/js/vault-scheduler.js` (registerJobHandler), `docs/js/vault-transcript.js` (captureEvent)

**vault-comms-transcode.js:**
```js
async function detectAvailableTier()
// Returns: 'webspeech' | 'local-llm' | 'external-api' | null

function startRealtimeTranscription(stream, sessionId, langHint)
// Level 1 (WebSpeech): SpeechRecognition API on live audio stream
// Calls captureEvent(sessionId, 'speech.segment', selfDid, {original, lang})
// On result: enqueues transcript.transcode job for translation if lang ≠ vault lang

async function transcodeSegment(segment, targetLang)
// Job handler for transcript.transcode
// Level 2: transformers.js pipeline('translation', ...) if available
// Level 3: POST to user-configured endpoint (with consent confirmation)
// Returns: { translated, targetLang, serviceUsed }

// wf:LanguageService provenance node added to each segment:
// { type: 'wf:LanguageService', provider: 'webspeech'|'local-llm'|'external', model, lang }
```

**Acceptance criteria:**
- [ ] `detectAvailableTier()` correctly identifies WebSpeech API availability
- [ ] Level 1: live transcription starts; `speech.segment` events appear in wf-events
- [ ] Level 2 stub: `local-llm` detected when transformers.js is present
- [ ] Level 3: blocked until user gives explicit consent per session
- [ ] Provenance `wf:LanguageService` node written into transcript RDFa

---

### VC-15 — Content Package & Manifest

**Session scope:** 1 session  
**Depends on:** VC-13 (transcript), VC-11 (receipts), VC-12 (jobs)  
**Read first:** `docs/js/vault-sanctuary-evidence.js` (OTS anchoring), `docs/js/vault-crypto.js` (toB64)

**vault-package.js — public API:**
```js
async function buildPackage(sessionId)
// Job handler for package.build
// Collects: transcript HTML, events NDJSON, receipt JSON-LD files
// Generates manifest.jsonld
// Enqueues ots.submit job for manifest hash
// Returns: { manifest, files: Map<name, blob> }

async function downloadPackage(sessionId)
// Calls buildPackage if not already built
// Assembles zip (JSZip or File System Access API)
// Triggers browser download

function generateManifest(sessionId, artefacts, odrlPolicyRef)
// Returns JSON-LD wf:ContentPackage with artefact hashes + ODRL policy
```

**Manifest shape:**
```json
{
  "@context": {"wf":"https://wellfare.social/ns/vault#", "dcterms":"http://purl.org/dc/terms/", "odrl":"http://www.w3.org/ns/odrl/2/"},
  "@type": "wf:ContentPackage",
  "@id": "urn:uuid:<sessionId>",
  "dcterms:title": "...",
  "wf:participants": [...],
  "odrl:hasPolicy": {"@id": "<agreement uid>"},
  "wf:artefacts": [
    {"@type":"wf:TranscriptArtefact", "wf:hash":"sha256-...", "dcterms:format":"text/html"},
    {"@type":"wf:EventLogArtefact",   "wf:hash":"sha256-...", "dcterms:format":"application/x-ndjson"},
    {"@type":"wf:ReceiptArtefact",    "wf:hash":"sha256-..."}
  ],
  "wf:revisionChainRoot": "<hash of first revision>",
  "wf:otsProof": null  // set to base64 .ots bytes when confirmed
}
```

**Acceptance criteria:**
- [ ] `buildPackage()` collects all session artefacts
- [ ] Manifest JSON-LD validates (all hashes present, ODRL ref present)
- [ ] `ots.submit` job enqueued for manifest hash
- [ ] `downloadPackage()` triggers browser download of zip
- [ ] Package contents open-able in browser (transcript.html renders RDFa)

---

## IDB version roadmap

| IDB version | When | New stores |
|-------------|------|------------|
| v3 | current | wf-s, wf-sc, wf-meds, wf-ml, wf-pc, wf-dl |
| v4 | VC-7 | + wf-contacts, wf-relationships, wf-agreements |
| v5 | VC-12 | + wf-jobs |
| v6 | VC-13 | + wf-events |

## Script load order roadmap (vault.html)

Current (v0.0.5):
```
vault-idb → vault-crypto → vault-did → vault-nym → vault-mock →
vault-sanctuary-pins → vault-sanctuary-log → vault-sanctuary-evidence →
vault-meds-reminders → vault-meds-lod → vault-meds-manager
```

Final target (v0.0.6):
```
vault-idb → vault-crypto → vault-did → vault-nym → vault-mock →
vault-directory → vault-handshake → vault-comms-gate → vault-comms-call →
vault-scheduler → vault-transcript → vault-comms-transcode → vault-package →
vault-cv →
vault-sanctuary-pins → vault-sanctuary-log → vault-sanctuary-evidence →
vault-meds-reminders → vault-meds-lod → vault-meds-manager
```
