#!/usr/bin/env bash
# Instala FFmpeg, faster-whisper (subtítulos), yt-dlp y HyperFrames (heygen-com/hyperframes).
# Linux (apt/dnf/pacman) y macOS (Homebrew). En Windows usa instalar.ps1.
set -euo pipefail
cd "$(dirname "$0")"

OS="$(uname -s)"
SUDO=""
if [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null; then SUDO="sudo"; fi

instalar_pkg() {  # instalar_pkg <apt> <dnf> <pacman> <brew>
  if [ "$OS" = Darwin ]; then
    command -v brew >/dev/null || { echo "Instala Homebrew primero: https://brew.sh"; exit 1; }
    brew install "$4"
  elif command -v apt-get >/dev/null; then $SUDO apt-get update -qq && $SUDO apt-get install -y "$1"
  elif command -v dnf >/dev/null; then $SUDO dnf install -y "$2"
  elif command -v pacman >/dev/null; then $SUDO pacman -S --noconfirm "$3"
  else echo "Gestor de paquetes no soportado; instala $1 a mano."; exit 1; fi
}

echo "== FFmpeg =="
command -v ffmpeg >/dev/null || instalar_pkg ffmpeg ffmpeg ffmpeg ffmpeg
ffmpeg -version | head -1

echo "== Python: faster-whisper + yt-dlp =="
command -v python3 >/dev/null || instalar_pkg python3-pip python3-pip python-pip python
python3 -m pip install --user -U -r requirements.txt yt-dlp \
  || python3 -m pip install --user --break-system-packages -U -r requirements.txt yt-dlp
python3 -m yt_dlp --version

echo "== Node.js 22+ (necesario para HyperFrames) =="
NODE_MAJOR=0
if command -v node >/dev/null; then NODE_MAJOR=$(node -v | sed -E 's/^v([0-9]+).*/\1/'); fi
if [ "$NODE_MAJOR" -lt 22 ]; then
  if [ "$OS" = Darwin ]; then
    brew install node
  else
    echo "HyperFrames necesita Node.js 22 o superior (tienes: ${NODE_MAJOR})."
    echo "Instálalo desde https://nodejs.org (o con nvm: 'nvm install 22') y vuelve a ejecutar este script."
    exit 1
  fi
fi
node -v

echo "== HyperFrames =="
npm install -g hyperframes || $SUDO npm install -g hyperframes
hyperframes --version || true

echo
echo "Listo:"
echo "  python3 subtitular.py video.mp4     # subtítulos en español"
echo "  python3 -m yt_dlp URL               # descargar un vídeo"
echo "  hyperframes init mi-video           # nuevo proyecto HTML -> vídeo"
