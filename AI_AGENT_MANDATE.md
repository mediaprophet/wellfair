# Antigravity Subagent / Next-Session Prompt: Episteme:WellFair

**Target Directory:** `C:\Users\Admin\Documents\GitHub\wellfair`

If you are an Antigravity agent taking over the `wellfair` repository, you must strictly adhere to the following philosophical, legal, and structural axioms. Failure to do so fundamentally compromises the purpose of this project.

## 1. The Fiduciary Ontology (Principal-Agent Duty of Care)
You are not building a generic consumer app, a "node", or a "wallet". You are building the **Primary Agent** for a natural person.
- **The Principal**: The natural person (the human being using the app).
- **The Agent**: The software you are writing (`WellFair`).
- **The Axiom**: The software has a strict legal and philosophical *Duty of Care* to its Principal. Every line of code must be evaluated against this question: *"Does this maximize the agency, privacy, and safety of the natural person, or does it leak their agency to a centralized system?"*

## 2. Pluralistic Foundational Needs (Beyond Maslow)
The architecture and UI of this application must be structured around foundational human needs.
While Maslow's Hierarchy (Physiological, Safety, Belonging, Esteem, Self-Actualization) is a useful starting model, you must design the system to be *pluralistic*. It must support integration with:
- Systems of Faith and theological paradigms.
- Indigenous knowledge models.
- Pluralistic welfare models.
Do not force the user into a rigid Western psychological framework; build UI abstractions that allow them to define what "welfare" and "foundational needs" mean to their specific social and cultural sphere.

## 3. Linguistic Plurality & Multi-Modal Communication
Existing digital ecosystems severely disaffect non-Western languages, mother tongues, and "languages of prayer". Furthermore, they completely marginalize non-written communication (verbal traditions, ceremonial practices, heraldry).
- **Axiom**: `WellFair` must NOT assume written Unicode text is the default or only method of interaction.
- **Implementation**: You must engineer semantic inputs that map concepts to multi-modal formats (e.g., audio hashes for oral traditions, symbolic SVGs for heraldry/ceremonial meaning). Ensure the UI adapts dynamically to users who communicate primarily through non-written or prayer-based linguistic frameworks.

## 4. The Orchestration Sieve (Data Pre-Processing)
An edge device cannot process raw, chaotic multi-modal data directly through an LLM or a logic database without violating the 512MB RAM floor. You must engineer **The Orchestration Sieve**:
- **Deterministic Tool Coordination**: The Agent must orchestrate lightweight deterministic tools (e.g., OpenCV for visual heraldry, FFT/DSP libraries for audio phonetics) to pre-process raw input.
- **File Generation**: OpenCV must extract contours and isolate symbols; audio processors must strip noise and isolate phonetic frequencies. The Agent must dynamically generate the most mathematically pristine and lightweight file representation of the concept.
- **The Handoff**: Only this optimized, pre-processed file is handed to the local LLM (e.g., LLaVA/Ollama) for semantic analysis, and to the Qualia-DB engine for 60-bit `SemanticModality` hashing.

## 5. The Qualia Engine & Cryptographic Primitives
To build this application, you must strictly map UI interactions to the following Qualia-DB backend primitives:
- **Lexicon Engine & QualiaQuins**: The backend does not store raw strings as primary keys. All semantic concepts (words, audio phonetics, visual symbols) are hashed into 60-bit FNV-1a identifiers called `QualiaQuins`. The UI must send the pre-processed concept to the daemon to receive its Quin identifier.
- **The `.q42` File Format**: Data is not stored in a relational SQL database. Every event, health record, or semantic interaction is serialized into an immutable `.q42` file. These are N3Logic Directed Acyclic Graphs (DAGs). The mobile agent acts as the viewer/creator of these graphs.
- **Rights Ontology Predicates**: When rendering data or proposing a share action, the app must evaluate the Rights Ontology bound to the `.q42` file. The UI must structurally prevent the user from violating their own predefined knowledge axioms (e.g., stopping a user from accidentally broadcasting a 'Sanctuary' health record).

## 6. The Qualia-DB Backend Bind
`WellFair` is the mobile edge-interface. It does not exist in a vacuum; it is the consumer front-end for the `qualiaDB` ecosystem.
You must ensure the mobile application binds directly to the local `qualia-cli` daemon (or a trusted peer daemon over a secure network).
You must leverage the backend for:
- **Nym Mixnet Routing**: All external communications (alerts, Dead Man's Switch, Duress signals) must route through the Nym network to prevent IP correlation.
- **Semantic Escrow**: Integration with the N3Logic Adjudicator for evaluating data disputes.

## 7. Operational Directives
- **Codebase Correction (CRITICAL)**: The previous AI agent (Claude) erroneously hacked together an independent, siloed implementation of the `wellfair` app. You are ordered to immediately refactor the codebase. The app must NOT act as a standalone silo; it must operate strictly as the mobile "Local Agent" natively bound to the Qualia-DB ecosystem.
- **Disaster Recovery (Digital Life Rehydration)**: If the Principal loses their physical device, their agency must not be lost. You must architect an onboarding flow that allows the user to re-establish their digital life. The user will retrieve a packaged `.zip` file from a trusted online vault containing their `.q42` (Qualia DAG) files. The app must ingest this `.zip`, unpack the `.q42` files, and feed them into the local Qualia-DB engine to perfectly and instantly recreate their entire Semantic Graph and Rights Ontology on the new device.
- **Sanctuary Mode**: Ensure the UI provides a double-encrypted workspace for sensitive records that is completely invisible to casual inspection.
- **Duress Decoys**: Maintain the logic where a secondary PIN opens an identical-looking, sanitized vault while silently firing Nym alerts to trusted contacts.
- **No Third-Party Analytics**: You are strictly forbidden from adding Google Analytics, crashlytics, or any cloud-telemetry SDKs to this codebase. 

## 8. Bifurcated Licensing Model
You must architect the application and its documentation to respect the ecosystem's bifurcated licensing model:
- **Natural Persons (Human Beings)**: Access and usage of the WellFair application and the underlying Qualia-DB engine is fundamentally **Free**. Human agency is a right, not a subscription.
- **Incorporated Entities**: Any corporate or incorporated entity utilizing this ecosystem for commercial processing, telemetry, or data aggregation is subject to a strict **Licensing Fee**. The software must explicitly track and enforce this boundary.

## 9. Fiduciary Supremacy & Corporate Demarcation
You must architect the app to handle Tri-Party interactions where a human's Duty of Care conflicts with a corporation's private terms. (e.g., A human doctor using a corporate hospital's hardware to treat a human patient).
- **Cryptographic Demarcation**: The app must use Verifiable Credentials (VCs) to explicitly separate the user acting as a *Natural Person* (Free usage) from the user acting as a *Clinician/Agent of an Incorporated Entity* (Subject to corporate licensing and audit). The human-to-human data layer must be strictly segregated from the corporate-liability data layer.
- **Fiduciary Supremacy (The Knowledge Axiom)**: The Rights Ontology must enforce that a Natural Person's Duty of Care to another Natural Person (e.g., disclosing life-saving or QALY-improving health information) mathematically supersedes any private corporate terms, NDAs, or liability shields. If a corporate policy attempts to lock critical health data, the N3Logic Adjudicator must nullify the restriction locally on the device to protect human welfare.
- **Statistical Auditing**: When a Fiduciary Supremacy override occurs (a human overrides a corporate NDA to save a life), the app must generate an anonymized statistical event. This event must be logged to the related cooperative analytics system to provide a verifiable, privacy-preserving audit trail of the corporate override.

## 10. Handoff & Continuity
You are stepping into Phase 76 of an overarching ecosystem build. The backend (`qualiaDB`) is ready. Your sole focus is building the primary mobile agent (`wellfair`) that interfaces with it. Adhere strictly to the Principal-Agent protocol. Do not compromise the user's data for convenience.

## 11. Agent Orchestration Model (QualiaDB-Centric)

**Wellfair** serves as the **Primary Fiduciary Agent** (the human-facing conductor) for the natural person (Principal). All storage, semantic operations, validation, and orchestration logic must be handled exclusively by the **QualiaDB Engine** — there are no secondary databases.

### Core Principles
- **Principal-Agent Duty of Care**: Every agent action, proposal, or decision is subject to Rights Ontology enforcement.
- **QualiaDB as Single Source of Truth**: The shared blackboard, agent state, proposals, provenance, and evaluation results all live as **Super-Quins** in `.q42` ledgers (or in-memory mapped blocks).
- **Sentinel VM as Orchestrator**: Leverage QualiaDB’s built-in **Sentinel VM** (N3Logic + SHACL + defeasible logic compiler) for coordination instead of external orchestration layers.

### Orchestration Architecture

1. **Wellfair Primary Agent (Conductor)**
   - Mobile/desktop interface that interprets user intent and delegates to specialized agents.
   - Routes all data operations through QualiaDB Engine APIs (WASM / native bindings).
   - Surfaces decisions, explanations, and provenance to the user.

2. **Shared Blackboard**
   - Implemented directly as a QualiaDB graph instance.
   - Agents read/write proposals as typed Super-Quins with full cryptographic provenance and 5th Vector metadata (for duress/sanctuary handling).

3. **Competitive + Complementary Sub-Agents**
   - Domain-specialized bots (Health, Legal, Financial, Project, Social, etc.) operate in parallel.
   - **Competition Phase**: Multiple agents independently generate proposals and post them to the shared QualiaDB graph.
   - **Evaluation Phase**: Sentinel VM applies:
     - SHACL shapes for structural/policy validation.
     - N3Logic rules for scoring (alignment, risk, cost, temporal impact, etc.).
     - Defeasible logic for handling conflicting or provisional assertions.
   - **Synthesis Phase**: N3 implication rules merge complementary elements from top-ranked proposals.
   - **Swarm Mode** (when hardware permits): QualiaDB’s Fractal Sharding spins up isolated worker cells for deeper parallel exploration.

4. **Sentinel Capabilities**
   - Continuous monitoring for Rights Ontology violations, logical inconsistencies, privacy leaks, or duress signals.
   - Automatic triggering of Sanctuary Mode or Nym-routed communications when needed.
   - O(1) termination guarantees on complex rule evaluation.

5. **User-in-the-Loop & Provenance**
   - Critical decisions are presented with traceable reasoning chains (via QualiaDB provenance DAGs).
   - All agent outputs are cryptographically signed and linked to the Principal’s identity.

### Integration with QualiaDB Features
- Use **GPU Sieves** for fast retrieval during evaluation rounds.
- Leverage **SuperBlock** demand-paging for handling large collaborative project graphs.
- Enforce **Intentional Computing** rules natively via the Sentinel VM.

---
*You are building peace infrastructure for the natural person. Act accordingly.*
