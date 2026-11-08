"""Reel v2: split-screen style (b-roll top / speaker bottom), short word captions."""
import subprocess, os, json, re
from PIL import Image
S = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
TOPH = 1010          # height of top b-roll panel (with blended edge)
FADE = 150           # blended edge height

SEG = [
    (0.40, 4.80, 1.00), (4.95, 9.80, 1.12), (10.00, 17.78, 1.00), (17.90, 20.18, 1.12),
    (20.50, 27.12, 1.00), (27.30, 28.50, 1.12), (30.50, 32.04, 1.12), (32.04, 32.80, 1.00),
    (39.20, 40.72, 1.00), (40.90, 44.95, 1.12), (50.10, 55.76, 1.00), (55.78, 58.30, 1.15),
]
outs, acc = [], 0.0
for a, b, z in SEG:
    outs.append(acc); acc += b - a
TOTAL = acc

def m(t, i):
    a, b, _ = SEG[i]
    return outs[i] + min(max(t, a), b) - a

# ---------- captions: 2-3 words, from word timestamps inside kept segments ----------
words = [w for s in json.load(open(f"{S}/tr.json")) for w in s["words"]]
FIX = {"llegue": "llega", "pelopelo": "pelo a pelo"}
kept = []
for i, (a, b, _) in enumerate(SEG):
    for w in words:
        mid = (w["s"] + w["e"]) / 2
        if a <= mid <= b and not (i == 6 and w["s"] < 30.5):
            txt = w["w"].strip()
            core = re.sub(r"[^\wáéíóúñ]", "", txt.lower())
            if core in FIX: txt = txt.lower().replace(core, FIX[core])
            kept.append((m(w["s"], i), m(w["e"], i), txt))
# drop filler: "Y" at sentence starts is fine; remove "ella" (técnica que [ella] me pide) for brevity
chunks, cur = [], []
for k, (s, e, t) in enumerate(kept):
    cur.append((s, e, t))
    nxt_gap = kept[k + 1][0] - e if k + 1 < len(kept) else 9
    n_chars = sum(len(x[2]) for x in cur)
    if len(cur) >= 3 or t[-1] in ".,?!:" or nxt_gap > 0.25 or n_chars > 16:
        chunks.append(cur); cur = []
if cur: chunks.append(cur)
caps = []
for c in chunks:
    s, e = c[0][0], c[-1][1]
    txt = " ".join(x[2] for x in c).rstrip(".,:")
    caps.append([s, e, txt])
for k in range(len(caps) - 1):          # hold each caption until the next one (no flicker)
    if caps[k + 1][0] - caps[k][1] < 0.6:
        caps[k][1] = caps[k + 1][0]

def ts(t):
    t = max(t, 0); return f"0:{int(t//60):02d}:{t%60:05.2f}"

ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Playfair Display,60,&H00FFFFFF,&H00FFFFFF,&H32000000,&H64000000,-1,0,0,0,100,100,0,0,1,2.4,3,5,80,80,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
for s, e, t in caps:
    ass += f"Dialogue: 1,{ts(s)},{ts(e)},Cap,,0,0,0,,{{\\pos(540,935)\\fscx90\\fscy90\\t(0,90,\\fscx100\\fscy100)}}{t}\n"
open(f"{S}/subs2.ass", "w").write(ass)
print("\n".join(f"{s:6.2f}-{e:6.2f} {t}" for s, e, t in caps))

# ---------- visual plan (output seconds) ----------
o = lambda i, t: m(t, i)
HOOK = (0.0, o(0, 2.10), "img/u15.jpg")                    # full-screen hook
SPLIT = [
    (o(0, 2.10), o(0, 4.80), "img/u11.jpg"),   # caso que no he visto
    (o(1, 7.90), o(1, 9.80), "img/u12.jpg"),   # entender el problema (brow mapping)
    (o(2, 10.0), o(2, 12.55), "img/u4.jpg"),   # ¿qué tiene / qué puedo modificar?
    (o(2, 12.55), o(2, 14.20), "img/u17.jpg"), # ¿qué no puedo modificar?
    (o(2, 14.20), o(2, 17.78), "img/u13.jpg"), # resultado realista
    (o(3, 17.90), o(3, 20.18), "img/u14.jpg"), # decido cómo trabajar
    (o(4, 20.50), o(4, 23.30), "img/u6.jpg"),  # ceja pelo a pelo
    (o(4, 23.30), o(4, 27.12), "img/u1.jpg"),  # procedimiento anterior
    (o(7, 32.04), o(8, 40.72), "img/u5.jpg"),  # manchas en sus cejas
    (o(9, 40.90), o(9, 44.95), "img/u16.jpg"), # remover
    (o(10, 52.00), o(10, 55.76), "img/u8.jpg"),# solucionar a largo plazo
]

# blended-edge mask for the top panel
mask = Image.new("L", (W, TOPH), 255)
for y in range(TOPH - FADE, TOPH):
    v = int(255 * (1 - (y - (TOPH - FADE)) / FADE) ** 1.4)
    for x in range(W): mask.putpixel((x, y), v)
mask.save(f"{S}/mask_top.png")

f, inputs = [], ["-i", f"{S}/in.mp4", "-loop", "1", "-i", f"{S}/mask_top.png"]
n = len(SEG)
for i, (a, b, z) in enumerate(SEG):
    sw, sh = int(W * z) // 2 * 2, int(H * z) // 2 * 2
    f.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,scale={sw}:{sh}:flags=lanczos,"
             f"crop={W}:{H}:(iw-{W})/2:(ih-{H})*0.35,setsar=1,fps=30[v{i}]")
    d = b - a
    f.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={d-0.03:.3f}:d=0.03[a{i}]")
f.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac]")
f.append("[vc]eq=contrast=1.05:saturation=1.08,colorbalance=rs=0.02:bs=-0.02,split[full][sp]")
# speaker for split view: face+chest band placed in bottom half
f.append(f"[sp]scale={int(W*1.2)}:{int(H*1.2)},crop={W}:{H-TOPH+FADE}:{int(W*0.1)}:600,pad={W}:{H}:0:{TOPH-FADE}:black[spk]")

cur = "spk"
def panel(img, j):
    im = Image.open(f"{S}/{img}").convert("RGB")
    r = max(W / im.width, TOPH / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - TOPH) // 2
    im = im.crop((x, y, x + W, y + TOPH)).convert("RGBA")
    im.putalpha(mask)
    path = f"{S}/panel_{j}.png"; im.save(path); return path
for j, (a, b, img) in enumerate(SPLIT):
    idx = 2 + j
    inputs += ["-loop", "1", "-t", f"{b - a + 0.1:.2f}", "-i", panel(img, j)]
    f.append(f"[{idx}:v]fps=30,format=rgba,setpts=PTS-STARTPTS+{a:.3f}/TB[tp{j}]")
    f.append(f"[{cur}][tp{j}]overlay=0:0:eof_action=pass:format=auto:enable='between(t,{a:.3f},{b:.3f})'[c{j}]")
    cur = f"c{j}"
union = "+".join(f"between(t,{a:.3f},{b-0.001:.3f})" for a, b, _ in SPLIT)
f.append(f"[full][{cur}]overlay=0:0:enable='{union}'[mix]")

# full-screen hook image
hi = 2 + len(SPLIT)
ha, hb, himg = HOOK
inputs += ["-loop", "1", "-t", f"{hb-ha+0.1:.2f}", "-i", f"{S}/{himg}"]
f.append(f"[{hi}:v]fps=30,scale={int(W*1.2)}:{int(H*1.2)}:force_original_aspect_ratio=increase,crop={int(W*1.2)}:{int(H*1.2)},"
         f"zoompan=z='1.12-0.10*on/{(hb-ha)*30:.0f}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps=30,"
         f"eq=contrast=1.05:saturation=1.05,setpts=PTS-STARTPTS+{ha:.3f}/TB[hk]")
f.append(f"[mix][hk]overlay=0:0:eof_action=pass:enable='between(t,{ha:.3f},{hb:.3f})',"
         f"ass={S}/subs2.ass:fontsdir={S}/fd2,format=yuv420p[vout]")
f.append("[ac]loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[aout]")

open(f"{S}/graph2.txt", "w").write(";\n".join(f))
out = f"{S}/reel_v2.mp4"
cmd = ["ffmpeg", "-y", "-v", "error"] + inputs + ["-filter_complex_script", f"{S}/graph2.txt",
       "-map", "[vout]", "-map", "[aout]", "-t", f"{TOTAL:.2f}",
       "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
print(f"total {TOTAL:.2f}s")
subprocess.run(cmd, check=True)
