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
- W7: oxigraph added to Cargo.toml; qualia-core-db moved to optional "qualia" feature
- W2/W3: QualiaStore now stores real Vec<[u64;5]> quints; insert/query all functional
- W4: store.rs (HealthStore + oxigraph); WasmHealthStore wasm export; SPARQL SELECT/ASK/CONSTRUCT
- W5: shapes.rs (6 SPARQL ASK health constraints); validate_health_turtle() wasm export
- WASM rebuilt: docs/pkg/ now 3.3 MB (up from 282 KB — oxigraph adds ~3 MB)
- All 5 commits now pushed to origin feature/qualia-db-integration (5 ahead of master)
- Working tree: clean

---

START HERE (next session):
1. Read the three documents above
2. Choose next task from TODO.md:
   - **CP1** (Cooperative Projects panel) — vault-projects.js + IDB v11 wf-projects/wf-contributions/wf-obligations
     This is the highest-impact user-visible feature. Requires no Rust work.
   - **W8** (dual-target Cargo.toml) — add native (non-wasm) target for Tauri; or
   - **W9** (per-persona demo CSVs) — wire 7 distinct health datasets to app.js personas
3. Note: CI will fail on the pages.yml stlite step until legacy_pwa/scripts/build_stlite.py
   paths inside the script are correct. Check CI logs after the first push to master.

---

KEY FACTS:
- Primary vault: docs/vault.html (phone-first PWA, currently working; Tauri app is the target)
- Analytics dashboard: docs/app.html (Streamlit/stlite, 512KB — read in chunks with offset/limit)
- Engine WASM: docs/pkg/wellfare_core_bg.wasm (282KB, v0.0.4-dev, already built and deployed)
- Rust source: wellfare-core/ (repo root — Cargo.toml, src/wasm.rs, src/qualia_bindings.rs etc.)
- QualiaStore.insert_quin() and query_subject() are stubs — they return mock values and do nothing
- WasmHealthStore and validate_health_turtle() are missing from WASM exports (vault-wasm.js calls them)
- qualiaDB external repo: https://github.com/mediaprophet/qualiaDB — Tauri v1.5 desktop, Kotlin/JNI Android, qualia-core-db engine
- Active branch: feature/qualia-db-integration (5 commits ahead of master, pushed)
- WASM at docs/pkg/: 3.3 MB (oxigraph included); new exports: WasmHealthStore, validate_health_turtle, QualiaStore (functional)
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
