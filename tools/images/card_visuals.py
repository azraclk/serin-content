"""Serin ses kartlarının piksel-art görselleri. Hepsi bu betikle, kodla çizilir; görüntü modeli kullanılmaz.
Çıktı: 1024x1024 kare, kayıpsız WebP, images/meditations/<kart>.webp.

Çizim blog_visuals.py'nin yardımcılarını (palet, ordered dither, parıltı, bulut) kullanır; ızgarayı 128x128'e
alıp 8 kat büyütür. Kartlar uygulamada geniş yatay, dikey ve daire olarak kırpılır; bu yüzden konu hep ortadaki
yaklaşık 80x68'lik (piksel ızgarasında) alana sığar, kenarlar yalnızca zemindir.

Kullanım (repo kökünden):
    pip install pillow numpy
    python -P tools/images/card_visuals.py                        # images/meditations/ altına yazar
    python -P tools/images/card_visuals.py build/cards --preview  # önizleme sayfası da yazar
"""
import importlib.util
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("blog_visuals", os.path.join(HERE, "blog_visuals.py"))
bv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bv)

N, S = 128, 8
C = bv.C
CX = CY = N // 2


def use_grid(n=N, s=S):
    """blog_visuals'ın yardımcıları ızgara boyutunu modül düzeyinde tutar; kare ızgaraya geçirir."""
    bv.W = bv.H = n
    bv.S = s
    bv.Y, bv.X = np.mgrid[0:n, 0:n]
    bv.BX = bv.B[bv.Y % 4, bv.X % 4]


def mask_fill(a, mask, c):
    a[mask] = C[c] if isinstance(c, str) else c


def circle(cx, cy, r):
    return (bv.X - cx) ** 2 + (bv.Y - cy) ** 2 <= r * r


def wave_polygon(top, amp, period, phase, bottom=N + 2):
    """Üst kenarı sinüs olan, altı tuvalin dışına inen çokgen."""
    pts = [(x, top + amp * math.sin(x / period + phase)) for x in range(-2, N + 3, 2)]
    return pts + [(N + 2, bottom), (-2, bottom)]


def rings(a, cx, cy, radii, colors, width=1):
    for i, r in enumerate(radii):
        c = colors[i % len(colors)]
        bv.paint(a, lambda d, r=r: d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=255, width=width), c)


# --- sahneler -------------------------------------------------------------------------------------------------

def s_velvet():
    """Kadife: gece gökyüzünde hilal, altta üst üste binen yumuşak kumaş kıvrımları."""
    a = bv.base(['night', 'indigo', 'violet', 'purple'], 0.0, 0.55, (CX, 44, 34, 0.55))
    bv.stars(a, 34, 11, ymax=60)
    moon = circle(CX, 44, 17) & ~circle(CX + 8, 38, 14)
    mask_fill(a, moon, 'pale')
    for x, y in [(54, 46), (56, 52), (52, 40)]:
        bv.px(a, x, y, 'lav2')
    for x, y in [(78, 30), (84, 52)]:
        bv.sparkle(a, x, y, 'warm')
    folds = [(70, 'indigo', 5.0, 0.0), (80, 'violet', 5.5, 1.4), (90, 'purple', 6.0, 2.6),
             (101, 'lav', 6.5, 0.7), (113, 'lav2', 7.0, 2.0)]
    for top, c, amp, ph in folds:
        bv.paint(a, lambda d, top=top, amp=amp, ph=ph: d.polygon(wave_polygon(top, amp, 11, ph), fill=255), c)
        # kıvrımın üst kenarına ince bir parlama
        for x in range(N):
            y = int(round(top + amp * math.sin(x / 11 + ph)))
            if (x // 2) % 2 == 0:
                bv.px(a, x, y, 'pale' if c in ('lav', 'lav2') else 'lav')
    return a


def s_tide():
    """Gelgit: ay, halka halka yükselip çekilen su bantları."""
    a = bv.base(['night', 'indigo', 'violet', 'purple'], 0.0, 0.45, (CX, 44, 30, 0.7))
    bv.stars(a, 26, 12, ymax=44)
    rings(a, CX, 44, [11, 16, 21], ['lav2', 'lav', 'purple'], 1)
    mask_fill(a, circle(CX, 44, 8), 'pale')
    mask_fill(a, circle(CX, 44, 6), 'white')
    mask_fill(a, circle(CX, 44, 3), 'warm')
    bands = [(68, 'violet', 2.0, 0.0), (77, 'purple', 3.5, 1.1), (87, 'lav', 4.5, 2.3),
             (98, 'lav2', 5.5, 0.4), (110, 'pale', 6.5, 1.8)]
    for top, c, amp, ph in bands:
        bv.paint(a, lambda d, top=top, amp=amp, ph=ph: d.polygon(wave_polygon(top, amp, 7, ph), fill=255), c)
    # ayın suda yansıması
    for i, y in enumerate(range(70, 104, 3)):
        w = 8 - i // 2
        if w > 0:
            bv.paint(a, lambda d, y=y, w=w: d.line((CX - w, y, CX + w, y), fill=255), 'white' if i % 2 == 0 else 'lav2')
    return a


def s_one_point():
    """Tek Nokta: tek bir ışık noktası ve ona doğru daralan halkalar."""
    a = bv.base(['night', 'indigo', 'violet', 'purple'], 0.05, 0.3, (CX, CY, 44, 0.75))
    bv.stars(a, 30, 13, ymax=N)
    rings(a, CX, CY, [34, 28, 22, 16, 11, 7], ['purple', 'lav', 'lav2', 'pale', 'white', 'white'], 1)
    for k in range(16):
        ang = math.radians(k * 22.5)
        r0, r1 = (38, 56) if k % 2 else (38, 48)
        bv.paint(a, lambda d, ang=ang, r0=r0, r1=r1: d.line(
            (CX + r0 * math.cos(ang), CY + r0 * math.sin(ang), CX + r1 * math.cos(ang), CY + r1 * math.sin(ang)),
            fill=255), 'violet')
    mask_fill(a, circle(CX, CY, 4), 'white')
    mask_fill(a, circle(CX, CY, 2), 'warm')
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        for k in (5, 6):
            bv.px(a, CX + dx * k, CY + dy * k, 'warm')
    return a


def s_singing_bowl():
    """Ses Kasesi: minder üstünde kase, çıkan halkalar, tokmak."""
    a = bv.base(['night', 'indigo', 'violet', 'purple', 'lav'], 0.05, 0.6, (CX, 62, 34, 0.55))
    bv.stars(a, 22, 14, ymax=38)
    for r, c in [(46, 'lav'), (40, 'lav2'), (34, 'pale')]:
        bv.paint(a, lambda d, r=r: d.arc((CX - r, 58 - r, CX + r, 58 + r), 215, 325, fill=255, width=1), c)
    bv.paint(a, lambda d: d.ellipse((34, 90, 94, 108), fill=255), 'indigo')       # minder
    bv.paint(a, lambda d: d.ellipse((38, 88, 90, 100), fill=255), 'violet')
    bv.paint(a, lambda d: d.pieslice((36, 52, 92, 96), 0, 180, fill=255), 'purple')  # kasenin gövdesi
    bv.paint(a, lambda d: d.pieslice((40, 58, 88, 96), 0, 180, fill=255), 'lav')
    bv.paint(a, lambda d: d.pieslice((46, 70, 66, 92), 20, 160, fill=255), 'lav2')    # parlama
    bv.paint(a, lambda d: d.ellipse((36, 48, 92, 64), fill=255), 'pale')             # ağız
    bv.paint(a, lambda d: d.ellipse((39, 50, 89, 62), fill=255), 'indigo')           # kasenin içi
    bv.paint(a, lambda d: d.ellipse((44, 52, 84, 60), fill=255), 'night')
    bv.paint(a, lambda d: d.line((106, 34, 94, 49), fill=255, width=2), 'warm')      # tokmak
    bv.paint(a, lambda d: d.ellipse((89, 46, 96, 53), fill=255), 'peach')
    for x, y in [(30, 44), (100, 70), (24, 72), (64, 30)]:
        bv.sparkle(a, x, y, 'warm', False)
    return a


def s_shoreline():
    """Kıyı: ufuk, deniz bantları, köpük ve ıslak kum."""
    a = bv.base(['purple', 'lav', 'lav2', 'pale', 'white'], 0.1, 0.62, (CX, 40, 34, 0.45))
    mask_fill(a, circle(CX, 46, 11), 'warm')
    mask_fill(a, circle(CX, 46, 8), 'white')
    bv.paint(a, lambda d: d.rectangle((0, 56, N, N), fill=255), 'lav')               # deniz
    for top, c in [(60, 'purple'), (68, 'violet')]:
        bv.paint(a, lambda d, top=top: d.rectangle((0, top, N, top + 4), fill=255), c)
    r = random.Random(21)
    for _ in range(26):                                                              # ışıltı çizgileri
        x, y, ln = r.randrange(20, 108), r.randrange(57, 80), r.randrange(3, 9)
        bv.paint(a, lambda d, x=x, y=y, ln=ln: d.line((x, y, x + ln, y), fill=255), r.choice(['lav2', 'pale', 'white']))
    shore = [(0, 86), (24, 82), (48, 88), (70, 83), (96, 89), (128, 84)]
    pts = [(x, y + 1.5 * math.sin(x / 5)) for x, y in shore]
    bv.paint(a, lambda d: d.polygon(pts + [(N, N), (0, N)], fill=255), 'pale')      # ıslak kum/köpük alanı
    bv.paint(a, lambda d: d.polygon([(x, y + 7) for x, y in shore] + [(N, N), (0, N)], fill=255), 'peach')
    bv.paint(a, lambda d: d.polygon([(x, y + 22) for x, y in shore] + [(N, N), (0, N)], fill=255), 'pink')
    for x in range(0, N, 3):                                                         # köpük sırası
        y = int(round(84 + 3 * math.sin(x / 9) + (3 if x % 6 == 0 else 0)))
        bv.px(a, x, y, 'white')
        bv.px(a, x + 1, y + 1, 'white')
    return a


def s_wind_chimes():
    """Rüzgâr Çanı: askı, değişen boylarda borular, rüzgâr çizgileri."""
    a = bv.base(['indigo', 'violet', 'purple', 'lav', 'lav2'], 0.05, 0.75, (CX, 66, 34, 0.45))
    bv.cloud(a, 4, 22, 30)
    bv.cloud(a, 92, 34, 30)
    bv.cloud(a, 14, 98, 26)
    bv.cloud(a, 92, 104, 28)
    bv.paint(a, lambda d: d.rectangle((38, 24, 90, 28), fill=255), 'night')           # askı çubuğu
    bv.paint(a, lambda d: d.line((38, 24, 90, 24), fill=255), 'violet')
    bv.paint(a, lambda d: d.line((CX, 8, CX, 24), fill=255), 'night')                  # tepe ipi
    bv.paint(a, lambda d: d.ellipse((CX - 3, 5, CX + 3, 11), outline=255), 'pale')
    tubes = [(44, 26, 'lav2'), (53, 34, 'pale'), (64, 42, 'white'), (75, 32, 'pale'), (84, 24, 'lav2')]
    for x, ln, c in tubes:
        bv.paint(a, lambda d, x=x: d.line((x, 28, x, 40), fill=255), 'night')
        bv.paint(a, lambda d, x=x, ln=ln: d.rectangle((x - 2, 40, x + 2, 40 + ln), fill=255), c)
        bv.paint(a, lambda d, x=x, ln=ln: d.line((x - 2, 40, x - 2, 40 + ln), fill=255), 'white')
        bv.paint(a, lambda d, x=x, ln=ln: d.line((x + 2, 40, x + 2, 40 + ln), fill=255), 'lav')
    bv.paint(a, lambda d: d.line((CX, 82, CX, 90), fill=255), 'night')                 # dil ipi
    mask_fill(a, circle(CX, 94, 5), 'warm')                                           # dil
    mask_fill(a, circle(CX, 94, 3), 'white')
    for y0, direction in [(48, 1), (62, -1), (76, 1)]:                                # rüzgâr
        for i in range(0, 28):
            x = 8 + i if direction > 0 else 120 - i
            y = int(round(y0 + 2.5 * math.sin(i / 3.5)))
            if i % 3 != 2:
                bv.px(a, x, y, 'white')
    return a


def s_night_rain():
    """Gece Yağmuru: kara bulut, çapraz yağmur çizgileri, su birikintisinde halkalar."""
    a = bv.base(['night', 'indigo', 'violet', 'purple'], 0.0, 0.5, (CX, 30, 34, 0.35))
    bv.stars(a, 16, 15, cols=('lav2', 'pale'), ymax=30)
    DY = 14
    blobs = [(40, 30 + DY, 10), (54, 24 + DY, 13), (70, 27 + DY, 12), (84, 31 + DY, 9)]
    body = np.zeros((N, N), bool)
    for cx, cy, rr in blobs:
        body |= circle(cx, cy, rr)
    body[30 + DY:38 + DY, 34:92] = True
    mask_fill(a, body, 'purple')
    light = np.zeros((N, N), bool)
    for cx, cy, rr in blobs:
        light |= circle(cx - 1, cy - 3, rr - 3)
    mask_fill(a, light & body & (bv.Y < 34 + DY), 'lav')
    mask_fill(a, body & (bv.Y >= 35 + DY), 'violet')
    mask_fill(a, body & (bv.Y >= 38 + DY), 'indigo')
    r = random.Random(16)
    for _ in range(46):
        x, y = r.randrange(18, 110), r.randrange(58, 96)
        ln = r.randrange(5, 10)
        bv.paint(a, lambda d, x=x, y=y, ln=ln: d.line((x, y, x - ln // 2, y + ln), fill=255),
                 r.choice(['lav2', 'lav2', 'pale', 'white']))
    bv.paint(a, lambda d: d.rectangle((0, 100, N, N), fill=255), 'indigo')              # zemin
    bv.paint(a, lambda d: d.ellipse((6, 100, 122, 128), fill=255), 'violet')            # su birikintisi
    for cx, cy, rx in [(34, 110, 10), (64, 114, 14), (94, 108, 9), (80, 118, 6)]:
        for k, c in [(0, 'pale'), (-4, 'lav')]:
            rr = rx + k
            if rr > 1:
                bv.paint(a, lambda d, cx=cx, cy=cy, rr=rr: d.ellipse((cx - rr, cy - rr // 3, cx + rr, cy + rr // 3), outline=255), c)
    return a


def s_pink_haze():
    """Pembe Sis: pembe tonlarda yumuşak bir sis ve ince benek gürültüsü, ortada soluk bir ışık."""
    a = bv.base(['purple', 'rose', 'pink', 'peach', 'pale', 'white'], 0.15, 0.7, (CX, 56, 36, 0.55))
    r = random.Random(17)
    for y in range(N):
        for x in range(N):
            d = math.hypot(x - CX, (y - 58) * 1.05)
            p = 0.30 if d > 34 else 0.30 * max(0.0, (d - 20) / 14)
            if r.random() < p:
                a[y, x] = C[r.choice(['pink', 'rose', 'peach', 'pink', 'pale', 'white', 'lav2'])]
    mask_fill(a, circle(CX, 58, 17), 'pale')
    mask_fill(a, circle(CX, 58, 13), 'white')
    mask_fill(a, circle(CX, 58, 7), 'warm')
    rings(a, CX, 58, [22, 27], ['peach', 'pink'], 1)
    return a


SCENES = [
    ('velvet', s_velvet),
    ('tide', s_tide),
    ('one-point', s_one_point),
    ('singing-bowl', s_singing_bowl),
    ('shoreline', s_shoreline),
    ('wind-chimes', s_wind_chimes),
    ('night-rain', s_night_rain),
    ('pink-haze', s_pink_haze),
]


def render(fn):
    return Image.fromarray(fn()).resize((N * S, N * S), Image.NEAREST)


def preview(imgs, path):
    """2 satır x 4: üstte kare, altta uygulamadaki hero (yatay) ve dikey kart kırpımı."""
    cell = 240
    sheet = Image.new('RGB', (4 * (cell + 10), 2 * (cell + 10) + 3 * 110), 'white')
    for i, (name, im) in enumerate(imgs.items()):
        sheet.paste(im.resize((cell, cell), Image.LANCZOS), ((i % 4) * (cell + 10), (i // 4) * (cell + 10)))
    y0 = 2 * (cell + 10) + 5
    for i, (name, im) in enumerate(imgs.items()):
        wide = im.crop((0, im.height * 11 // 40, im.width, im.height * 29 // 40)).resize((200, 100), Image.LANCZOS)
        tall = im.crop((im.width * 11 // 40, 0, im.width * 29 // 40, im.height)).resize((67, 100), Image.LANCZOS)
        circ = im.resize((100, 100), Image.LANCZOS)
        mask = Image.new('L', (100, 100), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 99, 99), fill=255)
        x = (i % 4) * (cell + 10)
        yy = y0 + (i // 4) * 0
        if i < 4:
            sheet.paste(wide, (x, y0))
            sheet.paste(tall, (x + 205, y0))
        else:
            sheet.paste(wide, (x, y0 + 110))
            sheet.paste(tall, (x + 205, y0 + 110))
    sheet.save(path)


def main():
    args = [x for x in sys.argv[1:] if not x.startswith('--')]
    out = args[0] if args else os.path.join(HERE, '..', '..', 'images', 'meditations')
    os.makedirs(out, exist_ok=True)
    use_grid()
    imgs = {}
    for name, fn in SCENES:
        im = render(fn)
        imgs[name] = im
        im.save(os.path.join(out, name + '.webp'), lossless=True)
        if '--png' in sys.argv:
            im.save(os.path.join(out, name + '.png'))
        print('written:', name)
    if '--preview' in sys.argv:
        preview(imgs, os.path.join(out, 'preview.png'))
        print('written: preview.png')


if __name__ == '__main__':
    main()
