"""Reel v3 with HyperFrames: cut the talk with ffmpeg, then write the HTML composition."""
import subprocess, os, json, re, sys
S = os.path.dirname(os.path.abspath(__file__))
P = f"{S}/reel3"
W, H = 1080, 1920
END = 3.2

SEG = [
    (0.40, 4.80, 1.00), (4.95, 9.80, 1.12), (10.00, 17.78, 1.00), (17.90, 20.18, 1.12),
    (20.50, 27.12, 1.00), (27.30, 28.50, 1.12), (30.50, 32.04, 1.12), (32.04, 32.80, 1.00),
    (39.20, 40.72, 1.00), (40.90, 44.95, 1.12), (50.10, 55.76, 1.00), (55.78, 58.30, 1.15),
]
outs, acc = [], 0.0
for a, b, z in SEG:
    outs.append(acc); acc += b - a
TALK = acc
TOTAL = round(TALK + END, 2)
def m(i, t):
    a, b, _ = SEG[i]; return round(outs[i] + min(max(t, a), b) - a, 3)

# ---------------- 1. talk.mp4 (jump cuts + punch-ins + grade + loudness) ----------------
if "--skip-video" not in sys.argv:
    f = []
    for i, (a, b, z) in enumerate(SEG):
        sw, sh = int(W * z) // 2 * 2, int(H * z) // 2 * 2
        f.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,scale={sw}:{sh}:flags=lanczos,"
                 f"crop={W}:{H}:(iw-{W})/2:(ih-{H})*0.35,setsar=1,fps=30[v{i}]")
        d = b - a
        f.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={d-0.03:.3f}:d=0.03[a{i}]")
    n = len(SEG)
    f.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac]")
    f.append(f"[vc]eq=contrast=1.05:saturation=1.07:gamma=0.98,colorbalance=rs=0.025:bs=-0.02:rh=0.02,"
             f"tpad=stop_mode=clone:stop_duration={END},format=yuv420p[vo]")
    f.append(f"[ac]apad=pad_dur={END},loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[ao]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{S}/in.mp4", "-filter_complex", ";".join(f),
                    "-map", "[vo]", "-map", "[ao]", "-t", f"{TOTAL}", "-c:v", "libx264", "-crf", "16",
                    "-preset", "medium", "-g", "30", "-c:a", "aac", "-b:a", "192k", f"{P}/assets/talk.mp4"],
                   check=True)

# ---------------- 2. caption groups from word timestamps ----------------
words = [w for s in json.load(open(f"{S}/tr.json")) for w in s["words"]]
FIX = {"llegue": "llega", "pelopelo": "pelo a pelo"}
KEY = {"técnica", "problema", "realista", "pelo a pelo", "manchas", "remover", "plazo", "modificar",
       "valorado", "pienso", "trabajar", "solucionar", "momento"}
kept = []
for i, (a, b, _) in enumerate(SEG):
    for w in words:
        mid = (w["s"] + w["e"]) / 2
        if a <= mid <= b and not (i == 6 and w["s"] < 30.5):
            txt = w["w"].strip()
            core = re.sub(r"[^\wáéíóúñ]", "", txt.lower())
            if core in FIX: txt = txt.lower().replace(core, FIX[core]); core = FIX[core]
            kept.append({"s": m(i, w["s"]), "e": m(i, w["e"]), "t": txt, "k": core in KEY})
groups, cur = [], []
for k, w in enumerate(kept):
    cur.append(w)
    gap = kept[k + 1]["s"] - w["e"] if k + 1 < len(kept) else 9
    if len(cur) >= 3 or w["t"][-1] in ".,?!:" or gap > 0.2 or sum(len(x["t"]) for x in cur) > 15:
        groups.append(cur); cur = []
if cur: groups.append(cur)

# ---------------- 3. visual plan ----------------
HOOK_END = m(0, 2.10)
QUEST = (m(2, 10.0), m(2, 17.78))       # questions card replaces b-roll + captions
Q_ITEMS = [(m(2, 10.12), "¿Qué tiene esta persona?"), (m(2, 11.34), "¿Qué <em>puedo</em> modificar?"),
           (m(2, 12.64), "¿Qué <em>no puedo</em> modificar?"), (m(2, 14.28), "¿Qué resultado sería <em>realista</em>?")]
SPLITS = [  # (start, end, [(t, img, label)])
    (m(0, 2.10), m(1, 7.10), [(m(0, 2.10), "u11", "CASO NUEVO"), (m(1, 4.95), "u12", "PRIMERO, ENTENDER")]),
    (m(1, 7.90), m(1, 9.80), [(m(1, 7.90), "u4", "EL PROBLEMA")]),
    (m(3, 17.90), m(4, 27.12), [(m(3, 17.90), "u14", "CÓMO TRABAJAR"), (m(4, 20.50), "u6", "CEJA PELO A PELO"),
                                (m(4, 23.30), "u1", "PROCEDIMIENTO ANTERIOR")]),
    (m(7, 32.04), m(9, 44.95), [(m(7, 32.04), "u5", "MANCHAS DE PIGMENTO"), (m(9, 41.90), "u16", "REMOCIÓN")]),
    (m(10, 51.80), m(10, 55.76), [(m(10, 51.80), "u8", "A LARGO PLAZO")]),
]
CAM_SPLIT_Y = 470   # px the talk moves down when the top panel is in

def no_caption(t):
    return QUEST[0] - 0.05 <= t < QUEST[1] - 0.05 or t < HOOK_END - 0.02 or t >= TALK

# ---------------- 4. HTML ----------------
css_fonts = """
@font-face{font-family:'Cormorant Garamond';font-style:italic;font-weight:500;src:url('assets/fonts/cormorant-garamond-latin-500-italic.woff2') format('woff2');}
@font-face{font-family:'Cormorant Garamond';font-style:italic;font-weight:600;src:url('assets/fonts/cormorant-garamond-latin-600-italic.woff2') format('woff2');}
@font-face{font-family:'Cormorant Garamond';font-style:normal;font-weight:600;src:url('assets/fonts/cormorant-garamond-latin-600-normal.woff2') format('woff2');}
"""
html = []
tl = []
z = 1
def add(s): html.append(s)

# talk video inside a camera wrapper (wrapper is untimed; the video is timed)
add(f'<div id="cam" style="position:absolute;left:0;top:0;width:{W}px;height:{H}px;z-index:1">'
    f'<video id="talk" class="clip" src="assets/talk.mp4" data-start="0" data-duration="{TOTAL}" '
    f'data-track-index="0" data-has-audio="true" playsinline style="position:absolute;left:0;top:0;width:{W}px;height:{H}px;object-fit:cover"></video></div>')
tl.append('tl.set("#cam",{y:0},0);')
# camera moves: down into the bottom half for each split window (merged when windows touch), back up after
wins = sorted([(a, b) for a, b, _ in SPLITS] + [QUEST])
merged = []
for a, b in wins:
    if merged and a - merged[-1][1] < 0.6: merged[-1][1] = max(merged[-1][1], b)
    else: merged.append([a, b])
for a, b in merged:
    tl.append(f'tl.to("#cam",{{y:{CAM_SPLIT_Y},duration:0.5,ease:"power3.inOut"}},{max(a-0.2,0):.3f});')
    tl.append(f'tl.to("#cam",{{y:0,duration:0.45,ease:"power3.inOut"}},{b-0.25:.3f});')

# split panels
for si, (a, b, items) in enumerate(SPLITS):
    for ii, (t0, img, label) in enumerate(items):
        t1 = items[ii + 1][0] if ii + 1 < len(items) else b
        pid = f"p{si}_{ii}"
        add(f'<div id="{pid}" class="clip panel" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-track-index="2" style="z-index:5">'
            f'<div class="pin" id="{pid}i"><img src="assets/img/{img}.jpg" alt=""></div>'
            f'<div class="tag" id="{pid}t"><span class="dot"></span>{label}</div></div>')
        first = ii == 0
        if first:   # reveal: wipe down from the top edge
            tl.append(f'tl.fromTo("#{pid}i",{{clipPath:"inset(0% 0% 100% 0%)"}},{{clipPath:"inset(0% 0% 0% 0%)",duration:0.55,ease:"expo.out"}},{t0:.3f});')
        else:       # blur swap on the same stage
            tl.append(f'tl.fromTo("#{pid}i",{{opacity:0,filter:"blur(14px)"}},{{opacity:1,filter:"blur(0px)",duration:0.22,ease:"power2.out"}},{t0:.3f});')
        tl.append(f'tl.fromTo("#{pid}i img",{{scale:1.14}},{{scale:1.02,duration:{t1 - t0:.3f},ease:"power1.out"}},{t0:.3f});')
        tl.append(f'tl.fromTo("#{pid}t",{{opacity:0,x:-24}},{{opacity:1,x:0,duration:0.45,ease:"expo.out"}},{t0 + 0.25:.3f});')
        if ii + 1 == len(items):
            tl.append(f'tl.to("#{pid}i",{{opacity:0,filter:"blur(10px)",duration:0.25,ease:"power2.in"}},{t1 - 0.28:.3f});')
            tl.append(f'tl.to("#{pid}t",{{opacity:0,duration:0.2,ease:"power2.in"}},{t1 - 0.3:.3f});')
        add(f'<audio id="sfx_{pid}" class="clip" src="assets/sfx/{"whoosh-short" if first else "click-soft"}.mp3" '
            f'data-start="{max(t0 - 0.05, 0):.3f}" data-duration="{0.55 if first else 0.35}" data-volume="{0.22 if first else 0.18}" data-track-index="6"></audio>')

# hook: full-screen image + title
add(f'<div id="hook" class="clip" data-start="0" data-duration="{HOOK_END + 0.35:.3f}" data-track-index="3" style="z-index:8">'
    f'<div id="hookimg"><img src="assets/img/u15.jpg" alt=""></div><div id="hookshade"></div>'
    f'<div id="hooktxt"><div class="kicker" id="hk">MICROBLADING · CRITERIO PROFESIONAL</div>'
    f'<h1 id="ht"><span class="w">Cómo</span> <span class="w">pienso</span> <span class="w">ante</span><br>'
    f'<em class="w">un caso nuevo</em></h1></div></div>')
tl.append(f'tl.fromTo("#hookimg img",{{scale:1.18}},{{scale:1.04,duration:{HOOK_END + 0.35:.3f},ease:"power2.out"}},0);')
tl.append('tl.fromTo("#hk",{opacity:0,y:-12},{opacity:1,y:0,duration:0.6,ease:"expo.out"},0);')
tl.append('tl.fromTo("#ht .w",{opacity:0,filter:"blur(8px)"},{opacity:1,filter:"blur(0px)",duration:0.2,stagger:0.08,ease:"power3.out"},0.0);')
tl.append(f'tl.to("#hook",{{opacity:0,duration:0.3,ease:"power2.in"}},{HOOK_END:.3f});')

# questions card
qa, qb = QUEST
add(f'<div id="quest" class="clip" data-start="{qa:.3f}" data-duration="{qb - qa:.3f}" data-track-index="4" style="z-index:6">'
    f'<div id="qbg"><img src="assets/img/u17.jpg" alt=""></div><div id="qshade"></div>'
    f'<div id="qbox"><div class="kicker" id="qk">ANTES DE ELEGIR LA TÉCNICA</div>'
    + "".join(f'<div class="q" id="q{k}"><span class="qn">0{k + 1}</span><span class="qt">{txt}</span></div>' for k, (_, txt) in enumerate(Q_ITEMS))
    + '</div></div>')
tl.append(f'tl.fromTo("#qbg",{{clipPath:"inset(0% 0% 100% 0%)"}},{{clipPath:"inset(0% 0% 0% 0%)",duration:0.55,ease:"expo.out"}},{qa:.3f});')
tl.append(f'tl.fromTo("#qbg img",{{scale:1.15}},{{scale:1.03,duration:{qb - qa:.3f},ease:"power1.out"}},{qa:.3f});')
tl.append(f'tl.fromTo("#qk",{{opacity:0,y:10}},{{opacity:1,y:0,duration:0.4,ease:"expo.out"}},{qa + 0.1:.3f});')
for k, (t, _) in enumerate(Q_ITEMS):
    tl.append(f'tl.fromTo("#q{k}",{{opacity:0,x:-40,filter:"blur(6px)"}},{{opacity:1,x:0,filter:"blur(0px)",duration:0.5,ease:"expo.out"}},{t - 0.05:.3f});')
    if k: tl.append(f'tl.to("#q{k - 1} .qt",{{opacity:0.55,duration:0.3}},{t - 0.05:.3f});')
    add(f'<audio id="sfx_q{k}" class="clip" src="assets/sfx/pop.mp3" data-start="{t - 0.05:.3f}" data-duration="0.7" data-volume="0.16" data-track-index="7"></audio>')
tl.append(f'tl.to("#quest",{{opacity:0,duration:0.3,ease:"power2.in"}},{qb - 0.32:.3f});')

# end card
add(f'<div id="endc" class="clip" data-start="{TALK - 0.2:.3f}" data-duration="{END + 0.2:.3f}" data-track-index="5" style="z-index:9">'
    f'<div id="endbg"></div><div id="endtxt"><div class="rule" id="er1"></div>'
    f'<h2 id="e1">Primero el problema.</h2><h2 id="e2"><em>Después la técnica.</em></h2>'
    f'<div class="rule" id="er2"></div><div class="kicker" id="e3" style="letter-spacing:.18em">GUÁRDALO PARA TU PRÓXIMA VALORACIÓN</div>'
    f'<div id="e4">@daymabeauty</div></div></div>')
e0 = TALK - 0.2
tl.append(f'tl.fromTo("#endbg",{{opacity:0}},{{opacity:1,duration:0.45,ease:"power2.inOut"}},{e0:.3f});')
tl.append(f'tl.fromTo(["#er1","#er2"],{{scaleX:0}},{{scaleX:1,duration:0.7,ease:"expo.out"}},{e0 + 0.3:.3f});')
tl.append(f'tl.fromTo("#e1",{{opacity:0,filter:"blur(8px)"}},{{opacity:1,filter:"blur(0px)",duration:0.25,ease:"power3.out"}},{e0 + 0.35:.3f});')
tl.append(f'tl.fromTo("#e2",{{opacity:0,filter:"blur(8px)"}},{{opacity:1,filter:"blur(0px)",duration:0.25,ease:"power3.out"}},{e0 + 0.75:.3f});')
tl.append(f'tl.fromTo(["#e3","#e4"],{{opacity:0,y:12}},{{opacity:1,y:0,duration:0.5,stagger:0.12,ease:"expo.out"}},{e0 + 0.85:.3f});')
add(f'<audio id="sfx_end" class="clip" src="assets/sfx/sparkle.mp3" data-start="{e0 + 0.3:.3f}" data-duration="1.75" data-volume="0.2" data-track-index="8"></audio>')

# captions (one group visible at a time; active word lights up in rose)
cap_html, ctl = [], []
for gi, g in enumerate(groups):
    s, e = g[0]["s"], g[-1]["e"]
    if no_caption(s): continue
    nxt = next((gg[0]["s"] for gg in groups[gi + 1:]), e + 1)
    e = (nxt - 0.05) if nxt - e < 0.6 else e + 0.15
    spans = []
    for wi, w in enumerate(g):
        t = w["t"].rstrip(".,:")
        cls = "cw key" if w["k"] else "cw"
        spans.append(f'<span class="{cls}" id="c{gi}_{wi}">{t}</span>')
    in_split = any(a - 0.1 <= s < b for a, b in merged)
    top = 905 if in_split else 1215
    cap_html.append(f'<div class="cg" id="cg{gi}" style="top:{top}px">{" ".join(spans)}</div>')
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
:root{{--rose:#F2C4BC;--rose-deep:#C98B80;--ink:#F7EFE9;--espresso:#140E0E;}}
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:var(--espresso);}}
#root{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:var(--espresso);}}
.panel{{position:absolute;left:0;top:0;width:{W}px;height:1010px;}}
.pin{{position:absolute;inset:0;overflow:hidden;
  -webkit-mask-image:linear-gradient(to bottom,#000 0%,#000 84%,transparent 100%);mask-image:linear-gradient(to bottom,#000 0%,#000 84%,transparent 100%);}}
.pin img,#hookimg img,#qbg img{{width:100%;height:100%;object-fit:cover;display:block;}}
.tag{{position:absolute;left:56px;top:190px;display:flex;align-items:center;gap:14px;padding:12px 22px 12px 18px;
  background:rgba(20,14,14,.55);backdrop-filter:blur(10px);border:1px solid rgba(242,196,188,.35);border-radius:999px;
  font-family:'Montserrat';font-weight:600;font-size:28px;letter-spacing:.2em;color:var(--ink);}}
.dot{{width:10px;height:10px;border-radius:50%;background:var(--rose);}}
#hook{{position:absolute;inset:0;}}
#hookimg{{position:absolute;inset:0;overflow:hidden;}}
#hookshade{{position:absolute;inset:0;background:linear-gradient(to bottom,rgba(20,14,14,.75) 0%,rgba(20,14,14,.15) 38%,rgba(20,14,14,0) 60%,rgba(20,14,14,.35) 100%);}}
#hooktxt{{position:absolute;left:0;top:250px;width:{W}px;text-align:center;padding:0 70px;}}
.kicker{{font-family:'Montserrat';font-weight:600;font-size:28px;letter-spacing:.32em;color:var(--rose);}}
#ht{{margin-top:28px;font-family:'Playfair Display';font-weight:700;font-size:104px;line-height:1.02;color:var(--ink);
  text-shadow:0 4px 24px rgba(20,10,10,.55);}}
#ht em{{font-family:'Cormorant Garamond';font-style:italic;font-weight:600;font-size:132px;color:var(--rose);}}
#quest{{position:absolute;left:0;top:0;width:{W}px;height:1010px;}}
#qbg{{position:absolute;inset:0;overflow:hidden;
  -webkit-mask-image:linear-gradient(to bottom,#000 0%,#000 84%,transparent 100%);mask-image:linear-gradient(to bottom,#000 0%,#000 84%,transparent 100%);}}
#qshade{{position:absolute;inset:0;background:linear-gradient(to bottom,rgba(20,14,14,.82),rgba(20,14,14,.6) 70%,rgba(20,14,14,0));}}
#qbox{{position:absolute;left:70px;top:230px;width:950px;}}
#qk{{margin-bottom:34px;}}
.q{{display:flex;align-items:baseline;gap:22px;margin-bottom:34px;}}
.qn{{font-family:'Cormorant Garamond';font-style:italic;font-weight:600;font-size:70px;color:var(--rose);width:84px;flex:none;}}
.qt{{font-family:'Playfair Display';font-weight:700;font-size:60px;line-height:1.15;color:var(--ink);}}
.qt em{{font-family:'Cormorant Garamond';font-style:italic;font-weight:600;font-size:76px;color:var(--rose);}}
#endc{{position:absolute;inset:0;}}
#endbg{{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 40%,rgba(58,34,32,.94),rgba(20,14,14,.98));}}
#endtxt{{position:absolute;left:0;top:640px;width:{W}px;text-align:center;}}
#endtxt h2{{font-family:'Playfair Display';font-weight:700;font-size:84px;line-height:1.1;color:var(--ink);}}
#endtxt h2 em{{font-family:'Cormorant Garamond';font-style:italic;font-weight:600;font-size:104px;color:var(--rose);}}
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
print("total", TOTAL, "groups", len(groups))
