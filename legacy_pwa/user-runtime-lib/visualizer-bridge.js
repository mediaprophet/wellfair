/**
 * WellFair Visualizer Bridge (Stage D)
 * ======================================
 * Translates merged implication results from the Informatics Engine into
 * mutations inside the Three.js scene graph.
 *
 * Responsibilities:
 *   D1. SPARQL mesh resolution  — FMA URI → Three.js mesh name
 *   D2. Hierarchy traversal     — parent FMA class → all child mesh names
 *   D3. Scene mutation          — apply highlight / pulse / stress-shader modes
 *   D4. Click handler           — anatomyUri → ExplanationCard → sidebar
 *   D5. System isolation mode   — dim non-implicated layers
 *
 * The bridge is pure client-side. It reads anatomy-mappings.ttl via the local
 * oxigraph store (wellfare-core) and mutates the THREE.Scene directly.
 * No network calls are made during highlighting.
 */

import { groupBySeverity }       from "./accumulator.js";
import { renderExplanationHtml } from "./explainer.js";

// ---------------------------------------------------------------------------
// SPARQL queries for mesh resolution (against anatomy-mappings.ttl)
// ---------------------------------------------------------------------------

/**
 * Resolve a list of exact FMA URIs to mesh IDs.
 * Returns rows: { meshId, highlightColor }
 */
const SPARQL_RESOLVE_MESHES = (fmaUris) => `
PREFIX app: <https://wellfair.app/ontology/>

SELECT DISTINCT ?meshId ?highlightColor WHERE {
  ?element app:mapsToAnatomy ?uri ;
           app:hasMeshId ?meshId .
  OPTIONAL {
    ?implication app:impliesPathologyIn ?uri ;
                 app:highlightColor ?highlightColor .
  }
  VALUES ?uri {
    ${fmaUris.map(u => `<${u}>`).join("\n    ")}
  }
}
`;

/**
 * Resolve a parent FMA class to all child mesh IDs via rdfs:subClassOf* traversal.
 * Used for diffuse conditions (EDS joints, connective tissue).
 */
const SPARQL_RESOLVE_HIERARCHY = (parentUri) => `
PREFIX app:  <https://wellfair.app/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?meshId WHERE {
  ?element app:mapsToAnatomy ?specificUri ;
           app:hasMeshId ?meshId .
  ?specificUri rdfs:subClassOf* <${parentUri}> .
}
`;

// ---------------------------------------------------------------------------
// Render mode constants
// ---------------------------------------------------------------------------

export const RenderMode = Object.freeze({
  HIGHLIGHT:     "highlight",     // D3 Mode 1: colour + emissive — direct causal target
  PULSE:         "pulse",         // D3 Mode 2: animated emissive — secondary / accumulating
  STRESS_SHADER: "stress_shader", // D3 Mode 3: structural vulnerability (EDS, connective tissue)
  DIMMED:        "dimmed",        // all non-implicated meshes
  BASELINE:      "baseline",      // full reset
});

const SEVERITY_EMISSIVE = { high: 0.9, medium: 0.6, low: 0.3 };
const SEVERITY_COLORS   = { high: 0xff3333, medium: 0xffaa00, low: 0xffffaa };

// Pulse animation state
const PULSING_MESHES = new Set();   // mesh.uuid values currently pulsing
let   _pulseRafId    = null;

// ---------------------------------------------------------------------------
// VisualizerBridge class
// ---------------------------------------------------------------------------

export class VisualizerBridge {
  /**
   * @param {object} opts
   * @param {THREE.Scene} opts.scene            - The Three.js scene instance
   * @param {function(string): Promise<string>} opts.sparqlQuery
   *   Executes SPARQL against the local store (same as engine.js)
   * @param {function(ExplanationCard): void} opts.onMeshClick
   *   Called when a highlighted mesh is clicked. Receives explanation card.
   * @param {boolean} [opts.darkMode=true]
   */
  constructor({ scene, sparqlQuery, onMeshClick, darkMode = true }) {
    this._scene        = scene;
    this._sparqlQuery  = sparqlQuery;
    this._onMeshClick  = onMeshClick;
    this._darkMode     = darkMode;

    // Track original materials for reset
    this._originalMaterials = new Map();  // mesh.uuid → { emissive, emissiveIntensity }

    // Current evaluation state
    this._currentMeshMap   = new Map();   // anatomyUri → meshId[]
    this._currentExplMap   = null;        // Map<anatomyUri, ExplanationCard>
    this._implicatedMeshes = new Set();   // mesh.uuid values currently highlighted

    // Raycaster (set up by caller via setRaycaster)
    this._raycaster = null;
    this._camera    = null;
  }

  // -------------------------------------------------------------------------
  // Raycaster setup (D4 prerequisite)
  // -------------------------------------------------------------------------

  setRaycaster(raycaster, camera) {
    this._raycaster = raycaster;
    this._camera    = camera;
  }

  // -------------------------------------------------------------------------
  // Main: apply evaluation results to the scene (D1 → D3 → D4 → D5)
  // -------------------------------------------------------------------------

  /**
   * Apply a full evaluation result to the scene.
   *
   * @param {import('./accumulator.js').MergedImplication[]} merged
   * @param {Map<string, ExplanationCard>} explanations
   */
  async applyResult(merged, explanations) {
    this._currentExplMap = explanations;

    // Reset scene to baseline first
    this.resetScene();

    if (merged.length === 0) return;

    const bands = groupBySeverity(merged);

    // Step D1: Resolve all exact-match FMA URIs to mesh IDs
    const allUris     = merged.map(m => m.anatomyUri);
    const meshMap     = await this._resolveMeshIds(allUris);
    this._currentMeshMap = meshMap;

    // Step D2: Hierarchy traversal for is_hierarchy_target URIs
    // The merged result doesn't directly flag this — we detect by
    // checking if the SPARQL exact match returned nothing for a URI.
    for (const impl of merged) {
      if (!meshMap.has(impl.anatomyUri) || meshMap.get(impl.anatomyUri).length === 0) {
        const childMeshIds = await this._resolveHierarchy(impl.anatomyUri);
        if (childMeshIds.length > 0) {
          meshMap.set(impl.anatomyUri, childMeshIds);
        }
      }
    }

    // Step D3: Apply render modes per severity band
    // High → highlight, Medium → pulse (if also in multi-source), Low → highlight (dim)
    for (const impl of merged) {
      const meshIds = meshMap.get(impl.anatomyUri) ?? [];
      const mode    = impl.sources.length > 1 && impl.severity !== "high"
        ? RenderMode.PULSE
        : RenderMode.HIGHLIGHT;

      for (const meshId of meshIds) {
        this._applyRenderMode(meshId, impl.severity, mode);
      }
    }

    // Step D5: Dim all non-implicated meshes
    const implicatedMeshIds = new Set([...meshMap.values()].flat());
    this._dimNonImplicated(implicatedMeshIds);
  }

  // -------------------------------------------------------------------------
  // D1: SPARQL mesh resolver
  // -------------------------------------------------------------------------

  async _resolveMeshIds(fmaUris) {
    const meshMap = new Map();
    if (fmaUris.length === 0) return meshMap;

    try {
      const json = JSON.parse(await this._sparqlQuery(SPARQL_RESOLVE_MESHES(fmaUris)));
      for (const row of (json?.results?.bindings ?? [])) {
        const uri    = row.meshId?.value  ? row : null;  // guard
        const meshId = row.meshId?.value;
        const color  = row.highlightColor?.value;

        // Group mesh IDs per anatomy URI — we need the reverse map too
        // Walk the existing mesh map to find which URI this meshId belongs to
        // (SPARQL doesn't return the matched URI here — do a second pass)
        if (meshId) {
          if (!meshMap.has("__all__")) meshMap.set("__all__", []);
          meshMap.get("__all__").push({ meshId, color });
        }
      }

      // Re-query each URI individually for proper mapping
      // (More efficient: modify SPARQL to return ?uri — but keeping query simple)
      meshMap.delete("__all__");
      for (const fmaUri of fmaUris) {
        const singleJson = JSON.parse(
          await this._sparqlQuery(SPARQL_RESOLVE_MESHES([fmaUri]))
        );
        const ids = (singleJson?.results?.bindings ?? [])
          .map(r => r.meshId?.value)
          .filter(Boolean);
        meshMap.set(fmaUri, ids);
      }
    } catch (err) {
      console.error("[visualizer-bridge] Mesh resolution failed:", err);
    }

    return meshMap;
  }

  // -------------------------------------------------------------------------
  // D2: Hierarchy traversal for diffuse conditions
  // -------------------------------------------------------------------------

  async _resolveHierarchy(parentUri) {
    try {
      const json = JSON.parse(await this._sparqlQuery(SPARQL_RESOLVE_HIERARCHY(parentUri)));
      return (json?.results?.bindings ?? [])
        .map(r => r.meshId?.value)
        .filter(Boolean);
    } catch {
      return [];
    }
  }

  // -------------------------------------------------------------------------
  // D3: Scene mutation — three render modes
  // -------------------------------------------------------------------------

  _applyRenderMode(meshId, severity, mode) {
    const mesh = this._scene.getObjectByName(meshId);
    if (!mesh?.isMesh || !mesh.material) return;

    // Capture original state before first mutation
    if (!this._originalMaterials.has(mesh.uuid)) {
      this._originalMaterials.set(mesh.uuid, {
        emissiveHex:       mesh.material.emissive?.getHex?.() ?? 0x000000,
        emissiveIntensity: mesh.material.emissiveIntensity ?? 0,
        opacity:           mesh.material.opacity ?? 1,
        transparent:       mesh.material.transparent ?? false,
      });
    }

    this._implicatedMeshes.add(mesh.uuid);
    const color    = SEVERITY_COLORS[severity]   ?? SEVERITY_COLORS.low;
    const intensity = SEVERITY_EMISSIVE[severity] ?? 0.3;

    switch (mode) {
      case RenderMode.HIGHLIGHT:
        mesh.material.emissive?.setHex(color);
        mesh.material.emissiveIntensity = intensity;
        mesh.userData.isImplicationTarget = true;
        mesh.userData.implicationSeverity = severity;
        break;

      case RenderMode.PULSE:
        mesh.material.emissive?.setHex(color);
        mesh.material.emissiveIntensity = intensity * 0.5;
        mesh.userData.isPulsing           = true;
        mesh.userData.pulseBaseIntensity  = intensity * 0.3;
        mesh.userData.pulsePeakIntensity  = intensity;
        mesh.userData.implicationSeverity = severity;
        PULSING_MESHES.add(mesh.uuid);
        this._ensurePulseLoop();
        break;

      case RenderMode.STRESS_SHADER:
        // Structural vulnerability — reduced opacity + colour tint
        mesh.material.emissive?.setHex(color);
        mesh.material.emissiveIntensity = intensity * 0.4;
        mesh.material.opacity = Math.min(1, (mesh.material.opacity ?? 1) * 0.7);
        mesh.material.transparent = true;
        mesh.userData.isStressMode        = true;
        mesh.userData.implicationSeverity = severity;
        break;

      default:
        break;
    }

    if (mesh.material.needsUpdate !== undefined) {
      mesh.material.needsUpdate = true;
    }
  }

  // -------------------------------------------------------------------------
  // D5: Dim non-implicated meshes
  // -------------------------------------------------------------------------

  _dimNonImplicated(implicatedMeshIds) {
    this._scene.traverse((child) => {
      if (!child.isMesh || !child.material) return;
      if (this._implicatedMeshes.has(child.uuid)) return;
      if (!child.userData?.name) return;  // skip unnamed utility meshes

      if (!this._originalMaterials.has(child.uuid)) {
        this._originalMaterials.set(child.uuid, {
          emissiveHex:       child.material.emissive?.getHex?.() ?? 0x000000,
          emissiveIntensity: child.material.emissiveIntensity ?? 0,
          opacity:           child.material.opacity ?? 1,
          transparent:       child.material.transparent ?? false,
        });
      }

      // Dim to ~15% opacity without changing emissive colour
      child.material.opacity      = 0.12;
      child.material.transparent  = true;
      child.material.emissiveIntensity = (child.material.emissiveIntensity ?? 0) * 0.1;
      if (child.material.needsUpdate !== undefined) child.material.needsUpdate = true;
    });
  }

  // -------------------------------------------------------------------------
  // Pulse animation loop
  // -------------------------------------------------------------------------

  _ensurePulseLoop() {
    if (_pulseRafId !== null) return;

    const animate = (time) => {
      if (PULSING_MESHES.size === 0) {
        _pulseRafId = null;
        return;
      }

      const t = time / 1000;
      PULSING_MESHES.forEach((uuid) => {
        const mesh = this._scene.getObjectByProperty("uuid", uuid);
        if (!mesh?.isMesh || !mesh.userData.isPulsing) {
          PULSING_MESHES.delete(uuid);
          return;
        }
        const base  = mesh.userData.pulseBaseIntensity ?? 0.2;
        const peak  = mesh.userData.pulsePeakIntensity ?? 0.6;
        const phase = (Math.sin(t * Math.PI * 1.2) + 1) / 2;  // 0–1, 1.2s period
        mesh.material.emissiveIntensity = base + (peak - base) * phase;
        if (mesh.material.needsUpdate !== undefined) mesh.material.needsUpdate = true;
      });

      _pulseRafId = requestAnimationFrame(animate);
    };

    _pulseRafId = requestAnimationFrame(animate);
  }

  // -------------------------------------------------------------------------
  // D4: Click handler — resolves anatomyUri from clicked mesh → explanation
  // -------------------------------------------------------------------------

  /**
   * Call this from the scene's click/pointer handler.
   * Pass the normalised mouse coordinates and the method handles the rest.
   *
   * @param {THREE.Vector2} mouse   - Normalised device coordinates (-1 to 1)
   * @returns {ExplanationCard|null}
   */
  handleClick(mouse) {
    if (!this._raycaster || !this._camera || !this._currentExplMap) return null;

    this._raycaster.setFromCamera(mouse, this._camera);

    // Intersect only named meshes that have implication data
    const candidates = [];
    this._scene.traverse((child) => {
      if (child.isMesh && child.userData.isImplicationTarget) {
        candidates.push(child);
      }
    });

    const intersects = this._raycaster.intersectObjects(candidates, false);
    if (intersects.length === 0) return null;

    const clicked = intersects[0].object;

    // Reverse map: mesh.name → anatomyUri
    for (const [anatomyUri, meshIds] of this._currentMeshMap.entries()) {
      if (meshIds.includes(clicked.name)) {
        const card = this._currentExplMap.get(anatomyUri);
        if (card) {
          this._onMeshClick(card);
          return card;
        }
      }
    }

    return null;
  }

  // -------------------------------------------------------------------------
  // Full scene reset
  // -------------------------------------------------------------------------

  resetScene() {
    // Stop pulse loop
    PULSING_MESHES.clear();
    if (_pulseRafId !== null) {
      cancelAnimationFrame(_pulseRafId);
      _pulseRafId = null;
    }

    // Restore all original materials
    this._originalMaterials.forEach((orig, uuid) => {
      const mesh = this._scene.getObjectByProperty("uuid", uuid);
      if (!mesh?.isMesh || !mesh.material) return;

      mesh.material.emissive?.setHex(orig.emissiveHex);
      mesh.material.emissiveIntensity = orig.emissiveIntensity;
      mesh.material.opacity           = orig.opacity;
      mesh.material.transparent       = orig.transparent;
      mesh.material.needsUpdate       = true;

      delete mesh.userData.isImplicationTarget;
      delete mesh.userData.isPulsing;
      delete mesh.userData.isStressMode;
      delete mesh.userData.implicationSeverity;
      delete mesh.userData.pulseBaseIntensity;
      delete mesh.userData.pulsePeakIntensity;
    });

    this._originalMaterials.clear();
    this._implicatedMeshes.clear();
    this._currentMeshMap.clear();
    this._currentExplMap = null;
  }
}


// ---------------------------------------------------------------------------
// Sidebar renderer — injects ExplanationCard HTML into a DOM container
// ---------------------------------------------------------------------------

/**
 * Attach a sidebar panel to a DOM element that auto-populates when
 * the VisualizerBridge fires onMeshClick.
 *
 * @param {HTMLElement}       container    - The sidebar DOM element
 * @param {VisualizerBridge}  bridge       - The active bridge instance
 * @param {boolean}           [darkMode]
 */
export function attachSidebar(container, bridge, darkMode = true) {
  // Override onMeshClick to render into the container
  const originalHandler = bridge._onMeshClick;
  bridge._onMeshClick = (card) => {
    container.innerHTML = renderExplanationHtml(card, darkMode);
    container.style.display = "block";
    originalHandler?.(card);
  };

  // Click outside to dismiss
  document.addEventListener("click", (e) => {
    if (!container.contains(e.target)) {
      container.style.display = "none";
    }
  });
}
