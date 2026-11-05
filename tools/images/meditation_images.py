#!/usr/bin/env python3
import sys
import random, math, subprocess, os
import numpy as np
from PIL import Image


K = "#131217"      # outline black
W = "#f6f5fb"      # white
L1 = "#d2ceee"     # light lavender
L2 = "#aaa4da"     # lavender
L3 = "#7e77c2"     # mid purple
D = "#433d86"      # deep purple
G = "#86c76f"      # green
Y = "#f1dc72"      # yellow
SW = 13            # stroke width

def svg(body, defs=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
<defs>{defs}</defs>
<g stroke-linejoin="round" stroke-linecap="round">{body}</g></svg>'''

def stars(n, box, seed, color=W, rmax=7):
    r = random.Random(seed)
    x0, y0, x1, y1 = box
    out = []
    for _ in range(n):
        rad = r.choice([1.5, 2, 2, 2.5, 3, 3, 4, 5, rmax])
        out.append(f'<circle cx="{r.uniform(x0,x1):.1f}" cy="{r.uniform(y0,y1):.1f}" r="{rad}" fill="{color}"/>')
    return "".join(out)

def sparkle(x, y, s, fill=W, stroke=True):
    d = f"M{x} {y-s} Q{x} {y} {x+s} {y} Q{x} {y} {x} {y+s} Q{x} {y} {x-s} {y} Q{x} {y} {x} {y-s}Z"
    st = f'stroke="{K}" stroke-width="{SW*0.6}"' if stroke else ""
    return f'<path d="{d}" fill="{fill}" {st}/>'

def cloud(circles, fill, extra_rect=None, sw=SW):
    s = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{K}" stroke-width="{sw}"/>' for x, y, r in circles)
    f = "".join(f'<circle cx="{x}" cy="{y}" r="{r-sw/2+0.5}" fill="{fill}"/>' for x, y, r in circles)
    if extra_rect:
        x, y, w, h = extra_rect
        s += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{K}" stroke-width="{sw}"/>'
        f += f'<rect x="{x+sw/2}" y="{y-1}" width="{w-sw}" height="{h}" fill="{fill}"/>'
    return s + f

def rays(cx, cy, n, r0, r1, width, fill=W, start=0, span=360, opacity=1):
    out = []
    for i in range(n):
        a = math.radians(start + span * (i + 0.5) / n)
        x0, y0 = cx + r0 * math.cos(a), cy + r0 * math.sin(a)
        x1, y1 = cx + r1 * math.cos(a), cy + r1 * math.sin(a)
        out.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{fill}" stroke-width="{width}" opacity="{opacity}"/>')
    return "".join(out)

def radial(id_, stops, cx="50%", cy="50%", r="50%"):
    s = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return f'<radialGradient id="{id_}" cx="{cx}" cy="{cy}" r="{r}">{s}</radialGradient>'

def linear(id_, stops, vertical=True):
    s = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    xy = 'x1="0" y1="0" x2="0" y2="1"' if vertical else 'x1="0" y1="0" x2="1" y2="0"'
    return f'<linearGradient id="{id_}" {xy}>{s}</linearGradient>'

def tulip(x, y, s=1.0, fill=L2):
    stem = f'<path d="M{x} {y} L{x} {y+60*s}" stroke="{G}" stroke-width="{10*s}" fill="none"/>'
    lf = f'<path d="M{x} {y+45*s} Q{x-30*s} {y+25*s} {x-34*s} {y+50*s} Q{x-15*s} {y+60*s} {x} {y+50*s}Z" fill="{G}"/>'
    rf = f'<path d="M{x} {y+45*s} Q{x+30*s} {y+25*s} {x+34*s} {y+50*s} Q{x+15*s} {y+60*s} {x} {y+50*s}Z" fill="{G}"/>'
    head = (f'<path d="M{x-26*s} {y-28*s} L{x-13*s} {y-14*s} L{x} {y-34*s} L{x+13*s} {y-14*s} L{x+26*s} {y-28*s} '
            f'Q{x+30*s} {y+2*s} {x} {y+4*s} Q{x-30*s} {y+2*s} {x-26*s} {y-28*s}Z" fill="{fill}"/>')
    return stem + lf + rf + head

def daisy(x, y, r, fill=L2):
    out = []
    for i in range(8):
        a = i * 45
        out.append(f'<ellipse cx="{x}" cy="{y - r*0.62}" rx="{r*0.32}" ry="{r*0.45}" transform="rotate({a} {x} {y})" fill="{fill}" stroke="{K}" stroke-width="{SW*0.5}"/>')
    out.append(f'<circle cx="{x}" cy="{y}" r="{r*0.3}" fill="{W}" stroke="{K}" stroke-width="{SW*0.5}"/>')
    out.append(f'<circle cx="{x}" cy="{y}" r="{r*0.1}" fill="{K}"/>')
    return "".join(out)

def leaf(x, y, ang, s=1.0, fill=L2):
    d = f"M0 0 Q{60*s} {-55*s} {150*s} 0 Q{60*s} {55*s} 0 0Z"
    veins = "".join(f'<path d="M{v*s} 0 L{(v+22)*s} {sgn*24*s}" stroke="{K}" stroke-width="{SW*0.45}" fill="none"/>'
                    for v in (30, 60, 90) for sgn in (-1, 1))
    mid = f'<path d="M{8*s} 0 L{135*s} 0" stroke="{K}" stroke-width="{SW*0.5}" fill="none"/>'
    return (f'<g transform="translate({x} {y}) rotate({ang})"><path d="{d}" fill="{fill}" stroke="{K}" stroke-width="{SW*0.8}"/>'
            f'{mid}{veins}</g>')


P1, P2, P3 = "#f6d3e3", "#eaa9c9", "#c97fae"   # pembe tonlar (pink-haze)
DK = "#2a2560"                                 # koyu mor

scenes = {}

# 1. velvet — draped velvet curtains framing a moon, plush cushion with tassels
defs = (radial("g", [(0, L1), (0.4, L3), (1, DK)], cy="38%", r="75%") +
        linear("cv", [(0, "#8f88d0"), (0.5, D), (1, DK)], vertical=False) +
        linear("cv2", [(0, DK), (0.5, D), (1, "#8f88d0")], vertical=False) +
        radial("cu", [(0, "#a39de0"), (0.6, L3), (1, D)], cy="35%"))
b = f'<rect width="1024" height="1024" fill="url(#g)"/>' + stars(200, (0, 0, 1024, 1024), 41)
b += f'<circle cx="512" cy="330" r="130" fill="{W}" stroke="{K}" stroke-width="{SW}"/>'
b += f'<circle cx="470" cy="300" r="18" fill="{L1}"/><circle cx="560" cy="360" r="12" fill="{L1}"/><circle cx="545" cy="280" r="8" fill="{L1}"/>'
for sx, sy, s in [(300, 200, 22), (724, 210, 24), (512, 120, 16), (330, 480, 14), (700, 470, 16)]:
    b += sparkle(sx, sy, s)
# curtains
left = "M-20 -20 L300 -20 C250 200 210 380 250 600 C270 720 220 820 170 1044 L-20 1044Z"
right = "M1044 -20 L724 -20 C774 200 814 380 774 600 C754 720 804 820 854 1044 L1044 1044Z"
b += f'<path d="{left}" fill="url(#cv)" stroke="{K}" stroke-width="{SW}"/>'
b += f'<path d="{right}" fill="url(#cv2)" stroke="{K}" stroke-width="{SW}"/>'
for x0, curve in [(60, 40), (140, 30), (220, 20)]:
    b += f'<path d="M{x0} 0 C{x0-curve} 300 {x0+curve} 650 {x0-curve*1.5} 1024" stroke="{K}" stroke-width="{SW*0.6}" fill="none"/>'
    b += f'<path d="M{x0+24} 40 C{x0-curve+24} 300 {x0+curve+24} 600 {x0-curve*1.5+30} 980" stroke="{L2}" stroke-width="7" fill="none" opacity="0.8"/>'
    xr = 1024 - x0
    b += f'<path d="M{xr} 0 C{xr+curve} 300 {xr-curve} 650 {xr+curve*1.5} 1024" stroke="{K}" stroke-width="{SW*0.6}" fill="none"/>'
    b += f'<path d="M{xr-24} 40 C{xr+curve-24} 300 {xr-curve-24} 600 {xr+curve*1.5-30} 980" stroke="{L2}" stroke-width="7" fill="none" opacity="0.8"/>'
# tiebacks
for x, sg in [(240, 1), (784, -1)]:
    b += f'<path d="M{x-sg*170} 600 C{x-sg*80} 640 {x} 630 {x+sg*20} 600" stroke="{W}" stroke-width="20" fill="none"/>'
    b += f'<path d="M{x-sg*170} 600 C{x-sg*80} 640 {x} 630 {x+sg*20} 600" stroke="{K}" stroke-width="{SW*0.5}" fill="none" opacity="0.6"/>'
# velvet cushion
cush = "M260 820 C250 740 330 700 512 700 C694 700 774 740 764 820 C774 900 694 940 512 940 C330 940 250 900 260 820Z"
b += f'<ellipse cx="512" cy="960" rx="320" ry="40" fill="{DK}" opacity="0.6"/>'
b += f'<path d="{cush}" fill="url(#cu)" stroke="{K}" stroke-width="{SW}"/>'
b += f'<path d="M330 760 C420 730 600 730 690 760" stroke="{W}" stroke-width="10" fill="none" opacity="0.85"/>'
b += f'<path d="M300 820 C400 800 624 800 724 820" stroke="{K}" stroke-width="{SW*0.5}" fill="none" opacity="0.6"/>'
b += f'<circle cx="512" cy="820" r="16" fill="{L1}" stroke="{K}" stroke-width="{SW*0.6}"/>'
scenes["velvet"] = svg(b, defs)

# 2. tide — the moon pulling curling waves
defs = radial("g", [(0, W), (0.25, L1), (1, D)], cy="18%", r="85%")
b = f'<rect width="1024" height="1024" fill="url(#g)"/>' + stars(160, (0, 0, 1024, 520), 12)
b += f'<circle cx="512" cy="200" r="120" fill="{W}" stroke="{K}" stroke-width="{SW}"/>'
b += f'<circle cx="470" cy="175" r="18" fill="{L1}"/><circle cx="555" cy="235" r="12" fill="{L1}"/>'
for rr in (165, 215):
    b += f'<circle cx="512" cy="200" r="{rr}" fill="none" stroke="{W}" stroke-width="7" stroke-dasharray="4 22"/>'
bands = [(470, 40, 0.0, L1), (580, 46, 1.3, L2), (700, 52, 2.4, L3), (830, 58, 0.7, D)]
for y, A, ph, fill in bands:
    pts = [(x, y + A * math.sin(x / 1024 * 2 * math.pi * 2 + ph)) for x in range(-20, 1050, 6)]
    d = f"M-20 1060 " + " ".join(f"L{x} {yy:.1f}" for x, yy in pts) + " L1050 1060Z"
    b += f'<path d="{d}" fill="{fill}" stroke="{K}" stroke-width="{SW}"/>'
    fp = " ".join(f"L{x} {yy+30:.1f}" for x, yy in pts)
    b += f'<path d="M-20 {pts[0][1]+30:.1f} {fp}" stroke="{W}" stroke-width="8" fill="none" stroke-dasharray="70 40"/>'
    for k in range(5):
        xc = (((math.pi / 2 - ph) / (2 * math.pi * 2) + k / 2) * 1024) - 1024
        yc = y - A
        for j, dx in enumerate((-40, -14, 14, 40)):
            b += f'<circle cx="{xc+dx:.0f}" cy="{yc+14+abs(dx)*0.25:.0f}" r="{9-j%2*3}" fill="{W}"/>'
scenes["tide"] = svg(b, defs)

# 2. one-point — a single candle flame (trataka focus)
defs = (radial("g", [(0, L2), (0.35, D), (1, K)], cy="40%", r="80%") +
        radial("fl", [(0, W), (0.5, "#fbf0c8"), (1, Y)], cy="65%") +
        linear("cd", [(0, W), (1, L1)], vertical=False))
b = f'<rect width="1024" height="1024" fill="url(#g)"/>' + stars(260, (0, 0, 1024, 1024), 42)
for rr, op in [(110, 1), (170, 0.8), (240, 0.6), (320, 0.4), (410, 0.25)]:
    b += f'<circle cx="512" cy="360" r="{rr}" fill="none" stroke="{W}" stroke-width="8" opacity="{op}"/>'
b += f'<path d="M512 220 C470 300 455 350 470 395 C482 430 542 430 554 395 C569 350 554 300 512 220Z" fill="url(#fl)" stroke="{K}" stroke-width="{SW}"/>'
b += f'<path d="M512 320 C496 350 492 375 500 395 C506 408 518 408 524 395 C532 375 528 350 512 320Z" fill="{W}"/>'
b += f'<path d="M512 400 L512 450" stroke="{K}" stroke-width="8"/>'
b += f'<rect x="420" y="450" width="184" height="330" rx="10" fill="url(#cd)" stroke="{K}" stroke-width="{SW}"/>'
b += f'<path d="M420 470 C440 500 460 480 470 520 C478 550 490 530 492 470" fill="{W}" stroke="{K}" stroke-width="{SW*0.6}"/>'
b += f'<path d="M560 470 C566 510 580 500 584 540 L590 470Z" fill="{W}" stroke="{K}" stroke-width="{SW*0.6}"/>'
b += f'<path d="M445 520 L445 750" stroke="{W}" stroke-width="12"/>'
b += f'<ellipse cx="512" cy="800" rx="200" ry="40" fill="{L3}" stroke="{K}" stroke-width="{SW}"/>'
b += f'<ellipse cx="512" cy="785" rx="160" ry="26" fill="{L2}" stroke="{K}" stroke-width="{SW*0.8}"/>'
b += f'<path d="M-20 900 C250 840 774 840 1044 900 L1044 1044 L-20 1044Z" fill="{K}"/>'
r = random.Random(43)
for x in range(40, 1024, 80):
    if 300 < x < 724:
        continue
    b += tulip(x + r.uniform(-12, 12), 960 + r.uniform(-10, 10), 0.9, r.choice([L2, L1]))
for sx, sy, s in [(200, 200, 22), (830, 230, 24), (160, 620, 16), (870, 620, 18)]:
    b += sparkle(sx, sy, s)
scenes["one_point"] = svg(b, defs)

# 4. singing-bowl — bowl on a cushion with sound rings
defs = radial("g", [(0, L1), (0.5, L3), (1, D)], cy="55%", r="75%") + linear("bw", [(0, L2), (1, L3)])
b = f'<rect width="1024" height="1024" fill="url(#g)"/>' + stars(200, (0, 0, 1024, 1024), 14)
for i, (rx, ry) in enumerate([(300, 90), (380, 125), (460, 160), (540, 195)]):
    b += f'<path d="M{512-rx} 540 A{rx} {ry} 0 0 1 {512+rx} 540" fill="none" stroke="{W}" stroke-width="10" opacity="{1-i*0.2}"/>'
for sx, sy, s in [(200, 260, 24), (830, 250, 26), (512, 150, 18), (150, 470, 14), (880, 470, 16)]:
    b += sparkle(sx, sy, s)
b += f'<ellipse cx="512" cy="860" rx="330" ry="80" fill="{L2}" stroke="{K}" stroke-width="{SW}"/>'
b += f'<ellipse cx="512" cy="830" rx="300" ry="70" fill="{L1}" stroke="{K}" stroke-width="{SW}"/>'
b += f'<path d="M260 820 Q512 870 764 820" stroke="{L2}" stroke-width="8" fill="none"/>'
b += f'<path d="M282 560 C290 760 410 830 512 830 C614 830 734 760 742 560Z" fill="url(#bw)" stroke="{K}" stroke-width="{SW}"/>'
b += f'<path d="M300 640 C380 690 644 690 724 640" stroke="{W}" stroke-width="8" fill="none"/>'
b += f'<path d="M318 690 C400 735 624 735 706 690" stroke="{L1}" stroke-width="6" fill="none"/>'
b += f'<path d="M330 600 C340 700 380 760 430 790" stroke="{L1}" stroke-width="14" fill="none" opacity="0.8"/>'
b += f'<ellipse cx="512" cy="560" rx="230" ry="50" fill="{D}" stroke="{K}" stroke-width="{SW}"/>'
b += f'<ellipse cx="512" cy="568" rx="196" ry="34" fill="{DK}"/>'
b += (f'<g transform="rotate(32 820 700)"><rect x="800" y="520" width="40" height="330" rx="20" fill="{W}" stroke="{K}" stroke-width="{SW}"/>'
      f'<rect x="796" y="520" width="48" height="80" rx="24" fill="{L3}" stroke="{K}" stroke-width="{SW}"/></g>')
scenes["singing_bowl"] = svg(b, defs)

# 3. shoreline — waves meeting the sand at sunset, shells
defs = (linear("g", [(0, L3), (0.5, L1), (0.62, W)]) + radial("sun", [(0, W), (0.7, "#fbf0c8"), (1, Y)]) +
        linear("sea", [(0, L2), (1, L3)]))
b = f'<rect width="1024" height="1024" fill="url(#g)"/>' + stars(70, (0, 0, 1024, 300), 44)
b += rays(512, 470, 11, 190, 330, 26, W, start=180, span=180)
b += f'<circle cx="512" cy="470" r="150" fill="url(#sun)" stroke="{K}" stroke-width="{SW}"/>'
b += cloud([(160, 200, 45), (215, 180, 58), (275, 202, 42)], W, (125, 202, 190, 42))
b += cloud([(760, 140, 38), (812, 122, 50), (866, 142, 36)], W, (730, 142, 170, 34))
b += f'<path d="M640 300 Q660 285 680 300 Q700 285 720 300" stroke="{K}" stroke-width="6" fill="none"/>'
b += f'<path d="M730 260 Q745 248 760 260 Q775 248 790 260" stroke="{K}" stroke-width="5" fill="none"/>'
b += f'<rect x="-20" y="470" width="1064" height="320" fill="url(#sea)" stroke="{K}" stroke-width="{SW}"/>'
for y, w in [(510, 280), (560, 340), (615, 300), (670, 360)]:
    b += f'<path d="M{512-w} {y} Q{512-w/2} {y-14} 512 {y} T{512+w} {y}" stroke="{W}" stroke-width="9" fill="none"/>'
# foam edge
foam = "M-20 740 " + " ".join(f"Q{x+32} {770 if i%2==0 else 735} {x+64} 752" for i, x in enumerate(range(-20, 1044, 64))) + " L1044 1044 L-20 1044Z"
b += f'<path d="{foam}" fill="{W}" stroke="{K}" stroke-width="{SW}"/>'
b += f'<path d="M-20 800 C200 770 400 820 600 790 C780 765 900 800 1044 785 L1044 1044 L-20 1044Z" fill="{L1}" stroke="{K}" stroke-width="{SW}"/>'
r = random.Random(45)
for _ in range(60):
    x, y = r.uniform(0, 1024), r.uniform(830, 1024)
    b += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r.choice([2,3,3,4])}" fill="{L3}"/>'
# starfish
st = []
for i in range(10):
    a = math.radians(-90 + i * 36)
    rr = 62 if i % 2 == 0 else 26
    st.append(f"{230 + rr*math.cos(a):.0f} {900 + rr*math.sin(a):.0f}")
b += f'<path d="M{" L".join(st)}Z" fill="{P2}" stroke="{K}" stroke-width="{SW*0.8}"/>'
for dx, dy in [(0, -30), (-20, 0), (20, 0), (-10, 22), (10, 22)]:
    b += f'<circle cx="{230+dx}" cy="{900+dy}" r="4" fill="{W}"/>'
# scallop shell
sx, sy = 770, 930
b += f'<path d="M{sx-70} {sy} C{sx-70} {sy-90} {sx+70} {sy-90} {sx+70} {sy} L{sx+20} {sy+30} L{sx-20} {sy+30}Z" fill="{W}" stroke="{K}" stroke-width="{SW*0.8}"/>'
for dx in (-48, -24, 0, 24, 48):
    b += f'<path d="M{sx} {sy+26} L{sx+dx*1.2} {sy-62+abs(dx)*0.5}" stroke="{K}" stroke-width="5"/>'
# spiral shell
b += f'<path d="M500 960 C470 920 520 880 560 900 C600 920 590 970 550 975 Z" fill="{L2}" stroke="{K}" stroke-width="{SW*0.7}"/>'
b += f'<path d="M545 955 C530 945 535 925 555 925" stroke="{K}" stroke-width="5" fill="none"/>'
scenes["shoreline"] = svg(b, defs)

# 6. wind-chimes — chimes hanging from a branch in the breeze
defs = radial("g", [(0, W), (0.35, L1), (1, L3)], cy="45%", r="75%")
b = f'<rect width="1024" height="1024" fill="url(#g)"/>' + stars(150, (0, 0, 1024, 1024), 16)
b += f'<path d="M-20 150 C200 110 400 160 600 120 C780 90 900 120 1044 80" stroke="{K}" stroke-width="34" fill="none"/>'
for (x, y, a, s, f) in [(150, 135, 160, 0.55, L2), (300, 140, 30, 0.6, L3), (700, 112, 150, 0.55, L2), (860, 105, 20, 0.6, L3), (950, 92, -30, 0.5, L1)]:
    b += leaf(x, y, a, s, f)
b += f'<path d="M512 134 L512 270" stroke="{K}" stroke-width="6"/>'
b += f'<path d="M512 140 L370 270 M512 140 L654 270" stroke="{K}" stroke-width="5"/>'
tubes = [(380, 300), (446, 380), (512, 440), (578, 380), (644, 300)]
for x, ln in tubes:
    b += f'<path d="M{x} 280 L{x} 320" stroke="{K}" stroke-width="5"/>'
    b += f'<rect x="{x-20}" y="320" width="40" height="{ln}" rx="12" fill="{W}" stroke="{K}" stroke-width="{SW*0.8}"/>'
    b += f'<path d="M{x-6} 340 L{x-6} {300+ln}" stroke="{L1}" stroke-width="8"/>'
b += f'<ellipse cx="512" cy="272" rx="170" ry="28" fill="{L3}" stroke="{K}" stroke-width="{SW}"/>'
b += f'<path d="M512 300 L512 800" stroke="{K}" stroke-width="5"/>'
b += f'<circle cx="512" cy="600" r="42" fill="{L2}" stroke="{K}" stroke-width="{SW*0.8}"/>'
b += f'<path d="M512 800 C470 850 470 900 512 950 C554 900 554 850 512 800Z" fill="{L2}" stroke="{K}" stroke-width="{SW}"/>'
b += f'<path d="M512 830 L512 925" stroke="{K}" stroke-width="5"/>'
for (x0, y0, w) in [(40, 520, 260), (720, 700, 280), (60, 860, 300), (690, 460, 250)]:
    b += f'<path d="M{x0} {y0} C{x0+w*0.3} {y0-30} {x0+w*0.6} {y0+30} {x0+w} {y0}" stroke="{W}" stroke-width="10" fill="none"/>'
    b += f'<path d="M{x0+40} {y0+34} C{x0+w*0.4} {y0+10} {x0+w*0.6} {y0+50} {x0+w-30} {y0+30}" stroke="{W}" stroke-width="7" fill="none" opacity="0.8"/>'
for sx, sy, s in [(230, 330, 18), (800, 260, 20), (250, 720, 14), (780, 880, 16)]:
    b += sparkle(sx, sy, s)
scenes["wind_chimes"] = svg(b, defs)

# 4. night-rain — rainy window with plants, tea and a candle on the sill
defs = linear("sky", [(0, K), (1, D)]) + linear("wall", [(0, L2), (1, L3)])
b = f'<rect width="1024" height="1024" fill="url(#wall)"/>' + stars(120, (0, 0, 1024, 1024), 46, L1)
b += f'<rect x="130" y="80" width="764" height="560" fill="url(#sky)" stroke="{K}" stroke-width="{SW}"/>'
b += stars(70, (140, 90, 884, 630), 47)
b += f'<circle cx="740" cy="190" r="56" fill="{W}" stroke="{K}" stroke-width="{SW*0.8}"/>'
b += f'<circle cx="766" cy="172" r="46" fill="{K}"/>'
b += cloud([(290, 190, 44), (345, 168, 58), (405, 190, 42)], L1, (248, 190, 198, 44))
b += cloud([(560, 280, 34), (600, 264, 44), (645, 282, 32)], L2, (528, 282, 148, 32))
r = random.Random(48)
for _ in range(60):
    x = r.uniform(150, 880); y = r.uniform(250, 600)
    b += f'<path d="M{x:.0f} {y:.0f} L{x-10:.0f} {y+40:.0f}" stroke="{L1}" stroke-width="6"/>'
for _ in range(14):
    x = r.uniform(170, 860); y = r.uniform(140, 600)
    b += f'<path d="M{x:.0f} {y:.0f} C{x+10:.0f} {y+14:.0f} {x+10:.0f} {y+24:.0f} {x:.0f} {y+26:.0f} C{x-10:.0f} {y+24:.0f} {x-10:.0f} {y+14:.0f} {x:.0f} {y:.0f}Z" fill="{L1}" stroke="{K}" stroke-width="4"/>'
b += f'<path d="M512 80 L512 640 M130 360 L894 360" stroke="{K}" stroke-width="{SW*1.6}"/>'
b += f'<rect x="90" y="630" width="844" height="44" fill="{W}" stroke="{K}" stroke-width="{SW}"/>'
b += f'<rect x="110" y="674" width="804" height="24" fill="{L1}" stroke="{K}" stroke-width="{SW*0.8}"/>'
# plant pot left
b += f'<path d="M180 510 L310 510 L290 632 L200 632Z" fill="{W}" stroke="{K}" stroke-width="{SW}"/>'
b += f'<path d="M180 530 L310 530" stroke="{K}" stroke-width="{SW*0.6}"/>'
for (x, y, a, s, f) in [(245, 510, -120, 0.75, G), (245, 510, -60, 0.8, G), (245, 510, -95, 0.95, "#a3d48f"), (245, 510, -150, 0.6, "#a3d48f"), (245, 510, -30, 0.6, G)]:
    b += leaf(x, y, a, s, f)
# mug
mx = 520
b += f'<path d="M{mx-60} 520 L{mx+60} 520 L{mx+52} 630 L{mx-52} 630Z" fill="{L2}" stroke="{K}" stroke-width="{SW}"/>'
b += f'<path d="M{mx+58} 545 C{mx+110} 545 {mx+110} 605 {mx+54} 605" stroke="{K}" stroke-width="{SW}" fill="none"/>'
b += f'<path d="M{mx-36} 545 L{mx-32} 610" stroke="{W}" stroke-width="9"/>'
b += f'<path d="M{mx-30} 590 C{mx-10} 570 {mx+10} 600 {mx+30} 580" stroke="{K}" stroke-width="5" fill="none"/>'
for dx in (-24, 6, 34):
    b += f'<path d="M{mx+dx} 500 C{mx+dx-16} 470 {mx+dx+16} 450 {mx+dx} 420" stroke="{W}" stroke-width="8" fill="none"/>'
# candle right
cx = 760
b += f'<rect x="{cx-36}" y="520" width="72" height="112" rx="6" fill="{W}" stroke="{K}" stroke-width="{SW}"/>'
b += f'<path d="M{cx} 520 L{cx} 500" stroke="{K}" stroke-width="6"/>'
b += f'<path d="M{cx} 438 C{cx-22} 470 {cx-22} 500 {cx} 504 C{cx+22} 500 {cx+22} 470 {cx} 438Z" fill="{Y}" stroke="{K}" stroke-width="{SW*0.7}"/>'
b += f'<circle cx="{cx}" cy="475" r="80" fill="{W}" opacity="0.18"/>'
# cozy knit blanket draped below
b += f'<path d="M-20 760 C200 720 420 780 600 750 C780 720 900 760 1044 740 L1044 1044 L-20 1044Z" fill="{D}" stroke="{K}" stroke-width="{SW}"/>'
for i in range(9):
    x = 40 + i * 120
    for j in range(4):
        y = 820 + j * 55
        b += f'<path d="M{x-25} {y} L{x} {y+26} L{x+25} {y}" stroke="{L2}" stroke-width="8" fill="none"/>'
scenes["night_rain"] = svg(b, defs)

# 5. pink-haze — layered misty pink hills under a soft sun
defs = (linear("g", [(0, P3), (0.45, P1), (0.7, W)]) + radial("sun", [(0, W), (0.7, "#fff1f6"), (1, P1)]))
b = f'<rect width="1024" height="1024" fill="url(#g)"/>' + stars(150, (0, 0, 1024, 500), 49)
b += rays(512, 430, 16, 200, 320, 20, W, opacity=0.9)
b += f'<circle cx="512" cy="430" r="150" fill="url(#sun)" stroke="{K}" stroke-width="{SW}"/>'
for sx, sy, s in [(170, 170, 24), (860, 190, 22), (512, 80, 16), (120, 420, 14), (900, 420, 16)]:
    b += sparkle(sx, sy, s)
b += cloud([(150, 300, 48), (208, 280, 60), (270, 302, 44)], W, (112, 302, 200, 44))
b += cloud([(760, 330, 42), (816, 310, 56), (876, 332, 40)], P1, (726, 332, 186, 40))
layers = [(560, 60, 0.4, P1), (650, 70, 1.6, P2), (750, 60, 2.6, "#d996c0"), (850, 55, 0.9, P3), (950, 45, 2.0, L3)]
for i, (y, A, ph, fill) in enumerate(layers):
    pts = [(x, y + A * math.sin(x / 1024 * 2 * math.pi * 1.3 + ph)) for x in range(-20, 1050, 8)]
    d = "M-20 1060 " + " ".join(f"L{x} {yy:.1f}" for x, yy in pts) + " L1050 1060Z"
    b += f'<path d="{d}" fill="{fill}" stroke="{K}" stroke-width="{SW}"/>'
    mist = " ".join(f"L{x} {yy+28:.1f}" for x, yy in pts)
    b += f'<path d="M-20 {pts[0][1]+28:.1f} {mist}" stroke="{W}" stroke-width="16" fill="none" opacity="0.55"/>'
r = random.Random(50)
for x in range(40, 1024, 90):
    b += tulip(x + r.uniform(-15, 15), 975 + r.uniform(-8, 8), 0.85, r.choice([P1, W, P2]))
scenes["pink_haze"] = svg(b, defs)


# Grenli doku (noktalı sprey efekti)
def grain(path):
    im = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    H, Wd, _ = im.shape
    rng = np.random.default_rng(sum(map(ord, os.path.basename(path))))
    lum = im.mean(axis=2)
    def up(k):
        n = rng.random((H // k + 1, Wd // k + 1))
        return np.kron(n, np.ones((k, k)))[:H, :Wd]
    n1, n2, n3 = rng.random((H, Wd)), up(2), up(3)
    dark = lum < 45
    light = lum > 225
    mid = ~dark & ~light
    white_sp = ((n1 > 0.965) | (n2 > 0.985)) & mid | ((n1 > 0.996) | (n3 > 0.9985)) & dark
    dark_sp = ((n1 < 0.035) | (n3 < 0.012)) & mid | ((n1 < 0.03) | (n2 < 0.008)) & light
    out = im.copy()
    out[white_sp] = out[white_sp] * 0.3 + np.array([250, 249, 255]) * 0.7
    out[dark_sp & mid] = out[dark_sp & mid] * 0.45 + np.array([45, 40, 95]) * 0.55
    sel = dark_sp & light
    out[sel] = out[sel] * 0.55 + np.array([150, 145, 205]) * 0.45
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(path, optimize=True)



def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "output"
    os.makedirs(out, exist_ok=True)
    for name, s in scenes.items():
        sp = os.path.join(out, f"{name}.svg")
        pp = os.path.join(out, f"{name.replace('_', '-')}.png")
        with open(sp, "w", encoding="utf-8") as f:
            f.write(s)
        subprocess.run(["rsvg-convert", "-w", "1024", "-h", "1024", sp, "-o", pp], check=True)
        grain(pp)
        os.remove(sp)
        print("✓", pp)


if __name__ == "__main__":
    main()
