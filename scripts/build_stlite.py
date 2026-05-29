import os
import json
import base64
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    directories = ["ui", "src", "config", "data/demo"]
    
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
            
            content = path.read_bytes()
            try:
                stlite_files[rel_path] = content.decode("utf-8")
            except UnicodeDecodeError:
                stlite_files[rel_path] = {
                    "data": base64.b64encode(content).decode("ascii")
                }

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
        bottom: 84px;
        right: 24px;
        z-index: 9999999;
        background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 14px 28px;
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 16px;
        letter-spacing: 0.05em;
        box-shadow: 0 4px 15px rgba(20, 184, 166, 0.4);
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
        display: flex;
        align-items: center;
        gap: 8px;
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
    <script src="https://cdn.jsdelivr.net/npm/@stlite/mountable/build/stlite.js"></script>
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

      // PWA Update Logic
      const updateBtn = document.getElementById('pwa-update-btn');
      let newWorker;

      if ('serviceWorker' in navigator) {{
        navigator.serviceWorker.register('sw.js').then(reg => {{
          reg.addEventListener('updatefound', () => {{
            newWorker = reg.installing;
            newWorker.addEventListener('statechange', () => {{
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {{
                // New update available
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
    output_path.write_text(html, encoding="utf-8")
    print(f"Successfully wrote {output_path}")

if __name__ == "__main__":
    main()
