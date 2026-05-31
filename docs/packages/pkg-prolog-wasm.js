/**
 * Prolog WASM Package — SWI-Prolog in the browser
 * =================================================
 * Provides blob URLs for swipl.js and swipl.wasm from OPFS cache.
 * Used by user-runtime-lib/wasm-worker.js instead of a hardcoded /static/ path.
 *
 * After installation, wasm-worker.js should call:
 *   const { jsUrl, wasmUrl } = await PrologWasm.getBlobUrls(packageManager);
 *   const module = await import(jsUrl);
 */

const PACKAGE_ID = "prolog-wasm";

export const PrologWasm = {
  /**
   * Check if swipl-wasm is installed and return blob URLs for both files.
   * Caller must call URL.revokeObjectURL() on both after the module is loaded.
   */
  async getBlobUrls(packageManager) {
    const jsUrl   = await packageManager.getWasmBlobUrl(PACKAGE_ID, "swipl.js");
    const wasmUrl = await packageManager.getWasmBlobUrl(PACKAGE_ID, "swipl.wasm");
    return { jsUrl, wasmUrl };
  },

  isInstalled(packageManager) {
    const stateJson = packageManager.getPackageState(PACKAGE_ID);
    if (!stateJson) return false;
    const state = JSON.parse(stateJson);
    return state.status === "installed" || state.status === "loaded";
  },
};
