# Subtítulos en español con FFmpeg + Whisper

Genera subtítulos `.srt`/`.vtt` en español a partir de cualquier audio o vídeo
usando [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (Whisper de
OpenAI optimizado; funciona bien en CPU) y FFmpeg.

## Instalación

Instala FFmpeg, faster-whisper, [yt-dlp](https://github.com/yt-dlp/yt-dlp) y
[HyperFrames](https://github.com/heygen-com/hyperframes) (HTML → vídeo, requiere Node.js 22+).

```bash
./instalar.sh                                               # Linux / macOS
powershell -ExecutionPolicy Bypass -File .\instalar.ps1     # Windows
```

### Descargar un vídeo y subtitularlo

```bash
python3 -m yt_dlp -f mp4 -o video.mp4 "URL"
python3 subtitular.py video.mp4 --quemar
```

## Uso

```bash
python3 subtitular.py video.mp4                  # crea video.srt
python3 subtitular.py video.mp4 --formato vtt    # crea video.vtt
python3 subtitular.py video.mp4 --quemar         # además crea video.subtitulado.mp4
python3 subtitular.py audio.mp3 --modelo medium  # más precisión
```

| Opción | Descripción |
|---|---|
| `--modelo` | `tiny`, `base`, `small` (por defecto), `medium`, `large-v3`, `turbo` |
| `--formato` | `srt` (por defecto) o `vtt` |
| `--salida` | ruta del archivo de subtítulos |
| `--dispositivo` | `auto`, `cpu` o `cuda` |
| `--detectar-idioma` | no forzar español; detectar el idioma automáticamente |
| `--quemar` | incrustar los subtítulos en el vídeo con FFmpeg |

El modelo se descarga la primera vez (~460 MB para `small`) y queda en caché en
`~/.cache/huggingface`. Se usa un filtro VAD para saltar los silencios.

### Añadir subtítulos como pista (sin recodificar)

```bash
ffmpeg -i video.mp4 -i video.srt -c copy -c:s mov_text -metadata:s:s:0 language=spa video.con_subs.mp4
```
