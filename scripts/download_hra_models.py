"""
WellFair – HuBMAP Human Reference Atlas (HRA) Model Downloader
===============================================================
Downloads a curated set of FHIR/UBERON-tagged GLB organ models
from the CCF 3D Reference Object Library (CC BY 4.0 License).

Source: https://github.com/hubmapconsortium/ccf-3d-reference-object-library
License: Creative Commons Attribution 4.0 International (CC BY 4.0)
Attribution: HuBMAP Consortium, Indiana University, CCF Release v1.1/v1.4

Usage:
    python scripts/download_hra_models.py
"""

import os
import sys
import urllib.request
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


BASE_URL = "https://raw.githubusercontent.com/hubmapconsortium/ccf-3d-reference-object-library/main"
OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "models" / "hra"

# ============================================================
# Curated HRA asset manifest – mapped to WellFair organ layers
# Each entry: (remote_path, local_filename, system, uberon_id, description)
# ============================================================
ASSETS = [
    # ---- ANDROGENOUS BASE BODY (gender-neutral reference body) ----
    (
        "Androgenous/Androgenous.glb",
        "baseline.glb",
        "integumentary",
        "UBERON:0000955",  # body proper
        "Androgenous full-body reference – used as healthy baseline and male personas",
    ),

    # ---- VH MALE ORGANS (v1.1) ----
    (
        "VH_Male/v1.1/VH_M_Heart.glb",
        "organ_heart_m.glb",
        "cardiovascular",
        "UBERON:0000948",  # heart
        "Visible Human Male heart – detailed anatomical mesh",
    ),
    (
        "VH_Male/v1.1/Allen_M_Brain.glb",
        "organ_brain_m.glb",
        "nervous",
        "UBERON:0000955",  # brain
        "Allen Institute Male brain atlas – FMA-mapped cortical mesh",
    ),
    (
        "VH_Male/v1.1/VH_M_Kidney_L.glb",
        "organ_kidney_l_m.glb",
        "urinary",
        "UBERON:0004538",  # left kidney
        "Visible Human Male left kidney",
    ),
    (
        "VH_Male/v1.1/VH_M_Kidney_R.glb",
        "organ_kidney_r_m.glb",
        "urinary",
        "UBERON:0004539",  # right kidney
        "Visible Human Male right kidney",
    ),
    (
        "VH_Male/v1.1/SBU_M_Intestine_Large.glb",
        "organ_large_intestine_m.glb",
        "digestive",
        "UBERON:0000059",  # large intestine
        "Stony Brook University Male large intestine",
    ),
    (
        "VH_Male/v1.1/VH_M_Gallbladder.glb",
        "organ_gallbladder_m.glb",
        "digestive",
        "UBERON:0002110",  # gallbladder
        "Visible Human Male gallbladder",
    ),
    (
        "VH_Male/v1.1/NIH_M_Lymph_Node.glb",
        "organ_lymph_node_m.glb",
        "immune",
        "UBERON:0000029",  # lymph node
        "NIH Male lymph node – immune system layer",
    ),
    (
        "VH_Male/v1.1/VH_M_Blood_Vasculature.glb",
        "organ_vasculature_m.glb",
        "cardiovascular",
        "UBERON:0004537",  # cardiovascular system
        "Visible Human Male blood vasculature network",
    ),

    # ---- VH MALE ORGANS (v1.4 – newer additions) ----
    (
        "VH_Male/v1.4/3d-vh-m-lung.glb",
        "organ_lung_m.glb",
        "respiratory",
        "UBERON:0002048",  # lung
        "Visible Human Male lung v1.4",
    ),
    (
        "VH_Male/v1.4/3d-vh-m-blood-vasculature.glb",
        "organ_vasculature_v14_m.glb",
        "cardiovascular",
        "UBERON:0004537",
        "Visible Human Male blood vasculature v1.4 (higher detail)",
    ),
]

# ============================================================
# Persona-to-GLB mapping for WellFair demo runtime
# Describes which model is used for each demo persona.
# ============================================================
PERSONA_MANIFEST = {
    "Healthy Baseline": "models/hra/baseline.glb",
    "Michael (Homeless / Family Separation)": "models/hra/baseline.glb",
    "Elena (Trauma Survivor)": "models/hra/baseline.glb",
    "Rebecca (Birth Trauma / PTSD)": "models/hra/baseline.glb",
    "Margaret (Elder Abuse / Neglect)": "models/hra/baseline.glb",
    "Robert (Elder Neglect)": "models/hra/baseline.glb",
    "Jordan (NDIS Exploitation)": "models/hra/baseline.glb",
}


def sizeof_fmt(num):
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(num) < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} TB"


def download(url, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        print(f"  ✓  {dest.name} already exists, skipping.")
        return

    print(f"  ↓  {dest.name}", end="", flush=True)
    try:
        tmp = dest.with_suffix(".tmp")
        with urllib.request.urlopen(url, timeout=120) as response:
            total = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            with open(tmp, "wb") as f:
                while chunk := response.read(65536):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        print(f"\r  ↓  {dest.name}  {sizeof_fmt(downloaded)} / {sizeof_fmt(total)}  ({pct:.0f}%)", end="", flush=True)
        tmp.rename(dest)
        print(f"\r  ✓  {dest.name}  {sizeof_fmt(dest.stat().st_size)}")
    except Exception as e:
        if tmp.exists():
            tmp.unlink()
        print(f"\r  ✗  {dest.name} — FAILED: {e}")


def write_manifest(output_dir: Path):
    """Write a JSON manifest of all downloaded assets for the JS loader to query."""
    import json
    manifest = []
    for remote_path, local_name, system, uberon, desc in ASSETS:
        dest = output_dir / local_name
        manifest.append({
            "filename": local_name,
            "system": system,
            "uberon_id": uberon,
            "description": desc,
            "size_bytes": dest.stat().st_size if dest.exists() else 0,
            "source": f"https://github.com/hubmapconsortium/ccf-3d-reference-object-library/blob/main/{remote_path}",
            "license": "CC BY 4.0",
            "attribution": "HuBMAP Consortium / Indiana University"
        })
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\n  ✓  Manifest written → {manifest_path}")

    persona_path = output_dir / "personas.json"
    persona_path.write_text(json.dumps(PERSONA_MANIFEST, indent=2))
    print(f"  ✓  Persona map written → {persona_path}")


def main():
    print("=" * 60)
    print("  WellFair – HuBMAP HRA Asset Downloader")
    print("  License: CC BY 4.0 | HuBMAP Consortium")
    print("=" * 60)
    print(f"\nOutput directory: {OUTPUT_DIR}\n")

    total_assets = len(ASSETS)
    for i, (remote_path, local_name, system, uberon, desc) in enumerate(ASSETS, 1):
        url = f"{BASE_URL}/{remote_path}"
        dest = OUTPUT_DIR / local_name
        print(f"[{i}/{total_assets}] {system.upper()}  ({uberon})")
        print(f"       {desc}")
        download(url, dest)

    write_manifest(OUTPUT_DIR)

    print("\n" + "=" * 60)
    print("  Download complete!")
    print(f"  Models in: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
