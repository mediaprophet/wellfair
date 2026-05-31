import os
import json
import ast
import base64
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    # Only bundle what is actually required for the app + the curated lightweight 3D assets.
    # Heavy 3D models must live in vendor/hologram/ (and be listed in manifest.json if present).
    directories = ["ui", "src", "config", "data/demo", "vendor"]

    # 3D hologram asset manifest (strongly recommended for keeping the PWA small).
    # Generate this automatically by running: python scripts/prepare_hologram_models.py
    HOLOGRAM_MANIFEST = root / "vendor" / "hologram" / "manifest.json"
    hologram_whitelist = None
    if HOLOGRAM_MANIFEST.exists():
        try:
            hologram_whitelist = set(json.loads(HOLOGRAM_MANIFEST.read_text(encoding="utf-8")))
            print(f"Using hologram manifest with {len(hologram_whitelist)} allowed assets.")
        except Exception as e:
            print(f"Warning: Could not parse hologram manifest: {e}")
    
    stlite_files = {}
    
    for d in directories:
        dir_path = root / d
        if not dir_path.exists():
            continue
            
        for path in dir_path.rglob("*"):
            if not path.is_file():
                continue
            if path.name.endswith(".pyc") or path.name == ".DS_Store":
                continue

            rel_path = str(path.relative_to(root)).replace("\\", "/")

            # Only include curated hologram assets if a manifest is present
            if hologram_whitelist is not None and rel_path.startswith("vendor/hologram/"):
                if rel_path not in hologram_whitelist:
                    continue

            # Additional size optimizations for smaller PWA bundles
            # Exclude large demo data files that are not essential for core PWA demo
            if rel_path.startswith("data/demo/") and (rel_path.endswith(".pkl") or "full" in rel_path.lower()):
                continue
            # Skip very large individual files unless they are critical 3D assets (pre-read check)
            try:
                if path.stat().st_size > 10 * 1024 * 1024 and not rel_path.startswith("vendor/hologram/"):
                    continue
            except Exception:
                pass

            content = path.read_bytes()
            try:
                stlite_files[rel_path] = content.decode("utf-8")
            except UnicodeDecodeError:
                stlite_files[rel_path] = {
                    "data": base64.b64encode(content).decode("ascii")
                }

    # --- Post-build verification: prevent silent missing-module disasters in Pyodide ---
    CRITICAL_MODULES = [
        "src/__init__.py",
        "src/utils.py",
        "src/phr_models/__init__.py",
        "src/phr_models/imaging.py",
        "src/phr_models/proxy_consent.py",
        "src/phr_models/profile.py",
        "src/phr_models/pathology.py",
        "ui/app.py",
        "ui/utils/__init__.py",
        "ui/utils/navigation.py",
        "ui/utils/components.py",
        "ui/utils/package_bridge.py",
        "ui/tabs/document_ingestion.py",
        "ui/tabs/packages_tab.py",
        "ui/tabs/personal_health.py",
        "ui/tabs/anatomy_3d.py",
    ]

    # Dynamically scan important __init__.py files for relative imports.
    # This automatically catches new submodules/packages without manual updates.
    # Add more package roots here as the project grows (especially anything imported via `from .xxx import`).
    INIT_FILES_TO_INTROSPECT = [
        "ui/utils/__init__.py",
        "src/phr_models/__init__.py",
    ]

    for init_path in INIT_FILES_TO_INTROSPECT:
        if init_path not in stlite_files:
            continue
        try:
            tree = ast.parse(stlite_files[init_path], filename=init_path)
            package_root = init_path.rsplit("/", 1)[0]  # e.g. "ui/utils" or "src/phr_models"

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.level > 0 and node.module:
                    module_name = node.module
                    # e.g. from .foo import bar  →  "package_root/foo.py"
                    rel_path = f"{package_root}/{module_name.replace('.', '/')}.py"
                    if rel_path not in CRITICAL_MODULES:
                        CRITICAL_MODULES.append(rel_path)

                    # Also add the __init__.py variant in case it's a package
                    pkg_init = f"{package_root}/{module_name.replace('.', '/')}/__init__.py"
                    if pkg_init not in CRITICAL_MODULES:
                        CRITICAL_MODULES.append(pkg_init)
        except Exception as e:
            print(f"Warning: Could not parse {init_path} for imports: {e}")

    # Validate that for every critical module we expect either the .py file or the package __init__.py
    actual_missing = []
    for m in CRITICAL_MODULES:
        if m in stlite_files:
            continue
        # For package-style paths (e.g. ui/utils/data_access/__init__.py), also accept the single-file version
        if m.endswith("/__init__.py"):
            single_file = m.replace("/__init__.py", ".py")
            if single_file in stlite_files:
                continue
        actual_missing.append(m)

    if actual_missing:
        print("ERROR: The following critical modules are MISSING from the Stlite bundle:")
        for m in actual_missing:
            print(f"     - {m}")
        print("   The WASM demo will fail to import these at runtime (ModuleNotFoundError).")
        print("   Make sure the files exist on disk and re-run this script.")
        # Fail the build so broken bundles are never shipped
        exit(1)
    else:
        print(f"OK: All {len(CRITICAL_MODULES)} critical modules present in bundle.")

    print(f"   Total files packaged: {len(stlite_files)}")

    # Post-build size audit for 3D assets (helps catch accidental bloat)
    hologram_size = 0
    for rel_path, content in stlite_files.items():
        if rel_path.startswith("vendor/hologram/") and not rel_path.endswith(".json"):
            size = len(content) if isinstance(content, str) else len(content.get("data", b""))
            hologram_size += size
    if hologram_size > 0:
        print(f"   Curated hologram assets total: {hologram_size / (1024*1024):.1f} MB (before base64)")

    # Warn about large assets that will inflate the PWA bundle
    large_assets = []
    for rel, content in stlite_files.items():
        size = len(content) if isinstance(content, str) else len(content.get("data", ""))
        if size > 5 * 1024 * 1024:  # > 5 MB
            large_assets.append((rel, size / (1024*1024)))

    if large_assets:
        print("\nWARNING: The following large assets are included in the bundle:")
        for rel, mb in sorted(large_assets, key=lambda x: -x[1]):
            print(f"     {rel}  ({mb:.1f} MB)")
        print("   These will significantly increase the download size of the PWA.")

    files_json = json.dumps(stlite_files).replace("<", "\\u003c")

    html = f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
    <meta name="theme-color" content="#030005" />
    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
    <title>Wellfair Vault (WASM Demo)</title>
    <link rel="manifest" href="manifest.webmanifest" />
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@stlite/mountable/build/stlite.css"/>
    <style>
      body, html {{ height: 100%; margin: 0; padding: 0; background-color: #030005; font-family: 'Outfit', sans-serif; }}
      #root {{ height: 100%; }}
      /* Loader Styles */
      #loader-wrapper {{
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background-color: #030005;
        background-image: radial-gradient(circle at 50% 50%, #1a0014 0%, #030005 60%);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 999999;
        transition: opacity 0.8s ease-out;
      }}
      .spinner {{
        width: 60px;
        height: 60px;
        border: 3px solid rgba(255, 30, 86, 0.1);
        border-radius: 50%;
        border-top-color: #ff1e56;
        animation: spin 1s ease-in-out infinite, pulse 2s infinite alternate;
        box-shadow: 0 0 20px rgba(255, 30, 86, 0.4);
      }}
      @keyframes spin {{ 
        to {{ transform: rotate(360deg); }} 
      }}
      @keyframes pulse {{
        from {{ box-shadow: 0 0 10px rgba(255, 30, 86, 0.2); }}
        to {{ box-shadow: 0 0 30px rgba(255, 30, 86, 0.6); }}
      }}
      .loader-text {{
        margin-top: 24px;
        color: #ffb3c6;
        font-weight: 600;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        font-size: 14px;
        animation: blink 1.5s infinite;
      }}
      @keyframes blink {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
      }}
      .hidden {{
        opacity: 0 !important;
        pointer-events: none;
      }}
      /* PWA Install Button */
      #pwa-install-btn {{
        display: none; /* Hidden by default until beforeinstallprompt fires */
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 9999999;
        background: linear-gradient(135deg, #ff1e56 0%, #d80032 100%);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 14px 28px;
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 16px;
        letter-spacing: 0.05em;
        box-shadow: 0 4px 15px rgba(255, 30, 86, 0.4);
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
        align-items: center;
        gap: 8px;
      }}
      #pwa-install-btn:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 30, 86, 0.6);
      }}
      #pwa-install-btn:active {{
        transform: translateY(1px);
      }}
      .install-icon {{
        width: 20px;
        height: 20px;
        fill: currentColor;
      }}
      #pwa-update-btn {{
        display: none; /* Hidden by default until an update is ready */
        position: fixed;
        top: 12px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 99999999;
        background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%);
        color: white;
        border: none;
        border-radius: 9999px;
        padding: 12px 24px;
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 15px;
        letter-spacing: 0.05em;
        box-shadow: 0 8px 30px rgba(20, 184, 166, 0.5);
        cursor: pointer;
        animation: pulseUpdate 2s infinite;
        display: flex;
        align-items: center;
        gap: 8px;
        white-space: nowrap;
      }}
      @keyframes pulseUpdate {{
        0%, 100% {{ box-shadow: 0 8px 30px rgba(20, 184, 166, 0.5); }}
        50% {{ box-shadow: 0 8px 40px rgba(20, 184, 166, 0.8); transform: translateX(-50%) scale(1.02); }}
      }}
      #pwa-update-btn:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(20, 184, 166, 0.6);
      }}
      #pwa-update-btn:active {{
        transform: translateY(1px);
      }}

    </style>
  </head>
  <body>
    <button id="pwa-update-btn" style="display: none;">
      <svg class="install-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"/>
      </svg>
      Update Available
    </button>
    <button id="pwa-install-btn" style="display: none;">
      <svg class="install-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
      </svg>
      Install App
    </button>
    <div id="loader-wrapper">
        <div class="spinner"></div>
        <div class="loader-text">Initializing Holographic Engine...</div>
    </div>
    <div id="root"></div>

    <!-- Device File Sources UI (visible on installed PWA) -->
    <div id="device-sources-bar" style="display: none; position: fixed; bottom: 0; left: 0; right: 0; background: #111113; border-top: 1px solid #27272a; padding: 8px 12px; z-index: 999999; font-family: system-ui, sans-serif;">
      <div style="max-width: 720px; margin: 0 auto; display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
        <span style="color: #a1a1aa; font-size: 13px;">📁 Device Data Sources</span>
        <button id="device-choose-folder" style="background: #27272a; color: white; border: 1px solid #3f3f46; padding: 6px 14px; border-radius: 6px; font-size: 13px; cursor: pointer;">
          Choose Export Folder on Phone
        </button>
        <span id="device-status" style="color: #4ade80; font-size: 12px;"></span>
        <button id="device-import-btn" style="display:none; background: #14b8a6; color: black; border: none; padding: 6px 14px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer;">
          Import &amp; Sync to Vault
        </button>
      </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/@stlite/mountable/build/stlite.js"></script>
    <!-- WellFair Device File System Bridge + UI (for installed PWA) -->
    <!-- Package Manager: boots before stlite, exposes window.wellfairPackages -->
    <script type="module" src="packages/index.js"></script>
    <!-- Package download overlay UI -->
    <script src="package-download-ui.js"></script>
    <script src="device-bridge.js"></script>
    <script src="device-ui.js"></script>
    <script>
      const files = {files_json};
      
      stlite.mount(
        {{
          requirements: ["pandas", "rdflib", "python-dateutil", "pytz", "plotly", "pyyaml", "tqdm", "pydantic"],
          entrypoint: "ui/app.py",
          files: files
        }},
        document.getElementById("root")
      )

      // Hide loader once Streamlit mounts the .stApp DOM element
      const observer = new MutationObserver((mutations, obs) => {{
        const stApp = document.querySelector('.stApp');
        if (stApp) {{
            const loader = document.getElementById('loader-wrapper');
            loader.classList.add('hidden');
            setTimeout(() => loader.remove(), 1000); // Remove from DOM after fade out
            obs.disconnect(); // Stop observing
        }}
      }});
      observer.observe(document.body, {{ childList: true, subtree: true }});

      // PWA Installation Logic
      let deferredPrompt;
      const installBtn = document.getElementById('pwa-install-btn');
      
      window.addEventListener('beforeinstallprompt', (e) => {{
        // Prevent the mini-infobar from appearing on mobile
        e.preventDefault();
        // Stash the event so it can be triggered later.
        deferredPrompt = e;
        // Update UI notify the user they can install the PWA
        installBtn.style.display = 'flex';
      }});

      installBtn.addEventListener('click', async () => {{
        // Hide the app provided install promotion
        installBtn.style.display = 'none';
        // Show the install prompt
        if (deferredPrompt) {{
          deferredPrompt.prompt();
          // Wait for the user to respond to the prompt
          const {{ outcome }} = await deferredPrompt.userChoice;
          console.log(`User response to the install prompt: ${{outcome}}`);
          // We've used the prompt, and can't use it again, throw it away
          deferredPrompt = null;
        }}
      }});

      window.addEventListener('appinstalled', () => {{
        // Hide the app-provided install promotion
        installBtn.style.display = 'none';
        // Clear the deferredPrompt so it can be garbage collected
        deferredPrompt = null;
        console.log('PWA was installed');
      }});

      // Device UI is now handled by docs/device-ui.js (loaded externally)
      // PWA Update Logic
      const updateBtn = document.getElementById('pwa-update-btn');
      let newWorker;

      if ('serviceWorker' in navigator) {{
        navigator.serviceWorker.register('sw.js').then(reg => {{
          reg.addEventListener('updatefound', () => {{
            newWorker = reg.installing;
            newWorker.addEventListener('statechange', () => {{
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {{
                // New update available - show both banner (more visible) and button
                const banner = document.getElementById('update-banner');
                if (banner) banner.style.display = 'flex';
                updateBtn.style.display = 'flex';
              }}
            }});
          }});
        }});

        let refreshing = false;
        navigator.serviceWorker.addEventListener('controllerchange', () => {{
          if (!refreshing) {{
            refreshing = true;
            window.location.reload();
          }}
        }});

        updateBtn.addEventListener('click', () => {{
          updateBtn.style.display = 'none';
          const banner = document.getElementById('update-banner');
          if (banner) banner.style.display = 'none';
          if (newWorker) {{
            newWorker.postMessage({{ type: 'SKIP_WAITING' }});
          }}
        }});
      }}
    </script>
  </body>
</html>
"""
    
    output_path = root / "docs" / "app.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # GitHub Pages needs .nojekyll so it doesn't try to process the site with Jekyll
    nojekyll = output_path.parent / ".nojekyll"
    nojekyll.touch(exist_ok=True)

    # Very robust write for huge files on Windows.
    # Write to a temp file first, then replace. This avoids many locking issues.
    temp_path = output_path.with_suffix(".tmp.html")
    with open(temp_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)

    if output_path.exists():
        try:
            output_path.unlink()
        except PermissionError:
            print("Warning: Old app.html is locked. You may need to close any browser tab viewing it.")

    temp_path.replace(output_path)

    final_size = output_path.stat().st_size / (1024 * 1024)
    print(f"Successfully wrote {output_path} ({final_size:.1f} MB)")

if __name__ == "__main__":
    main()
