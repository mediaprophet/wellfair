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

    html = f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Wellfair Vault (WASM Demo)</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@stlite/mountable/build/stlite.css"/>
    <style>
      body, html {{ height: 100%; margin: 0; padding: 0; }}
      #root {{ height: 100%; }}
    </style>
  </head>
  <body>
    <div id="root"></div>
    <script src="https://cdn.jsdelivr.net/npm/@stlite/mountable/build/stlite.js"></script>
    <script>
      const files = {json.dumps(stlite_files)};
      
      stlite.mount(
        {{
          requirements: ["pandas", "rdflib", "python-dateutil", "pytz", "plotly", "pyyaml", "tqdm", "pydantic"],
          entrypoint: "ui/app.py",
          files: files
        }},
        document.getElementById("root")
      )
    </script>
  </body>
</html>
"""
    
    output_path = root / "docs" / "app.html"
    output_path.write_text(html, encoding="utf-8")
    print(f"Successfully wrote {output_path}")

if __name__ == "__main__":
    main()
