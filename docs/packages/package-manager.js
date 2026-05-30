/**
 * WellFair Package Manager
 * ==========================
 * Manages optional capability packages:
 *   - Checks what's installed (OPFS metadata)
 *   - Downloads package components to OPFS
 *   - Tracks install state and reports capabilities
 *   - Exposes a synchronous capability check for feature gating
 *
 * Exposed on window.wellfairPackages (set in index.js).
 * State mirrored on window.wellfairPackageState for Python/Pyodide access.
 *
 * OPFS layout:
 *   wellfair/
 *     meta.json              — installed package index
 *     wasm/
 *       prolog/
 *         swipl.js
 *         swipl.wasm
 *     models/
 *       gemma-2b-it-gpu-int4.bin
 *       gemma-2b-it-cpu-int4.bin
 */

import { FEATURE_REQUIREMENTS } from "./capabilities.js";

const META_PATH = "wellfair/meta.json";

// Package states
export const PKG_STATE = Object.freeze({
  BUNDLED:      "bundled",
  NOT_INSTALLED:"not-installed",
  DOWNLOADING:  "downloading",
  INSTALLED:    "installed",
  LOADED:       "loaded",
  ERROR:        "error",
});

export class PackageManager extends EventTarget {
  constructor() {
    super();
    /** @type {Map<string, {status: string, progress: number, error?: string}>} */
    this._state  = new Map();
    /** @type {Set<string>} */
    this._caps   = new Set();
    this._ready  = false;
    this._opfsRoot = null;
    this._registry = null;
  }

  // ---------------------------------------------------------------------------
  // Initialisation
  // ---------------------------------------------------------------------------

  async init() {
    try {
      this._registry = await this._loadRegistry();
      this._opfsRoot = await navigator.storage.getDirectory();
      await this._restoreStateFromMeta();
      this._ready = true;
      this._syncWindowState();
      this.dispatchEvent(new CustomEvent("ready", { detail: { capabilities: [...this._caps] } }));
    } catch (err) {
      console.error("[PackageManager] init failed:", err);
    }
  }

  // ---------------------------------------------------------------------------
  // Capability queries (synchronous — always safe to call)
  // ---------------------------------------------------------------------------

  /** Returns true if ALL required capabilities for featureId are available. */
  canUse(featureId) {
    const required = FEATURE_REQUIREMENTS[featureId] ?? [];
    return required.every(cap => this._caps.has(cap));
  }

  /** Returns capability tokens for all packages that are missing. */
  missingFor(featureId) {
    const required = FEATURE_REQUIREMENTS[featureId] ?? [];
    return required.filter(cap => !this._caps.has(cap));
  }

  /** Returns the full capability set as a plain JS array. */
  getCapabilities() {
    return [...this._caps];
  }

  /** Returns JSON-serialisable state for one package. */
  getPackageState(packageId) {
    const s = this._state.get(packageId);
    if (!s) return null;
    return JSON.stringify(s);
  }

  /** Returns JSON-serialisable state for all packages. */
  getAllStates() {
    const out = {};
    for (const [id, state] of this._state) {
      out[id] = state;
    }
    return JSON.stringify(out);
  }

  // ---------------------------------------------------------------------------
  // Installation
  // ---------------------------------------------------------------------------

  /**
   * Install a package. Downloads all components to OPFS.
   * @param {string} packageId
   * @param {function(number, number, number): void} [onProgress] (fraction, loaded, total)
   * @returns {Promise<void>}
   */
  async install(packageId, onProgress) {
    const pkg = this._registry?.packages.find(p => p.id === packageId);
    if (!pkg) throw new Error(`Unknown package: ${packageId}`);
    if (pkg.bundled) return;  // nothing to download
    if (pkg.status === "future") throw new Error(`Package ${packageId} is not yet available.`);

    this._setStatus(packageId, PKG_STATE.DOWNLOADING, 0);

    try {
      const components = pkg.components ?? [];
      let totalBytes = components.reduce((s, c) => s + (c.sizeBytes ?? 0), 0);
      let downloadedBytes = 0;

      for (const component of components) {
        const componentProgress = (loaded, total) => {
          downloadedBytes += loaded;
          const fraction = totalBytes > 0 ? downloadedBytes / totalBytes : 0;
          this._setStatus(packageId, PKG_STATE.DOWNLOADING, fraction);
          onProgress?.(fraction, downloadedBytes, totalBytes);
        };

        await this._downloadComponent(component, componentProgress);
      }

      await this._saveMeta(packageId, { version: pkg.version });
      this._applyCapabilities(pkg);
      this._setStatus(packageId, PKG_STATE.INSTALLED, 1);
      this._syncWindowState();
      this.dispatchEvent(new CustomEvent("installed", { detail: { packageId } }));
    } catch (err) {
      this._setStatus(packageId, PKG_STATE.ERROR, 0, err.message);
      this._syncWindowState();
      throw err;
    }
  }

  /**
   * Install a model file for a package that has a model registry (e.g. llm-mediapipe).
   * Handles auth-gated models by prompting the user to provide the file.
   *
   * @param {string} packageId
   * @param {string} modelId
   * @param {File|null} file  - Provide File if the user selected it manually; null to attempt direct download.
   * @param {function} [onProgress]
   */
  async installModel(packageId, modelId, file, onProgress) {
    const pkg = this._registry?.packages.find(p => p.id === packageId);
    if (!pkg) throw new Error(`Unknown package: ${packageId}`);
    const model = pkg.models?.find(m => m.id === modelId);
    if (!model) throw new Error(`Unknown model: ${modelId}`);

    const key = `${packageId}:${modelId}`;
    this._setStatus(key, PKG_STATE.DOWNLOADING, 0);

    try {
      if (file) {
        await this._writeFileToOpfs(model.opfsPath, file, onProgress);
      } else if (model.directDownloadUrl) {
        await this._downloadToOpfs(model.directDownloadUrl, model.opfsPath, onProgress);
      } else {
        throw new Error(
          `Model '${model.name}' requires manual download.\n` +
          `Please download from: ${model.sourceUrl}\n` +
          `Then use 'Load from file' to import it.`
        );
      }

      await this._saveMeta(key, { modelId, opfsPath: model.opfsPath });
      this._setStatus(key, PKG_STATE.INSTALLED, 1);

      // Grant LLM capabilities once any model is present for this package
      this._applyCapabilities(pkg);
      this._syncWindowState();
      this.dispatchEvent(new CustomEvent("model-installed", { detail: { packageId, modelId } }));
    } catch (err) {
      this._setStatus(key, PKG_STATE.ERROR, 0, err.message);
      this._syncWindowState();
      throw err;
    }
  }

  /** Check whether a specific model is stored in OPFS. */
  async isModelInstalled(packageId, modelId) {
    const pkg = this._registry?.packages.find(p => p.id === packageId);
    const model = pkg?.models?.find(m => m.id === modelId);
    if (!model) return false;
    return this._opfsFileExists(model.opfsPath);
  }

  /** Get a blob URL for an installed model (caller must revoke after use). */
  async getModelBlobUrl(packageId, modelId) {
    const pkg = this._registry?.packages.find(p => p.id === packageId);
    const model = pkg?.models?.find(m => m.id === modelId);
    if (!model) throw new Error(`Unknown model: ${modelId}`);
    const file = await this._readOpfsFile(model.opfsPath);
    return URL.createObjectURL(file);
  }

  /** Get an installed WASM file blob URL. Used by wasm-worker.js. */
  async getWasmBlobUrl(packageId, filename) {
    const pkg = this._registry?.packages.find(p => p.id === packageId);
    const component = pkg?.components?.find(c => c.opfsPath?.endsWith(filename));
    if (!component?.opfsPath) throw new Error(`Component ${filename} not found in ${packageId}`);
    const file = await this._readOpfsFile(component.opfsPath);
    return URL.createObjectURL(file);
  }

  // ---------------------------------------------------------------------------
  // Registry
  // ---------------------------------------------------------------------------

  getRegistry() {
    return this._registry;
  }

  isReady() {
    return this._ready;
  }

  // ---------------------------------------------------------------------------
  // Download UI trigger (called from Python via bridge)
  // ---------------------------------------------------------------------------

  showInstallUI(packageId) {
    this.dispatchEvent(new CustomEvent("show-install-ui", { detail: { packageId } }));
    // package-download-ui.js listens for this and shows the overlay
    window.dispatchEvent(new CustomEvent("wellfair:show-install-ui", { detail: { packageId } }));
  }

  // ---------------------------------------------------------------------------
  // Private: OPFS helpers
  // ---------------------------------------------------------------------------

  async _downloadComponent(component, onProgress) {
    if (!component.opfsPath) return;  // CDN-only, no local caching needed
    if (await this._opfsFileExists(component.opfsPath)) return;  // already cached
    await this._downloadToOpfs(component.url, component.opfsPath, onProgress);
  }

  async _downloadToOpfs(url, opfsRelPath, onProgress) {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Download failed: ${url} (HTTP ${response.status})`);
    }
    const contentLength = parseInt(response.headers.get("content-length") || "0");

    const { fileHandle } = await this._opfsHandleForPath(opfsRelPath, true);
    const writable = await fileHandle.createWritable();

    let downloaded = 0;
    const reader = response.body.getReader();
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        await writable.write(value);
        downloaded += value.length;
        if (contentLength > 0) {
          onProgress?.(downloaded / contentLength, downloaded, contentLength);
        }
      }
      await writable.close();
    } catch (err) {
      await writable.abort().catch(() => {});
      throw err;
    }
  }

  async _writeFileToOpfs(opfsRelPath, file, onProgress) {
    const { fileHandle } = await this._opfsHandleForPath(opfsRelPath, true);
    const writable = await fileHandle.createWritable();
    const reader = file.stream().getReader();
    let written = 0;
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        await writable.write(value);
        written += value.length;
        onProgress?.(written / file.size, written, file.size);
      }
      await writable.close();
    } catch (err) {
      await writable.abort().catch(() => {});
      throw err;
    }
  }

  async _readOpfsFile(opfsRelPath) {
    const { fileHandle } = await this._opfsHandleForPath(opfsRelPath, false);
    return fileHandle.getFile();
  }

  async _opfsFileExists(opfsRelPath) {
    try {
      await this._opfsHandleForPath(opfsRelPath, false);
      return true;
    } catch {
      return false;
    }
  }

  async _opfsHandleForPath(relPath, create) {
    const parts = relPath.split("/");
    const fileName = parts.pop();
    let dir = this._opfsRoot;
    for (const part of parts) {
      dir = await dir.getDirectoryHandle(part, { create });
    }
    const fileHandle = await dir.getFileHandle(fileName, { create });
    return { dir, fileHandle };
  }

  // ---------------------------------------------------------------------------
  // Private: Metadata persistence
  // ---------------------------------------------------------------------------

  async _restoreStateFromMeta() {
    // Always mark bundled packages first
    for (const pkg of (this._registry?.packages ?? [])) {
      if (pkg.bundled) {
        this._state.set(pkg.id, { status: PKG_STATE.BUNDLED, progress: 1 });
        this._applyCapabilities(pkg);
      } else {
        this._state.set(pkg.id, { status: PKG_STATE.NOT_INSTALLED, progress: 0 });
      }
    }

    // Then load saved installation state from OPFS
    if (!this._opfsRoot) return;
    try {
      const { fileHandle } = await this._opfsHandleForPath(META_PATH, false);
      const file = await fileHandle.getFile();
      const meta = JSON.parse(await file.text());

      for (const [key, record] of Object.entries(meta.installed ?? {})) {
        const packageId = key.includes(":") ? key.split(":")[0] : key;
        const pkg = this._registry?.packages.find(p => p.id === packageId);
        if (pkg) {
          // Verify the files actually exist before marking installed
          const allPresent = await this._verifyPackageFiles(pkg);
          if (allPresent) {
            this._state.set(key, { status: PKG_STATE.INSTALLED, progress: 1 });
            this._applyCapabilities(pkg);
          } else {
            this._state.set(key, { status: PKG_STATE.NOT_INSTALLED, progress: 0 });
          }
        }
      }
    } catch {
      // meta.json not yet written — fresh install, no state to restore
    }
  }

  async _verifyPackageFiles(pkg) {
    for (const component of (pkg.components ?? [])) {
      if (component.opfsPath && !(await this._opfsFileExists(component.opfsPath))) {
        return false;
      }
    }
    return true;
  }

  async _saveMeta(key, record) {
    let meta = { installed: {} };
    try {
      const { fileHandle } = await this._opfsHandleForPath(META_PATH, false);
      const file = await fileHandle.getFile();
      meta = JSON.parse(await file.text());
    } catch {
      // first write — start fresh
    }
    meta.installed[key] = { ...record, installedAt: Date.now() };
    const { fileHandle } = await this._opfsHandleForPath(META_PATH, true);
    const writable = await fileHandle.createWritable();
    await writable.write(JSON.stringify(meta, null, 2));
    await writable.close();
  }

  // ---------------------------------------------------------------------------
  // Private: Capability management
  // ---------------------------------------------------------------------------

  _applyCapabilities(pkg) {
    for (const cap of (pkg.provides ?? [])) {
      this._caps.add(cap);
    }
  }

  _setStatus(key, status, progress, error) {
    this._state.set(key, { status, progress, ...(error ? { error } : {}) });
  }

  // Mirror state to window.wellfairPackageState for Python/Pyodide access
  _syncWindowState() {
    const packages = {};
    for (const [id, state] of this._state) {
      packages[id] = state;
    }
    window.wellfairPackageState = {
      ready:        this._ready,
      capabilities: [...this._caps],
      packages,
    };
  }

  async _loadRegistry() {
    const res = await fetch(new URL("registry.json", import.meta.url));
    if (!res.ok) throw new Error("Failed to load package registry");
    return res.json();
  }
}
