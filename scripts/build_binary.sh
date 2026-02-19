#!/usr/bin/env bash
set -euo pipefail

OUTPUT_NAME="${1:-omni-swarm-node}"

echo "[INFO] Installing build dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller

echo "[INFO] Building one-file binary..."
python -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --name "${OUTPUT_NAME}" \
  core/__main__.py

ARTIFACT="dist/${OUTPUT_NAME}"
if [[ ! -f "${ARTIFACT}" ]]; then
  echo "[ERROR] Expected artifact not found: ${ARTIFACT}"
  exit 1
fi

echo "[OK] Build completed: ${ARTIFACT}"
