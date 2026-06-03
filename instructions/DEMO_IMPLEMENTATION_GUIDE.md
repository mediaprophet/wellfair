# Wellfair Demo Implementation Guide

**Date:** 28 May 2026  
**Purpose:** This document provides a complete implementation strategy for the synthetic demo person system in wellfair, including UI requirements, folder structure, and integration points.

---

## 1. Overview

The wellfair demo system enables users to instantiate complex, realistic personas with synthetic Samsung Health data that illustrates different wellbeing challenges and use cases. Each persona generates:
- Realistic sleep patterns reflecting their circumstances
- Activity and heart rate patterns aligned with their situation
- Weight/biometric trends
- Contextual metadata and welfare indicators

### Personas Currently Supported
1. **Michael R.** – Homelessness & family separation stress
2. **Elena V.** – PTSD, trauma recovery, housing instability
3. **Rebecca L.** – Complex trauma, autonomy vs. safety, river living
4. **Margaret T.** – Elder abuse, financial exploitation, isolation
5. **Robert K.** – Elder abuse by partner, medical sabotage
6. **Jordan M.** – NDIS exploitation, disability, systemic abuse

---

## 2. Folder Structure

```
/demo/
├── PERSONAS.md                           # Metadata file with persona profiles
├── personas/
│   ├── michael_r/
│   │   ├── person.json                   # Demographic + metadata
│   │   ├── samsung_export/               # Synthetic Samsung Health CSVs
│   │   │   ├── com.samsung.health.weight.*.csv
│   │   │   ├── com.samsung.shealth.sleep.*.csv
│   │   │   ├── com.samsung.health.heart_rate.*.csv
│   │   │   └── com.samsung.health.pedometer_step_count.*.csv
│   │   └── maslow_assessment.json        # Welfare model evaluation
│   ├── elena_v/
│   │   ├── person.json
│   │   ├── samsung_export/
│   │   └── maslow_assessment.json
│   ├── rebecca_l/
│   ├── margaret_t/
│   ├── robert_k/
│   └── jordan_m/
└── manifest.json                         # Global demo manifest
```

---

## 3. Data File Formats

### person.json
```json
{
  "id": "michael_r",
  "name": "Michael R.",
  "age": 42,
  "gender": "male",
  "location": "Sydney, Australia",
  "situation": "Homelessness & family separation",
  "created_date": "2026-05-28",
  "data_start_date": "2026-05-01",
  "data_end_date": "2026-05-28",
  "maslow_assessment": "see maslow_assessment.json",
  "use_case_tags": ["homelessness", "stress", "family_separation", "health_inequity"]
}
```

### maslow_assessment.json
```json
{
  "person_id": "michael_r",
  "assessment_date": "2026-05-28",
  "maslow_hierarchy": {
    "physiological": {
      "score": 20,
      "factors": ["inconsistent_sleep", "irregular_meals", "physical_pain"]
    },
    "safety": {
      "score": 15,
      "factors": ["homelessness", "financial_instability", "lack_of_support"]
    },
    "love_belonging": {
      "score": 10,
      "factors": ["family_separation", "children_court_order"]
    },
    "esteem": {
      "score": 25,
      "factors": ["loss_of_provider_identity", "employment_instability"]
    },
    "self_actualization": {
      "score": 5,
      "factors": ["survival_mode", "no_capacity_for_growth"]
    }
  },
  "total_wellbeing_score": 15,
  "critical_areas": ["physiological", "safety"],
  "recommended_interventions": ["housing_support", "mental_health_counseling", "financial_assistance"]
}
```

---

## 4. UI Integration Points

### 4.1 Demo Selector Modal (Sidebar)
Add to `ui/app.py`:
```python
# After profile selector, add:
if profile == "gemini":
    st.sidebar.subheader("📊 Demo Personas")
    demo_mode = st.sidebar.radio(
        "Select demo person",
        options=["None", "Michael R.", "Elena V.", "Rebecca L.", "Margaret T.", "Robert K.", "Jordan M."],
        horizontal=False
    )
    if demo_mode != "None":
        export_path = str(PROJECT_ROOT / "demo" / "personas" / f"{demo_mode.lower().replace(' ', '_')}" / "samsung_export")
```

### 4.2 Persona Information Card (Main View)
Create a new tab or modal `ui/tabs/demo_persona_info.py` that displays:
- Persona photo/avatar placeholder
- Current situation summary
- Maslow hierarchy assessment (visual gauge)
- Key health indicators from the synthetic data
- Use case tags

### 4.3 Settings Panel Implementation
Currently blank — populate with:
- Demo/Development toggles
- Data refresh options
- Cache settings
- Persona presets (for quick testing)

### 4.4 Demo Dashboard Tab
New optional tab showing:
- All available personas as selectable cards
- Maslow hierarchy comparisons across personas
- Sleep pattern analytics by persona
- Welfare assessment scores

---

## 5. Synthetic Data Generation

### Pattern by Persona

**Michael R. – Homelessness/Stress**
- Sleep: Highly fragmented (6–7 hours split across multiple periods)
- Efficiency: 45–55% (frequent awakenings)
- Deep sleep: Very low (< 20 minutes/night)
- REM sleep: Suppressed (~40 minutes)
- Activity: Highly variable (0–15,000 steps depending on work)
- Heart rate: Elevated resting (75–85 bpm), high variability

**Elena V. – PTSD/Trauma Recovery**
- Sleep: Severely disrupted (5–6 hours fragmented)
- Efficiency: 35–50% (nightmares, early waking)
- Deep sleep: Very low (< 15 minutes)
- REM sleep: Highly irregular (fluctuates 20–100 minutes)
- Activity: Erratic (0–8,000 steps, volatile changes)
- Heart rate: Highly elevated and variable (80–95 bpm resting, frequent spikes)

**Rebecca L. – Autonomy/Chronic Trauma**
- Sleep: Extremely poor (4–6 hours, highly fragmented)
- Efficiency: 25–40% (hypervigilance awakenings)
- Deep sleep: Minimal (< 10 minutes)
- REM sleep: Severely suppressed (< 30 minutes)
- Activity: Highly variable with periodic high activity (survival-related movement)
- Heart rate: Chronically elevated (85–100 bpm), poor HRV

**Margaret T. – Elder Abuse**
- Sleep: Poor and anxiety-driven (6–7 hours, frequent night awakenings)
- Efficiency: 40–50% (worry-related arousals)
- Deep sleep: Low (30–40 minutes)
- REM sleep: Suppressed (~60 minutes)
- Activity: Very low (< 3,000 steps/day, sedentary)
- Heart rate: Chronically elevated (~75–80 bpm), anxiety spikes during day

**Robert K. – Elder Abuse/Medical Neglect**
- Sleep: Severely disrupted (4–5 hours, frequent breathing-related arousals)
- Efficiency: 30–40% (physiological and anxiety factors)
- Deep sleep: Very low (< 20 minutes)
- REM sleep: Poor (< 60 minutes)
- Activity: Extremely low (< 2,000 steps, mobility-limited)
- Heart rate: Highly irregular and dangerous (60–100 bpm wide swings), poor HRV

**Jordan M. – NDIS Exploitation/Disability**
- Sleep: Poor (5–7 hours, disrupted by pain and anxiety)
- Efficiency: 35–55% (pain-related awakenings)
- Deep sleep: Low (20–40 minutes)
- REM sleep: Suppressed (50–80 minutes)
- Activity: Highly limited (1,000–4,000 steps on good days, mostly zero)
- Heart rate: Elevated and variable (75–90 bpm resting, frequent anxiety spikes)

---

## 6. Integration with Existing Systems

### 6.1 Synthetic Export Generation
Extend `scripts/generate_synthetic_export.py` to accept persona profiles:
```python
def generate_persona_export(persona_id: str, output_dir: Path) -> None:
    """Generate Samsung Health export for a specific persona."""
    manifest = load_demo_manifest()
    persona = manifest["personas"][persona_id]
    # Generate CSVs based on persona patterns
```

### 6.2 Cache & Loading
- Cached data should key on persona ID
- Demo exports should be regenerated on demand (they're lightweight)
- Session state should track active persona

### 6.3 Output & RDF Generation
- When a persona is selected, generate RDF in `demo/personas/{person_id}/solid_pod/`
- Tag RDF with persona metadata for future welfare analysis
- Store Maslow assessments alongside RDF

---

## 7. UI Components Required

### Components to Create

| Component | File | Purpose |
|-----------|------|---------|
| Persona Selector Modal | `ui/modals/persona_selector.py` | Modal for choosing demo person |
| Persona Info Card | `ui/components/persona_card.py` | Display current persona info |
| Maslow Gauge | `ui/components/maslow_gauge.py` | Visual welfare hierarchy indicator |
| Demo Dashboard | `ui/tabs/demo_dashboard.py` | Overview of all personas |
| Persona Data Generator | `scripts/generate_persona_exports.py` | Batch synthetic data generator |

---

## 8. Deployment Checklist

- [ ] Create `/demo/` folder structure
- [ ] Generate synthetic data for all 6 personas
- [ ] Create `person.json` and `maslow_assessment.json` for each
- [ ] Create demo manifest file
- [ ] Implement persona selector UI in sidebar
- [ ] Implement persona info card display
- [ ] Extend synthetic export generator for personas
- [ ] Populate settings panel with demo-related options
- [ ] Test end-to-end persona loading
- [ ] Document demo usage in README

---

## 9. Future Enhancements

- Welfare trend analysis (showing Maslow scores over time)
- Sanctuary Mode demo scenarios
- Multi-person family/household demos
- Interventions tracking (how persona improves with support)
- Export demo data as anonymised datasets for research
- Integration with professional dashboards (casework, assessments)
