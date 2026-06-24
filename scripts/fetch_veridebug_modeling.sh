#!/usr/bin/env bash
# Fetch VeriDebug's llama_grit modeling file (missing from the HF weight repo).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/react/modeling_llama_gritlm.py"
URL="https://raw.githubusercontent.com/CatIIIIIIII/VeriDebug/main/src/modeling_llama_gritlm.py"

if [[ -f "$DEST" ]]; then
  echo "Already present: $DEST"
  exit 0
fi

echo "Downloading $URL"
curl -fsSL "$URL" -o "$DEST"
echo "Saved $DEST"
