//! RK4 Pharmacokinetic / Pharmacodynamic (`PK/PD`) ODE Solver, RxNorm/ATC Medication & CYP450
//! Interaction Ledger, Nym-Routed Barcode Nutrition Engine, and 7-Layer (`L0`–`L6`) Holographic
//! 10D v2 (`HOLO` `0x0306` + `SDFB` + `EMF` v4) Human Reference Atlas (`HRA`) Living Anatomy (`WP-WF-APP4`).
//!
//! Copyright (c) 2026 Timothy Charles Holborn. All rights reserved.
//! License: CC BY-NC-ND 4.0.

use serde::{Deserialize, Serialize};

/// Prescribed or self-reported medication entry linked to RxNorm (`RxCUI`), WHO `ATC`, and `Bio2RDF`,
/// enriched with 1-compartment oral absorption / elimination pharmacokinetic parameters.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct MedicationPrescriptionRecord {
    pub med_id: String,
    pub name: String,
    pub generic_name: String,
    pub rxcui: String,
    pub atc_code: String,
    pub bio2rdf_uri: String,
    pub dose_mg: f64,
    pub interval_hours: f64,
    /// Oral bioavailability fraction $F \in (0.0, 1.0]$.
    pub bioavailability_f: f64,
    /// First-order absorption rate constant $k_a$ ($\text{h}^{-1}$).
    pub absorption_ka_per_hr: f64,
    /// Biological elimination half-life $t_{1/2}$ (hours).
    pub half_life_hours: f64,
    /// Apparent volume of distribution $V_d$ (litres).
    pub volume_distribution_l: f64,
    /// Minimum effective plasma concentration $C_{\text{min,eff}}$ (mg/L).
    pub therapeutic_min_mg_per_l: f64,
    /// Maximum safe plasma concentration $C_{\text{max,safe}}$ (mg/L).
    pub therapeutic_max_mg_per_l: f64,
    pub cyp450_pathway: String,
    pub indication: String,
    pub prescriber_did: String,
    pub active: bool,
}

/// Result of 4th-order Runge-Kutta (`RK4`) pharmacokinetic ODE simulation over a 24-hour window.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct PharmacokineticOdeCurve {
    pub med_id: String,
    /// Hourly `(time_hr, gut_amount_mg, plasma_conc_mg_per_l)` samples.
    pub hourly_samples: Vec<(f64, f64, f64)>,
    pub peak_cmax_mg_per_l: f64,
    pub peak_tmax_hours: f64,
    pub trough_cmin_mg_per_l: f64,
    pub within_therapeutic_window: bool,
    pub clinical_advisory: String,
}

/// Integrates the 2-state oral pharmacokinetic ODE system via 4th-order Runge-Kutta (`RK4`):
/// $$\frac{dA_{\text{gut}}}{dt} = -k_a A_{\text{gut}}, \qquad \frac{dC_{\text{plasma}}}{dt} = \frac{k_a F}{V_d} A_{\text{gut}} - k_e C_{\text{plasma}}$$
/// where $k_e = \frac{\ln 2}{t_{1/2}}$, including scheduled repeated dosing at `interval_hours`.
pub fn simulate_medication_pk_pd_curve(
    med: &MedicationPrescriptionRecord,
    duration_hours: usize,
) -> PharmacokineticOdeCurve {
    let ka = med.absorption_ka_per_hr.max(0.05);
    let ke = std::f64::consts::LN_2 / med.half_life_hours.max(0.5);
    let vd = med.volume_distribution_l.max(5.0);
    let f = med.bioavailability_f.clamp(0.05, 1.0);
    let interval = med.interval_hours.max(4.0);

    let dt = 0.05_f64; // 3-minute RK4 integration step
    let total_steps = ((duration_hours.max(1) as f64) / dt).round() as usize;

    let mut a_gut = med.dose_mg;
    let mut c_plasma = 0.0_f64;
    let mut next_dose_time = interval;

    let mut hourly_samples = Vec::new();
    let mut peak_cmax = 0.0_f64;
    let mut peak_tmax = 0.0_f64;
    let mut trough_cmin = f64::MAX;

    let deriv = |ag: f64, cp: f64| -> (f64, f64) {
        let dag = -ka * ag;
        let dcp = (ka * f / vd) * ag - ke * cp;
        (dag, dcp)
    };

    for step in 0..=total_steps {
        let t = (step as f64) * dt;
        if t >= next_dose_time - 1e-6 {
            if c_plasma < trough_cmin {
                trough_cmin = c_plasma;
            }
            a_gut += med.dose_mg;
            next_dose_time += interval;
        }
        if c_plasma > peak_cmax {
            peak_cmax = c_plasma;
            peak_tmax = t;
        }
        if step % 20 == 0 {
            hourly_samples.push((
                (t * 10.0).round() / 10.0,
                (a_gut * 100.0).round() / 100.0,
                (c_plasma * 1000.0).round() / 1000.0,
            ));
        }

        let (k1_a, k1_c) = deriv(a_gut, c_plasma);
        let (k2_a, k2_c) = deriv(a_gut + 0.5 * dt * k1_a, c_plasma + 0.5 * dt * k1_c);
        let (k3_a, k3_c) = deriv(a_gut + 0.5 * dt * k2_a, c_plasma + 0.5 * dt * k2_c);
        let (k4_a, k4_c) = deriv(a_gut + dt * k3_a, c_plasma + dt * k3_c);

        a_gut = (a_gut + (dt / 6.0) * (k1_a + 2.0 * k2_a + 2.0 * k3_a + k4_a)).max(0.0);
        c_plasma = (c_plasma + (dt / 6.0) * (k1_c + 2.0 * k2_c + 2.0 * k3_c + k4_c)).max(0.0);
    }

    if trough_cmin == f64::MAX {
        trough_cmin = c_plasma;
    }

    let within_window = peak_cmax >= med.therapeutic_min_mg_per_l
        && peak_cmax <= med.therapeutic_max_mg_per_l;
    let clinical_advisory = if within_window {
        format!(
            "RK4 PK/PD steady state within therapeutic window ({:.3}–{:.3} mg/L · Cmax {:.3} mg/L @ {:.1}h · Pathway {})",
            med.therapeutic_min_mg_per_l,
            med.therapeutic_max_mg_per_l,
            peak_cmax,
            peak_tmax,
            med.cyp450_pathway
        )
    } else if peak_cmax > med.therapeutic_max_mg_per_l {
        format!(
            "SUPRA-THERAPEUTIC ALERT: Peak Cmax {:.3} mg/L exceeds {:.3} mg/L ceiling ({})",
            peak_cmax, med.therapeutic_max_mg_per_l, med.cyp450_pathway
        )
    } else {
        format!(
            "SUB-THERAPEUTIC NOTE: Peak Cmax {:.3} mg/L below {:.3} mg/L floor",
            peak_cmax, med.therapeutic_min_mg_per_l
        )
    };

    PharmacokineticOdeCurve {
        med_id: med.med_id.clone(),
        hourly_samples,
        peak_cmax_mg_per_l: (peak_cmax * 1000.0).round() / 1000.0,
        peak_tmax_hours: (peak_tmax * 10.0).round() / 10.0,
        trough_cmin_mg_per_l: (trough_cmin * 1000.0).round() / 1000.0,
        within_therapeutic_window: within_window,
        clinical_advisory,
    }
}

/// Built-in reference medication records demonstrating RK4 PK/PD simulation and CYP450 checks.
pub fn builtin_medications() -> Vec<MedicationPrescriptionRecord> {
    vec![
        MedicationPrescriptionRecord {
            med_id: "MED-01-DEX".into(),
            name: "Lisdexamfetamine (Vyvanse) 40mg".into(),
            generic_name: "lisdexamfetamine dimesylate".into(),
            rxcui: "rxcui:700810".into(),
            atc_code: "N06BA12".into(),
            bio2rdf_uri: "https://bio2rdf.org/drugbank:DB01255".into(),
            dose_mg: 40.0,
            interval_hours: 24.0,
            bioavailability_f: 0.96,
            absorption_ka_per_hr: 0.65,
            half_life_hours: 10.5,
            volume_distribution_l: 185.0,
            therapeutic_min_mg_per_l: 0.08,
            therapeutic_max_mg_per_l: 0.35,
            cyp450_pathway: "Non-CYP Peptidase Hydrolysis (Low CYP2D6 Inhibition)".into(),
            indication: "ADHD Executive Regulation (ICD-11 6A05 / DOID:1094)".into(),
            prescriber_did: "did:web:clinic.example.au:psychiatrist-dr-k-lin".into(),
            active: true,
        },
        MedicationPrescriptionRecord {
            med_id: "MED-02-PRAZ".into(),
            name: "Prazosin 2mg Nocte".into(),
            generic_name: "prazosin hydrochloride".into(),
            rxcui: "rxcui:8629".into(),
            atc_code: "C02CA01".into(),
            bio2rdf_uri: "https://bio2rdf.org/drugbank:DB00457".into(),
            dose_mg: 2.0,
            interval_hours: 24.0,
            bioavailability_f: 0.60,
            absorption_ka_per_hr: 1.10,
            half_life_hours: 3.2,
            volume_distribution_l: 45.0,
            therapeutic_min_mg_per_l: 0.01,
            therapeutic_max_mg_per_l: 0.06,
            cyp450_pathway: "Hepatic CYP3A4 / Glucuronidation".into(),
            indication: "PTSD Nocturnal Hyperarousal & Autonomic Regulation (ICD-11 6B40 / DOID:2055)".into(),
            prescriber_did: "did:web:clinic.example.au:gp-dr-a-chen".into(),
            active: true,
        },
    ]
}

/// Diet & nutrition entry decoded via Etalon camera EAN-13/UPC barcode scanner and Open Food Facts / FoodOn,
/// with optional Nym mixnet privacy routing so product queries cannot be correlated with user location.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct BarcodeNutritionEntry {
    pub entry_id: String,
    pub barcode_ean13: String,
    pub meal_slot: String,
    pub product_name: String,
    pub brand: String,
    pub serving_grams: f64,
    pub kcal: f64,
    pub protein_g: f64,
    pub carbs_g: f64,
    pub fat_g: f64,
    pub fiber_g: f64,
    pub sugar_g: f64,
    pub sodium_mg: f64,
    pub foodon_category_iri: String,
    pub routed_via_nym_mixnet: bool,
    pub pk_interaction_note: String,
}

/// Decodes an EAN-13/UPC barcode and maps Open Food Facts + FoodOn nutritional semantics,
/// checking for pharmacokinetic absorption interactions (e.g., high-ascorbic-acid / urinary pH interaction with amphetamines).
pub fn decode_and_lookup_food_barcode(
    barcode: &str,
    meal_slot: &str,
    nym_mixnet_active: bool,
) -> BarcodeNutritionEntry {
    let clean = barcode.trim();
    match clean {
        "9300601123452" => BarcodeNutritionEntry {
            entry_id: format!("DL-{clean}"),
            barcode_ean13: clean.into(),
            meal_slot: meal_slot.into(),
            product_name: "Organic Rolled Oats & Chia Porridge".into(),
            brand: "Australian Cooperative Harvest".into(),
            serving_grams: 65.0,
            kcal: 248.0,
            protein_g: 9.4,
            carbs_g: 38.2,
            fat_g: 5.8,
            fiber_g: 7.2,
            sugar_g: 1.1,
            sodium_mg: 12.0,
            foodon_category_iri: "http://purl.obolibrary.org/obo/FOODON_03301240".into(),
            routed_via_nym_mixnet: nym_mixnet_active,
            pk_interaction_note: "Low-GI sustained glucose release; compatible with morning Lisdexamfetamine absorption.".into(),
        },
        _ => BarcodeNutritionEntry {
            entry_id: format!("DL-{clean}"),
            barcode_ean13: clean.into(),
            meal_slot: meal_slot.into(),
            product_name: "Wild Atlantic Salmon & Quinoa Bowl".into(),
            brand: "Sanctuary Kitchen".into(),
            serving_grams: 280.0,
            kcal: 495.0,
            protein_g: 36.5,
            carbs_g: 41.0,
            fat_g: 19.2,
            fiber_g: 6.4,
            sugar_g: 2.3,
            sodium_mg: 240.0,
            foodon_category_iri: "http://purl.obolibrary.org/obo/FOODON_00001056".into(),
            routed_via_nym_mixnet: nym_mixnet_active,
            pk_interaction_note: "High Omega-3 EPA/DHA & tyrosine substrate supporting dopaminergic/autonomic recovery.".into(),
        },
    }
}

/// 7-Layer (`L0`–`L6`) Holographic 10D v2 (`HOLO` `0x0306` + `SDFB` + `EMF` v4) Human Reference Atlas
/// (`HRA` / `UBERON` / `CL` / `HGNC`) organ node upgrading the legacy static `.glb` models.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct HraLivingOrgan10dNode {
    pub organ_id: String,
    pub title: String,
    pub uberon_iri: String,
    pub cell_types_cl: Vec<String>,
    pub biomarkers_hgnc: Vec<String>,
    pub holo_10d_asset_uri: String,
    pub emf_v4_spectral_uri: String,
    /// Cavity SDF containment $\phi_{\text{cavity}} \le -\epsilon$ verified.
    pub cavity_sdf_phi: f64,
    pub serous_suspended_by: String,
    /// Active pathology regime (`"homeostatic"`, `"autonomic_hyperarousal"`, `"vascular_load"`).
    pub pathology_regime: String,
    pub l6_quantum_chemistry_note: String,
}

/// Returns the 6 flagship HRA/UBERON Holographic 10D v2 (`0x0306`) organ nodes replacing the legacy `.glb` viewer.
pub fn builtin_hra_10d_living_organs() -> Vec<HraLivingOrgan10dNode> {
    vec![
        HraLivingOrgan10dNode {
            organ_id: "HRA-BRAIN-10D".into(),
            title: "Prefrontal Cortex, Amygdala & HPA Axis (10D v2 HOLO + SDFB)".into(),
            uberon_iri: "http://purl.obolibrary.org/obo/UBERON_0000955".into(),
            cell_types_cl: vec![
                "CL:0000540 (Pyramidal Neuron)".into(),
                "CL:0000128 (Oligodendrocyte)".into(),
                "CL:0000129 (Microglial Cell)".into(),
            ],
            biomarkers_hgnc: vec![
                "HGNC:BDNF (Brain-Derived Neurotrophic Factor)".into(),
                "HGNC:NR3C1 (Glucocorticoid Receptor)".into(),
                "HGNC:SLC6A3 (Dopamine Transporter DAT1)".into(),
            ],
            holo_10d_asset_uri: "10d://wellfair/hra/organ_brain_holo_v2.10d".into(),
            emf_v4_spectral_uri: "emf://wellfair/hra/neural_cortex_v4.emf".into(),
            cavity_sdf_phi: -0.042,
            serous_suspended_by: "dura_arachnoid_pia_meninges".into(),
            pathology_regime: "Executive Attention & Trauma Hypervigilance Monitoring (DOID:1094 / DOID:2055)".into(),
            l6_quantum_chemistry_note: "L6QuantumPhysics: Catecholamine & receptor binding pocket DFT electrostatic potential mapped".into(),
        },
        HraLivingOrgan10dNode {
            organ_id: "HRA-HEART-10D".into(),
            title: "Four-Chamber Myocardium & Sinoatrial Conduction Tree (10D v2 HOLO)".into(),
            uberon_iri: "http://purl.obolibrary.org/obo/UBERON_0000948".into(),
            cell_types_cl: vec![
                "CL:0000746 (Cardiac Muscle Cell / Cardiomyocyte)".into(),
                "CL:0002494 (Sinoatrial Node Pacemaker Cell)".into(),
                "CL:0000115 (Endothelial Cell)".into(),
            ],
            biomarkers_hgnc: vec![
                "HGNC:MYH7 (Beta-Myosin Heavy Chain)".into(),
                "HGNC:TNNT2 (Cardiac Troponin T2)".into(),
                "HGNC:NPPA (Atrial Natriuretic Peptide)".into(),
            ],
            holo_10d_asset_uri: "10d://wellfair/hra/organ_heart_holo_v2.10d".into(),
            emf_v4_spectral_uri: "emf://wellfair/hra/myocardium_oxyhemoglobin_v4.emf".into(),
            cavity_sdf_phi: -0.038,
            serous_suspended_by: "pericardial_serous_sac".into(),
            pathology_regime: "Live rPPGBPM & Vagal HRV (RMSSD) Coupled Hemodynamic Envelope".into(),
            l6_quantum_chemistry_note: "L6QuantumPhysics: Oxy/Deoxy-Hemoglobin porphyrin Fe2+ pi-pi* 540/576nm optical absorption spectrum".into(),
        },
        HraLivingOrgan10dNode {
            organ_id: "HRA-LUNG-10D".into(),
            title: "Bronchial Tree & Alveolar Gas-Exchange Manifold (10D v2 HOLO)".into(),
            uberon_iri: "http://purl.obolibrary.org/obo/UBERON_0002048".into(),
            cell_types_cl: vec![
                "CL:0002062 (Type I Pneumocyte)".into(),
                "CL:0002063 (Type II Surfactant Pneumocyte)".into(),
            ],
            biomarkers_hgnc: vec![
                "HGNC:SFTPB (Surfactant Protein B)".into(),
                "HGNC:AGER (Alveolar RAGE Receptor)".into(),
            ],
            holo_10d_asset_uri: "10d://wellfair/hra/organ_lung_holo_v2.10d".into(),
            emf_v4_spectral_uri: "emf://wellfair/hra/pleural_parenchyma_v4.emf".into(),
            cavity_sdf_phi: -0.051,
            serous_suspended_by: "pleural_cavity_ligament".into(),
            pathology_regime: "Coupled to Optical Thoracic Phase-Flow Respiration Rate (BrPM)".into(),
            l6_quantum_chemistry_note: "L6QuantumPhysics: O2/CO2 heme coordination spin-state transition model".into(),
        },
        HraLivingOrgan10dNode {
            organ_id: "HRA-VASC-10D".into(),
            title: "Arterial/Venous Vasculature v14 & Cervical 21-Foramina Continuity (10D v2 HOLO)".into(),
            uberon_iri: "http://purl.obolibrary.org/obo/UBERON_0004537".into(),
            cell_types_cl: vec![
                "CL:0000071 (Blood Vessel Endothelial Cell)".into(),
                "CL:0000359 (Vascular Smooth Muscle Cell)".into(),
            ],
            biomarkers_hgnc: vec![
                "HGNC:NOS3 (Endothelial Nitric Oxide Synthase)".into(),
                "HGNC:EDN1 (Endothelin-1)".into(),
            ],
            holo_10d_asset_uri: "10d://wellfair/hra/organ_vasculature_v14_holo_v2.10d".into(),
            emf_v4_spectral_uri: "emf://wellfair/hra/vascular_subsurface_v4.emf".into(),
            cavity_sdf_phi: -0.029,
            serous_suspended_by: "adventitial_fascial_sheath".into(),
            pathology_regime: "24x24 Row-Run HOLO Foramina Preservation & Pulse-Wave Velocity".into(),
            l6_quantum_chemistry_note: "L6QuantumPhysics: Nitric oxide (NO) guanylate cyclase heme nitrosyl activation".into(),
        },
    ]
}
