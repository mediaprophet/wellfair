# Definition and Implementation Instructions: Pathway B (Shared Rust Core & WASM)
**Application:** wellfare
**Module:** Shared Core & WebAssembly Engine
**Purpose:** To define the architecture, dependencies, data-flow, and step-by-step implementation checklist for migrating the core data processing and ontology-mapping logic from Python to a shared Rust core, exposing it via WASM for browser-only static deployment (GitHub Pages) and via FFI for native mobile deployment.

---

## 1. Architectural Architecture & Core Components

The architecture relies on compiling a single Rust library (`wellfare-core`) to multiple target platforms to guarantee identical data parsing, validation, and semantic reasoning logic across Web, Desktop, and Mobile.

```
                           ┌──────────────────────────┐
                           │   Rust Core Library      │
                           │    (wellfare-core)       │
                           │   CSV Parsers & Serde    │
                           │   RDF-Star Statements    │
                           └─────────────┬────────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              ▼ (wasm-bindgen)           ▼ (flutter_rust_bridge)    ▼ (PyO3)
       ┌─────────────┐            ┌─────────────┐            ┌─────────────┐
       │    WASM     │            │ Mobile FFI  │            │ Python Lib  │
       │   Target    │            │  Bindings   │            │  Extension  │
       └──────┬──────┘            └──────┬──────┘            └──────┬──────┘
              │                          │                          │
              ▼                          ▼                          ▼
       ┌─────────────┐            ┌─────────────┐            ┌─────────────┐
       │ Web Client  │            │ Flutter App │            │  Streamlit  │
       │ (Local JS)  │            │  (iOS/And)  │            │  Backend    │
       └─────────────┘            └─────────────┘            └─────────────┘
```

### 1.1 Local-First Privacy (Zero-Leak Principle)
*   No raw files (Samsung Health export, PDF diagnostics, location telemetry) ever leave the user's physical device.
*   All CSV parsing, semantic RDF serialization, and Prolog compliance auditing are done locally on the CPU (browser tab or native sandbox).
*   Data is stored locally in encrypted storage and synced only to the user's private Solid Pod via authenticated API calls.

---

## 2. Technical Stack and Configuration

### 2.1 Rust Crate (`wellfare-core`)
*   **Parsers**: `csv` crate for fast record processing; `serde` for serialization.
*   **RDF Serialization**: A lightweight RDF-Star string builder or `rio` for generating N-Triples/Turtle.
*   **WASM Binding**: `wasm-bindgen` to export types and functions to JavaScript.
*   **Logic Engine**: Trealla Prolog (`trealla-rust` / `tpl`) compiled to WASM to run compliance and threat audits locally.

### 2.2 Web Browser Client (GitHub Pages)
*   **Framework**: Flutter Web (compiled to WASM/Web) or simple local JS/React.
*   **Ingestion**: `FileUploader` accepts Samsung Health zip exports directly.
*   **Local Storage**:
    *   *Origin Private File System (OPFS)*: For secure sandbox file storage (databases, raw files).
    *   *IndexedDB*: For fast state management and metadata indexing.

### 2.3 Mobile App Client (Flutter FFI)
*   **Bridge**: `flutter_rust_bridge` to execute Rust methods natively on mobile threads.
*   **Storage**: Encrypted SQLite or SQLite with SQLCipher (via `drift` or `sqflite`).

---

## 3. Implementation Plan & Progress Checklist

Below is the execution checklist. We will check off these tasks step-by-step.

### Phase 1: Rust Core Setup (`wellfare-core`)
- [x] Initialize Cargo workspace and create `wellfare-core` library.
- [x] Define shared domain model structs (Weight, Sleep, HeartRate, Steps, DiagnosticReport).
- [x] Implement robust CSV parser in Rust utilizing `csv` and `serde`.
- [x] Implement timestamp normalization utilizing timezone offsets.
- [x] Integrate RDF-Star statement generator for parsed records.

### Phase 2: Web Assembly (WASM) Compilation
- [ ] Setup `wasm-bindgen` targets and configure Cargo for WASM compilation.
- [ ] Expose JS/TS friendly entry points (`parse_health_zip`, `generate_rdf_triples`).
- [ ] Verify WASM builds cleanly using `wasm-pack`.

### Phase 3: Browser Local Ingestion & Storage
- [ ] Build a file uploader input in the client.
- [ ] Read files into browser memory and process them locally via the WASM module.
- [ ] Setup OPFS (Origin Private File System) adapter to persist processed Turtle files locally.
- [ ] Configure IndexedDB index database for quick querying of timeline events.

### Phase 4: Flutter Mobile FFI Setup
- [ ] Generate mobile FFI headers and bindings using `flutter_rust_bridge`.
- [ ] Integrate compiled native library binaries (`.a` and `.so`) into iOS/Android build setups.
- [ ] Wire up Flutter UI views to the shared Rust parsing engine.

### Phase 5: Verification & Deployment
- [ ] Build static target files and deploy to GitHub Pages.
- [ ] Test zero-leak sandbox processing by checking network tabs.
