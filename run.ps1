$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ProjectDir ".venv/Scripts/python.exe"

if (Test-Path $VenvPython) {
    & $VenvPython (Join-Path $ProjectDir "main.py")
} else {
    Write-Error "Run .\setup.ps1 first so Padh Le uses its isolated Python 3.11 environment."
    exit 1
}
