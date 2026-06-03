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

LAST SESSION (2026-06-03 — session 2):
- Completed all handover start-up tasks: 0.1 CI fix, 0.2 two clean commits, 0.3 CLAUDE.md pivot, W1 wellfare-core to root
- Three commits on feature/qualia-db-integration (3 ahead of master, not pushed):
  - 70f5bb6: chore(restructure) — legacy Python/Rust → legacy_pwa/, CI fix, TODO.md, instructions/
  - dd9a5a3: feat(qualiadb) — vault-wasm.js bridge, vault-idb.js v10, vault-sentinel.js, CLAUDE.md update
  - 20c5f80: chore(W1) — wellfare-core moved to repo root, CI path restored
- Working tree is clean (only untracked 32-02.url Windows shortcut, ignore it)
- No CI verification done yet — requires pushing to GitHub for GitHub Actions to run

---

START HERE (next session):
1. Read the three documents above
2. Choose: W2–W7 (implement real QualiaStore in wellfare-core) OR CP1 (Cooperative Projects panel in vault.html)
   - W2–W7: start with W7 (add oxigraph to Cargo.toml) then W4 (WasmHealthStore), then W2/W3 (real insert/query)
   - CP1: vault-projects.js new module, IDB v11 stores (wf-projects, wf-contributions, wf-obligations)
3. Push branch to GitHub to trigger CI verification of the pages.yml build path
   (run: git push -u origin feature/qualia-db-integration)

---

KEY FACTS:
- Primary vault: docs/vault.html (phone-first PWA, currently working; Tauri app is the target)
- Analytics dashboard: docs/app.html (Streamlit/stlite, 512KB — read in chunks with offset/limit)
- Engine WASM: docs/pkg/wellfare_core_bg.wasm (282KB, v0.0.4-dev, already built and deployed)
- Rust source: wellfare-core/ (repo root — Cargo.toml, src/wasm.rs, src/qualia_bindings.rs etc.)
- QualiaStore.insert_quin() and query_subject() are stubs — they return mock values and do nothing
- WasmHealthStore and validate_health_turtle() are missing from WASM exports (vault-wasm.js calls them)
- qualiaDB external repo: https://github.com/mediaprophet/qualiaDB — Tauri v1.5 desktop, Kotlin/JNI Android, qualia-core-db engine
- Active branch: feature/qualia-db-integration (3 commits ahead of master, not yet pushed)
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
