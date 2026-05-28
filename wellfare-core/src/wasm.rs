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
