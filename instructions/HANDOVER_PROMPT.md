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

LAST SESSION (2026-06-03):
- Comprehensive architecture review across WellFair repo + qualiaDB repo + cooperative.html + Android app modules
- Decided: primary vault pivots from browser PWA to Tauri v2 native app (iOS/Android); vault.html WebView is preserved as the UI shell
- Decided: cooperative projects (obligation matrix, µ-units, Merkle commits, PFM, credential vault, Maslow VP, directory harmonization) are all in scope
- Wrote TODO.md (master task list) and instructions/HANDOVER_CURRENT.md (living handover) — both are new and complete
- Did NOT commit anything — working tree has staged deletions and modified JS files

---

CRITICAL BLOCKER — do this before any other work:
The CI workflow (.github/workflows/pages.yml) does `cd wellfare-core` but the Rust crate source has been moved to `legacy_pwa/wellfare-core/` in an uncommitted working-tree change. The CI is currently broken. Fix this first (TODO item 0.1), then commit the working tree cleanly as two commits (TODO item 0.2).

---

START HERE (first session after this handover):
1. Read the three documents above
2. Fix CI path (TODO 0.1) — 15 min
3. Commit working tree cleanly as two commits (TODO 0.2) — 20 min
4. Update CLAUDE.md to reflect the architecture pivot (TODO 0.3) — 20 min
5. Move wellfare-core to repo root (TODO W1) and verify CI still builds — 30 min
6. Then start TODO W2–W7 (complete QualiaStore + SPARQL + SHACL in wellfare-core) OR TODO CP1 (cooperative projects panel) — your call based on priority

---

KEY FACTS:
- Primary vault: docs/vault.html (phone-first PWA, currently working; Tauri app is the target)
- Analytics dashboard: docs/app.html (Streamlit/stlite, 512KB — read in chunks with offset/limit)
- Engine WASM: docs/pkg/wellfare_core_bg.wasm (282KB, v0.0.4-dev, already built and deployed)
- Rust source: legacy_pwa/wellfare-core/ (Cargo.toml, src/wasm.rs, src/qualia_bindings.rs etc.)
- QualiaStore.insert_quin() and query_subject() are stubs — they return mock values and do nothing
- WasmHealthStore and validate_health_turtle() are missing from WASM exports (vault-wasm.js calls them)
- qualiaDB external repo: https://github.com/mediaprophet/qualiaDB — Tauri v1.5 desktop, Kotlin/JNI Android, qualia-core-db engine
- Active branch: feature/qualia-db-integration (no commits ahead of master — all work is in the working tree)
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
