**Project: Human-Centric Health Informatics – Privacy-Aware Personal Health Record (PHR) Module**  
**Working Draft – Instructions for Antigravity**  
**Focus:** Standardising modular components for a privacy-first, user-controlled health app that supports real human needs (self-management, clinical collaboration, carer support) while respecting legal and ethical boundaries in Australia.

### 1. Core Privacy & Sharing Modes (Confidentiality Layers)
Design the app with **three explicit, user-selectable data modes** at the point of data entry or import. These modes must be persistent, visually distinct, and enforceable at the storage, display, and sharing layers.

- **Mode A – Strictly Confidential (Self + Doctor only, high sensitivity)**  
  Purpose: Allow patients to record information they would normally hesitate to disclose (e.g. illicit drug use, non-prescribed substance use, sexual history, mental health episodes, domestic violence, etc.) purely for health-risk assessment and clinical decision-making.  
  - Data is encrypted at rest and in transit.  
  - Default: visible only to the patient and any explicitly authorised clinician (via secure doctor link or My Health Record-style consent).  
  - Patient must explicitly confirm “I understand this will be shared with my doctor for health purposes only” before saving.  
  - Audit log of access (doctor only).  
  - Option to later “downgrade” to Mode B if the patient becomes comfortable sharing more widely.

- **Mode B – Privileged / Confidential (Doctor-facing, clinically relevant)**  
  Purpose: Information the patient intends their doctor to see but does not want shared with family/carers (e.g. detailed symptom timelines, medication side-effects, adherence issues, sensitive family history).  
  - Still encrypted and access-controlled.  
  - Can be selectively shared with named clinicians.  
  - Not visible in carer/family views unless patient explicitly promotes it.

- **Mode C – Shared (Friends / Family / Next of Kin / Carer)**  
  Purpose: Information useful for daily support, emergency contact, or carer coordination (e.g. current medications list, allergies, emergency contacts, basic care instructions).  
  - Granular sharing controls (specific people or groups).  
  - Read-only or limited edit rights for carers.  
  - Clear visual indicator that this data is in “shared” mode.

**Implementation note for Antigravity:** Every data field or record must carry a `privacy_mode` tag (A/B/C) + timestamp + user consent record. UI must make the chosen mode unmistakable (colour + icon + tooltip).

### 2. Medication Management & Adherence Tracking
Extend the existing Samsung Health import with a dedicated, user-centric medication module.

Required fields per medication entry:
- Medication name + strength + form (tablet, inhaler, etc.)
- Prescribed dose & schedule
- `adherence_status` (options):  
  – Taken (exact time)  
  – Taken (estimated time)  
  – Missed / Not taken  
  – Not reported yet (default for passive imports)  
  – Declined / Stopped (with optional reason)
- `data_quality` tag: Exact | Estimate | Self-report | Device-imported | Clinician-verified | Other
- Source (Samsung Health, manual entry, pharmacy import, etc.)
- Notes field that can itself be tagged with privacy_mode A/B/C
- Start date / end date / review date

**Features:**
- Ability to bulk-import from Samsung Health and then enrich with adherence data.
- Gentle reminders + “mark as taken” with one tap (respecting user fatigue).
- Visual timeline showing gaps or patterns (useful for doctor discussions).
- Option to generate a “Medication Summary Report” filtered by privacy mode.

### 3. Pathology Import Process (Interactive PDF → Structured Data)
Create a robust, user-guided import pipeline:

1. User uploads PDF(s) or provides a secure link/pointer to pathology reports.
2. System performs OCR + structured extraction (using best available medical PDF parsers).
3. Presents an **interactive review screen**:
   - Side-by-side view: original PDF page vs extracted table.
   - User can correct values, units, reference ranges, dates, test names.
   - Flag any uncertain extractions for manual review.
   - Option to apply privacy_mode per report or per test (e.g. drug screen results may be Mode A).
4. Once user confirms accuracy, data is stored in a clean tabular format (FHIR-friendly Observation resources or simple JSON schema).
5. Store both the original PDF (encrypted) and the verified structured data.

**Goal:** Minimise transcription errors while keeping the human in full control of verification.

### 4. Google Location / Mapping Data Import
Support import of Google Timeline / Location History (common on Android phones) for:
- Activity context (e.g. correlating location patterns with symptoms, exercise, or environmental triggers)
- Safety / carer features (last known location in emergency, with consent)
- Research/insight features (e.g. time spent indoors vs outdoors, travel history)

Process:
- User exports Google Takeout Location History (JSON) or connects via secure Google API (if feasible).
- Import wizard that lets user select date ranges and which semantic categories to keep (home, work, medical facilities, travel, etc.).
- Apply privacy_mode at import (most location data will likely be Mode C or B; highly sensitive locations can be Mode A or stripped).
- Store as time-stamped geo-events with optional privacy tag.

### Next Steps for Standardisation (Human-Centric Informatics Lens)
These components should become reusable building blocks:
- Privacy Mode engine (tag + consent + UI + access control)
- Data Quality & Provenance tracking (exact/estimate + source)
- Interactive Document Import & Verification pattern
- Consent & Sharing Layer (aligned with Australian Privacy Principles + My Health Record consent model)

Before we iterate into code or Respec, I recommend we:
1. Map these requirements against relevant standards (FHIR, OpenEHR, Australian Digital Health standards).
2. Explore research on “privacy by design” in personal health records and trauma-informed data collection (especially for Mode A).
3. Define a simple JSON schema / data model that can be versioned and later formalised in Respec.

Would you like me to:
- Draft the full set of instructions as a clean prompt for Antigravity right now?
- First produce a lightweight data schema / component diagram?
- Or research specific standards / papers before we lock in the instructions?

Let me know how you want to iterate on this health-app module.