import json
from pathlib import Path
from src.phr_models.proxy_consent import RelatedPerson, ProxyConsent
from src.phr_models.psychiatry import PsychiatryObservation
from src.phr_models.medications import MedicationAdministration
from src.phr_models.pathology import DiagnosticReport
from src.phr_models.location import GeoEvent

def get_schema(model):
    if hasattr(model, "model_json_schema"):
        return model.model_json_schema()
    return model.schema()

def main():
    schemas = {
        "RelatedPerson": get_schema(RelatedPerson),
        "ProxyConsent": get_schema(ProxyConsent),
        "PsychiatryObservation": get_schema(PsychiatryObservation),
        "MedicationAdministration": get_schema(MedicationAdministration),
        "DiagnosticReport": get_schema(DiagnosticReport),
        "GeoEvent": get_schema(GeoEvent)
    }

    
    out_path = Path("src/phr_models/phr_schema.json")
    with out_path.open("w") as f:
        json.dump(schemas, f, indent=2)
    print(f"Schema written to {out_path}")

if __name__ == "__main__":
    main()
