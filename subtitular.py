#!/usr/bin/env python3
"""Genera subtítulos en español (.srt / .vtt) a partir de audio o vídeo con Whisper.

Uso:
    python subtitular.py video.mp4                    # crea video.srt
    python subtitular.py video.mp4 --modelo medium    # más preciso, más lento
    python subtitular.py video.mp4 --formato vtt
    python subtitular.py video.mp4 --quemar           # crea video.subtitulado.mp4
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def ts(segundos: float, sep: str = ",") -> str:
    ms = int(round(segundos * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def escribir(segmentos, destino: Path, formato: str) -> None:
    with destino.open("w", encoding="utf-8") as f:
        if formato == "vtt":
            f.write("WEBVTT\n\n")
        i = 0
        for seg in segmentos:
            texto = seg.text.strip()
            if not texto:
                continue
            i += 1
            if formato == "srt":
                f.write(f"{i}\n{ts(seg.start)} --> {ts(seg.end)}\n{texto}\n\n")
            else:
                f.write(f"{ts(seg.start, '.')} --> {ts(seg.end, '.')}\n{texto}\n\n")
            print(f"[{ts(seg.start)}] {texto}", flush=True)


def quemar(video: Path, srt: Path) -> Path:
    salida = video.with_name(f"{video.stem}.subtitulado{video.suffix}")
    ruta = str(srt.resolve()).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-vf", f"subtitles='{ruta}'",
         "-c:a", "copy", str(salida)],
        check=True,
    )
    return salida


def main() -> int:
    p = argparse.ArgumentParser(description="Subtítulos en español con Whisper")
    p.add_argument("entrada", type=Path, help="archivo de audio o vídeo")
    p.add_argument("--modelo", default="small",
                   help="tiny, base, small, medium, large-v3, turbo (por defecto: small)")
    p.add_argument("--formato", choices=["srt", "vtt"], default="srt")
    p.add_argument("--salida", type=Path, help="ruta del archivo de subtítulos")
    p.add_argument("--dispositivo", default="auto", help="auto, cpu o cuda")
    p.add_argument("--detectar-idioma", action="store_true",
                   help="detectar el idioma automáticamente en vez de forzar español")
    p.add_argument("--quemar", action="store_true",
                   help="incrustar los subtítulos en el vídeo con FFmpeg")
    a = p.parse_args()

    if not shutil.which("ffmpeg"):
        print("Error: FFmpeg no está instalado. Ejecuta ./instalar.sh", file=sys.stderr)
        return 1
    if not a.entrada.exists():
        print(f"Error: no existe {a.entrada}", file=sys.stderr)
        return 1

    from faster_whisper import WhisperModel

    compute = "int8" if a.dispositivo in ("cpu", "auto") else "float16"
    print(f"Cargando modelo '{a.modelo}'...", flush=True)
    modelo = WhisperModel(a.modelo, device=a.dispositivo, compute_type=compute)

    segmentos, info = modelo.transcribe(
        str(a.entrada),
        language=None if a.detectar_idioma else "es",
        task="transcribe",
        vad_filter=True,
        beam_size=5,
    )
    print(f"Idioma: {info.language}  Duración: {info.duration:.1f}s", flush=True)

    destino = a.salida or a.entrada.with_suffix(f".{a.formato}")
    escribir(segmentos, destino, a.formato)
    print(f"\nSubtítulos guardados en {destino}")

    if a.quemar:
        srt = destino
        if a.formato != "srt":
            srt = destino.with_suffix(".srt")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(destino), str(srt)], check=True)
        print(f"Vídeo subtitulado: {quemar(a.entrada, srt)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
