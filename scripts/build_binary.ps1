# Build OmniSwarm standalone binary via PyInstaller (Windows)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

param(
    [string]$OutputName = "omni-swarm-node"
)

Write-Output "[INFO] Installing build dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller

Write-Output "[INFO] Building one-file binary..."
python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --name $OutputName `
    core/__main__.py

$artifact = Join-Path "dist" ($OutputName + ".exe")
if (-not (Test-Path $artifact)) {
    throw "Expected artifact not found: $artifact"
}

Write-Output "[OK] Build completed: $artifact"
