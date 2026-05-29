# WellFair v0.0.2 Release Notes

**Date:** 29 May 2026

## Highlights

### Data Handling & Persistence (Major Focus)
- Real PDF text extraction for pathology reports and questionnaires using `pypdf`.
- Improved pathology lab value parser (handles common Australian report formats).
- Structured `DiagnosticReport` + `PathologyObservation` records now created from uploaded PDFs.
- Interactive, repeatable diagnostic questionnaires (fuller DASS-21, BDI-II, PHQ-9, GAD-7, etc.).
- Multiple completions of the same questionnaire are now properly supported with timestamps and history.
- **File-based persistence** added via `src/persistence.py`:
  - Questionnaires and pathology reports are saved to `data/vault/` as JSON.
  - Data survives app restarts in native Streamlit.
- Structured data now appears in:
  - Mental Health tab
  - Semantic Timeline / Calendar

### Mobile / PWA Improvements
- Device File System Bridge (`File System Access API`) for installed PWAs.
- Users can now point at real folders on their phone (e.g. Samsung Health exports) and import them directly.
- New "📱 Device Exports" profile option that loads from `/device_data`.

### RDF & Export
- Improved RDF generation for both questionnaires and pathology reports.
- Downloadable Turtle (.ttl) files for individual records.

### Other
- Version bumped to 0.0.2.
- Better component reuse across UI (info banners, metric cards, alert cards).
- Many small responsiveness and usability fixes.

## Known Limitations
- Full persistence in the Stlite/Pyodide PWA is still limited (browser storage constraints).
- Pathology PDF parsing is regex-based and works best on common lab formats.
- Interactive questionnaires are currently limited to a subset of the available screening forms.

## Next Phase (Planned)
- Prolog integration for logical rules and inference over vault data.
- Local small LLM support (for better PDF extraction, summarization, and form assistance).
- Communications module (secure messaging, agent-to-agent, etc.).

---

**This release focuses on making the core data layer actually useful and persistent.**
