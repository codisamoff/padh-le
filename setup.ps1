$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $ProjectDir ".venv"

if (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCommand = "py"
    $PythonArgs = @("-3.11")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCommand = "python"
    $PythonArgs = @()
} else {
    throw "Python 3.11 is required but was not found."
}

& $PythonCommand @PythonArgs -c "import sys; assert sys.version_info[:2] == (3, 11), 'Python 3.11 is required'"
if ($LASTEXITCODE -ne 0) { throw "Python 3.11 is required." }

$drive = (Get-Item $ProjectDir).PSDrive
if ($drive.Free -lt 5GB) {
    Write-Warning "Less than 5 GB of free disk space is available. Computer-vision dependencies can require several GB."
}

if ((Test-Path $VenvDir) -and -not (Test-Path $VenvDir -PathType Container)) {
    throw "$VenvDir exists but is not a directory; it was not changed."
}
if (-not (Test-Path $VenvDir)) {
    & $PythonCommand @PythonArgs -m venv $VenvDir
}

$VenvPython = Join-Path $VenvDir "Scripts/python.exe"
if (-not (Test-Path $VenvPython)) { throw "$VenvDir does not contain a Python executable; it was not changed." }
& $VenvPython -c "import sys; assert sys.version_info[:2] == (3, 11), 'Existing .venv is not Python 3.11'"
if ($LASTEXITCODE -ne 0) { throw "Existing .venv is not a Python 3.11 environment; it was not changed." }
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install --no-cache-dir -e $ProjectDir
& $VenvPython -c "import cv2, mediapipe, numpy, pygame, ultralytics, yaml; print('Runtime imports passed.')"
& $VenvPython -m startup_check

Write-Host ""
Write-Host "Padh Le is installed. Start it with: .\run.ps1"
