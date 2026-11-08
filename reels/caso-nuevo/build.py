import subprocess, os
S = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920

# (src_start, src_end, zoom)  -- redundancies removed
SEG = [
    (0.40, 4.80, 1.00),   # Te voy a mostrar ... no he valorado
    (4.95, 9.80, 1.14),   # Lo primero ... entender el problema
    (10.00, 17.78, 1.00), # preguntas
    (17.90, 20.18, 1.14), # decido cómo trabajar
    (20.50, 27.12, 1.00), # ejemplo: ceja pelo a pelo, procedimiento mal realizado
    (27.30, 28.50, 1.14), # Aquí no podría trabajar
    (30.50, 32.04, 1.14), # la técnica que ella me está pidiendo
    (32.04, 32.80, 1.00), # porque
    (39.20, 40.72, 1.00), # tiene manchas en sus cejas
    (40.90, 44.95, 1.14), # Entonces, en este caso ... remover
    (50.10, 55.76, 1.00), # Antes de pensar ... a largo plazo
    (55.78, 58.30, 1.18), # No es nada más en el momento
]
outs, acc = [], 0.0
for a, b, z in SEG:
    outs.append(acc); acc += b - a
TOTAL = acc

def m(t, hint=None):
    """map source time -> output time"""
    for i, (a, b, z) in enumerate(SEG):
        if hint is not None and i != hint: continue
        if a - 0.05 <= t <= b + 0.05:
            return outs[i] + min(max(t, a), b) - a
    raise ValueError(t)

ROSE = "&HBCC4F2&"   # BGR of #D99B8C (blush/rose from the set)
CREAM = "&HF6F8FB&"
def k(word):  # keyword: italic, rose
    return r"{\i1\c" + ROSE + "}" + word + r"{\i0\c" + CREAM + "}"

# captions: (src_start, src_end, text, seg_hint_start, seg_hint_end)
CAP = [
    (0.50, 2.08, "Te voy a mostrar " + k("cómo pienso")),
    (2.08, 3.82, "cuando me llega un " + k("caso nuevo")),
    (3.82, 4.75, "que no he valorado"),
    (5.02, 6.04, "Lo primero que hago"),
    (6.04, 7.85, "es dejar de pensar en la " + k("técnica")),
    (7.96, 9.75, "Primero quiero " + k("entender el problema")),
    (10.12, 11.10, "¿Qué tiene esta persona?"),
    (11.34, 12.50, "¿Qué " + k("puedo") + " modificar?"),
    (12.64, 14.05, "¿Qué " + k("no puedo") + " modificar?"),
    (14.28, 15.95, "¿Qué resultado sería " + k("realista")),
    (15.95, 17.75, "según lo que me está pidiendo?"),
    (17.98, 20.15, "Después decido " + k("cómo trabajar")),
    (20.60, 21.05, "Por ejemplo:"),
    (21.10, 23.26, "quiere una ceja " + k("pelo a pelo")),
    (23.26, 24.70, "pero tiene un procedimiento anterior"),
    (24.70, 27.10, k("mal realizado") + " en otro sitio"),
]
# captions that straddle cuts: given directly in output time
def seg_t(i, src):
    return m(src, i)
CAP_OUT = [(m(t0), m(t1), txt) for t0, t1, txt in CAP]
CAP_OUT += [
    (seg_t(5, 27.38), seg_t(6, 32.04), "Aquí no podría trabajar la técnica que me pide"),
    (seg_t(7, 32.04), seg_t(8, 40.70), "porque tiene " + k("manchas") + " en sus cejas"),
    (seg_t(9, 41.00), seg_t(9, 41.85), "En este caso,"),
    (seg_t(9, 41.90), seg_t(9, 43.65), "para un resultado " + k("realista")),
    (seg_t(9, 43.70), seg_t(9, 44.95), "tendría que " + k("remover")),
    (seg_t(10, 50.20), seg_t(10, 51.70), "Antes de pensar en cualquier técnica"),
    (seg_t(10, 51.82), seg_t(10, 54.04), "pienso cómo " + k("solucionar")),
    (seg_t(10, 54.04), seg_t(10, 55.76), "este problema " + k("a largo plazo")),
    (seg_t(11, 55.82), seg_t(11, 57.95), "No solo " + k("en el momento")),
]

# b-roll inserts (output start, output end, image)
BROLL = [
    (m(7.96), m(11.10), "img/u4.jpg"),   # entender el problema
    (m(21.80), m(24.65), "img/u6.jpg"),  # ceja pelo a pelo
    (seg_t(5, 27.32), seg_t(6, 32.04), "img/u1.jpg"),  # procedimiento / técnica que pide
    (seg_t(9, 41.90), seg_t(9, 44.95), "img/u8.jpg"),  # resultado realista
]

def ts(t):
    t = max(t, 0)
    h = int(t // 3600); mi = int(t % 3600 // 60); s = t % 60
    return f"{h}:{mi:02d}:{s:05.2f}"

ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Playfair Display SemiBold,76,&H00F6F8FB,&H00FFFFFF,&H28140C0A,&H50140C0A,0,0,0,0,100,100,0,0,1,3.2,6,2,90,90,540,1
Style: Kicker,Montserrat Thin SemiBold,34,&H00E6EDF6,&H00FFFFFF,&H64140C0A,&H78140C0A,0,0,0,0,100,100,9,0,1,1.2,3,8,80,80,190,1
Style: Title,Playfair Display SemiBold,84,&H00E6EDF6,&H00FFFFFF,&H50140C0A,&H78140C0A,0,0,0,0,100,100,0,0,1,2.4,6,8,90,90,240,1
Style: End,Playfair Display SemiBold,78,&H00E6EDF6,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,90,90,0,1
Style: EndS,Montserrat Thin SemiBold,36,&H00BCC4F2,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,10,0,1,0,0,5,90,90,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
CREAM_RESET = r"{\c" + CREAM + "}"
for a, b, txt in sorted(CAP_OUT):
    pop = r"{\fad(90,60)\fscx92\fscy92\t(0,140,\fscx100\fscy100)}"
    ass += f"Dialogue: 1,{ts(a)},{ts(b)},Cap,,0,0,0,,{pop}{CREAM_RESET}{txt}\n"
# hook title (first ~4.4s)
ass += f"Dialogue: 2,{ts(0.15)},{ts(4.6)},Kicker,,0,0,0,,{{\\fad(300,250)\\c{ROSE}}}MICROBLADING  ·  CRITERIO PROFESIONAL\n"
ass += f"Dialogue: 2,{ts(0.25)},{ts(4.6)},Title,,0,0,0,,{{\\fad(350,250)\\blur0.6}}Cómo pienso ante\\N{{\\i1\\c{ROSE}}}un caso nuevo\n"
# end card
END = 2.6
ass += f"Dialogue: 3,{ts(TOTAL+0.2)},{ts(TOTAL+END)},End,,0,0,0,,{{\\fad(400,0)\\pos(540,880)}}Primero el problema.\\N{{\\i1\\c{ROSE}}}Después la técnica.\n"
ass += f"Dialogue: 3,{ts(TOTAL+0.6)},{ts(TOTAL+END)},EndS,,0,0,0,,{{\\fad(400,0)\\pos(540,1110)}}GUARDA ESTE VIDEO PARA TU PRÓXIMA VALORACIÓN\n"
ass += f"Dialogue: 3,{ts(TOTAL+0.9)},{ts(TOTAL+END)},EndS,,0,0,0,,{{\\fad(400,0)\\pos(540,1180)\\c{CREAM}}}@daymabeauty\n"
open(f"{S}/subs.ass", "w").write(ass)

# ---------- filter graph ----------
f = []
n = len(SEG)
for i, (a, b, z) in enumerate(SEG):
    sw, sh = int(W * z) // 2 * 2, int(H * z) // 2 * 2
    # crop biased slightly upward to keep face framed when punched in
    f.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,scale={sw}:{sh}:flags=lanczos,"
             f"crop={W}:{H}:(iw-{W})/2:(ih-{H})*0.35,setsar=1,fps=30[v{i}]")
    d = b - a
    f.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={d-0.03:.3f}:d=0.03[a{i}]")
f.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac]")
# warm, soft grade in line with the set (rosy/warm)
f.append("[vc]eq=contrast=1.04:saturation=1.06:gamma=0.98,colorbalance=rs=0.02:bs=-0.02:rh=0.02,"
         f"vignette=PI/5,tpad=stop_mode=clone:stop_duration={END}[vg]")

inputs = ["-i", f"{S}/in.mp4"]
cur = "vg"
for j, (a, b, img) in enumerate(BROLL):
    idx = j + 1
    dur = b - a
    inputs += ["-loop", "1", "-t", f"{dur + 0.1:.2f}", "-i", f"{S}/{img}"]
    # cover-fit, slow Ken Burns push-in, grade, fade
    if img.endswith(("u6.jpg",)):
        f.append(f"[{idx}:v]fps=30,split[bg{j}][fg{j}];"
                 f"[bg{j}]scale=-2:{H}:flags=bicubic,crop={W}:{H},gblur=sigma=40,eq=brightness=-0.12[bgb{j}];"
                 f"[fg{j}]scale={W}:-2,pad={W}:ih+8:0:4:color=0xF2C4BC[fgp{j}];"
                 f"[bgb{j}][fgp{j}]overlay=0:(H-h)/2-120[im{j}]")
        src = f"[im{j}]"
    else:
        f.append(f"[{idx}:v]fps=30[im{j}]"); src = f"[im{j}]"
    f.append(f"{src}scale={W*1.25:.0f}:{H*1.25:.0f}:force_original_aspect_ratio=increase,crop={W*1.25:.0f}:{H*1.25:.0f},"
             f"zoompan=z='1+0.09*on/({dur*30:.0f})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps=30,"
             f"eq=contrast=1.03:saturation=0.95,colorbalance=rs=0.03:bs=-0.01,vignette=PI/5,format=yuva420p,"
             f"fade=t=in:st=0:d=0.18:alpha=1,fade=t=out:st={dur-0.18:.2f}:d=0.18:alpha=1,setpts=PTS-STARTPTS+{a:.3f}/TB[b{j}]")
    f.append(f"[{cur}][b{j}]overlay=0:0:eof_action=pass:enable='between(t,{a:.3f},{b:.3f})'[o{j}]")
    cur = f"o{j}"
# end card darkening
f.append(f"[{cur}]drawbox=x=0:y=0:w=iw:h=ih:color=0x0A0C14@0.78:t=fill:enable='gte(t,{TOTAL:.3f})',"
         f"ass={S}/subs.ass:fontsdir={S}/fd,format=yuv420p[vout]")
f.append(f"[ac]apad=pad_dur={END},loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[aout]")

open(f"{S}/graph.txt", "w").write(";\n".join(f))
out = f"{S}/reel_final.mp4"
cmd = ["ffmpeg", "-y", "-v", "error", "-stats"] + inputs + ["-filter_complex_script", f"{S}/graph.txt",
       "-map", "[vout]", "-map", "[aout]", "-t", f"{TOTAL+END:.2f}",
       "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
print(f"total {TOTAL:.2f}s + end {END}s")
subprocess.run(cmd, check=True)
