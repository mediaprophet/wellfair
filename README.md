# Webizen WellFair (`0.0.41-wellfair-native-overhaul`)

**Copyright (c) 2026 Timothy Charles Holborn**  
**https://www.linkedin.com/in/ubiquitous/ | timothy.holborn@gmail.com**  
**License:** Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)

Native Desktop & Mobile Personal Sanctuary, Biophysical Telehealth (`rPPG`), Pharmacokinetic (`RK4`) Medication & Nutrition Engine, Holographic 10D v2 (`HOLO` `0x0306`) Human Reference Atlas (`HRA` / `UBERON` / `CL` / `HGNC`), Dual-PIN Plausible-Deniability Duress Vault, and Role-Tailored Verifiable PDF (`%PDF-1.7` + PAdES B-B & `QECP`) Specialist Co-Signing Workbench built on **QualiaDB**, **Etalon**, and **Aether Native**.

---

## Transformational Architecture (`WP-WF-APP1..6`)

1. **`crates/wellfair-core-q42` — Biophysical Telehealth, RK4 Pharmacokinetics, 10D v2 Living Anatomy & Sanctuary Vault**:
   - **Multi-Band Camera rPPG & Consent-Gated WebRTC DataChannel (`biophysical_rppg_telehealth.rs`)**:
     - Chrominance (`CHROM`, De Haan & Jeanne) and Plane-Orthogonal-to-Skin (`POS`, Wang et al.) blood-volume-pulse extraction from camera facial ROIs (`Forehead`, `LeftCheek`, `RightCheek`) with Hann-windowed radix-2 Cooley-Tukey FFT spectral estimation, SNR quality certification, Vagal HRV (`RMSSD`, `SDNN`, `LF/HF` ratio), Thoracic Optical Phase-Flow Respiration (`vision_respiration`), Presentation Attack Detection (`vision_liveness_pad`), and Vocal Formant/Jitter Prosody (`qualia-audio`).
     - Streams granular, consent-gated, hash-chained `SignedCallTelemetryFramePacket` frames over a `Noise_XX` + `ML-KEM-1024` WebRTC DataChannel.
   - **4th-Order Runge-Kutta (`RK4`) Pharmacokinetic ODE Solver, Nym Barcode Nutrition & 7-Layer (`L0`–`L6`) 10D v2 Living Anatomy (`pharmacokinetics_meds_diet_anatomy.rs`)**:
     - Solves the coupled 1-compartment oral absorption ODE system ($\frac{dA_{\text{gut}}}{dt} = -k_a A_{\text{gut}}$, $\frac{dC_{\text{plasma}}}{dt} = \frac{F \cdot k_a \cdot A_{\text{gut}}}{V_d} - k_e C_{\text{plasma}}$) via `RK4`, computes $C_{\max}$, $t_{\max}$, therapeutic window status, and CYP450 metabolic interaction alerts.
     - Nym-routed offline/anonymous Camera Barcode Nutrition Scanner (`Open Food Facts` + `FoodOn`) and 7-Layer (`L0`–`L6` `L6QuantumPhysics`) Holographic 10D v2 (`HOLO` `0x0306` + `SDFB` + `EMF` v4) Human Reference Atlas (`HRA` / `UBERON` / `CL` / `HGNC`) organ mapping.
   - **Dual-PIN Plausible-Deniability Duress Vault, 7 N3Logic Clinical/Trauma Rules, Wearable `.q42` Compiler & Delegated-Agent Guard (`sanctuary_duress_n3_shacl_wallet.rs`)**:
     - Dual-PIN authentication: entering the **Duress Decoy PIN** (`9911`) opens a benign fitness/hydration cover vault while silently freezing all active online specialist leases; entering the **Normal Sanctuary PIN** (`4210`) unlocks the full encrypted `.q42` (`Q42\0` v4 `NQuin48`) Sanctuary Vault.
     - Evaluates the 7 N3Logic clinical/trauma-cascade rules (`mental_health.n3`, `vitals.n3`, `nutrition.n3`, `sleep_analysis.n3`, `womens_health.n3`, `fitness_goals.n3`, `trauma_cascade.n3`) and enforces the **Delegated-Agent Principle** (`DelegatedNaturalPersonAgent` — AI agents are strictly bounded, revocable instruments of natural persons, never independent legal entities).
2. **`crates/wellfair-aether-ui` — Native Desktop & Mobile Aether RSX Application**:
   - 7-Workspace native shell (`Telehealth & Camera rPPG`, `Medications, Diet & 10D v2 Anatomy`, `7-Rule N3 Clinical & Wearable .q42`, `Sanctuary Vault & Plausible-Deniability Duress`, `Specialist Lease & Verifiable PDF Co-Sign`, `Zero-Trust Welfare Vouchers & Cooperative Projects`, `Chat-Graph & Delegated Natural-Person Agents`) with Adaptive Responsive Layout (`Desktop 3-Pane Workbench` vs. `Mobile Portrait Sanctuary Card`).
3. **`native/` — Desktop & Mobile Launch Binary (`wellfair`)**:
   - Launches the native Aether GPU window or runs headless CLI diagnostics (`rppg-sim`, `pk-sim`, `verify-duress`, `compile-biometrics`).
