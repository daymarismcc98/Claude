"""Story 15 s, draw-my-life style with a real hand that draws every stroke and writes every line.
Palette: white paper, black ink, sand + caramel accents. Voice: Latin American (Mexico) female, Piper es_MX-claude-high."""
import os, re, math, subprocess
from PIL import ImageFont, Image
S = os.path.dirname(os.path.abspath(__file__))
P = f"{S}/reel7"
W, H, T = 1080, 1920, 15.0
SCENE_X = [0, 1080, 2160, 3240]
PANS = [(3.3, 1), (7.9, 2), (10.85, 3)]
HAND_H_NEW = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reel7/assets/img/hand.png')).size[1]
HAND_W, HAND_H, TIP = 1464, HAND_H_NEW, (209, 591)
CARAMEL, SAND, INK = "#B9824F", "#D9C3A0", "#111"
FONT = {700: ImageFont.truetype(f"{S}/fonts/caveat-700.ttf", 100), 500: ImageFont.truetype(f"{S}/fonts/caveat-500.ttf", 100)}

tl, svg, html, segs, extra_audio = [], {k: [] for k in range(4)}, {k: [] for k in range(4)}, [], []
uid = [0]
def nid(p): uid[0] += 1; return f"{p}{uid[0]}"

# ---------- path sampling (M L C c Z) for the hand ----------
def parse(d):
    toks = re.findall(r"[MLCcZ]|-?\d+\.?\d*", d)
    pts, cur, start, i, cmd = [], (0, 0), (0, 0), 0, None
    polys = []
    while i < len(toks):
        if toks[i] in "MLCcZ": cmd = toks[i]; i += 1
        if cmd == "Z":
            polys[-1].append(start); cur = start; continue
        if cmd == "M":
            cur = (float(toks[i]), float(toks[i + 1])); start = cur; polys.append([cur]); i += 2; cmd = "L"
        elif cmd == "L":
            cur = (float(toks[i]), float(toks[i + 1])); polys[-1].append(cur); i += 2
        elif cmd in "Cc":
            v = [float(x) for x in toks[i:i + 6]]; i += 6
            if cmd == "c": v = [v[0] + cur[0], v[1] + cur[1], v[2] + cur[0], v[3] + cur[1], v[4] + cur[0], v[5] + cur[1]]
            p0 = cur
            for k in range(1, 13):
                t = k / 12
                x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * v[0] + 3 * (1 - t) * t * t * v[2] + t ** 3 * v[4]
                y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * v[1] + 3 * (1 - t) * t * t * v[3] + t ** 3 * v[5]
                polys[-1].append((x, y))
            cur = (v[4], v[5])
    pts = [p for poly in polys for p in poly]
    return pts

def along(pts, f):
    L = [0]
    for a, b in zip(pts, pts[1:]): L.append(L[-1] + math.dist(a, b))
    tgt = f * L[-1]
    for k in range(1, len(L)):
        if L[k] >= tgt:
            u = (tgt - L[k - 1]) / max(L[k] - L[k - 1], 1e-6)
            return (pts[k - 1][0] + u * (pts[k][0] - pts[k - 1][0]), pts[k - 1][1] + u * (pts[k][1] - pts[k - 1][1]))
    return pts[-1]

def ease_io(u): return 2 * u * u if u < 0.5 else 1 - (-2 * u + 2) ** 2 / 2

# ---------- drawing primitives ----------
def stroke(sc, d, t0, dur, w=7, color=INK, hand=True, ease="power1.inOut", fill=None, clip=None):
    i = nid("d")
    svg[sc].append(f'<path id="{i}" d="{d}" pathLength="1" fill="none" stroke="{color}" stroke-width="{w}" '
                   f'stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1 1"' + (f' clip-path="url(#{clip})"' if clip else '') + '/>')
    tl.append(f'tl.fromTo("#{i}",{{strokeDashoffset:1}},{{strokeDashoffset:0,duration:{dur},ease:"{ease}"}},{t0:.3f});')
    if hand:
        pts = [(x + SCENE_X[sc], y) for x, y in parse(d)]
        e = ease_io if ease == "power1.inOut" else (lambda u: u)
        segs.append((t0, dur, lambda f, pts=pts, e=e: along(pts, e(f))))
    return i

def write(sc, text, x, y, size, t0, dur, w=900, cls="hw", hl=None, weight=700, hand=True):
    left = "left" in cls
    i = nid("w")
    if hl:
        hid = nid("h")
        tw = FONT[weight].getlength(text) * size / 100
        hx = x + (w - tw) / 2 - 14
        html[sc].append(f'<div class="hl" id="{hid}" style="left:{hx:.0f}px;top:{y + size * 0.62:.0f}px;width:{tw + 28:.0f}px;height:{size * 0.42:.0f}px"></div>')
        tl.append(f'tl.fromTo("#{hid}",{{scaleX:0}},{{scaleX:1,duration:{dur:.2f},ease:"none"}},{t0:.3f});')
    html[sc].append(f'<div class="{cls}" id="{i}" style="left:{x}px;top:{y}px;font-size:{size}px;width:{w}px">{text}</div>')
    tl.append(f'tl.fromTo("#{i}",{{clipPath:"inset(-25% 100% -25% -3%)"}},{{clipPath:"inset(-25% -3% -25% -3%)",duration:{dur},ease:"none"}},{t0:.3f});')
    if hand:
        tw = FONT[weight].getlength(text) * size / 100
        x0 = (x if left else x + (w - tw) / 2) + SCENE_X[sc]
        yb = y + size * 0.78
        segs.append((t0, dur, lambda f, x0=x0, tw=tw, yb=yb: (x0 + f * tw, yb - 18 * abs(math.sin(f * tw / 22)))))
    return i

def zigzag(x0, x1, ytop, ybot, step):
    d, x, up = f"M{x0} {ybot}", x0, True
    while x < x1:
        x = min(x + step, x1); d += f" L{x} {ytop if up else ybot}"; up = not up
    return d

def star(cx, cy, r):
    p = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.42
        p.append(f"{cx + rr * math.cos(a):.1f} {cy + rr * math.sin(a):.1f}")
    return "M" + " L".join(p) + " Z"

def pop_star(sc, cx, cy, r, t0, color=CARAMEL):
    i = nid("st")
    svg[sc].append(f'<path id="{i}" d="{star(cx, cy, r)}" fill="{color}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>')
    tl.append(f'tl.fromTo("#{i}",{{scale:0,opacity:0,transformOrigin:"{cx}px {cy}px",rotation:-25}},{{scale:1,opacity:1,rotation:0,duration:0.35,ease:"back.out(2.4)"}},{t0:.3f});')

BOTTLE = ("M500 640 C500 600 580 600 580 640 L580 720 L500 720 Z",
          "M478 720 L602 721 L601 790 L479 789 Z",
          "M500 790 L500 830 C440 850 400 900 400 960 L401 1380 C401 1405 420 1421 445 1420 L635 1421 C660 1421 680 1405 679 1380 L680 960 C680 900 640 850 580 830 L580 790",
          "M425 1040 L655 1043 L653 1300 L423 1297 Z")

# ================= S1 · gancho (0 – 3.3) =================
write(0, "Que te lo recomienden…", 90, 250, 96, 0.0, 0.7)
t = 0.75
for k, d in enumerate(BOTTLE):
    stroke(0, d, t, [0.14, 0.12, 0.3, 0.14][k]); t += [0.14, 0.12, 0.3, 0.14][k]
svg[0].append('<clipPath id="cl_body"><path d="M402 1000 L678 1000 L679 1380 C679 1405 660 1421 635 1421 L445 1420 C420 1421 401 1405 401 1380 Z M425 1040 L425 1297 L653 1300 L655 1043 Z" clip-rule="evenodd"/></clipPath>')
stroke(0, zigzag(405, 680, 1000, 1425, 18), 1.47, 0.3, w=13, color="rgba(185,130,79,.85)", ease="none", clip="cl_body")   # liquid colouring
stroke(0, "M440 1110 C480 1104 560 1112 640 1106 M440 1170 C500 1166 540 1172 600 1168", 1.47, 0.25, w=5, hand=False)
stroke(0, "M700 640 C700 590 760 560 860 560 C960 560 1020 590 1020 640 C1020 672 1000 696 968 708 L1045 768 L925 718 C905 720 882 722 860 722 C760 722 700 690 700 640 Z", 1.8, 0.3, w=6)
write(0, "¡Es buenísimo!", 715, 600, 56, 2.1, 0.32, w=290, weight=700)
pop_star(0, 1000, 520, 26, 2.3); pop_star(0, 690, 560, 18, 2.4, SAND)
write(0, "¡no es suficiente!", 90, 360, 120, 2.45, 0.6, cls="hw big", hl=True)
stroke(0, "M190 880 C185 800 305 795 302 865 C300 915 246 918 246 985", 3.0, 0.22, w=13, color=CARAMEL)
q = nid("q"); svg[0].append(f'<circle id="{q}" cx="246" cy="1040" r="12" fill="{CARAMEL}"/>')
tl.append(f'tl.fromTo("#{q}",{{scale:0,transformOrigin:"246px 1040px"}},{{scale:1,duration:0.2,ease:"back.out(3)"}},3.2);')

# ================= S2 · la etiqueta (3.3 – 7.9) =================
write(1, "01 · LA ETIQUETA", 90, 245, 40, 3.45, 0.2, cls="kick", hand=False)
write(1, "¿Qué contiene y", 90, 295, 92, 3.5, 0.42)
write(1, "para qué está indicado?", 90, 390, 92, 3.92, 0.45)
stroke(1, "M420 590 L420 530 L660 530 L660 590", 4.37, 0.12)
stroke(1, "M200 640 C200 605 240 590 300 590 L780 590 C840 590 880 605 880 640 L880 1130 C880 1160 860 1180 830 1180 L250 1180 C220 1180 200 1160 200 1130 Z", 4.49, 0.22)
stroke(1, "M250 720 L830 723 L828 1080 L252 1077 Z", 4.6, 0.15, w=6, hand=False)
for k in range(5):
    y = 780 + k * 66; n = [9, 6, 8, 5, 9][k]
    stroke(1, f"M300 {y} " + " ".join("c18 -12 36 12 54 0" for _ in range(n)), 4.62 + k * 0.05, 0.22, w=4, color="#8C8478", hand=False)
mg = nid("mg")
svg[1].append(f'<g id="{mg}"><circle cx="0" cy="0" r="92" fill="rgba(217,195,160,.45)" stroke="{INK}" stroke-width="8"/>'
              f'<path d="M66 66 L150 150" stroke="{INK}" stroke-width="16" stroke-linecap="round"/></g>')
tl.append(f'tl.set("#{mg}",{{x:330,y:850,scale:0,transformOrigin:"0px 0px"}},0);')
tl.append(f'tl.to("#{mg}",{{scale:1,duration:0.3,ease:"back.out(2)"}},5.05);')
tl.append(f'tl.to("#{mg}",{{x:720,y:1010,duration:2.5,ease:"sine.inOut"}},5.2);')
for k, (tt, label) in enumerate([(4.79, "Composición"), (5.83, "Formulación"), (6.65, "Técnicas indicadas")]):
    y = 1260 + k * 100
    stroke(1, f"M250 {y} L302 {y + 2} L300 {y + 54} L248 {y + 52} Z", tt - 0.12, 0.14, w=5)
    write(1, label, 340, y - 22, 78, tt + 0.02, 0.4, w=640, cls="hw left")
    stroke(1, f"M258 {y + 26} L276 {y + 46} L318 {y - 8}", tt + 0.44, 0.14, w=10, color=CARAMEL)
    extra_audio.append((tt + 0.5, "pop", 0.14))
pop_star(1, 960, 1290, 24, 7.25); pop_star(1, 1000, 1400, 16, 7.35, SAND)

# ================= S3 · el origen (7.9 – 10.85) =================
write(2, "02 · EL ORIGEN", 90, 245, 40, 8.05, 0.2, cls="kick", hand=False)
write(2, "¿Puedes rastrearlo?", 90, 295, 100, 8.1, 0.4)
small = [f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="12" stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="1 1" id="sb{k}"/>' for k, d in enumerate(BOTTLE)]
svg[2].append('<g transform="translate(-10 470) scale(0.48)">' + "".join(small) +
              f'<path id="sbf" d="{zigzag(412, 668, 1000, 1395, 30)}" fill="none" stroke="{CARAMEL}" stroke-width="30" stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="1 1"/></g>')
for k in range(4): tl.append(f'tl.fromTo("#sb{k}",{{strokeDashoffset:1}},{{strokeDashoffset:0,duration:0.25}},{8.1 + k * 0.05:.2f});')
tl.append('tl.fromTo("#sbf",{strokeDashoffset:1},{strokeDashoffset:0,duration:0.3,ease:"none"},8.3);')
# station 1 · lote (tag)
stroke(2, "M330 960 C400 900 420 760 470 735", 8.5, 0.12, w=4)
stroke(2, "M480 700 L620 700 L660 735 L620 770 L480 770 Z", 8.62, 0.18, w=6)
stroke(2, zigzag(522, 615, 708, 762, 14), 8.8, 0.12, w=8, color=SAND, ease="none", hand=False)
write(2, "Lote", 690, 682, 78, 8.75, 0.2, w=380, cls="hw left")
stroke(2, "M840 752 L1010 754", 8.95, 0.1, w=4, color="#8C8478")
# station 2 · vencimiento (calendar)
stroke(2, "M330 1010 C400 1000 430 980 470 975", 9.07, 0.08, w=4)
stroke(2, "M480 920 L640 921 L640 1030 L480 1029 Z M480 952 L640 953", 9.13, 0.18, w=6)
stroke(2, "M515 900 L515 935 M605 900 L605 935", 9.31, 0.07, w=7, hand=False)
stroke(2, zigzag(488, 632, 960, 1022, 16), 9.33, 0.14, w=8, color=SAND, ease="none", hand=False)
write(2, "Vencimiento", 690, 922, 78, 9.33, 0.42, w=380, cls="hw left")
# station 3 · fabricante (factory)
stroke(2, "M330 1060 C410 1110 430 1200 470 1215", 9.85, 0.1, w=4)
stroke(2, "M480 1290 L480 1190 L530 1220 L530 1190 L580 1220 L580 1190 L630 1220 L630 1290 Z", 9.95, 0.2, w=6)
stroke(2, "M600 1205 L600 1150 L620 1150 L620 1210", 10.15, 0.08, w=6, hand=False)
stroke(2, "M612 1138 C598 1118 628 1102 614 1080 C602 1062 626 1048 620 1030", 10.15, 0.2, w=5, color=CARAMEL, hand=False)
write(2, "Fabricante", 690, 1182, 78, 10.15, 0.35, w=380, cls="hw left")
write(2, "= trazabilidad", 90, 1385, 100, 10.38, 0.4, cls="hw big", hl=True, hand=False)

# ================= S4 · reflexión (10.85 – 15) =================
write(3, "Un pigmento no se elige", 90, 245, 88, 11.1, 0.55)
write(3, "por recomendación.", 90, 345, 88, 11.65, 0.45)
stroke(3, "M470 1120 C420 1080 400 1030 400 980 C400 900 465 840 540 840 C615 840 680 900 680 980 C680 1030 660 1080 610 1120 L610 1180 L470 1180 Z", 12.12, 0.35)
stroke(3, "M480 1205 L600 1205 M495 1232 L585 1232", 12.47, 0.12, w=7)
stroke(3, "M500 1100 L500 1040 L520 1000 L540 1050 L560 1000 L580 1040 L580 1100", 12.6, 0.15, w=6, color=CARAMEL)
write(3, "Se elige por información.", 60, 455, 104, 12.78, 0.62, w=960, hl=True)
svg[3].append('<clipPath id="cl_b4"><path d="M470 1120 C420 1080 400 1030 400 980 C400 900 465 840 540 840 C615 840 680 900 680 980 C680 1030 660 1080 610 1120 L610 1180 L470 1180 Z"/></clipPath>')
stroke(3, zigzag(395, 690, 835, 1185, 20), 13.42, 0.35, w=16, color="rgba(217,195,160,.8)", ease="none", hand=False, clip="cl_b4")
for k, (cx, cy, r, c) in enumerate([(330, 860, 30, CARAMEL), (760, 820, 24, SAND), (800, 1070, 34, CARAMEL), (280, 1080, 20, SAND), (540, 740, 22, CARAMEL)]):
    pop_star(3, cx, cy, r, 13.45 + k * 0.06, c)
extra_audio.append((13.4, "sparkle", 0.16))
sig = nid("sig")
html[3].append(f'<div id="{sig}" class="sig"><div class="b">DAYMA BEAUTY</div><div class="s">Formación en micropigmentación</div></div>')
tl.append(f'tl.fromTo("#{sig}",{{opacity:0,y:14}},{{opacity:1,y:0,duration:0.5,ease:"expo.out"}},13.55);')

# ---------- camera pans across the whiteboard ----------
tl.insert(0, 'tl.set("#world",{x:0},0);')
for t, k in PANS:
    tl.append(f'tl.to("#world",{{x:{-SCENE_X[k]},duration:0.42,ease:"power3.inOut"}},{t});')
    extra_audio.append((t - 0.04, "whoosh-short", 0.26))

# ---------- the hand: follows the primary stroke, leaves the frame when idle ----------
segs.sort(key=lambda s: s[0])
sched, busy = [], 0.0
for t0, dur, fn in segs:
    a, b = max(t0, busy), t0 + dur
    if b - a < 0.06: continue
    f0 = (a - t0) / dur
    sched.append((a, b, lambda f, fn=fn, f0=f0: fn(f0 + f * (1 - f0))))
    busy = b
def scene_at(t):
    k = 0
    for pt, sk in PANS:
        if t >= pt + 0.2: k = sk
    return k
def rest(t):
    k = scene_at(t)
    return (SCENE_X[k] + 1300, 1250)
keys = []   # (time, x, y, rot)
def tip_to_pos(p): return (p[0] - TIP[0], p[1] - TIP[1])
cur_t, cur = 0.0, None
for idx, (a, b, fn) in enumerate(sched):
    start = fn(0)
    if cur is None:
        keys.append((0.0, *tip_to_pos(start)))
    else:
        gap = a - cur_t
        pan_between = any(cur_t < pt + 0.42 and a > pt for pt, _ in PANS)
        if gap > 0.7 or pan_between:
            r = rest(cur_t + 0.05)
            keys.append((cur_t + 0.25, r[0] - TIP[0], r[1] - TIP[1]))
            r2 = rest(a - 0.05)
            keys.append((a - 0.28, r2[0] - TIP[0], r2[1] - TIP[1]))
        keys.append((a, *tip_to_pos(start)))
    n = max(2, int((b - a) * 20))
    for j in range(1, n + 1):
        keys.append((a + (b - a) * j / n, *tip_to_pos(fn(j / n))))
    cur_t = b
r = rest(cur_t + 0.05)
keys.append((cur_t + 0.35, r[0] - TIP[0], r[1] - TIP[1]))
keys.sort(key=lambda k: k[0])
ht = [f'tl.set("#hand",{{x:{keys[0][1]:.1f},y:{keys[0][2]:.1f}}},0);']
for (t0, x0, y0), (t1, x1, y1) in zip(keys, keys[1:]):
    if t1 - t0 < 0.005: ht.append(f'tl.set("#hand",{{x:{x1:.1f},y:{y1:.1f}}},{t1:.3f});'); continue
    ht.append(f'tl.to("#hand",{{x:{x1:.1f},y:{y1:.1f},duration:{t1 - t0:.3f},ease:"none"}},{t0:.3f});')

# ---------- sound: marker while the hand draws, room tone, whooshes, pops ----------
mer = []
for a, b, _ in sched:
    if mer and a <= mer[-1][1] + 0.06: mer[-1][1] = max(mer[-1][1], b)
    else: mer.append([a, b])
expr = "+".join(f"between(t\\,{a:.2f}\\,{b:.2f})" for a, b in mer)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.6:d={T}:seed=7",
                "-af", f"bandpass=f=2600:width_type=h:w=2400,tremolo=f=11:d=0.8,volume=volume=1.0*({expr}):eval=frame,lowpass=f=7000",
                "-ac", "2", "-ar", "48000", f"{P}/assets/sfx/marker.wav"], check=True)

scenes = ""
for k in range(4):
    scenes += (f'<div class="scene" id="sc{k}" style="left:{SCENE_X[k]}px">'
               f'<svg class="ink" viewBox="0 0 {W} {H}" width="{W}" height="{H}"><g filter="url(#rough)">{"".join(svg[k])}</g></svg>'
               f'{"".join(html[k])}</div>')
aud = "".join(f'<audio id="fx{k}" class="clip" src="assets/sfx/{n}.mp3" data-start="{t:.2f}" data-duration="{0.55 if n != "sparkle" else 1.7}" data-volume="{v}" data-track-index="{20 + k}"></audio>'
              for k, (t, n, v) in enumerate(extra_audio))

index = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={W}, height={H}" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
@font-face{{font-family:'Caveat';font-weight:500;src:url('assets/fonts/caveat-latin-500-normal.woff2') format('woff2');}}
@font-face{{font-family:'Caveat';font-weight:700;src:url('assets/fonts/caveat-latin-700-normal.woff2') format('woff2');}}
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:#FBFAF7;}}
#root{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:radial-gradient(ellipse at 50% 40%,#FFFFFF 0%,#F8F6F2 70%,#EFEBE4 100%);}}
#world{{position:absolute;left:0;top:0;width:{4 * W}px;height:{H}px;}}
.scene{{position:absolute;top:0;width:{W}px;height:{H}px;}}
.ink{{position:absolute;left:0;top:0;overflow:visible;}}
.hw{{position:absolute;font-family:'Caveat';font-weight:700;color:{INK};line-height:1.05;white-space:nowrap;text-align:center;}}
.hw.left{{text-align:left;}}
.hw.big{{font-size:120px;}}
.kick{{position:absolute;font-family:'Montserrat';font-weight:600;font-size:40px;letter-spacing:.3em;color:#7A6548;white-space:nowrap;text-align:center;}}
.hl{{position:absolute;background:#E8D7BA;border-radius:10px 28px 12px 30px;transform-origin:left center;}}
.sig{{position:absolute;left:0;top:1370px;width:{W}px;text-align:center;}}
.sig .ln{{width:90px;height:3px;background:{SAND};margin:0 auto 22px;border-radius:2px;}}
.sig .b{{font-family:'Montserrat';font-weight:600;font-size:32px;letter-spacing:.42em;color:{INK};}}
.sig .s{{margin-top:6px;font-family:'Caveat';font-weight:500;font-size:54px;color:#4A4033;}}
#hand{{position:absolute;left:0;top:0;width:{HAND_W}px;height:{HAND_H}px;z-index:30;pointer-events:none;}}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{T}" data-width="{W}" data-height="{H}">
<svg width="0" height="0" style="position:absolute"><defs><filter id="rough"><feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="4"/><feDisplacementMap in="SourceGraphic" scale="3.5"/></filter></defs></svg>
<div id="world">{scenes}<img id="hand" src="assets/img/hand.png" alt=""></div>
<audio id="vo" class="clip" src="assets/vo/vo.wav" data-start="0" data-duration="{T}" data-volume="1" data-track-index="10"></audio>
<audio id="marker" class="clip" src="assets/sfx/marker.wav" data-start="0" data-duration="{T}" data-volume="1" data-track-index="11"></audio>
{aud}
</div>
<script>
const tl = gsap.timeline({{paused:true}});
{chr(10).join(tl)}
{chr(10).join(ht)}
window.__timelines["main"] = tl;
</script>
</body>
</html>"""
open(f"{P}/index.html", "w").write(index)
print("hand segments", len(sched), "keys", len(keys), "marker runs", len(mer))
