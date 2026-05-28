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
    <title>Wellfair Vault (WASM Demo)</title>
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
    </style>
  </head>
  <body>
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

    </script>
  </body>
</html>
"""
    
    output_path = root / "docs" / "app.html"
    output_path.write_text(html, encoding="utf-8")
    print(f"Successfully wrote {output_path}")

if __name__ == "__main__":
    main()
