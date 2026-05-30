/**
 * WellFair Package System Entry Point
 * =====================================
 * Boots the PackageManager and exposes it on window.wellfairPackages.
 * Also seeds window.wellfairPackageState (a plain object) for synchronous
 * access from Python/Pyodide in the stlite Streamlit runtime.
 *
 * Loaded as <script type="module" src="packages/index.js"> in the HTML
 * template (scripts/build_stlite.py) before stlite.mount() is called.
 */

import { PackageManager } from "./package-manager.js";
import { MediaPipeLlmProfile } from "./pkg-llm-mediapipe.js";
import { PrologWasm } from "./pkg-prolog-wasm.js";

// Seed the window state immediately (before async init) so Python can
// read it without a race — it will be populated once init() resolves.
window.wellfairPackageState = {
  ready:        false,
  capabilities: [],
  packages:     {},
};

const manager = new PackageManager();

// Expose the manager and profile classes globally
window.wellfairPackages     = manager;
window.WellfairLlmProfiles  = { mediapipe: MediaPipeLlmProfile };
window.WellfairPrologWasm   = PrologWasm;

// Boot asynchronously — stlite takes ~5s to initialise anyway
manager.init().then(() => {
  console.log(
    "[wellfair:packages] Ready. Capabilities:",
    manager.getCapabilities().join(", ") || "(base only)"
  );
}).catch(err => {
  console.error("[wellfair:packages] Init failed:", err);
});

// Expose a convenience "canUse" on window for quick feature-gate checks
// from any inline script in app.html
window.wellfairCanUse = (featureId) => manager.canUse(featureId);
