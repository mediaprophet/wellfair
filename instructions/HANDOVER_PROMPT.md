# WellFair — Session Start Prompt
> Paste the block below at the start of a new Claude Code session.
> Update the "Last session" and "Start here" lines when the active task changes.

---

```
You are picking up the WellFair + qualiaDB project. Read the following documents before doing anything else — in this order:

1. CLAUDE.md                              — mandatory project orientation, terminology, architecture constraints
2. instructions/HANDOVER_CURRENT.md       — current state, decisions made, what is blocked, what to do next
3. TODO.md                                — master task list; find the first unchecked [ ] item in your area

Do NOT start writing code until you have read all three. They are short and contain decisions that will save you from going the wrong direction.

---

LAST SESSION (2026-06-04 — session 3):
- Completed W2/W3/W4/W5/W7 in wellfare-core (commit b1814e9, pushed)
- W7: oxigraph 0.4 added to Cargo.toml; qualia-core-db moved to optional "qualia" Cargo feature
  (qualia-core-db depends on wgpu — too heavy for default WASM binary; enable with --features qualia)
- W2/W3: QualiaStore: functional Vec<[u64;5]> store; insert_quin/query_subject/predicate/context all work;
  wasm-bindgen auto-converts u64 ↔ BigInt — matches vault-wasm.js Lexicon/JSONtoQuinSerializer
- W4: store.rs (HealthStore + oxigraph::Store); WasmHealthStore WASM export (new/load_turtle/query);
  SPARQL SELECT/ASK/CONSTRUCT verified in .d.ts
- W5: shapes.rs (6 SPARQL ASK constraints: sleep efficiency/duration, heart rate, weight, body fat, steps);
  validate_health_turtle() returns {"valid":bool,"checked":6,"violations":[...]}
- WASM rebuilt: docs/pkg/ now 3.3 MB (up from 282 KB; oxigraph adds ~3 MB; wasm-opt applied)
- 6 commits total on feature/qualia-db-integration, all pushed; working tree clean

---

START HERE (next session):
1. Read the three documents above
2. Start **CP1** (recommended — highest-impact user-visible feature, no Rust needed):
   - Create docs/js/vault-projects.js (project list, join flow, contribution log, obligation dashboard)
   - Add IDB v11 in vault-idb.js (stores: wf-projects, wf-contributions, wf-obligations)
   - Wire "Projects" panel into vault.html nav
   - See TODO.md section CP for full task list (CP1–CP6)
3. Alternative: OC1 (Ontology Converter in app.html) — now unblocked by W4; file picker → Turtle/JSON-LD → N-Quads via WasmHealthStore

---

KEY FACTS:
- Primary vault: docs/vault.html (phone-first PWA, currently working; Tauri app is the target)
- Analytics dashboard: docs/app.html (Streamlit/stlite, 512KB — read in chunks with offset/limit)
- Engine WASM: docs/pkg/wellfare_core_bg.wasm (3.3 MB, v0.0.4-dev + oxigraph, built and deployed)
- Rust source: wellfare-core/ (repo root — store.rs, shapes.rs, qualia_bindings.rs, wasm.rs etc.)
- WASM exports (all verified in .d.ts): WasmHealthStore, validate_health_turtle, QualiaStore (all functional — not stubs)
- qualiaDB external repo: https://github.com/mediaprophet/qualiaDB — Tauri v1.5 (needs v2 upgrade), Kotlin/JNI Android
- Active branch: feature/qualia-db-integration (6 commits ahead of master, pushed)
- Demo PIN: 1234 — use vault.html?demo for UI-only checks (no PIN required)
- Dev server: python -m http.server 3000 --directory docs
- Testing: always use mcp__Claude_in_Chrome__* tools — Claude app preview lacks WebCrypto

---

TERMINOLOGY (enforced — do not use the wrong terms):
- "Identity credentials" — never "DIDs" or "VCs" in user-facing text
- "Verified Directory" in code — "Contacts" or "Directory" in UI — never "sovereign" or "self-sovereign"
- SHACL/RDFS for shapes about people — OWL only for policy artefacts (EdgeConstraint etc.)
- wf: namespace → https://wellfare.social/ns/vault#

---

ARCHITECTURE (locked — do not revisit without explicit instruction):
- Phone is authoritative vault; desktop is always stateless
- Gun.eco for WebRTC signalling only — health data never touches Gun relay nodes
- Tauri v2 is the target mobile platform — vault.html WebView is the UI, Rust handles all crypto/storage/Nym
- wellfare-core is the bridge crate (health-specific Rust wrapping qualia-core-db)
- Lightning + Nym is the unified payment rail for welfare payments, cooperative obligations, and research bounties
- Directory harmonization: Verified Directory + SocialBook + cooperative contributor list = one wf-contacts graph

Update instructions/HANDOVER_CURRENT.md and TODO.md at the end of this session.
```
