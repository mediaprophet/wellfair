/// QualiaStore — in-memory quint store exposed to WASM.
///
/// A quint is a 5-tuple (Subject, Predicate, Object, Context, Metadata) of u64 IDs.
/// IDs are assigned by the JS-side Lexicon (vault-wasm.js); this module is the
/// storage layer only.
///
/// Full qualia-core-db wiring (W10) is deferred: the `qualia` Cargo feature gates
/// that dependency to avoid pulling wgpu into the default WASM binary.

#[cfg(target_arch = "wasm32")]
use wasm_bindgen::prelude::*;
#[cfg(target_arch = "wasm32")]
use js_sys::Float64Array;

#[cfg(target_arch = "wasm32")]
#[wasm_bindgen]
pub struct QualiaStore {
    quins: Vec<[u64; 5]>,
}

#[cfg(target_arch = "wasm32")]
#[wasm_bindgen]
impl QualiaStore {
    #[wasm_bindgen(constructor)]
    pub fn new() -> Self {
        Self { quins: Vec::new() }
    }

    /// Insert a quint (s, p, o, c, m).  Returns true on success.
    pub fn insert_quin(&mut self, s: u64, p: u64, o: u64, c: u64, m: u64) -> bool {
        self.quins.push([s, p, o, c, m]);
        true
    }

    /// Return all quints with the given subject as a flat Float64Array
    /// (groups of 5: [s,p,o,c,m, s,p,o,c,m, ...]).
    pub fn query_subject(&self, s: u64) -> Float64Array {
        let matches: Vec<f64> = self
            .quins
            .iter()
            .filter(|q| q[0] == s)
            .flat_map(|q| q.iter().map(|&x| x as f64))
            .collect();
        Float64Array::from(matches.as_slice())
    }

    /// Return all quints with the given predicate as a flat Float64Array.
    pub fn query_predicate(&self, p: u64) -> Float64Array {
        let matches: Vec<f64> = self
            .quins
            .iter()
            .filter(|q| q[1] == p)
            .flat_map(|q| q.iter().map(|&x| x as f64))
            .collect();
        Float64Array::from(matches.as_slice())
    }

    /// Return all quints in the given context as a flat Float64Array.
    pub fn query_context(&self, c: u64) -> Float64Array {
        let matches: Vec<f64> = self
            .quins
            .iter()
            .filter(|q| q[3] == c)
            .flat_map(|q| q.iter().map(|&x| x as f64))
            .collect();
        Float64Array::from(matches.as_slice())
    }

    /// Total number of quints stored.
    pub fn len(&self) -> u32 {
        self.quins.len() as u32
    }

    /// Clear all stored quints.
    pub fn clear(&mut self) {
        self.quins.clear();
    }
}
