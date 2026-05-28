#!/usr/bin/env bash
# Convenience launcher for wellfair Streamlit UI
set -euo pipefail
cd "$(dirname "$0")"
python -m streamlit run ui/app.py --server.headless true
