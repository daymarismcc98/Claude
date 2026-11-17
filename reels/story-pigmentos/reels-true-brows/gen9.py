"""Faceless hook + close scenes in the same draw-my-life system (reuses gen7's helpers, hand and sound).
Builds three HyperFrames projects: reel9_hookA, reel9_hookB, reel9_close, each with the trainer's own voice."""
import os, re, shutil, subprocess, sys
S = os.path.dirname(os.path.abspath(__file__))
SRC = open(f"{S}/gen7.py").read()
HEAD = SRC.split("# ================= S1")[0].replace('transformOrigin:"{cx}px {cy}px"', 'svgOrigin:"{cx} {cy}"')
TAIL = SRC.split("# ---------- camera pans across the whiteboard ----------")[1]
TAIL = "# ---------- camera ----------" + TAIL
TAIL = TAIL.replace("volume=volume=1.0*(", "volume=volume=0.35*(").replace("for k in range(4):", "for k in range(len(SCENE_X)):")

EXTRA_HELPERS = r'''
RED = "#C8463D"
def tf(d, s, dx, dy):
    """scale + translate an M/L/C/c/Z path"""
    out, toks, cmd, i = [], re.findall(r"[MLCcZ]|-?\d+\.?\d*", d), None, 0
    while i < len(toks):
        t = toks[i]
        if t in "MLCcZ":
            cmd = t; out.append(t); i += 1; continue
        if cmd == "c":
            out += [f"{float(toks[i + k]) * s:.1f}" for k in range(6)]; i += 6
        else:
            n = 6 if cmd == "C" else 2
            for k in range(0, n, 2):
                out += [f"{float(toks[i + k]) * s + dx:.1f}", f"{float(toks[i + k + 1]) * s + dy:.1f}"]
            i += n
    return " ".join(out)

def stamp(sc, text, x, y, size, t0, color=RED, rot=-6, w=900):
    """big word that lands like a rubber stamp (no hand)"""
    i = nid("sp")
    html[sc].append(f'<div class="hw" id="{i}" style="left:{x}px;top:{y}px;font-size:{size}px;width:{w}px;color:{color}">{text}</div>')
    tl.append(f'tl.fromTo("#{i}",{{scale:2.4,opacity:0,rotation:{rot - 8}}},{{scale:1,opacity:1,rotation:{rot},duration:0.22,ease:"power4.in"}},{t0:.3f});')
    for k, (sx, sy) in enumerate([(-14, 8), (12, -6), (-8, 5), (0, 0)]):
        tl.append(f'tl.to("#world",{{x:{sx},y:{sy},duration:0.04,ease:"none"}},{t0 + 0.22 + k * 0.04:.3f});')
    extra_audio.append((t0 + 0.18, "pop", 0.10))

def BOTTLE_SMALL(dx, dy, s=0.32):
    return [tf(d, s, dx, dy) for d in (
        "M500 640 C500 600 580 600 580 640 L580 720 L500 720 Z", "M478 720 L602 721 L601 790 L479 789 Z",
        "M500 790 L500 830 C440 850 400 900 400 960 L401 1380 C401 1405 420 1421 445 1420 L635 1421 C660 1421 680 1405 679 1380 L680 960 C680 900 640 850 580 830 L580 790")]
'''


SCENES = {
"hookA": (r'''
# ===== HOOK A · "Este error con los pigmentos lo cometen casi todas las alumnas" =====
tri = nid("tri")
svg[0].append(f'<g id="{tri}"><path d="M540 250 L700 520 L380 520 Z" fill="rgba(200,70,61,.10)" stroke="{RED}" stroke-width="14" stroke-linejoin="round"/>'
              f'<path d="M540 335 L540 435" stroke="{RED}" stroke-width="16" stroke-linecap="round"/><circle cx="540" cy="478" r="11" fill="{RED}"/></g>')
tl.append(f'tl.fromTo("#{tri}",{{scale:1.35,rotation:-8,svgOrigin:"540 400"}},{{scale:1,rotation:0,duration:0.3,ease:"back.out(3)"}},0);')
stamp(0, "¡ERROR!", 90, 540, 210, 0.28)
write(0, "con los pigmentos", 90, 800, 104, 0.62, 0.62)
for k, cx in enumerate((300, 470, 640)):
    for j, d in enumerate(BOTTLE_SMALL(cx - 160, 780)):
        stroke(0, d, 1.28 + k * 0.17 + j * 0.05, 0.12 if j < 2 else 0.2, w=6, hand=(j == 2))
    stroke(0, zigzag(cx - 30, cx + 52, 1090, 1225, 12), 1.5 + k * 0.17, 0.12, w=8, color="rgba(185,130,79,.85)", ease="none", hand=False)
write(0, "lo cometen casi", 90, 1290, 92, 1.86, 0.42)
write(0, "TODAS las alumnas", 60, 1390, 128, 2.3, 0.5, w=960)
stroke(0, "M120 1560 C320 1600 700 1590 960 1545", 2.82, 0.22, w=10, color=RED)
pop_star(0, 930, 640, 28, 0.55, RED); pop_star(0, 150, 700, 20, 0.62, CARAMEL)
''', (6.98, 10.12)),

"hookB": (r'''
# ===== HOOK B · "Antes de comprar un pigmento, revisa esto" =====
stop = nid("stop")
oct = " ".join(f"{540 + 150 * math.cos(math.pi / 8 + k * math.pi / 4):.0f} {420 + 150 * math.sin(math.pi / 8 + k * math.pi / 4):.0f}" for k in range(8))
svg[0].append(f'<g id="{stop}"><path d="M{oct} Z" fill="{RED}" stroke="{INK}" stroke-width="6"/></g>')
html[0].append('<div class="hw" id="stopw" style="left:90px;top:345px;width:900px;font-size:120px;color:#fff">ALTO</div>')
tl.append(f'tl.fromTo("#{stop}",{{scale:1.25,svgOrigin:"540 420"}},{{scale:1,duration:0.3,ease:"back.out(3)"}},0);')
tl.append('tl.fromTo("#stopw",{scale:1.25,transformOrigin:"50% 50%"},{scale:1,duration:0.3,ease:"back.out(3)"},0);')
write(0, "Antes de comprar", 90, 620, 116, 0.14, 0.55)
write(0, "un pigmento…", 90, 740, 116, 0.7, 0.45)
stroke(0, "M380 960 L700 960 L740 1270 L340 1270 Z", 1.05, 0.25)
stroke(0, "M450 960 C450 890 630 890 630 960", 1.3, 0.12)
for j, d in enumerate(BOTTLE_SMALL(395, 720, 0.25)):
    stroke(0, d, 1.25 + j * 0.03, 0.1, w=6, hand=False)
write(0, "revisa ESTO", 90, 1290, 140, 1.42, 0.45)
stroke(0, "M540 1470 L540 1570 M490 1525 L540 1575 L590 1525", 1.95, 0.25, w=12, color=RED)
pop_star(0, 860, 960, 26, 1.1, CARAMEL); pop_star(0, 220, 1050, 20, 1.2, SAND)
''', (13.95, 16.55)),

"close": (r'''
# ===== CLOSE · "Esto y mucho más lo enseño en mi curso True Brows. Comenta guía y te dejo toda la información" =====
write(0, "Esto y mucho más", 90, 210, 84, 0.12, 0.5)
write(0, "lo enseño en mi curso", 90, 305, 84, 0.66, 0.6)
brow = "M260 640 C330 560 470 520 640 535 C720 542 790 565 830 600 C760 585 690 580 620 585 C480 595 360 630 260 640 Z"
stroke(0, brow, 1.3, 0.35, w=6)
for k in range(13):
    x = 290 + k * 42; y = 625 - 30 * math.sin(k / 12 * math.pi) - k * 2
    stroke(0, f"M{x} {y + 8} C{x + 8} {y - 20} {x + 22} {y - 45} {x + 40} {y - 62}", 1.55 + k * 0.025, 0.12, w=4, color=CARAMEL, hand=False)
write(0, "TRUE BROWS", 60, 690, 170, 1.95, 0.6, w=960, hl=True)
pop_star(0, 150, 720, 30, 2.6); pop_star(0, 935, 690, 24, 2.68, SAND); pop_star(0, 900, 880, 18, 2.75)
write(0, "Comenta", 90, 925, 96, 2.82, 0.36)
stroke(0, "M300 1090 C300 1060 320 1050 350 1050 L730 1050 C760 1050 780 1060 780 1090 L780 1250 C780 1280 760 1290 730 1290 L470 1290 L400 1360 L410 1290 L350 1290 C320 1290 300 1280 300 1250 Z", 3.2, 0.3, w=8)
write(0, "GUÍA", 90, 1080, 170, 3.34, 0.36)
stroke(0, "M870 1130 L870 1300 M830 1260 L870 1305 L910 1260", 3.75, 0.2, w=10, color=RED)
write(0, "y te dejo toda la información", 60, 1390, 78, 3.95, 0.7, w=960)
stroke(0, "M90 1520 C80 1470 140 1450 160 1495 C180 1450 240 1470 230 1520 C220 1560 160 1590 160 1600 C160 1590 100 1560 90 1520 Z", 4.7, 0.25, w=6, color=RED, hand=False)
pop_star(0, 960, 1530, 26, 4.75)
''', (57.65, 62.90)),
}

def make(name):
    code, (a, b) = SCENES[name]
    T = round(b - a + (0.8 if name == "close" else 0), 2)
    P = f"{S}/reel9_{name}"
    if os.path.exists(P): shutil.rmtree(P)
    subprocess.run(["npx", "-y", "hyperframes@0.9.25", "init", P, "--skip-skills"], check=True, capture_output=True)
    for sub in ("fonts", "img", "sfx", "vo"): os.makedirs(f"{P}/assets/{sub}", exist_ok=True)
    for f in os.listdir(f"{S}/reel7/assets/fonts"): shutil.copy(f"{S}/reel7/assets/fonts/{f}", f"{P}/assets/fonts/")
    shutil.copy(f"{S}/reel7/assets/img/hand.png", f"{P}/assets/img/")
    for f in ("pop.mp3", "sparkle.mp3", "whoosh-short.mp3"): shutil.copy(f"{S}/reel7/assets/sfx/{f}", f"{P}/assets/sfx/")
    hold = 0.8 if name == "close" else 0
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{S}/hooks/c1.mp4", "-vn", "-af",
                    f"atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={b - a - 0.05:.2f}:d=0.05,apad=pad_dur={hold + 0.1},"
                    "highpass=f=80,afftdn=nf=-28,loudnorm=I=-15:TP=-1.5,aresample=48000", "-ac", "2", "-t", f"{T}", f"{P}/assets/vo/vo.wav"], check=True)
    head = HEAD.replace('P = f"{S}/reel7"', f'P = "{P}"').replace("W, H, T = 1080, 1920, 15.0", f"W, H, T = 1080, 1920, {T}")
    head = head.replace("SCENE_X = [0, 1080, 2160, 3240]", "SCENE_X = [0]").replace("PANS = [(3.3, 1), (7.9, 2), (10.85, 3)]", "PANS = []")
    head = head.replace("{k: [] for k in range(4)}", "{k: [] for k in range(1)}")
    full = head + EXTRA_HELPERS + code + TAIL
    ns = {"__file__": f"{S}/gen7.py"}
    exec(compile(full, f"gen9_{name}", "exec"), ns)
    print(name, "T", T)

for n in (sys.argv[1:] or SCENES):
    make(n)
