/**
 * WellFair Package Download UI
 * ==============================
 * Shows a full-screen overlay when a package needs to be installed.
 * Handles the model-import flow for auth-gated models (user picks .bin file).
 * Triggered by window event 'wellfair:show-install-ui' or called directly.
 *
 * Works alongside package-manager.js — reads the registry from
 * window.wellfairPackages and delegates actual download/import to it.
 */

(function () {
  "use strict";

  // Inject styles
  const style = document.createElement("style");
  style.textContent = `
    #wf-pkg-overlay {
      position: fixed; inset: 0; z-index: 9999999;
      background: rgba(3,0,5,0.92);
      display: flex; align-items: center; justify-content: center;
      font-family: 'Outfit', system-ui, sans-serif;
      backdrop-filter: blur(8px);
      animation: wfFadeIn 0.2s ease-out;
    }
    @keyframes wfFadeIn { from { opacity: 0 } to { opacity: 1 } }
    #wf-pkg-overlay.hidden { display: none; }
    .wf-pkg-card {
      background: #111113;
      border: 1px solid #27272a;
      border-radius: 20px;
      padding: 32px;
      max-width: 520px;
      width: calc(100vw - 40px);
      color: #f4f4f5;
    }
    .wf-pkg-card h2 { margin: 0 0 8px; font-size: 1.3rem; }
    .wf-pkg-card p  { color: #a1a1aa; font-size: 0.9rem; line-height: 1.5; margin: 0 0 16px; }
    .wf-pkg-icon    { font-size: 2.5rem; margin-bottom: 12px; }
    .wf-pkg-size    { color: #71717a; font-size: 0.8rem; margin-bottom: 20px; }
    .wf-pkg-section { margin-top: 16px; padding-top: 16px; border-top: 1px solid #27272a; }
    .wf-pkg-section h3 { font-size: 0.85rem; color: #a1a1aa; text-transform: uppercase; letter-spacing: 0.08em; margin: 0 0 10px; }
    .wf-model-row {
      display: flex; align-items: center; gap: 12px;
      padding: 10px 12px; border-radius: 10px;
      border: 1px solid #27272a; margin-bottom: 8px; cursor: pointer;
      transition: border-color 0.15s, background 0.15s;
    }
    .wf-model-row:hover { border-color: #14b8a6; background: rgba(20,184,166,0.06); }
    .wf-model-row.selected { border-color: #14b8a6; background: rgba(20,184,166,0.12); }
    .wf-model-meta { flex: 1; }
    .wf-model-name  { font-size: 0.9rem; font-weight: 600; }
    .wf-model-desc  { font-size: 0.75rem; color: #71717a; margin-top: 2px; }
    .wf-model-size  { font-size: 0.75rem; color: #a1a1aa; white-space: nowrap; }
    .wf-badge-auth  { background: rgba(251,191,36,0.15); color: #fbbf24; font-size: 0.7rem;
                      padding: 2px 8px; border-radius: 20px; white-space: nowrap; }
    .wf-btn {
      width: 100%; padding: 13px; border: none; border-radius: 12px;
      font-family: inherit; font-size: 0.95rem; font-weight: 700;
      cursor: pointer; transition: opacity 0.15s, transform 0.1s;
      margin-bottom: 8px;
    }
    .wf-btn:active { transform: scale(0.98); }
    .wf-btn-primary  { background: linear-gradient(135deg,#14b8a6,#0d9488); color: #000; }
    .wf-btn-kaggle   { background: #20beff; color: #000; }
    .wf-btn-file     { background: #27272a; color: #f4f4f5; border: 1px solid #3f3f46; }
    .wf-btn-close    { background: transparent; color: #71717a; border: 1px solid #27272a; margin-top: 4px; }
    .wf-btn:disabled { opacity: 0.45; cursor: not-allowed; }
    .wf-progress-wrap { margin: 12px 0; }
    .wf-progress-bar  { height: 6px; border-radius: 3px; background: #27272a; overflow: hidden; }
    .wf-progress-fill { height: 100%; border-radius: 3px;
                        background: linear-gradient(90deg,#14b8a6,#06b6d4);
                        transition: width 0.3s; }
    .wf-progress-label { font-size: 0.78rem; color: #a1a1aa; margin-top: 6px; }
    .wf-error   { background: rgba(239,68,68,0.1); color: #f87171;
                  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin-top: 12px; }
    .wf-success { background: rgba(20,184,166,0.12); color: #2dd4bf;
                  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin-top: 12px; }
  `;
  document.head.appendChild(style);

  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------
  let _overlay    = null;
  let _packageId  = null;
  let _selectedModel = null;

  const PACKAGE_ICONS = {
    "prolog-wasm":   "🧠",
    "llm-mediapipe": "🤖",
    "oxigraph":      "🗄️",
  };

  // ---------------------------------------------------------------------------
  // Trigger
  // ---------------------------------------------------------------------------
  window.addEventListener("wellfair:show-install-ui", (e) => {
    show(e.detail?.packageId);
  });

  function show(packageId) {
    _packageId = packageId;
    if (_overlay) _overlay.remove();
    _overlay = buildOverlay(packageId);
    document.body.appendChild(_overlay);
  }

  function hide() {
    _overlay?.remove();
    _overlay = null;
  }

  // ---------------------------------------------------------------------------
  // Build overlay
  // ---------------------------------------------------------------------------
  function buildOverlay(packageId) {
    const mgr      = window.wellfairPackages;
    const registry = mgr?.getRegistry();
    const pkg      = registry?.packages.find(p => p.id === packageId);
    if (!pkg) return buildErrorOverlay(`Unknown package: ${packageId}`);

    const icon = PACKAGE_ICONS[packageId] ?? "📦";
    const el   = document.createElement("div");
    el.id      = "wf-pkg-overlay";

    const sizeMb = pkg.downloadSizeBytes > 0
      ? ` — ${(pkg.downloadSizeBytes / 1e6).toFixed(0)} MB runtime`
      : "";

    let modelHtml = "";
    if (pkg.models?.length) {
      _selectedModel = pkg.models.find(m => m.preferred)?.id ?? pkg.models[0].id;

      const modelRows = pkg.models.map(m => {
        const sizeMb = (m.sizeBytes / 1e9).toFixed(1) + " GB";
        const authBadge = m.requiresAuth ? `<span class="wf-badge-auth">Kaggle licence</span>` : "";
        const sel = m.id === _selectedModel ? " selected" : "";
        return `
          <div class="wf-model-row${sel}" data-model-id="${m.id}">
            <div class="wf-model-meta">
              <div class="wf-model-name">${m.name}</div>
              <div class="wf-model-desc">${m.description}</div>
            </div>
            <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;">
              <span class="wf-model-size">${sizeMb}</span>
              ${authBadge}
            </div>
          </div>`;
      }).join("");

      const selectedModel = pkg.models.find(m => m.id === _selectedModel);
      const needsAuth = selectedModel?.requiresAuth;

      modelHtml = `
        <div class="wf-pkg-section">
          <h3>Select model</h3>
          ${modelRows}
        </div>
        <div class="wf-pkg-section" id="wf-model-actions">
          ${needsAuth ? buildAuthModelActions(selectedModel) : buildDirectModelActions(selectedModel)}
        </div>`;
    } else {
      modelHtml = `
        <div class="wf-pkg-section" id="wf-model-actions">
          <button class="wf-btn wf-btn-primary" id="wf-install-btn">
            Download &amp; Install${sizeMb}
          </button>
        </div>`;
    }

    el.innerHTML = `
      <div class="wf-pkg-card">
        <div class="wf-pkg-icon">${icon}</div>
        <h2>${pkg.name}</h2>
        <p>${pkg.description}</p>
        ${pkg.downloadSizeBytes > 0 ? `<div class="wf-pkg-size">Runtime: ${(pkg.downloadSizeBytes / 1e6).toFixed(0)} MB</div>` : ""}
        ${modelHtml}
        <div id="wf-progress-area"></div>
        <button class="wf-btn wf-btn-close" id="wf-close-btn">Cancel</button>
      </div>`;

    // Event listeners
    el.querySelectorAll(".wf-model-row").forEach(row => {
      row.addEventListener("click", () => {
        el.querySelectorAll(".wf-model-row").forEach(r => r.classList.remove("selected"));
        row.classList.add("selected");
        _selectedModel = row.dataset.modelId;
        const model = pkg.models.find(m => m.id === _selectedModel);
        el.querySelector("#wf-model-actions").innerHTML =
          model?.requiresAuth ? buildAuthModelActions(model) : buildDirectModelActions(model);
        bindModelActions(el, pkg, model);
      });
    });

    el.querySelector("#wf-close-btn")?.addEventListener("click", hide);

    if (!pkg.models?.length) {
      el.querySelector("#wf-install-btn")?.addEventListener("click", () => {
        startRuntimeInstall(pkg, el);
      });
    } else {
      const model = pkg.models.find(m => m.id === _selectedModel);
      bindModelActions(el, pkg, model);
    }

    return el;
  }

  function buildAuthModelActions(model) {
    return `
      <p style="font-size:0.82rem;color:#a1a1aa;margin:0 0 10px;">
        This model requires accepting Google's Gemma licence on Kaggle.
        Download the <strong>${model.name}</strong> <code>.bin</code> file,
        then import it here. It will be stored privately on your device.
      </p>
      <button class="wf-btn wf-btn-kaggle" id="wf-kaggle-btn">Open Kaggle Download Page</button>
      <button class="wf-btn wf-btn-file"   id="wf-file-btn">Load from file (.bin)</button>`;
  }

  function buildDirectModelActions(model) {
    const sizeMb = model ? ((model.sizeBytes / 1e9).toFixed(1) + " GB") : "";
    return `
      <button class="wf-btn wf-btn-primary" id="wf-direct-btn">
        Download model (${sizeMb})
      </button>`;
  }

  function bindModelActions(el, pkg, model) {
    el.querySelector("#wf-kaggle-btn")?.addEventListener("click", () => {
      window.open(model.sourceUrl, "_blank", "noopener");
    });

    el.querySelector("#wf-file-btn")?.addEventListener("click", () => {
      const input = document.createElement("input");
      input.type   = "file";
      input.accept = ".bin,.task";
      input.addEventListener("change", async () => {
        const file = input.files[0];
        if (!file) return;
        await startModelImport(pkg, model, file, el);
      });
      input.click();
    });

    el.querySelector("#wf-direct-btn")?.addEventListener("click", () => {
      startModelImport(pkg, model, null, el);
    });
  }

  // ---------------------------------------------------------------------------
  // Install flows
  // ---------------------------------------------------------------------------
  async function startRuntimeInstall(pkg, el) {
    const progress = el.querySelector("#wf-progress-area");
    progress.innerHTML = buildProgressHtml("Downloading runtime…", 0);
    disableButtons(el);

    try {
      await window.wellfairPackages.install(pkg.id, (fraction, loaded, total) => {
        const pct  = Math.round(fraction * 100);
        const mbDone  = (loaded  / 1e6).toFixed(1);
        const mbTotal = (total   / 1e6).toFixed(1);
        progress.innerHTML = buildProgressHtml(`Downloading… ${mbDone} / ${mbTotal} MB`, fraction);
      });
      progress.innerHTML = `<div class="wf-success">Installed successfully. Reload the app to use this package.</div>`;
      setTimeout(hide, 3000);
    } catch (err) {
      progress.innerHTML = `<div class="wf-error">${escapeHtml(err.message)}</div>`;
      enableButtons(el);
    }
  }

  async function startModelImport(pkg, model, file, el) {
    const progress = el.querySelector("#wf-progress-area");
    disableButtons(el);

    if (!file && !model.directDownloadUrl) {
      progress.innerHTML = `<div class="wf-error">
        Direct download is not available for this model (requires Kaggle authentication).
        Please use "Load from file" after downloading from Kaggle.
      </div>`;
      enableButtons(el);
      return;
    }

    const label = file
      ? `Importing ${(file.size / 1e9).toFixed(1)} GB…`
      : `Downloading ${(model.sizeBytes / 1e9).toFixed(1)} GB…`;
    progress.innerHTML = buildProgressHtml(label, 0);

    try {
      // First install the runtime components if not already installed
      const runtimeState = window.wellfairPackages.getPackageState(pkg.id);
      const parsed = runtimeState ? JSON.parse(runtimeState) : null;
      if (!parsed || (parsed.status !== "installed" && parsed.status !== "bundled")) {
        progress.innerHTML = buildProgressHtml("Installing runtime (~5 MB)…", 0);
        await window.wellfairPackages.install(pkg.id, (f) => {
          progress.innerHTML = buildProgressHtml(`Installing runtime… ${Math.round(f * 100)}%`, f);
        });
      }

      // Now import the model
      await window.wellfairPackages.installModel(pkg.id, model.id, file, (fraction, loaded, total) => {
        const pct       = Math.round(fraction * 100);
        const gbDone    = (loaded / 1e9).toFixed(2);
        const gbTotal   = (total  / 1e9).toFixed(2);
        progress.innerHTML = buildProgressHtml(
          `${file ? "Importing" : "Downloading"} model… ${gbDone} / ${gbTotal} GB (${pct}%)`,
          fraction
        );
      });

      progress.innerHTML = `<div class="wf-success">
        Model installed. On-device LLM is ready.
        This page will reload in 3 seconds.
      </div>`;
      setTimeout(() => { hide(); location.reload(); }, 3000);
    } catch (err) {
      progress.innerHTML = `<div class="wf-error">${escapeHtml(err.message)}</div>`;
      enableButtons(el);
    }
  }

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------
  function buildProgressHtml(label, fraction) {
    const pct = Math.round(fraction * 100);
    return `
      <div class="wf-progress-wrap">
        <div class="wf-progress-bar">
          <div class="wf-progress-fill" style="width:${pct}%"></div>
        </div>
        <div class="wf-progress-label">${escapeHtml(label)}</div>
      </div>`;
  }

  function buildErrorOverlay(msg) {
    const el = document.createElement("div");
    el.id = "wf-pkg-overlay";
    el.innerHTML = `
      <div class="wf-pkg-card">
        <div class="wf-error">${escapeHtml(msg)}</div>
        <button class="wf-btn wf-btn-close" id="wf-close-btn">Close</button>
      </div>`;
    el.querySelector("#wf-close-btn")?.addEventListener("click", hide);
    return el;
  }

  function disableButtons(el) {
    el.querySelectorAll(".wf-btn:not(#wf-close-btn)").forEach(b => { b.disabled = true; });
  }

  function enableButtons(el) {
    el.querySelectorAll(".wf-btn").forEach(b => { b.disabled = false; });
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  // Expose for programmatic use
  window.wellfairShowInstallUI = show;
})();
