"""Reel v4 (piel grasa / pelo a pelo) with HyperFrames: join the takes with ffmpeg, write the composition."""
import subprocess, os, json, re, sys
S = os.path.dirname(os.path.abspath(__file__))
PX = f"{S}/r4/px"
P = f"{S}/reel4"
W, H = 1080, 1920
END = 3.4

# (clip, in, out, zoom) — dead air trimmed, repeated "necesitamos" at the head of c10 removed,
# camera swipe at the end of c05 removed; c04 split for a punch-in on "o la profesional…"
TAKES = [
    ("c01", 0.75, 4.45, 1.00), ("c02", 0.55, 4.95, 1.08), ("c03", 0.85, 4.95, 1.00),
    ("c04", 0.65, 5.00, 1.00), ("c04", 5.00, 7.85, 1.12), ("c05", 0.60, 4.65, 1.08),
    ("c06", 0.50, 2.20, 1.00), ("c07", 0.00, 2.20, 1.12), ("c08", 0.00, 0.95, 1.00),
    ("c09", 0.22, 3.92, 1.00), ("c10", 0.50, 2.85, 1.12), ("c11", 0.05, 3.10, 1.00),
]
GAIN = {"c10": 4.5, "c05": 1.0, "c06": 1.0}
outs, acc = [], 0.0
for _, a, b, _ in TAKES:
    outs.append(round(acc, 3)); acc += b - a
TALK = round(acc, 3)
TOTAL = round(TALK + END, 2)

def m(clip, t, k=None):
    """clip-local time -> output time (first take of that clip containing t)"""
    for i, (c, a, b, _) in enumerate(TAKES):
        if c == clip and (k is None or k == i) and a - 0.05 <= t <= b + 0.05:
            return round(outs[i] + min(max(t, a), b) - a, 3)
    raise ValueError((clip, t))

# ---------------- 1. talk.mp4 ----------------
if "--skip-video" not in sys.argv:
    inputs, f = [], []
    for i, (c, a, b, z) in enumerate(TAKES):
        inputs += ["-i", f"{PX}/{c}.mp4"]
        sw, sh = int(W * z) // 2 * 2, int(H * z) // 2 * 2
        f.append(f"[{i}:v]trim={a}:{b},setpts=PTS-STARTPTS,scale={sw}:{sh}:flags=lanczos,"
                 f"crop={W}:{H}:(iw-{W})/2:(ih-{H})*0.3,setsar=1,fps=30[v{i}]")
        d = b - a
        f.append(f"[{i}:a]atrim={a}:{b},asetpts=PTS-STARTPTS,volume={GAIN.get(c, 0)}dB,"
                 f"afade=t=in:d=0.02,afade=t=out:st={d - 0.03:.3f}:d=0.03[a{i}]")
    n = len(TAKES)
    f.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac]")
    f.append(f"[vc]eq=contrast=1.04:saturation=1.03:gamma=1.0,colorbalance=rs=0.015:bs=-0.015,"
             f"tpad=stop_mode=clone:stop_duration={END},format=yuv420p[vo]")
    f.append(f"[ac]highpass=f=80,afftdn=nf=-30,apad=pad_dur={END},loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[ao]")
    os.makedirs(f"{P}/assets", exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error"] + inputs + ["-filter_complex", ";".join(f),
                    "-map", "[vo]", "-map", "[ao]", "-t", f"{TOTAL}", "-c:v", "libx264", "-crf", "16",
                    "-preset", "medium", "-g", "30", "-c:a", "aac", "-b:a", "192k", f"{P}/assets/talk.mp4"], check=True)

# ---------------- 2. caption words ----------------
tr = json.load(open(f"{PX}/tr4.json"))
KEY = {"desesperada", "pelo", "piel", "sombreado", "nunca", "técnica", "grasa", "automáticamente",
       "evaluar", "adaptar", "entender", "ampliar", "formación", "completa", "profesional", "clientes"}
kept = []
for i, (c, a, b, _) in enumerate(TAKES):
    for w in tr[f"{c}.mp4"]:
        mid = (w["s"] + w["e"]) / 2
        if a <= mid <= b:
            txt = w["w"].strip().replace("...", "")
            if txt.lower() == "ella" and c == "c02": txt = "Ella"
            core = re.sub(r"[^\wáéíóúñ]", "", txt.lower())
            s = max(w["s"], a); e = min(w["e"], b)
            if c == "c02" and core == "ella": s = 0.55
            kept.append({"s": m(c, s, i), "e": m(c, e, i), "t": txt, "k": core in KEY})
groups, cur = [], []
for k, w in enumerate(kept):
    cur.append(w)
    gap = kept[k + 1]["s"] - w["e"] if k + 1 < len(kept) else 9
    if len(cur) >= 3 or w["t"][-1] in ".,?!:" or gap > 0.2 or sum(len(x["t"]) for x in cur) > 15:
        groups.append(cur); cur = []
if cur: groups.append(cur)

# ---------------- 3. visual plan (output seconds) ----------------
HOOK = (0.0, 1.85)
SPLITS = [  # (start, end, [(t, img, label)])
    (1.85, m("c01", 4.45), [(1.85, "v_upset", "CLIENTE DESESPERADA")]),
    (m("c02", 0.55), m("c03", 4.95), [(m("c02", 0.55), "u6", "PIDIÓ PELO A PELO"),
                                      (m("c02", 2.45), "v_skin", "¿POR SU TIPO DE PIEL?"),
                                      (m("c03", 0.85), "u15", "UN SOMBREADO QUE NUNCA QUISO")]),
    (m("c05", 0.60), m("c05", 4.65), [(m("c05", 0.60), "v_oily", "PIEL GRASA ≠ DESCARTAR")]),
    (m("c09", 1.50), m("c10", 2.85), [(m("c09", 1.50), "v_salon", "¿MÁS CLIENTES?"),
                                      (m("c10", 0.50), "u14", "AMPLÍA LO QUE OFRECES")]),
    (m("c11", 0.05), m("c11", 3.10), [(m("c11", 0.05), "v_class", "FORMACIÓN COMPLETA")]),
]
CARDS = [
    {"id": "vs", "a": m("c04", 1.55, 3), "b": m("c04", 7.85, 4), "bg": "u16", "kicker": "AHORA YO PIENSO…",
     "items": [(m("c04", 1.74, 3), "¿Realmente <em>no se podía</em> hacer pelo a pelo?", "A"),
               (m("c04", 5.32, 4), "¿O la profesional <em>no sabía</em> cómo trabajar esa piel?", "B")]},
    {"id": "st", "a": m("c06", 0.50), "b": m("c08", 0.95), "bg": "u12", "kicker": "SIGNIFICA QUE NECESITAS SABER",
     "items": [(m("c07", 0.00), "<em>Evaluar</em>", "01"), (m("c07", 0.86), "<em>Adaptar</em>", "02"),
               (m("c07", 1.56), "<em>Entender</em> cómo trabajarla", "03")]},
]
CAM_SPLIT_Y = 470

def blocked(t):
    return t < HOOK[1] - 0.02 or t >= TALK or any(c["a"] - 0.05 <= t < c["b"] - 0.05 for c in CARDS)

css_fonts = """
@font-face{font-family:'Cormorant Garamond';font-style:italic;font-weight:500;src:url('assets/fonts/cormorant-garamond-latin-500-italic.woff2') format('woff2');}
@font-face{font-family:'Cormorant Garamond';font-style:italic;font-weight:600;src:url('assets/fonts/cormorant-garamond-latin-600-italic.woff2') format('woff2');}
@font-face{font-family:'Cormorant Garamond';font-style:normal;font-weight:600;src:url('assets/fonts/cormorant-garamond-latin-600-normal.woff2') format('woff2');}
"""
html, tl = [], []
add = html.append

add(f'<div id="cam" style="position:absolute;left:0;top:0;width:{W}px;height:{H}px;z-index:1">'
    f'<video id="talk" class="clip" src="assets/talk.mp4" data-start="0" data-duration="{TOTAL}" '
    f'data-track-index="0" data-has-audio="true" playsinline style="position:absolute;left:0;top:0;width:{W}px;height:{H}px;object-fit:cover"></video></div>')

tl.append('tl.set("#cam",{y:0},0);')
wins = sorted([(a, b) for a, b, _ in SPLITS] + [(c["a"], c["b"]) for c in CARDS])
merged = []
for a, b in wins:
    if merged and a - merged[-1][1] < 0.6: merged[-1][1] = max(merged[-1][1], b)
    else: merged.append([a, b])
for a, b in merged:
    tl.append(f'tl.to("#cam",{{y:{CAM_SPLIT_Y},duration:0.5,ease:"power3.inOut"}},{max(a - 0.2, 0):.3f});')
    tl.append(f'tl.to("#cam",{{y:0,duration:0.45,ease:"power3.inOut"}},{b - 0.25:.3f});')

for si, (a, b, items) in enumerate(SPLITS):
    for ii, (t0, img, label) in enumerate(items):
        t1 = items[ii + 1][0] if ii + 1 < len(items) else b
        pid = f"p{si}_{ii}"
        add(f'<div id="{pid}" class="clip panel" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-track-index="2" style="z-index:5">'
            f'<div class="pin" id="{pid}i"><img src="assets/img/{img}.jpg" alt=""></div>'
            f'<div class="tag" id="{pid}t"><span class="dot"></span>{label}</div></div>')
        first = ii == 0
        if first:
            tl.append(f'tl.fromTo("#{pid}i",{{clipPath:"inset(0% 0% 100% 0%)"}},{{clipPath:"inset(0% 0% 0% 0%)",duration:0.55,ease:"expo.out"}},{t0:.3f});')
        else:
            tl.append(f'tl.fromTo("#{pid}i",{{opacity:0,filter:"blur(14px)"}},{{opacity:1,filter:"blur(0px)",duration:0.22,ease:"power2.out"}},{t0:.3f});')
        tl.append(f'tl.fromTo("#{pid}i img",{{scale:1.14}},{{scale:1.02,duration:{t1 - t0:.3f},ease:"power1.out"}},{t0:.3f});')
        tl.append(f'tl.fromTo("#{pid}t",{{opacity:0,x:-24}},{{opacity:1,x:0,duration:0.45,ease:"expo.out"}},{t0 + 0.25:.3f});')
        if ii + 1 == len(items):
            tl.append(f'tl.to("#{pid}i",{{opacity:0,filter:"blur(10px)",duration:0.25,ease:"power2.in"}},{t1 - 0.28:.3f});')
            tl.append(f'tl.to("#{pid}t",{{opacity:0,duration:0.2,ease:"power2.in"}},{t1 - 0.3:.3f});')
        add(f'<audio id="sfx_{pid}" class="clip" src="assets/sfx/{"whoosh-short" if first else "click-soft"}.mp3" '
            f'data-start="{max(t0 - 0.05, 0):.3f}" data-duration="{0.55 if first else 0.35}" data-volume="{0.22 if first else 0.18}" data-track-index="6"></audio>')

for c in CARDS:
    cid, qa, qb = c["id"], c["a"], c["b"]
    rows = "".join(f'<div class="q" id="{cid}{k}"><span class="qn">{n}</span><span class="qt">{txt}</span></div>'
                   for k, (_, txt, n) in enumerate(c["items"]))
    add(f'<div id="{cid}" class="clip card" data-start="{qa:.3f}" data-duration="{qb - qa:.3f}" data-track-index="4" style="z-index:6">'
        f'<div class="cbg" id="{cid}bg"><img src="assets/img/{c["bg"]}.jpg" alt=""></div><div class="cshade"></div>'
        f'<div class="cbox"><div class="kicker" id="{cid}k">{c["kicker"]}</div>{rows}</div></div>')
    tl.append(f'tl.fromTo("#{cid}bg",{{clipPath:"inset(0% 0% 100% 0%)"}},{{clipPath:"inset(0% 0% 0% 0%)",duration:0.55,ease:"expo.out"}},{qa:.3f});')
    tl.append(f'tl.fromTo("#{cid}bg img",{{scale:1.15}},{{scale:1.03,duration:{qb - qa:.3f},ease:"power1.out"}},{qa:.3f});')
    tl.append(f'tl.fromTo("#{cid}k",{{opacity:0,y:10}},{{opacity:1,y:0,duration:0.4,ease:"expo.out"}},{qa + 0.1:.3f});')
    for k, (t, _, _) in enumerate(c["items"]):
        tl.append(f'tl.fromTo("#{cid}{k}",{{opacity:0,x:-40,filter:"blur(6px)"}},{{opacity:1,x:0,filter:"blur(0px)",duration:0.5,ease:"expo.out"}},{t - 0.05:.3f});')
        if k: tl.append(f'tl.to("#{cid}{k - 1} .qt",{{opacity:0.55,duration:0.3}},{t - 0.05:.3f});')
        add(f'<audio id="sfx_{cid}{k}" class="clip" src="assets/sfx/pop.mp3" data-start="{t - 0.05:.3f}" data-duration="0.7" data-volume="0.16" data-track-index="7"></audio>')
    tl.append(f'tl.to("#{cid}",{{opacity:0,duration:0.3,ease:"power2.in"}},{qb - 0.32:.3f});')

# hook title over the speaker (frame 0 already shows face + line)
add(f'<div id="hook" class="clip" data-start="0" data-duration="{HOOK[1] + 0.3:.3f}" data-track-index="3" style="z-index:8">'
    f'<div id="hookshade"></div><div id="hooktxt"><div class="kicker" id="hk">PELO A PELO · PIEL GRASA</div>'
    f'<h1 id="ht"><span class="w">¿No</span> <span class="w">se</span> <span class="w">podía…</span><br>'
    f'<em class="w">o no sabían cómo?</em></h1></div></div>')
tl.append('tl.fromTo("#hk",{opacity:0.6},{opacity:1,duration:0.4,ease:"power2.out"},0);')
tl.append('tl.fromTo("#ht em",{scale:1},{scale:1.04,duration:0.35,ease:"power2.out"},0.9);')
tl.append(f'tl.to("#hook",{{opacity:0,duration:0.3,ease:"power2.in"}},{HOOK[1]:.3f});')

# end card
e0 = TALK - 0.15
add(f'<div id="endc" class="clip" data-start="{e0:.3f}" data-duration="{TOTAL - e0:.3f}" data-track-index="5" style="z-index:9">'
    f'<div id="endbg"></div><div id="endtxt"><div class="rule" id="er1"></div>'
    f'<h2 id="e1">Evaluar. Adaptar.</h2><h2 id="e2"><em>Entender.</em></h2>'
    f'<div class="rule" id="er2"></div><div class="kicker" id="e3" style="letter-spacing:.18em">ESO SOLO TE LO DA UNA FORMACIÓN COMPLETA</div>'
    f'<div id="e4">@daymabeauty</div></div></div>')
tl.append(f'tl.fromTo("#endbg",{{opacity:0}},{{opacity:1,duration:0.45,ease:"power2.inOut"}},{e0:.3f});')
tl.append(f'tl.fromTo(["#er1","#er2"],{{scaleX:0}},{{scaleX:1,duration:0.7,ease:"expo.out"}},{e0 + 0.3:.3f});')
tl.append(f'tl.fromTo("#e1",{{opacity:0,filter:"blur(8px)"}},{{opacity:1,filter:"blur(0px)",duration:0.25,ease:"power3.out"}},{e0 + 0.35:.3f});')
tl.append(f'tl.fromTo("#e2",{{opacity:0,filter:"blur(8px)"}},{{opacity:1,filter:"blur(0px)",duration:0.25,ease:"power3.out"}},{e0 + 0.7:.3f});')
tl.append(f'tl.fromTo(["#e3","#e4"],{{opacity:0,y:12}},{{opacity:1,y:0,duration:0.5,stagger:0.12,ease:"expo.out"}},{e0 + 0.85:.3f});')
add(f'<audio id="sfx_end" class="clip" src="assets/sfx/sparkle.mp3" data-start="{e0 + 0.3:.3f}" data-duration="1.75" data-volume="0.2" data-track-index="8"></audio>')

# captions
cap_html, ctl = [], []
for gi, g in enumerate(groups):
    s, e = g[0]["s"], g[-1]["e"]
    if blocked(s): continue
    nxt = next((gg[0]["s"] for gg in groups[gi + 1:]), e + 1)
    e = (nxt - 0.05) if nxt - e < 0.6 else e + 0.15
    for c in CARDS:                       # never run into a card
        if s < c["a"] < e: e = c["a"] - 0.05
    if e >= TALK - 0.15: e = TALK - 0.2
    in_split = any(a - 0.1 <= s < b for a, b in merged)
    top = 905 if in_split else 1215
    spans = " ".join(f'<span class="{"cw key" if w["k"] else "cw"}" id="c{gi}_{wi}">{w["t"].rstrip(".,:")}</span>' for wi, w in enumerate(g))
    cls = "cg" if in_split else "cg full"
    cap_html.append(f'<div class="{cls}" id="cg{gi}" style="top:{top}px"><span class="cbx">{spans}</span></div>')
    ctl.append(f'tl.set("#cg{gi}",{{visibility:"visible",opacity:1}},{s - 0.04:.3f});')
    ctl.append(f'tl.fromTo("#cg{gi} .cw",{{opacity:0,y:14}},{{opacity:1,y:0,duration:0.18,stagger:0.05,ease:"power3.out"}},{s - 0.04:.3f});')
    for wi, w in enumerate(g):
        if not w["k"]:
            ctl.append(f'tl.fromTo("#c{gi}_{wi}",{{color:"#F7EFE9"}},{{color:"#F2C4BC",duration:0.08,overwrite:"auto"}},{w["s"]:.3f});')
            ctl.append(f'tl.to("#c{gi}_{wi}",{{color:"#F7EFE9",duration:0.12,overwrite:"auto"}},{w["e"]:.3f});')
    ctl.append(f'tl.to("#cg{gi}",{{opacity:0,duration:0.1,ease:"power2.in"}},{e - 0.1:.3f});')
    ctl.append(f'tl.set("#cg{gi}",{{opacity:0,visibility:"hidden"}},{e:.3f});')

captions = f"""<template>
<style>
{css_fonts}
#root{{position:absolute;inset:0;}}
.cg{{position:absolute;left:0;top:905px;width:{W}px;padding:0 90px;text-align:center;visibility:hidden;opacity:0;
  font-family:'Playfair Display';font-weight:700;font-size:62px;line-height:1.15;color:#F7EFE9;
  text-shadow:0 3px 14px rgba(20,10,10,.65),0 1px 2px rgba(20,10,10,.8);}}
.cw{{display:inline-block;}}
.full .cbx{{display:inline-block;padding:10px 30px 16px;border-radius:22px;background:rgba(20,14,14,.58);backdrop-filter:blur(6px);}}
.key{{font-family:'Cormorant Garamond';font-style:italic;font-weight:600;font-size:80px;color:#F2C4BC;line-height:1;}}
</style>
<div id="root" data-composition-id="captions" data-width="{W}" data-height="{H}">
{chr(10).join(cap_html)}
</div>
<script>
const tl = gsap.timeline({{paused:true}});
{chr(10).join(ctl)}
window.__timelines["captions"] = tl;
</script>
</template>"""
os.makedirs(f"{P}/compositions", exist_ok=True)
open(f"{P}/compositions/captions.html", "w").write(captions)

index = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={W}, height={H}" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
{css_fonts}
:root{{--rose:#F2C4BC;--ink:#F7EFE9;--espresso:#140E0E;}}
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:var(--espresso);}}
#root{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:var(--espresso);}}
.panel,.card{{position:absolute;left:0;top:0;width:{W}px;height:1010px;}}
.pin,.cbg{{position:absolute;inset:0;overflow:hidden;
  -webkit-mask-image:linear-gradient(to bottom,#000 0%,#000 84%,transparent 100%);mask-image:linear-gradient(to bottom,#000 0%,#000 84%,transparent 100%);}}
.pin img,.cbg img{{width:100%;height:100%;object-fit:cover;display:block;}}
.tag{{position:absolute;left:56px;top:190px;display:flex;align-items:center;gap:14px;padding:12px 22px 12px 18px;
  background:rgba(20,14,14,.55);backdrop-filter:blur(10px);border:1px solid rgba(242,196,188,.35);border-radius:999px;
  font-family:'Montserrat';font-weight:600;font-size:28px;letter-spacing:.2em;color:var(--ink);}}
.dot{{width:10px;height:10px;border-radius:50%;background:var(--rose);}}
.kicker{{font-family:'Montserrat';font-weight:600;font-size:28px;letter-spacing:.32em;color:var(--rose);}}
#hook{{position:absolute;inset:0;}}
#hookshade{{position:absolute;left:0;top:0;width:{W}px;height:900px;background:linear-gradient(to bottom,rgba(20,14,14,.72),rgba(20,14,14,.35) 60%,rgba(20,14,14,0));}}
#hooktxt{{position:absolute;left:0;top:210px;width:{W}px;text-align:center;padding:0 60px;}}
#ht{{margin-top:26px;font-family:'Playfair Display';font-weight:700;font-size:104px;line-height:1.02;color:var(--ink);text-shadow:0 4px 24px rgba(20,10,10,.55);}}
#ht em{{display:inline-block;font-family:'Cormorant Garamond';font-style:italic;font-weight:600;font-size:124px;color:var(--rose);}}
.cshade{{position:absolute;inset:0;background:linear-gradient(to bottom,rgba(20,14,14,.84),rgba(20,14,14,.62) 70%,rgba(20,14,14,0));}}
.cbox{{position:absolute;left:70px;top:230px;width:950px;}}
.cbox .kicker{{margin-bottom:34px;}}
.q{{display:flex;align-items:baseline;gap:22px;margin-bottom:34px;}}
.qn{{font-family:'Cormorant Garamond';font-style:italic;font-weight:600;font-size:70px;color:var(--rose);width:84px;flex:none;}}
.qt{{font-family:'Playfair Display';font-weight:700;font-size:60px;line-height:1.15;color:var(--ink);}}
.qt em{{font-family:'Cormorant Garamond';font-style:italic;font-weight:600;font-size:78px;color:var(--rose);}}
#endc{{position:absolute;inset:0;}}
#endbg{{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 40%,rgba(58,34,32,.94),rgba(20,14,14,.98));}}
#endtxt{{position:absolute;left:0;top:640px;width:{W}px;text-align:center;}}
#endtxt h2{{font-family:'Playfair Display';font-weight:700;font-size:88px;line-height:1.1;color:var(--ink);}}
#endtxt h2 em{{font-family:'Cormorant Garamond';font-style:italic;font-weight:600;font-size:116px;color:var(--rose);}}
.rule{{width:120px;height:2px;background:var(--rose);margin:38px auto;transform-origin:center;}}
#e4{{margin-top:22px;font-family:'Cormorant Garamond';font-style:italic;font-weight:600;font-size:48px;color:var(--ink);}}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{W}" data-height="{H}">
{chr(10).join(html)}
<div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{TOTAL}" data-track-index="9" data-track-kind="captions" data-width="{W}" data-height="{H}" style="z-index:20"></div>
</div>
<script>
const tl = gsap.timeline({{paused:true}});
{chr(10).join(tl)}
window.__timelines["main"] = tl;
</script>
</body>
</html>"""
open(f"{P}/index.html", "w").write(index)
print("talk", TALK, "total", TOTAL, "groups", len(groups))
print("splits", [(round(a, 2), round(b, 2)) for a, b, _ in SPLITS], "cards", [(c["a"], c["b"]) for c in CARDS])
