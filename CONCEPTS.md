# The Untransferable Code — Conceptual Framework

> This document is written for AI agents, developers, and contributors who want to
> understand the philosophical foundation behind WellFair's design decisions.
> Architecture choices that might otherwise seem unusual — SHACL over OWL, local-first
> compute, the vault-as-extension-of-self model — follow directly from these concepts.

Reference: [*The Untransferable Code*](https://www.youtube.com/watch?v=HJJs-Ve-Dhg) (Timothy Holborn, 2026)

---

## The core idea

Around the year 2000, the internet shifted from a distributed, relational web toward an
**extraction model** — one that treats human beings as data points to be harvested,
processed, and monetised. This is what we call a **silicon-centric** architecture: the
hardware and platform are primary; the person is an input.

The untransferable code is the counter-thesis:

> *"True technological solutions for protecting human agency cannot be stolen.
> They are inextricably bound to the lived experience and inalienable dignity
> of the natural person."*

Genuine human agency — the capacity to act from within one's own lived experience — is
**untransferable**. It cannot be extracted, stored, bought, or replicated. Any system
that tries to capture it produces something **hollow**: it can verify a record, but it
lacks the capacity to map the common sense needed to protect genuine human agency.

---

## Key terms

**Natural person**
The legal and philosophical term for a human being — as distinct from a corporation,
legal entity, or data profile. In WellFair's design, the natural person is always the
subject, never the object. Code, data, and interfaces exist to extend what the natural
person can do — not to represent or replace them.

**Inalienable**
Cannot be transferred, extracted, or taken away. Used here in the same sense as
"inalienable rights" — qualities or capacities that belong to the natural person by
virtue of being a person, and that no system or agreement can legitimately remove.
The untransferable code is inalienable: it is bound to lived experience in a way that
makes extraction produce only a hollow copy.

**Lived experience**
The actual texture of a person's life — embodied, contextual, relational. A heart rate
reading is a data point. The context of that reading — the stress of eviction proceedings,
the grief of bereavement, the safety of home — is lived experience. No ontological class
or database record can fully contain it.

**Silicon-centric**
An architecture in which the platform, server, or device is the primary node and the
person is a peripheral input. The dominant model of digital health is silicon-centric:
your data lives on someone else's hardware, interpreted by someone else's model,
surfaced to you through someone else's interface.

**Administrative violence**
Harm caused not by direct physical action but by institutional and bureaucratic systems:
incorrect records, denied access, data used against the person it describes, systems
that make a person legible to institutions while making institutions illegible to the
person. WellFair is designed to protect against administrative violence by ensuring the
natural person retains access to and control of their own records.

**Peace infrastructure**
Infrastructure whose primary purpose is protection rather than extraction. Timothy
Holborn developed the computational vault model as peace infrastructure — an inalienable
extension of the self, engineered so that the vault and the natural person it serves
cannot be separated. Compare: a home is peace infrastructure; a CCTV network is not.

**Hollow**
What commercial digital-health models become when they extract data without preserving
the lived context that gives it meaning. A hollow system can verify a claim — "this
person had a heart rate of 95 BPM at 3am" — but cannot understand what that means
within a life. It optimises for the transferable signal and discards the untransferable
context.

**Relational web**
The architecture the internet was designed to be — and the architecture the brain
actually uses. There is no central processor in the human brain; it operates through
chemical synapses crossing gaps between independent nodes. A relational web of data
mirrors this: no central authority, no silo, data flowing through trust relationships
between distributed nodes. Contrast with platform-centric architectures where all data
routes through a single corporate node.

**Verifiable claims / chyrographs**
Instruments of trust that can be verified without requiring a central authority. Medieval
chyrographs (documents split and distributed between parties, reunited to verify
authenticity) are the historical antecedent. W3C Verifiable Credentials are the modern
form. Both allow a claim to be verified without the verifier needing to trust a
centralised registry.

**Computational vault**
The technical instantiation of peace infrastructure. A vault is not a cloud service;
it is a plug-and-play cartridge operating within a federated, socially-aware personal
cloud. Instead of handing data over to a company, a vault pulls distinct encrypted
claims from external nodes, evaluating facts dynamically through verifiable credentials
and query structures. WellFair is a computational vault.

---

## How this maps to WellFair's design decisions

### Local-first compute (P3 / P3A)
If the vault is an inalienable extension of the natural person, it must run on the
natural person's hardware — not on a server that can be switched off, rate-limited,
or subpoenaed. Local-first is not a performance optimisation; it is an architectural
expression of inalienability.

### SHACL/RDFS shapes, not OWL class membership
OWL class membership assigns a natural person to a class: `Person A rdf:type owl:Class`.
This is precisely the reduction the untransferable code resists — a person reduced to a
category, a type, a transferable label. SHACL shapes describe *constraints on how data
about a person should be structured* without asserting what kind of thing the person is.
The person remains prior to the description. The description serves them.

### N3Logic for clinical reasoning
N3Logic rules reason from context — causal, conditional, relational. They can encode
"if a person has had fewer than 5 hours of sleep for 7 consecutive nights AND their
resting heart rate is elevated AND their recorded stress events include housing
instability, THEN flag for adrenal fatigue review." This is contextual, relational
reasoning grounded in the specific situation of a specific natural person.
OWL entailment reasons from class hierarchies — it is good at inferring class membership,
but class membership is exactly what we are avoiding for people.

### Maslow over metrics
A biometric reading without context is hollow. A reading understood within the frame of
Maslow's hierarchy — does this person have adequate shelter? are their close relationships
stable? are they experiencing safety? — becomes meaningful. WellFair maps data to
Maslow's hierarchy because lived experience is not a list of measurements; it is a
structure of needs being met or unmet within a relational world.

### Sanctuary Mode and Proxy Consent
Sanctuary Mode exists because some natural persons face a specific form of administrative
violence: their own data being accessed by people who would use it against them. A duress
PIN or device-lock trigger that instantly obscures sensitive records is not a UI feature;
it is peace infrastructure. Proxy Consent models the actual legal and relational
structures through which natural persons delegate and receive care — guardians, designated
carers, medical professionals — with strict limits that preserve the dignity of the
person being cared for.

### The Social Web (P3-SWA)
A vault that cannot connect to anything is not peace infrastructure; it is isolation.
The Social Web dimension of P3-SWA means the vault can federate — share specific records
with specific parties through open, decentralised protocols (Solid, WebID, ActivityPub)
without becoming a silo or surrendering control to an intermediary. The relational web
is preserved; the inalienability of the vault is preserved.

---

## What this means when you contribute code

1. **The natural person is the subject, not the object.** If you find yourself writing
   code that aggregates people into categories, assigns them to classes, or treats their
   data as the primary artifact, pause and reconsider the design.

2. **Hollow correctness is not enough.** A system that correctly validates a record but
   strips the context that makes it meaningful has failed. Tests should verify that
   context — provenance, relationships, Maslow mapping — is preserved alongside the data.

3. **Extensions must be opt-in and teardown-clean.** Nothing loads until the natural
   person triggers it. Everything releases memory when done. The vault does not accumulate
   background state on behalf of third parties.

4. **Inalienability is an architectural constraint, not a policy.** Local-first is not
   a configuration option that can be toggled off for convenience. The vault runs on the
   natural person's hardware. If a proposed feature requires data to leave the device
   without explicit user action, it requires explicit justification against this
   foundational constraint.

5. **Common sense cannot be fully encoded.** The untransferable code is a reminder that
   the system will always be incomplete — it can support the natural person's judgment but
   cannot replace it. Design interfaces and reasoning outputs accordingly: surfaces for
   human review, not autonomous decisions about people.

---

## The lineage

The design draws on a long tradition of decentralised trust infrastructure:

- **Medieval chyrographs and marcher lords** — frontier resilience built on distributed
  logistics and cryptographic instruments of trust, long before digital encryption
- **Knights Templar financial networks** — complex encrypted holdings across volatile
  territories, demonstrating that trust can be maintained without central authority
- **W3C community groups (2012 onwards)** — WebID, the read/write web, Verifiable
  Credentials — royalty-free open standards for a new web of data
- **Solid Protocol** — Tim Berners-Lee's project for personal data pods, the technical
  substrate of the relational web vision
- **WellFair** — a computational vault implementing these principles as health and
  wellbeing infrastructure for the natural person

The through-line: decentralised, trust-based, resilient at the edges, serving the
natural person rather than the institution.
