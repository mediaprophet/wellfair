use wasm_bindgen::prelude::*;
use wasm_bindgen::JsValue;
use serde_wasm_bindgen;

use crate::parser::{parse_weight_csv, parse_sleep_csv, parse_heart_rate_csv, parse_steps_csv};
use crate::rdf::{weight_to_turtle, sleep_to_turtle, heart_rate_to_turtle, steps_to_turtle};

#[wasm_bindgen]
pub fn parse_weight_csv_json(content: &str) -> Result<JsValue, JsValue> {
    match parse_weight_csv(content) {
        Ok(records) => serde_wasm_bindgen::to_value(&records).map_err(|e| JsValue::from_str(&format!("serde error: {}", e))),
        Err(e) => Err(JsValue::from_str(&e)),
    }
}

#[wasm_bindgen]
pub fn parse_sleep_csv_json(content: &str) -> Result<JsValue, JsValue> {
    match parse_sleep_csv(content) {
        Ok(records) => serde_wasm_bindgen::to_value(&records).map_err(|e| JsValue::from_str(&format!("serde error: {}", e))),
        Err(e) => Err(JsValue::from_str(&e)),
    }
}

#[wasm_bindgen]
pub fn parse_heart_rate_csv_json(content: &str) -> Result<JsValue, JsValue> {
    match parse_heart_rate_csv(content) {
        Ok(records) => serde_wasm_bindgen::to_value(&records).map_err(|e| JsValue::from_str(&format!("serde error: {}", e))),
        Err(e) => Err(JsValue::from_str(&e)),
    }
}

#[wasm_bindgen]
pub fn parse_steps_csv_json(content: &str) -> Result<JsValue, JsValue> {
    match parse_steps_csv(content) {
        Ok(records) => serde_wasm_bindgen::to_value(&records).map_err(|e| JsValue::from_str(&format!("serde error: {}", e))),
        Err(e) => Err(JsValue::from_str(&e)),
    }
}

#[wasm_bindgen]
pub fn weight_turtle_from_csv(content: &str) -> Result<String, JsValue> {
    match parse_weight_csv(content) {
        Ok(records) => Ok(weight_to_turtle(&records)),
        Err(e) => Err(JsValue::from_str(&e)),
    }
}

#[wasm_bindgen]
pub fn sleep_turtle_from_csv(content: &str) -> Result<String, JsValue> {
    match parse_sleep_csv(content) {
        Ok(records) => Ok(sleep_to_turtle(&records)),
        Err(e) => Err(JsValue::from_str(&e)),
    }
}

#[wasm_bindgen]
pub fn heart_rate_turtle_from_csv(content: &str) -> Result<String, JsValue> {
    match parse_heart_rate_csv(content) {
        Ok(records) => Ok(heart_rate_to_turtle(&records)),
        Err(e) => Err(JsValue::from_str(&e)),
    }
}

#[wasm_bindgen]
pub fn steps_turtle_from_csv(content: &str) -> Result<String, JsValue> {
    match parse_steps_csv(content) {
        Ok(records) => Ok(steps_to_turtle(&records)),
        Err(e) => Err(JsValue::from_str(&e)),
    }
}

// ==========================================
// QUALIADB OPFS STORE
// ==========================================

// See qualia_bindings.rs for the QualiaStore implementation

// ==========================================
// SPARQL HEALTH STORE  (W4)
// ==========================================

/// In-memory RDF store exposed to JS.  Load Turtle, run SPARQL SELECT/ASK/CONSTRUCT.
#[wasm_bindgen]
pub struct WasmHealthStore {
    inner: crate::store::HealthStore,
}

#[wasm_bindgen]
impl WasmHealthStore {
    #[wasm_bindgen(constructor)]
    pub fn new() -> Result<WasmHealthStore, JsValue> {
        crate::store::HealthStore::new()
            .map(|inner| WasmHealthStore { inner })
            .map_err(|e| JsValue::from_str(&e))
    }

    /// Load a Turtle document into the store (appends — call on a fresh store to replace).
    pub fn load_turtle(&mut self, turtle: &str) -> Result<(), JsValue> {
        self.inner.load_turtle(turtle).map_err(|e| JsValue::from_str(&e))
    }

    /// Execute a SPARQL query; returns JSON SPARQL results string.
    pub fn query(&self, sparql: &str) -> Result<String, JsValue> {
        self.inner.query(sparql).map_err(|e| JsValue::from_str(&e))
    }
}

// ==========================================
// SHACL VALIDATION  (W5)
// ==========================================

/// Validate a Turtle document against built-in health shapes (SPARQL ASK constraints).
/// Returns a JSON string: `{"valid":bool,"checked":N,"violations":[{"shape":"...","message":"..."}]}`
#[wasm_bindgen]
pub fn validate_health_turtle(turtle: &str) -> String {
    crate::shapes::validate_turtle(turtle).to_json()
}

// ==========================================
// VAULT DATA → TURTLE  (wf: namespace)
// ==========================================

/// Serialize vault medication records (JSON array from wf-meds IDB store) → Turtle.
#[wasm_bindgen]
pub fn vault_meds_to_turtle(json: &str) -> Result<String, JsValue> {
    crate::rdf::vault_meds_to_turtle(json).map_err(|e| JsValue::from_str(&e))
}

/// Serialize vault diet log entries (JSON array from wf-dl IDB store) → Turtle.
#[wasm_bindgen]
pub fn vault_diet_to_turtle(json: &str) -> Result<String, JsValue> {
    crate::rdf::vault_diet_to_turtle(json).map_err(|e| JsValue::from_str(&e))
}

/// Serialize vault biometric records (JSON array from wf-biometrics IDB store) → Turtle.
#[wasm_bindgen]
pub fn vault_biometrics_to_turtle(json: &str) -> Result<String, JsValue> {
    crate::rdf::vault_biometrics_to_turtle(json).map_err(|e| JsValue::from_str(&e))
}

// ==========================================
// SENTINEL OPCODES
// ==========================================

/// Placeholder for SentinelOpcode logic that replaces SHACL
#[wasm_bindgen]
pub fn validate_health_quin(_subject: u64) -> String {
    // Logic will be evaluated natively in QualiaDB Core 1
    r#"{"valid":true,"checked":1,"violations":[]}"#.to_string()
}
