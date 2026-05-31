# Episteme:WellFair

**v0.0.6-dev** · [Technical reference →](techinfo.md) · [License: CC BY-NC-ND 4.0](COPYRIGHT.md)

> *Peace infrastructure for the natural person — running on your hardware, connected to the world on your terms.*

---

## Why this exists

Imagine you are trying to leave a dangerous situation. Your phone is your lifeline — but every app on it reports your location, your contacts, your movements to servers you don't control. Your medical records live in a hospital system you can't access without an appointment. Your welfare payments are tied to a bank account that can be monitored or frozen. A transaction can reveal where you slept last night.

For trafficking survivors, people fleeing domestic violence, and anyone whose safety depends on information control, **data privacy is not a preference — it is a survival requirement**.

WellFair was designed around this reality. Your health data, your identity credentials, your communications — they live on your device, encrypted, under your control. When you choose to share them (with a doctor, a lawyer, a social worker), you do so on your own terms, for a defined purpose, and the sharing stops when you say so.

This is what we mean by **peace infrastructure**: software that extends your capacity to act in the world without exposing you to the people trying to harm you.

See: [*The Untransferable Code*](https://www.youtube.com/watch?v=HJJs-Ve-Dhg) — the philosophical foundation of this work.

---

## What works today

Everything below runs in your browser. No accounts. No servers. No data leaves your device unless you explicitly share it.

**Health vault**
- Medication tracker — daily schedule, take/skip log, overdue alerts
- Drug interaction engine — RxNorm/Wikidata lookups, severity badges
- Diet log — daily food entries, macro totals, barcode scanner (camera)
- Biometrics import — Samsung Health CSV → encrypted vault via WebAssembly parser
- Export any health data as Turtle RDF, run SPARQL queries, validate against SHACL shapes

**Privacy & safety**
- Sanctuary Mode — a hidden, double-encrypted workspace for sensitive records (Unvarnished Log, Contingency Protocols)
- Duress decoy — a second PIN opens an identical-looking vault, fires a silent alert to your trusted contacts, hides Sanctuary entirely
- Dead Man's Switch — configurable check-in; sends anonymous alerts via Nym Mixnet if you miss one
- Tripwire Dashboard, Synthesis Engine, Evidentiary Export — build a verifiable record of what happened, signed with your identity credentials, anchored to Bitcoin via OpenTimestamps

**Verified communications**
- Verified Directory — encrypted contact graph; institutions must prove who they are before they can ring you
- Semantic Handshake — both parties sign a cryptographic agreement specifying exactly what may be shared before a call begins
- Inbound caller gating — unknown callers are held at a verification screen; invalid signatures are silently rejected
- Voice/video calls — end-to-end encrypted, vault-to-vault or guest link (no installation required for the other party)
- Live data sharing during calls — approve or deny each section independently; every share generates a signed receipt
- Call profiles — per-contact presets (GP, mental health, legal, crisis support, carer, etc.)
- Language transcoding — three-tier progressive: WebSpeech (live, local) → local LLM → external API (consent-gated per session)
- Call transcript export — HTML+RDFa, cryptographic event chain, participant revision signing

**Human-Centric Wallet**
- Lightning wallet integration (HCW-1) — confidential transaction infrastructure; transaction-to-location linkage is prevented by design
- Nym Mixnet routing — anonymous messaging that cannot be correlated to your IP address

**Semantic health core** *(legacy layer — local research use)*
- Samsung Health CSV → RDF/Turtle via Rust/WebAssembly
- In-browser SPARQL (oxigraph), SHACL validation
- HuBMAP Human Reference Atlas semantic linking

---

## Quick start

```bash
python -m http.server 3000 --directory docs
```

| Page | URL | Purpose |
|---|---|---|
| **Daily vault** | `http://localhost:3000/vault.html` | Your phone — PIN unlocks full owner workspace |
| **Demo mode** | `http://localhost:3000/vault.html?demo` | No PIN — sample data, nothing saved |
| **Desktop connector** | `http://localhost:3000/connector/` | Stateless desktop terminal — closes clean |
| **Pairing bridge** | `http://localhost:3000/webconnect.html` | Phone-side QR scan → profile → serve |
| **Guest call link** | `http://localhost:3000/join.html?id=<session>` | Join a call without installing anything |
| **Nym test harness** | `http://localhost:3000/nym-test.html` | Validate Nym SDK before activating |

**Demo PIN: `1234`** (full vault with real persistence)

Requires Chrome 111+, Edge 111+, or Firefox 130+ (Ed25519 + X25519 WebCrypto).

The phone (`vault.html`) is the authoritative datastore. The desktop connector holds nothing — closing the tab destroys all session state.

---

## What we're building next

**HCW-3 — Exchange on-ramp**: Let people receive welfare payments and convert to spendable value without creating a financial trail linking transactions to their location or identity.

**HCW-4 — Blind Proxy**: An intermediary layer that lets institutions pay into a vault-controlled address without ever learning the recipient's real identity — designed specifically for welfare and emergency payments.

**HCW-5 through HCW-10**: Progressive credential disclosure, integration with Solid/ActivityPub for selective federation, and peer-to-peer data sharing with verifiable provenance — so a doctor or social worker can pull exactly the records they need, nothing more.

**Nym activation**: The anonymous routing layer is built and wired; it needs one validation run against the Nym Sandbox testnet to set the final SDK URL.

**Real-device testing**: iOS Safari, Android Chrome, Firefox 130+ — the matrix is in [`instructions/BROWSER_COMPAT.md`](instructions/BROWSER_COMPAT.md).

---

## Who we're looking for

This project is at a stage where the right collaborators would make an enormous difference:

- **Privacy engineers** — the crypto primitives are solid; there's deep work to be done on the anonymous payment layer and Nym integration
- **Health informaticists** — the RDF/SHACL/FHIR layer needs clinical review; the data models should reflect how health records are actually used in emergency situations
- **Social workers and lived-experience advisors** — the features we're building (sanctuary mode, duress decoy, dead man's switch) need to be validated against real threat models by people who know them
- **UI/UX designers** — the vault is functional; it needs to be fast and clear under stress, on a phone screen, possibly with shaking hands
- **Semantic web engineers** — the ODRL/SHACL access profile layer, identity credentials, and transcript RDFa need people who understand the standards deeply

If any of this resonates, open an issue or reach out directly.

---

## Technical reference

Full architecture, IDB schema, module inventory, capability table, and remaining task list: **[techinfo.md](techinfo.md)**

---

## License

**Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**

Copyright © 2025–2026 Timothy Charles Holborn.

See [`LICENSE`](LICENSE) and [`COPYRIGHT.md`](COPYRIGHT.md) for full details.
