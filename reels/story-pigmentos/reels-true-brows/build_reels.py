"""Assemble two Reel versions: [her hook] + [draw-my-life video] + [her True Brows close]."""
import subprocess, os
H = os.path.dirname(os.path.abspath(__file__))
S = os.path.dirname(H)
SRC = f"{H}/c1.mp4"
DRAW = f"{S}/reel_v8_ig.mp4"
WHOOSH = f"{S}/hf/package/dist/skills/media-use/audio/assets/sfx/whoosh-short.mp3"
DRAW_AUDIO = f"{H}/draw_audio.wav"
DRAW_END, DRAW_VO_CUT = 13.45, 12.97
CLOSE = (57.65, 62.90)
HOLD = 0.8
HOOKS = {
    "A": ((6.98, 10.12), r"Este {\c&H6AA8E0&}error{\c&HFFFFFF&} con los pigmentos\Nlo cometen casi\Ntodas las alumnas"),
    "B": ((13.95, 16.55), r"Antes de comprar\Nun pigmento,\N{\c&H6AA8E0&}revisa esto"),
}

HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Big,Montserrat Thin ExtraBold,118,&H00FFFFFF,&H00FFFFFF,&H00101418,&H64000000,0,0,0,0,100,100,0,0,1,6,4,8,50,50,270,1
Style: Mid,Montserrat Thin ExtraBold,100,&H00FFFFFF,&H00FFFFFF,&H00101418,&H64000000,0,0,0,0,100,100,0,0,1,5.5,4,8,50,50,270,1
Style: Pill,Montserrat Thin ExtraBold,150,&H00101418,&H00FFFFFF,&H006AA8E0,&H006AA8E0,0,0,0,0,100,100,6,0,3,22,0,5,0,0,0,1
Style: Hand,Caveat,104,&H00FFFFFF,&H00FFFFFF,&H00101418,&H64000000,-1,0,0,0,100,100,0,0,1,4,3,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
def ts(t): return f"0:{int(t // 60):02d}:{t % 60:05.2f}"

def ass_hook(text, dur, path):
    ev = f"Dialogue: 1,{ts(0)},{ts(dur)},Big,,0,0,0,,{{\\fad(0,120)\\fscx96\\fscy96\\t(0,160,\\fscx100\\fscy100)}}{text}\n"
    open(path, "w").write(HEAD + ev)

def ass_close(path):
    d = CLOSE[1] - CLOSE[0] + HOLD
    ev = ""
    ev += f"Dialogue: 1,{ts(0.08)},{ts(2.85)},Mid,,0,0,0,,{{\\fad(80,80)}}Esto y mucho más\\Nlo enseño en mi curso\\N{{\\c&H6AA8E0&}}TRUE BROWS\n"
    ev += f"Dialogue: 1,{ts(2.87)},{ts(d)},Mid,,0,0,0,,{{\\fad(80,0)}}Comenta\n"
    ev += f"Dialogue: 2,{ts(3.15)},{ts(d)},Pill,,0,0,0,,{{\\pos(540,640)\\fad(60,0)\\fscx40\\fscy40\\t(0,220,\\fscx108\\fscy108)\\t(220,340,\\fscx100\\fscy100)}}GUÍA\n"
    ev += f"Dialogue: 1,{ts(3.9)},{ts(d)},Hand,,0,0,0,,{{\\pos(540,860)\\fad(120,0)}}y te dejo toda la información\n"
    open(path, "w").write(HEAD + ev)

def build(ver):
    (h0, h1), htxt = HOOKS[ver]
    hd = h1 - h0
    ass_hook(htxt, hd, f"{H}/hook{ver}.ass")
    ass_close(f"{H}/close.ass")
    fd = f"{H}/fd"
    face = "scale=1188:2112:flags=lanczos,crop=1080:1920:54:70,eq=contrast=1.04:saturation=1.05:gamma=0.98,unsharp=5:5:0.5,setsar=1,fps=30"
    f = [
        f"[0:v]trim={h0}:{h1},setpts=PTS-STARTPTS,{face},ass={H}/hook{ver}.ass:fontsdir={fd}[v0]",
        f"[0:a]atrim={h0}:{h1},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={hd - 0.04:.2f}:d=0.04,aresample=48000,aformat=channel_layouts=stereo[a0]",
        f"[1:v]trim=0:{DRAW_END},setpts=PTS-STARTPTS,fps=30,setsar=1[v1]",
        f"[3:a]atrim=0:{DRAW_END},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo[a1]",
        f"[0:v]trim={CLOSE[0]}:{CLOSE[1]},setpts=PTS-STARTPTS,{face},tpad=stop_mode=clone:stop_duration={HOLD},ass={H}/close.ass:fontsdir={fd}[v2]",
        f"[0:a]atrim={CLOSE[0]}:{CLOSE[1]},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={CLOSE[1] - CLOSE[0] - 0.06:.2f}:d=0.06,apad=pad_dur={HOLD},aresample=48000,aformat=channel_layouts=stereo[a2]",
        "[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[vc][ac]",
        f"[2:a]adelay={int((hd - 0.12) * 1000)}|{int((hd - 0.12) * 1000)},volume=0.12[w1]",
        f"[2:a]adelay={int((hd + DRAW_END - 0.12) * 1000)}|{int((hd + DRAW_END - 0.12) * 1000)},volume=0.10[w2]",
        "[ac][w1][w2]amix=inputs=3:normalize=0:duration=first,highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[ao]",
        "[vc]format=yuv420p[vo]",
    ]
    out = f"{H}/reel_true_brows_{ver}.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", SRC, "-i", DRAW, "-i", WHOOSH, "-i", DRAW_AUDIO, "-filter_complex", ";".join(f),
                    "-map", "[vo]", "-map", "[ao]", "-c:v", "libx264", "-crf", "18", "-preset", "slow",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], check=True)
    print(ver, out, "hook", round(hd, 2), "total", round(hd + DRAW_END + CLOSE[1] - CLOSE[0] + HOLD, 2))

for v in ("A", "B"):
    build(v)
