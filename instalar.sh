#!/usr/bin/env bash
# Instala FFmpeg y faster-whisper.
set -euo pipefail

if ! command -v ffmpeg >/dev/null; then
  echo "Instalando FFmpeg..."
  case "$(uname -s)" in
    Linux)
      if command -v apt-get >/dev/null; then sudo apt-get update && sudo apt-get install -y ffmpeg
      elif command -v dnf >/dev/null; then sudo dnf install -y ffmpeg
      elif command -v pacman >/dev/null; then sudo pacman -S --noconfirm ffmpeg
      else echo "Instala FFmpeg manualmente: https://ffmpeg.org/download.html"; exit 1; fi ;;
    Darwin) brew install ffmpeg ;;
    *) echo "En Windows: winget install Gyan.FFmpeg"; exit 1 ;;
  esac
fi
ffmpeg -version | head -1

python3 -m pip install -r requirements.txt
echo "Listo. Prueba: python3 subtitular.py tu_video.mp4"
