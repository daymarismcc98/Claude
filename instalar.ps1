# Instala FFmpeg, Python, faster-whisper, yt-dlp, Node.js 22+ y HyperFrames en Windows.
# Ejecutar en PowerShell:  powershell -ExecutionPolicy Bypass -File .\instalar.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Instalar($id) {
    winget install --id $id -e --accept-source-agreements --accept-package-agreements
}
function Refrescar {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { Instalar "Gyan.FFmpeg" }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { Instalar "Python.Python.3.12" }
$nodeMajor = 0
if (Get-Command node -ErrorAction SilentlyContinue) { $nodeMajor = [int]((node -v) -replace '^v(\d+).*', '$1') }
if ($nodeMajor -lt 22) { Instalar "OpenJS.NodeJS.LTS" }
Refrescar

python -m pip install -U -r requirements.txt yt-dlp
npm install -g hyperframes

ffmpeg -version | Select-Object -First 1
python -m yt_dlp --version
node -v
hyperframes --version
Write-Host "`nListo. Prueba: python subtitular.py video.mp4"
