/**
 * WellFair LLM Profile — MediaPipe / LiteRT (Android)
 * ======================================================
 * Runs language model inference locally using Google's MediaPipe Tasks GenAI API.
 * Designed for Android Chrome; works on any Chromium with WebAssembly + WebGL.
 *
 * Platform: Android Chrome, desktop Chromium (GPU recommended)
 * Runtime: @mediapipe/tasks-genai (~5 MB, loaded from CDN)
 * Models: LiteRT-format .bin files (stored in OPFS after user download)
 *
 * Model acquisition:
 *   Gemma models require accepting Google's licence on Kaggle before download.
 *   The user downloads the .bin file and imports it via the "Load from file" button.
 *   Once imported, the model is stored in OPFS and available offline.
 *
 * Usage:
 *   const profile = new MediaPipeLlmProfile(packageManager);
 *   await profile.load("gemma-2b-it-gpu-int4");
 *   const text = await profile.generate(prompt);
 *   await profile.unload();
 */

const PACKAGE_ID        = "llm-mediapipe";
const MEDIAPIPE_CDN     = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-genai@0.10.14";
const MEDIAPIPE_WASM    = `${MEDIAPIPE_CDN}/wasm`;

// Default generation parameters
const DEFAULT_MAX_TOKENS  = 1024;
const DEFAULT_TOP_K       = 40;
const DEFAULT_TEMPERATURE = 0.8;
const DEFAULT_RANDOM_SEED = 42;

export class MediaPipeLlmProfile {
  /** @param {import("./package-manager.js").PackageManager} packageManager */
  constructor(packageManager) {
    this._pkgMgr       = packageManager;
    this._genAi        = null;   // FilesetResolver result
    this._model        = null;   // LlmInference instance
    this._modelBlobUrl = null;   // URL to revoke after loading
    this._loadedModelId = null;
  }

  // ---------------------------------------------------------------------------
  // Compatibility check
  // ---------------------------------------------------------------------------

  static async isCompatible() {
    // WebAssembly required
    if (typeof WebAssembly === "undefined") return false;
    // SharedArrayBuffer required for MediaPipe WASM (needs COOP/COEP headers)
    // Fall back gracefully if not available — MediaPipe has a fallback path
    return true;
  }

  // ---------------------------------------------------------------------------
  // Model loading
  // ---------------------------------------------------------------------------

  /**
   * Load a model into memory. Automatically resolves the blob URL from OPFS.
   * @param {string} modelId - e.g. "gemma-2b-it-gpu-int4"
   * @param {object} [opts]
   * @param {number} [opts.maxTokens]
   * @param {number} [opts.topK]
   * @param {number} [opts.temperature]
   */
  async load(modelId, opts = {}) {
    if (this._loadedModelId === modelId && this._model) return;  // already loaded

    // Get the model's blob URL from OPFS
    const blobUrl = await this._pkgMgr.getModelBlobUrl(PACKAGE_ID, modelId);
    this._modelBlobUrl = blobUrl;

    // Determine if GPU should be used
    const registry = this._pkgMgr.getRegistry();
    const pkg      = registry?.packages.find(p => p.id === PACKAGE_ID);
    const modelDef = pkg?.models?.find(m => m.id === modelId);
    const useGpu   = modelDef?.useGpu ?? false;

    // Lazy-init the MediaPipe WASM module
    if (!this._genAi) {
      this._genAi = await this._initGenAi();
    }

    const { LlmInference } = await this._getTasksGenAi();

    this._model = await LlmInference.createFromOptions(this._genAi, {
      baseOptions: {
        modelAssetPath: blobUrl,
        delegate: useGpu ? "GPU" : "CPU",
      },
      maxTokens:  opts.maxTokens  ?? DEFAULT_MAX_TOKENS,
      topK:       opts.topK       ?? DEFAULT_TOP_K,
      temperature:opts.temperature ?? DEFAULT_TEMPERATURE,
      randomSeed: DEFAULT_RANDOM_SEED,
    });

    this._loadedModelId = modelId;
  }

  // ---------------------------------------------------------------------------
  // Inference
  // ---------------------------------------------------------------------------

  /**
   * Generate a response for the given prompt.
   * @param {string} prompt
   * @param {object} [opts]
   * @returns {Promise<string>}
   */
  async generate(prompt, opts = {}) {
    this._assertLoaded();
    return this._model.generateResponse(prompt);
  }

  /**
   * Generate with streaming — calls onToken for each partial result.
   * @param {string} prompt
   * @param {function(string, boolean): void} onToken  (partial, done)
   */
  generateStream(prompt, onToken) {
    this._assertLoaded();
    this._model.generateResponse(prompt, onToken);
  }

  /**
   * Run the WellFair structured extraction prompt against a document.
   * Returns JSON matching extraction_schema.json (expert authoring pipeline).
   */
  async extractStructured(documentText) {
    this._assertLoaded();
    const prompt = buildExtractionPrompt(documentText);
    const raw = await this.generate(prompt);
    return parseJsonResponse(raw);
  }

  /**
   * Build a plain-English explanation for an anatomical implication.
   * Used by the Explainer module (user-runtime-lib/explainer.js).
   */
  async explain(implProps) {
    this._assertLoaded();
    const { structureName, severity, mechanismSummary, citation } = implProps;
    const prompt = buildExplainerPrompt(structureName, severity, mechanismSummary, citation);
    return this.generate(prompt);
  }

  // ---------------------------------------------------------------------------
  // Lifecycle
  // ---------------------------------------------------------------------------

  async unload() {
    if (this._model) {
      this._model.close?.();
      this._model = null;
    }
    if (this._modelBlobUrl) {
      URL.revokeObjectURL(this._modelBlobUrl);
      this._modelBlobUrl = null;
    }
    this._loadedModelId = null;
  }

  isLoaded() {
    return this._model !== null;
  }

  // ---------------------------------------------------------------------------
  // Private
  // ---------------------------------------------------------------------------

  _assertLoaded() {
    if (!this._model) throw new Error("No model loaded. Call load() first.");
  }

  async _initGenAi() {
    const { FilesetResolver } = await this._getTasksGenAi();
    return FilesetResolver.forGenAiTasks(MEDIAPIPE_WASM);
  }

  async _getTasksGenAi() {
    // Dynamic import from CDN. The module is cached by the browser after first load.
    return import(`${MEDIAPIPE_CDN}/genai_bundle.mjs`);
  }
}

// ---------------------------------------------------------------------------
// Prompt builders
// ---------------------------------------------------------------------------

function buildExtractionPrompt(documentText) {
  return (
    `You are a biomedical knowledge extraction assistant. Extract structured logical implications from the following document as JSON conforming to the WellFair extraction schema.\n\n` +
    `Use only standard ontology URIs (SNOMED-CT, FMA, HPO, LOINC). ` +
    `If you cannot identify a standard URI, set the field to "unresolved".\n\n` +
    `Document:\n${documentText.slice(0, 8000)}\n\n` +
    `Output JSON only. Begin with {`
  );
}

function buildExplainerPrompt(structureName, severity, mechanismSummary, citation) {
  return (
    `Rewrite the following clinical mechanism summary in plain English for a non-expert. ` +
    `Keep it to 2-3 sentences. Do not add medical advice. Do not change the core meaning.\n\n` +
    `Structure: ${structureName}\n` +
    `Severity: ${severity}\n` +
    `Mechanism: ${mechanismSummary}\n` +
    `Source: ${citation}\n\n` +
    `Plain English explanation:`
  );
}

function parseJsonResponse(rawText) {
  // Strip any markdown code block fencing the model may have added
  const cleaned = rawText.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/, "").trim();
  const startIdx = cleaned.indexOf("{");
  if (startIdx === -1) throw new Error("No JSON object in LLM response");
  return JSON.parse(cleaned.slice(startIdx));
}

// ---------------------------------------------------------------------------
// Static profile metadata (used by the install UI)
// ---------------------------------------------------------------------------

MediaPipeLlmProfile.id       = "mediapipe";
MediaPipeLlmProfile.name     = "MediaPipe / LiteRT";
MediaPipeLlmProfile.platform = ["android", "chromium"];
