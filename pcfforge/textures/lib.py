"""Bibliothèque de textures génériques + export VTF/VMT.

Chaque texture est générée À LA DEMANDE (seulement celles utilisées par la spec).
Registre : nom -> dict(fn, blend, grid, seqs, S, rate, desc)
  - blend 'add'   : lueurs, étincelles, énergie (fond noir, couleur prémultipliée)
  - blend 'alpha' : fumée, pétales, débris (translucide, trié)
Les textures claires/neutres sont teintées par la couleur de la particule.
"""
import os, math, glob, numpy as np
from PIL import Image, ImageDraw, ImageFilter
from srctools.vtf import VTF, ImageFormats, SheetSequence, VTFFlags, TexCoord
from . import shapes as sh
from . import vtf as VT
from .shapes import grid, sstep, fbm, rot, mix, hexc, to_img

# ------------------------------------------------------------------ nouveaux générateurs
def smoke(S, seed=0):
    """Bouffée de fumée volumétrique, éclairée par le haut (neutre, à teinter)."""
    x, y = grid(S); r = np.hypot(x, y)
    n = fbm(S, 6, seed + 90, base=3); n2 = fbm(S, 4, seed + 91, base=6)
    a = np.clip(1 - (r + (n - .5) * .7) / .9, 0, 1) ** 1.3
    a = a * (.6 + .4 * n2)
    light = np.clip(.55 - y * .35 + (n2 - .5) * .5, 0, 1)
    lum = .45 + .55 * light
    return np.dstack([lum] * 3), a

def flame_frame(S, k, n_frames=16, seed=0):
    """Flamme stylisée animée (frame k / n) — neutre chaude, à teinter."""
    x, y = grid(S); t = k / n_frames
    n = fbm(S, 5, seed + 70 + k % n_frames, base=3)
    yy = (y + 1) / 2                                   # 0 haut, 1 bas
    w = .55 * yy ** .6 + .05
    xx = x + (n - .5) * .5 * (1 - yy) + .08 * math.sin(t * 6.28 * 2) * (1 - yy)
    body = sstep(0, .15, w - np.abs(xx)) * sstep(0, .25, yy) * sstep(1.02, .85, yy)
    tongue = (n > .45 + .4 * (1 - yy)).astype(np.float32)
    a = np.clip(body * (.4 + .6 * tongue), 0, 1)
    heat = np.clip(yy * 1.2 - np.abs(xx) * .6, 0, 1)
    col = mix(hexc('#ff6a1a'), hexc('#fff3c0'), heat)
    return col, a

def explosion_frame(S, k, n_frames=16, seed=0):
    """Boule d'explosion qui gonfle, refroidit et se dissipe (flipbook)."""
    x, y = grid(S); t = k / (n_frames - 1)
    r = np.hypot(x, y)
    n = fbm(S, 6, seed + 30, base=3)
    R = .35 + .5 * t ** .6
    a = np.clip(1 - (r + (n - .5) * .5) / R, 0, 1) ** .8 * (1 - t ** 2.2)
    heat = np.clip((1 - r / R) * (1.2 - t * 1.4) + (n - .5) * .4, 0, 1)
    col = mix(hexc('#2a2420'), hexc('#ff8a2a'), np.clip(heat * 1.5, 0, 1))
    col = mix(col, hexc('#fff0b0'), np.clip(heat * 2 - 1, 0, 1))
    return col, a

def shard(S, v=0, seed=0):
    """Éclat anguleux (roche, cristal, glace) — neutre, à teinter."""
    rr = np.random.default_rng(seed + v)
    n = 5 + v % 3
    ang = np.sort(rr.random(n)) * 2 * np.pi
    rad = rr.uniform(.35, .9, n)
    pts = [(S / 2 + math.cos(a) * r * S / 2, S / 2 + math.sin(a) * r * S / 2 * .7) for a, r in zip(ang, rad)]
    im = Image.new('L', (S, S), 0); ImageDraw.Draw(im).polygon(pts, fill=255)
    a = np.asarray(im.filter(ImageFilter.GaussianBlur(S * .004)), np.float32) / 255
    x, y = grid(S)
    facet = .55 + .45 * np.clip(-x * .6 - y * .8 + .3, 0, 1) + (fbm(S, 3, seed + v) - .5) * .2
    return np.dstack([facet] * 3), a

def crack_decal(S, seed=0):
    """Fissures au sol (décal alpha sombre)."""
    _, a = sh.veins_decal(S, seed=seed, branches=7)
    return np.dstack([np.full((S, S), .08)] * 3), np.clip(a * 1.2, 0, 1)

def magic_circle(S, seed=0):
    """Cercle rituel (anneaux + glyphes) additif."""
    im = Image.new('L', (S, S), 0); d = ImageDraw.Draw(im); c = S / 2
    rr = np.random.default_rng(seed)
    for rad, w in ((.47, .012), (.40, .006), (.24, .008)):
        R = rad * S; d.ellipse([c - R, c - R, c + R, c + R], outline=255, width=max(1, int(w * S)))
    for i in range(6):                                       # hexagramme
        a0 = i / 6 * 2 * math.pi; a1 = (i + 2) / 6 * 2 * math.pi; R = .40 * S
        d.line([(c + math.cos(a0) * R, c + math.sin(a0) * R), (c + math.cos(a1) * R, c + math.sin(a1) * R)], fill=255, width=max(1, int(.005 * S)))
    for i in range(24):                                      # glyphes
        a0 = i / 24 * 2 * math.pi; R = .435 * S; gx, gy = c + math.cos(a0) * R, c + math.sin(a0) * R; g = S * .012
        for _ in range(3):
            p = [(gx + rr.uniform(-g, g), gy + rr.uniform(-g, g)) for _ in range(2)]
            d.line(p, fill=255, width=max(1, int(.004 * S)))
    core = np.asarray(im, np.float32) / 255
    halo = np.asarray(im.filter(ImageFilter.GaussianBlur(S * .01)), np.float32) / 255
    return np.ones((S, S, 3), np.float32), np.clip(core + halo, 0, 1)

def droplet(S):
    """Goutte (eau, sang, poison) — neutre avec reflet."""
    x, y = grid(S)
    e = (x / .35) ** 2 + ((y - .15) / .5) ** 2 * (1 + .6 * np.clip(-y, 0, 1))
    a = sstep(1, .9, e)
    lum = .5 + .5 * np.clip(-x * .5 - y * .5, 0, 1)
    hl = np.exp(-(((x + .12) / .08) ** 2 + ((y + .05) / .15) ** 2))
    return np.dstack([np.clip(lum + hl, 0, 1)] * 3), a

def lightning_strand(S, seed=0):
    """Brin d'éclair tuilable horizontalement (corde)."""
    rr = np.random.default_rng(seed)
    y, x = np.mgrid[0:S, 0:S].astype(np.float32); v = (y + .5) / S * 2 - 1; u = x / S
    path = np.zeros(S)
    for f, a in ((1, .35), (3, .15), (7, .06)):
        ph = rr.random() * 6.28; path += a * np.sin(2 * np.pi * f * np.arange(S) / S + ph)
    dv = v - path[None, :]
    a = np.exp(-(dv / .05) ** 2) + .35 * np.exp(-(dv / .25) ** 2)
    return np.ones((S, S, 3), np.float32), np.clip(a, 0, 1)

def flare(S):
    x, y = grid(S); r = np.hypot(x, y)
    a = np.exp(-(r / .12) ** 2) + .5 * np.exp(-(np.abs(y) / .02) ** 2) * np.clip(1 - np.abs(x), 0, 1) ** 2 \
        + .25 * np.exp(-(np.abs(x) / .02) ** 2) * np.clip(1 - np.abs(y), 0, 1) ** 2 + .25 * np.clip(1 - r, 0, 1) ** 3
    return np.ones((S, S, 3), np.float32), np.clip(a, 0, 1)

def soft_ring(S):
    return sh.ring(S, width=.14)

def feather(S, v=0):
    x, y = grid(S); x, y = rot(x, y, -math.pi / 4); t = np.clip((x / .95 + 1) / 2, 0, 1)
    wid = .22 * np.sin(np.pi * t) ** .5; d = wid - np.abs(y)
    barbs = .6 + .4 * np.abs(np.sin((x - np.abs(y) * 1.5) * 60))
    a = sstep(0, .03, d) * (np.abs(x) < .95) * (.85 + .15 * barbs)
    lum = (.6 + .4 * t) * barbs; lum = np.maximum(lum, np.exp(-(y / .01) ** 2))
    return np.dstack([lum] * 3), a

def streak(S):
    """Motion streak: bright head, long thin tail (sprite trails, fast debris)."""
    x, y = grid(S); t = np.clip((x + 1) / 2, 0, 1)                     # 0 = tail, 1 = head
    w = .02 + .1 * t ** 2
    a = np.exp(-(y / w) ** 2) * t ** 1.5 + np.exp(-(((x - .8) / .15) ** 2 + (y / .08) ** 2))
    return np.ones((S, S, 3), np.float32), np.clip(a, 0, 1)

def slash(S):
    """Crescent stroke (slash, whip, arc): thick in the middle, tapered ends, bright inner edge."""
    x, y = grid(S); r = np.hypot(x, y + .55); ang = np.arctan2(x, y + .55)
    along = np.clip(1 - np.abs(ang) / 1.1, 0, 1)
    w = .09 * along ** .7
    d = np.abs(r - .95)
    a = sstep(0, .02, w - d) * along + .5 * np.exp(-((r - .95 + w * .6) / .015) ** 2) * along
    return np.ones((S, S, 3), np.float32), np.clip(a, 0, 1)

def noise_puff(S, seed=0):
    """Soft broken-up energy puff (secondary volume, never a clean disc)."""
    x, y = grid(S); r = np.hypot(x, y)
    n = fbm(S, 5, seed + 120, base=4)
    a = np.clip(1 - r, 0, 1) ** 1.5 * sstep(.35, .75, n)
    return np.ones((S, S, 3), np.float32), a

def energy_frame(S, k, n_frames=8, seed=0):
    """Energy wisp licking upward (flipbook): shape changes every frame, looped."""
    x, y = grid(S); t = k / n_frames
    yy = (y + 1) / 2
    n = fbm(S, 4, seed + 150 + k, base=3)
    w = .38 * np.sin(np.pi * np.clip(yy, 0, 1)) ** .6 + .02
    xx = x + (n - .5) * .45 * (1 - yy) + .1 * math.sin(t * 2 * math.pi) * (1 - yy)
    body = sstep(0, .12, w - np.abs(xx)) * sstep(0, .2, yy)
    core = np.exp(-(xx / (w * .35 + .01)) ** 2) * sstep(.1, .5, yy)
    return np.ones((S, S, 3), np.float32), np.clip(body * (.35 + .65 * n) + .5 * core, 0, 1)

def chakra_tongue_frame(S, k, n_frames=8, seed=0):
    """Anime chakra flame (looped flipbook): 2-3 pointed licks from a round base, cel-shaded in 3 bands.

    Neutral white, tinted by the particle colour: edge band darker, core band brightest.
    Every field is periodic in t, so the last frame flows into the first.
    """
    x, y = grid(S); t = k / n_frames * 2 * math.pi
    yy = (1 - y) / 2                                      # 0 base (bottom) -> 1 top
    r = np.random.default_rng(seed + 300)
    d = np.full((S, S), -1.0, np.float32); wmax = np.zeros((S, S), np.float32)
    licks = [(0.0, .80, .30, 0.0), (-.24, .58, .19, 2.1), (.23, .64, .19, 4.2)]
    yb = .16                                              # root height: the base stays inside the frame
    for x0, h, wid, ph in licks:
        u = np.clip((yy - yb) / h, 0, 1.2)                          # 0 base -> 1 tip of this lick
        sway = .16 * np.sin(t + ph + u * 3.2) * u ** 1.4 + .05 * np.sin(2 * t + ph * 1.7 + u * 6) * u ** 2
        cx = x0 * (1 - .35 * u) + sway
        w = wid * (1 - u) ** .8 * (.55 + .45 * np.sin(np.clip(u, 0, 1) * np.pi * .5 + .6))
        dd = np.where((yy <= yb + h) & (yy >= yb), w - np.abs(x - cx), -1.0)
        wmax = np.where(dd > d, w, wmax); d = np.maximum(d, dd)
    base = np.hypot(x / .40, (yy - yb - .02) / .13) - 1              # round base joining the licks
    d = np.maximum(d, -base * .3)
    wmax = np.where(-base * .3 >= d, .6, wmax)
    e = 5.0 / S
    a = sstep(-e, e, d) * (1 - .5 * sstep(.35, 1.0, yy))       # tips thinner and more transparent
    inner = np.clip(d / np.maximum(wmax, 1e-3), 0, 1)
    band = .62 + .22 * sstep(.25, .35, inner) + .16 * sstep(.6, .7, inner)
    return np.dstack([band] * 3), np.clip(a, 0, 1)


def chakra_body(S, v=0):
    """Translucent chakra volume: no hard edge (overlaps must merge into one mass, not read as balls),
    marbled interior like anime chakra (lighter veins, darker pockets)."""
    x, y = grid(S); r = np.hypot(x, y)
    n = fbm(S, 4, 320 + v, base=3); m = fbm(S, 3, 340 + v, base=5)
    a = np.clip(1 - r / (.92 + (n - .5) * .12), 0, 1) ** 1.7 * (.75 + .25 * n)
    lum = .7 + .3 * sstep(.45, .75, m)
    return np.dstack([lum] * 3), a


def soft_line(S):
    """Tileable glowing line for ropes (along U): bright thin core, soft falloff across V."""
    x, y = grid(S)
    core = np.exp(-(y / .12) ** 2); glow = np.exp(-(y / .45) ** 2) * .45
    return np.ones((S, S, 3), np.float32), np.clip(core + glow, 0, 1)


def _loop_fbm(S, k, n, seed, base=3, octaves=5):
    """Looping noise for flipbooks: two fields cross-faded on a circle, so frame n == frame 0."""
    a = 2 * math.pi * k / n
    f1, f2 = fbm(S, octaves, seed, base), fbm(S, octaves, seed + 1, base)
    f3 = fbm(S, octaves, seed + 2, base)
    return .5 + (f1 - .5) * math.cos(a) + (f2 - .5) * math.sin(a) * .8 + (f3 - .5) * .35


def ink_spike(S, v=0):
    """Berserk-like ink flame: black torn spikes rising from a ragged root, blood-red glow inside the lower half.
    Coloured texture (drawn for a white particle colour)."""
    x, y = grid(S); yy = (1 - y) / 2
    r = np.random.default_rng(400 + v)
    n_hi = fbm(S, 6, 410 + v, base=8)
    d = np.full((S, S), -1.0, np.float32)
    k = 3 + v % 3
    for i in range(k):
        x0 = (i - (k - 1) / 2) * .24 + r.uniform(-.05, .05)
        h = r.uniform(.45, .72) if i != k // 2 else .82
        lean = r.uniform(-.2, .2)
        u = np.clip((yy - .05) / h, 0, 1.3)
        cx = x0 * (1 - .45 * u) + lean * u ** 1.6
        wdt = (.14 + .05 * r.random()) * (1 - u) ** 1.2 * np.clip(.35 + u * 3, 0, 1)   # narrow root, body, tip
        dd = np.where(yy <= .05 + h, wdt - np.abs(x - cx) + (n_hi - .5) * .06, -1.0)
        d = np.maximum(d, dd)
    e = 2.0 / S
    a = sstep(-e, e, d) * sstep(.0, .14, yy + (n_hi - .5) * .1)       # ragged root fading into the blade
    inner = sstep(.035, .085, d)
    heat = inner * np.clip(.75 - yy * 1.8, 0, 1)                       # blood-red glow deep and low inside
    col = mix(hexc('#060206'), hexc('#a00d18'), np.clip(heat * 1.4, 0, 1) ** 1.2)
    col = mix(col, hexc('#33103f'), (1 - sstep(.0, .02, d)) * .7)       # thin purple rim on the silhouette
    return col, np.clip(a, 0, 1)


def miasma_frame(S, k, n_frames=8, seed=0):
    """Boiling demonic miasma (looped flipbook): torn black-purple smoke, lit from below in dark red."""
    x, y = grid(S); r = np.hypot(x, y)
    n = _loop_fbm(S, k, n_frames, 430 + seed, base=3)
    m = _loop_fbm(S, k, n_frames, 440 + seed, base=7, octaves=4)
    edge = .72 + (n - .5) * .5
    a = sstep(edge, edge - .3, r) * (.65 + .35 * m)
    a *= sstep(.2, .45, m + (1 - r / edge) * .9)                       # torn only at the rim, solid core
    under = np.clip((y + .1) * 1.4, 0, 1) * sstep(edge - .35, edge - .05, r)   # lower rim catches red light
    col = mix(hexc('#0d0710'), hexc('#241031'), sstep(.4, .8, m))
    col = mix(col, hexc('#7c0b18'), under)
    return col, np.clip(a, 0, 1)


def crackle(S, v=0):
    """Branching jagged bolt (additive, white core): demonic sparks around a blade. Tinted by the particle."""
    r = np.random.default_rng(460 + v)
    big = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(big)
    def bolt(p, ang, length, width, depth):
        pts = [p]
        for _ in range(7):
            ang += r.uniform(-.7, .7)
            step = length / 7
            p = (p[0] + math.cos(ang) * step, p[1] + math.sin(ang) * step); pts.append(p)
            if depth < 2 and r.random() < .3:
                bolt(p, ang + r.choice([-1, 1]) * r.uniform(.5, 1.1), length * .45, max(1, width * .6), depth + 1)
        dr.line(pts, fill=255, width=int(width), joint='curve')
    c = (S / 2, S / 2)
    for i in range(2):
        bolt(c, r.uniform(0, 2 * math.pi) + i * math.pi, S * .45, S * .025, 0)
    core = np.asarray(big, np.float32) / 255
    glow = np.asarray(big.filter(ImageFilter.GaussianBlur(S * .025)), np.float32) / 255
    a = np.clip(core + glow * 1.6, 0, 1)
    return np.ones((S, S, 3), np.float32), a


def sparkle(S, v=0):
    """Glint: 4-point star (long thin rays, one pair longer) with a tight hot core and a soft halo. Additive."""
    x, y = grid(S); r = np.hypot(x, y)
    ang = v * .35                                            # variants: small rotation and ray balance
    xr, yr = rot(x, y, ang)
    long_k, short_k = (1.0, .55) if v % 2 == 0 else (.8, .8)
    ray = lambda u, w, L: np.exp(-(w / (.012 + .02 * np.abs(u))) ** 2) * np.clip(1 - np.abs(u) / L, 0, 1) ** 2
    rays = np.maximum(ray(xr, yr, .95 * long_k), ray(yr, xr, .95 * short_k))
    core = np.exp(-(r / .05) ** 2); halo = np.exp(-(r / .22) ** 2) * .35
    a = np.clip(core + rays * .9 + halo, 0, 1)
    return np.ones((S, S, 3), np.float32), a


def nebula(S, v=0):
    """Cosmic nebula wisp: ridged (filamentary) noise inside a soft irregular mass. Additive, to tint.
    Filaments are what separates a nebula from a glow ball."""
    x, y = grid(S); r = np.hypot(x, y)
    n = fbm(S, 5, 480 + v, base=3)
    rid = 1 - np.abs(fbm(S, 6, 490 + v, base=4) * 2 - 1)            # ridges -> fine filaments
    rid2 = 1 - np.abs(fbm(S, 5, 500 + v, base=7) * 2 - 1)
    mass = sstep(.95 + (n - .5) * .5, .2, r)
    a = mass * (.18 + .55 * rid ** 5 + .35 * rid2 ** 8)
    lum = .75 + .25 * rid ** 3
    return np.dstack([lum] * 3), np.clip(a, 0, 1)


def curl(S, v=0):
    """Thin energy wisp that curls at one end: loose, wobbling, tapering stroke with a glow (additive, to tint)."""
    r_ = np.random.default_rng(510 + v)
    big = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(big)
    turns = r_.uniform(.6, 1.05); a0 = r_.uniform(0, 2 * math.pi); k = 90
    ph1, ph2 = r_.uniform(0, 6.28, 2)
    pts = []
    for i in range(k):
        t = i / (k - 1)
        rad = S * .44 * (1 - t * .62) * (1 + .1 * math.sin(7 * t + ph1) + .05 * math.sin(17 * t + ph2))
        a = a0 + (t ** 1.4) * turns * 2 * math.pi                  # straight-ish start, curls at the end
        pts.append((S / 2 + rad * math.cos(a), S / 2 + rad * math.sin(a)))
    for i in range(k - 1):
        t = i / (k - 1)
        env = math.sin(math.pi * min(1, t * 1.15)) ** .6            # tapers at both ends
        dr.line([pts[i], pts[i + 1]], fill=int(255 * env), width=max(1, int(S * .016 * env + .5)))
    core = np.asarray(big, np.float32) / 255
    glow = np.asarray(big.filter(ImageFilter.GaussianBlur(S * .02)), np.float32) / 255
    return np.ones((S, S, 3), np.float32), np.clip(core + glow * 1.3, 0, 1)


def _jagged(r_, p0, p1, rough, depth):
    """Midpoint displacement: straight segments with sharp kinks, like a real discharge."""
    if depth == 0:
        return [p0, p1]
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1
    off = r_.normal(0, rough) * L
    m = (mx - dy / L * off, my + dx / L * off)
    return _jagged(r_, p0, m, rough, depth - 1)[:-1] + _jagged(r_, m, p1, rough, depth - 1)


def black_bolt(S, v=0):
    """Kuro Kaminari arc: black ink discharge (sharp kinks, forks) with a thin electric-blue core.
    Coloured texture, alpha-blended: reads as BLACK lightning on any background."""
    r_ = np.random.default_rng(530 + v)
    ink = Image.new('L', (S, S), 0); core = Image.new('L', (S, S), 0)
    di, dc = ImageDraw.Draw(ink), ImageDraw.Draw(core)
    y0, y1 = S * r_.uniform(.35, .65), S * r_.uniform(.35, .65)
    main = _jagged(r_, (S * .04, y0), (S * .96, y1), .16, 6)
    strokes = [(main, 1.0)]
    for _ in range(3 + v % 2):                               # forks leave the main path at an angle
        i = int(r_.uniform(.15, .8) * len(main)); p = main[i]
        ang = r_.uniform(-1.1, 1.1) + (0 if r_.random() < .5 else math.pi) * 0
        L = S * r_.uniform(.15, .3)
        end = (p[0] + math.cos(ang) * L, p[1] + math.sin(ang) * L * r_.choice([-1, 1]))
        strokes.append((_jagged(r_, p, end, .22, 4), .5))
    for pts, k in strokes:
        n = len(pts)
        for i in range(n - 1):
            taper = k * (1 - .6 * i / n)                     # thinner towards the ends
            di.line([pts[i], pts[i + 1]], fill=255, width=max(1, int(S * .03 * taper)))
            dc.line([pts[i], pts[i + 1]], fill=int(255 * min(1, k * 1.2)), width=max(1, int(S * .008 * taper)))
    ink_a = np.asarray(ink.filter(ImageFilter.GaussianBlur(S * .004)), np.float32) / 255
    halo = np.asarray(ink.filter(ImageFilter.GaussianBlur(S * .025)), np.float32) / 255 * .3
    c = np.asarray(core.filter(ImageFilter.GaussianBlur(S * .003)), np.float32) / 255
    col = mix(hexc('#040406'), hexc('#9fc3ff'), np.clip(c * 1.4, 0, 1))
    return col, np.clip(ink_a + halo, 0, 1)


def lightning_anim_frame(S, k, n_frames=16, seed=0):
    """Animated Kuro Kaminari discharge (2 sequences x 8 frames): strikes from left to right (frames 0-2),
    crackles with changing forks (3-5), then thins out and fades (6-7). Black ink, electric-blue core, faint blue
    glow so it also reads on dark maps. Coloured texture (white particle colour), alpha-blended."""
    seq, f = divmod(k, 8)
    r_ = np.random.default_rng(560 + seed + seq * 7)
    y0, y1 = S * r_.uniform(.38, .62), S * r_.uniform(.38, .62)
    main = _jagged(r_, (S * .04, y0), (S * .96, y1), .15, 6)
    forks = []
    for j in range(4):
        i = int(r_.uniform(.15, .85) * len(main))
        forks.append((i, r_.uniform(-1.2, 1.2), r_.uniform(.12, .28), r_.integers(1 << 30)))
    reveal = min(1.0, (f + 1) / 3)                       # strike: the path grows over 3 frames
    life = 1.0 if f < 6 else (1.0 - (f - 5) * .35)       # fade on the last frames
    n = max(2, int(len(main) * reveal))
    jit = np.random.default_rng(700 + seq * 13 + f)             # the path shivers from frame to frame
    main = [(x_, y_ + jit.normal(0, S * .002)) for x_, y_ in main]
    ink = Image.new('L', (S, S), 0); core = Image.new('L', (S, S), 0)
    di, dc = ImageDraw.Draw(ink), ImageDraw.Draw(core)
    wk = S * .04 * life
    for i in range(n - 1):
        di.line([main[i], main[i + 1]], fill=255, width=max(1, int(wk)))
        dc.line([main[i], main[i + 1]], fill=255, width=max(1, int(wk * .3)))
    if f >= 2:                                           # forks flicker: a different subset each frame
        fr = np.random.default_rng(900 + seq * 31 + f)
        for i, ang, L_, sd in forks:
            if i >= n or fr.random() < .45:
                continue
            p = main[i]; L2 = S * L_ * (.7 + .5 * fr.random())
            end = (p[0] + math.cos(ang) * L2, p[1] + math.sin(ang) * L2)
            br = _jagged(np.random.default_rng(sd + f), p, end, .25, 3)
            di.line(br, fill=200, width=max(1, int(wk * .55)))
            dc.line(br, fill=170, width=max(1, int(wk * .18)))
    ink_a = np.asarray(ink.filter(ImageFilter.GaussianBlur(S * .004)), np.float32) / 255
    glow = np.asarray(core.filter(ImageFilter.GaussianBlur(S * .03)), np.float32) / 255
    c = np.asarray(core.filter(ImageFilter.GaussianBlur(S * .003)), np.float32) / 255
    a = np.clip(ink_a + glow * 1.3 * life, 0, 1) * life
    col = mix(hexc('#050508'), hexc('#a9ccff'), np.clip(c * 1.4 + glow * .6, 0, 1))
    return col, a


def bolt_strand(S, seed=0):
    """Tileable JAGGED lightning for ropes (additive): a few long straight segments with sharp kinks, white-hot
    core, electric glow (the tint). Drawn three times side by side, blurred, then the middle tile is kept, so the
    glow wraps and the rope shows no seam."""
    r_ = np.random.default_rng(600 + seed)
    W2, H = S * 2, S
    pts = _jagged(r_, (0, H / 2), (W2, H / 2), .12, 4)
    pts = [(x_, min(H * .8, max(H * .2, y_))) for x_, y_ in pts]
    big = Image.new('L', (W2 * 3, H), 0); core = Image.new('L', (W2 * 3, H), 0)
    for k in range(3):
        sh = [(x_ + W2 * k, y_) for x_, y_ in pts]
        ImageDraw.Draw(big).line(sh, fill=255, width=max(2, int(H * .07)))
        ImageDraw.Draw(core).line(sh, fill=255, width=max(1, int(H * .025)))
    g = np.asarray(big.filter(ImageFilter.GaussianBlur(H * .07)), np.float32)[:, W2:W2 * 2] / 255
    c = np.asarray(core.filter(ImageFilter.GaussianBlur(H * .006)), np.float32)[:, W2:W2 * 2] / 255
    a = np.clip(c * 1.3 + g * .7, 0, 1)
    rgb = np.clip(.5 + .5 * c, 0, 1)                             # core whiter than the tinted glow
    img = Image.fromarray((np.dstack([rgb, rgb, rgb, a]) * 255).astype(np.uint8), 'RGBA').resize((S, S), Image.LANCZOS)
    arr = np.asarray(img, np.float32) / 255
    return arr[..., :3], arr[..., 3]


def _hex_dist(x, y):
    """Distance to the centre of a flat-top regular hexagon (1 = on the edge midpoints)."""
    ax_, ay_ = np.abs(x), np.abs(y)
    return np.maximum(ax_ * .866 + ay_ * .5, ay_) / .866


def hex_cell(S, v=0):
    """Barrier cell (Black Clover-like): crisp bright hexagon border, light fill brighter towards the border,
    soft outer glow. Additive, white: tint = barrier colour. Variant 1: inner bevel line."""
    x, y = grid(S)
    d = _hex_dist(x / .9, y / .9)
    edge = np.exp(-((d - .92) / .028) ** 2)
    glow = np.exp(-((d - .92) / .12) ** 2) * .35
    fill = np.where(d < .92, .1 + .16 * sstep(.3, .92, d), 0)
    inner = np.exp(-((d - .74) / .02) ** 2) * .35 if v == 1 else 0
    a = np.clip(edge + glow + fill + inner, 0, 1)
    rgb = np.clip(.75 + .25 * edge, 0, 1)
    return np.dstack([rgb] * 3), a


def hex_patch(S):
    """Impact patch: honeycomb of small flat-top cells (exact hex grid, cube rounding) fading out from the
    centre, hot centre cell. Additive, white: tint = barrier colour."""
    x, y = grid(S)
    k = 4.0                                                  # cell size: vertex radius = 1 / k
    px, py = x * k, y * k
    q = 2 / 3 * px; r = -1 / 3 * px + math.sqrt(3) / 3 * py
    cx_, cz_ = q, r; cy_ = -cx_ - cz_
    rx, ry, rz = np.round(cx_), np.round(cy_), np.round(cz_)
    dx, dy, dz = np.abs(rx - cx_), np.abs(ry - cy_), np.abs(rz - cz_)
    rx = np.where((dx > dy) & (dx > dz), -ry - rz, rx)
    rz = np.where(~((dx > dy) & (dx > dz)) & ~(dy > dz), -rx - ry, rz)
    hx, hy = 1.5 * rx, math.sqrt(3) * (rz + rx / 2)
    d = _hex_dist((px - hx) / 1.0, (py - hy) / 1.0)
    lines = np.exp(-((d - .97) / .06) ** 2)
    fill = np.where(d < .95, .22, 0)
    rr = np.hypot(x, y)
    fall = np.clip(1 - rr / .95, 0, 1) ** 1.2
    a = np.clip((lines + fill) * fall + np.exp(-(rr / .25) ** 2) * .45, 0, 1)
    return np.ones((S, S, 3), np.float32), a


def hex_shard(S, v=0):
    """Broken barrier piece: a hexagon cut by one or two straight cracks (4 variants), bright rim, light fill."""
    x, y = grid(S)
    r_ = np.random.default_rng(620 + v)
    d = _hex_dist(x / .8, y / .8)
    keep = d < .92
    for _ in range(v % 3):                                  # straight cuts through the cell
        ang = r_.uniform(0, math.pi); o = r_.uniform(-.25, .25)
        keep &= (x * math.cos(ang) + y * math.sin(ang)) < o
    m = keep.astype(np.float32)
    img = Image.fromarray((m * 255).astype(np.uint8))
    er = np.asarray(img.filter(ImageFilter.MinFilter(5)), np.float32) / 255
    rim = np.clip(m - er, 0, 1)
    a = np.clip(m * .35 + rim * .9, 0, 1)
    a = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(S * .006)), np.float32) / 255
    return np.ones((S, S, 3), np.float32), a


def rune_line(S):
    """Tileable glowing line for ropes, broken into 2 segments with a bright node in each (a magic-circle stroke):
    when the rope texture scrolls, the circle visibly turns. Additive, white: tint = colour."""
    x, y = grid(S)
    u = (x + 1) / 2                                          # 0..1 along the rope (tiles)
    f = (u * 2) % 1                                          # 2 segments per tile
    core = np.exp(-(y / .1) ** 2); glow = np.exp(-(y / .3) ** 2) * .3
    seg = sstep(.04, .12, np.minimum(f, 1 - f))              # clear gap at each segment end
    node = np.exp(-((f - .5) / .05) ** 2) * np.exp(-(y / .22) ** 2)
    a = np.clip((core + glow) * seg + node * .85, 0, 1)
    return np.ones((S, S, 3), np.float32), a


def black_strand(S):
    """Tileable crackling line for ropes: black ink band with a thin white-blue core (coloured, alpha)."""
    x, y = grid(S)
    ink = np.exp(-(y / .38) ** 2); core = np.exp(-(y / .07) ** 2)
    col = mix(hexc('#040406'), hexc('#e4eeff'), core)
    return col, np.clip(ink * .95 + core * .05, 0, 1)


def shield_film(S, v=0):
    """Liquid barrier skin: a very soft round mass crossed by a few smooth, warped light bands (caustics in
    water, no cells). Many overlapping sprites on a surface read as one translucent film whose edge glows
    (more layers stack along the silhouette). Additive, white: tint = barrier colour."""
    x, y = grid(S); r = np.hypot(x, y)
    w = fbm(S, 3, 640 + v, base=2) - .5
    xr, yr = rot(x, y, .8 * v)
    band = .5 + .5 * np.sin((yr + w * .9 + .25 * np.sin(xr * 2.2 + v)) * 7.0)
    mass = np.clip(1 - r, 0, 1) ** 1.6
    a = mass * (.32 + .6 * band ** 6)
    return np.ones((S, S, 3), np.float32), np.clip(a, 0, 1)


def _flow(x, y, ph, seed, waves=7, scale=3.0, drift=(0.0, -1.0)):
    """Looping flowing field in [-1, 1]: a sum of travelling sine waves whose phase turns a whole number of times
    over the loop (ph 0..1), so the last frame flows back into the first. `drift` biases the travel direction
    (y points down: (0, -1) = rising)."""
    r_ = np.random.default_rng(seed); acc = np.zeros_like(x)
    dx, dy = drift
    for i in range(waves):
        ang = r_.uniform(0, 2 * math.pi); k = scale * r_.uniform(.6, 1.5)
        kx, ky = k * math.cos(ang), k * math.sin(ang)
        m = 1 if i % 3 else 2                               # whole turns per loop -> seamless
        sgn = 1 if (kx * dx + ky * dy) <= 0 else -1          # waves travel along the drift
        acc += np.sin(kx * x + ky * y + sgn * 2 * math.pi * m * ph + r_.uniform(0, 2 * math.pi))
    return acc / math.sqrt(waves)


def _warped(x, y, ph, seed, scale=3.0, warp=.35, drift=(0.0, -1.0)):
    """Domain-warped flow: liquid, curling shapes that keep moving and loop seamlessly."""
    wx = _flow(x, y, ph, seed + 1, 5, scale * .7, drift); wy = _flow(x, y, ph, seed + 2, 5, scale * .7, drift)
    return _flow(x + warp * wx, y + warp * wy, ph, seed, 7, scale, drift)


RIM_W, RIM_H = 40 / 56, 52 / 56                   # bc_shield: oval 80 x 104 u drawn on a sprite of radius 56


def shield_rim_frame(S, k, n_frames=8, w=RIM_W, h=RIM_H):
    """Barrier bubble outline seen from the camera (looped flipbook): bright soft edge that ripples and flickers
    like flowing energy, lower rim lit more, faint Fresnel density inside. Highlights run up both sides.
    Additive, white: tint = barrier colour."""
    x, y = grid(S); ph = k / n_frames
    wob = _flow(x, y, ph, 700, 6, 5.0) * .018                # the outline itself ripples
    rho = np.hypot(x / w, y / h) + wob
    ang = np.abs(np.arctan2(x, y)) / math.pi                # 0 bottom, 1 top
    run = (.5 + .5 * np.cos(2 * math.pi * (ang * 2 - ph))) ** 4
    fl = .5 + .5 * _warped(x, y, ph, 710, 6.0, .3)
    low = .55 + .45 * np.clip(y / h, 0, 1) ** .6
    edge = np.exp(-((rho - 1) / .016) ** 2) * (.35 + .35 * fl + .3 * run) * low
    glow = np.exp(-((rho - 1) / .07) ** 2) * (.15 + .15 * fl + .1 * run) * low
    inside = (rho < 1) * (.03 + .3 * np.clip(rho, 0, 1) ** 12)
    return np.ones((S, S, 3), np.float32), np.clip(edge + glow + inside, 0, 1)


def shield_veins_frame(S, k, n_frames=16):
    """Energy veins crawling over a bubble's skin (looped flipbook): thin, branching, liquid filaments of light
    that drift and curl inside a soft round patch. Additive, white: tint = colour."""
    x, y = grid(S); ph = k / n_frames; r = np.hypot(x, y)
    f = _warped(x, y, ph, 720, 4.0, .45, (1.0, -.4))
    vein = np.clip(1 - np.abs(f) * 1.8, 0, 1) ** 5          # ridges of the flow -> filaments
    g = _warped(x, y, ph, 730, 2.0, .3, (1.0, -.4))
    a = vein * (.45 + .55 * (.5 + .5 * g)) + .06
    return np.ones((S, S, 3), np.float32), np.clip(a * np.clip(1 - r, 0, 1) ** 1.3, 0, 1)


def energy_cloud_frame(S, k, n_frames=16):
    """Boiling energy cloud lit from inside (looped flipbook): billowy mass whose scalloped outline rolls upward,
    bright soft rim, darker body with faint inner streaks (the reference bubble's inner clouds).
    Additive, white: tint = colour."""
    x, y = grid(S); ph = k / n_frames; r = np.hypot(x * .95, y * 1.1)
    f = _warped(x, y, ph, 740, 3.2, .35)
    f2 = _warped(x, y, ph, 760, 7.5, .25); f3 = _flow(x, y, ph, 770, 7, 14.0)
    d = .55 - r + .13 * f + .06 * f2 + .03 * f3             # > 0 inside; billows on billows roll up the edge
    rim = np.exp(-((d - .035) / .045) ** 2) * (.75 - .25 * y)
    halo = np.exp(-(np.maximum(-d, 0) / .08) ** 2) * (d < 0) * .22
    streak = (.5 + .5 * _warped(x, y, ph, 750, 6.0, .4)) ** 3
    body = sstep(0, .2, d) * (.22 + .25 * streak)
    return np.ones((S, S, 3), np.float32), np.clip(rim + halo + body, 0, 1)


def shield_wisp(S, v=0):
    """Rim-lit energy cloud (the inner flow of a barrier bubble): a billowy mass, faint inside, with a bright
    soft edge along its scalloped outline. Additive, white: tint = colour."""
    x, y = grid(S); r = np.hypot(x, y)
    n = fbm(S, 3, 660 + v, base=3)
    d = (n - .5) * 1.1 + .5 - r                              # > 0 inside the cloud, billowy outline at 0
    rim = np.exp(-((d - .03) / .05) ** 2) * (.8 - .3 * y)   # edge lit more on top, like rising energy
    glow = np.exp(-(np.maximum(-d, 0) / .1) ** 2) * (d < 0) * .25
    body = sstep(0, .25, d) * (.3 + .25 * fbm(S, 4, 680 + v, base=5))
    a = np.clip(rim + glow + body, 0, 1) * np.clip(1 - r, 0, 1) ** .5
    return np.ones((S, S, 3), np.float32), a


# ------------------------------------------------------------------ cercle magique au sol (bc_zone)
# Pièces d'un cercle magique géométrique (sans runes), dessinées pour un sprite à plat au sol (orientation 2), toutes
# à la même échelle : l'anneau extérieur est à 0,955 du rayon du sprite. Chaque pièce a une symétrie de rotation
# (10°, 30°…) : en boucle, une copie neuve à rotation 0 recouvre exactement l'ancienne qui a tourné d'une symétrie.
# Additives, blanches : teinte = couleur de la particule.
def _ring_line(r, r0, w=.0045, glow=.02, gk=.25):
    return np.exp(-((r - r0) / w) ** 2) + gk * np.exp(-((r - r0) / glow) ** 2)


def _seg_dist(x, y, p, q):
    px, py = x - p[0], y - p[1]; dx, dy = q[0] - p[0], q[1] - p[1]
    t = np.clip((px * dx + py * dy) / (dx * dx + dy * dy), 0, 1)
    return np.hypot(px - t * dx, py - t * dy)


def _line(d, w=.0045, glow=.018, gk=.25):
    return np.exp(-(d / w) ** 2) + gk * np.exp(-(d / glow) ** 2)


def mc_outer(S):
    """Outer band: bright double ring, 36 radial ticks between the lines, faint fill fading toward the centre."""
    x, y = grid(S); r = np.hypot(x, y); ang = np.arctan2(y, x)
    a = _ring_line(r, .955, .006) * 1.0 + _ring_line(r, .895) * .8
    k = 36; ph = (ang / (2 * math.pi) * k) % 1
    tick = np.exp(-((np.minimum(ph, 1 - ph) * 2 * math.pi * r / k) / .004) ** 2) * ((r > .905) & (r < .945))
    a += tick * .8
    a += np.clip((r - .55) / .4, 0, 1) ** 2 * (r < .955) * .07          # centre plus transparent que le bord
    return np.ones((S, S, 3), np.float32), np.clip(a, 0, 1)


def mc_orbit(S):
    """Middle band: two thin rings and 12 small satellite circles riding on them (30° symmetry)."""
    x, y = grid(S); r = np.hypot(x, y)
    a = _ring_line(r, .70) * .9 + _ring_line(r, .62) * .55
    for i in range(12):
        t = 2 * math.pi * i / 12; cx, cy = .66 * math.cos(t), .66 * math.sin(t)
        d = np.hypot(x - cx, y - cy)
        a += _ring_line(d, .042, .004, .012) * .9 + np.exp(-(d / .008) ** 2) * .8
    return np.ones((S, S, 3), np.float32), np.clip(a, 0, 1)


def mc_star(S):
    """Geometry: two hexagrams 30° apart (a 12-point star of 4 triangles) inscribed in the outer band, plus the
    dodecagon through their inner crossings (30° symmetry)."""
    x, y = grid(S); d = np.full((S, S), 9.0, np.float32)
    R = .86
    for tri in range(4):
        base = math.radians(90 + 30 * tri)
        pts = [(R * math.cos(base + 2 * math.pi * j / 3), R * math.sin(base + 2 * math.pi * j / 3)) for j in range(3)]
        for j in range(3):
            d = np.minimum(d, _seg_dist(x, y, pts[j], pts[(j + 1) % 3]))
    a = _line(d, .0035, .015, .2) * .75
    r = np.hypot(x, y)
    a += _ring_line(r, R, .0035, .012, .2) * .5
    return np.ones((S, S, 3), np.float32), np.clip(a, 0, 1)


def mc_inner(S):
    """Small central rings with 12 tiny diamonds (30° symmetry); the centre itself stays empty."""
    x, y = grid(S); r = np.hypot(x, y); ang = np.arctan2(y, x)
    a = _ring_line(r, .30, .004) * .9 + _ring_line(r, .255, .0035) * .5
    k = 12; ph = ((ang / (2 * math.pi) * k) % 1 - .5) * 2 * math.pi * .345 / k     # tangential offset (sprite units)
    dia = (np.abs(ph) / .022 + np.abs(r - .345) / .03) < 1
    a += dia * .55 + np.exp(-((np.abs(ph) / .022 + np.abs(r - .345) / .03) - 1) ** 2 / .02) * .25
    return np.ones((S, S, 3), np.float32), np.clip(a, 0, 1)


def mc_edge_frame(S, k, n_frames=8):
    """Energy along the circle's edge (looped flipbook): soft glow band on the outer ring whose brightness flows
    around the circle and breathes slightly. Radially symmetric on average, no rotation needed."""
    x, y = grid(S); r = np.hypot(x, y); ang = np.arctan2(y, x); ph = k / n_frames
    flow = .5 + .5 * np.sin(5 * ang - 2 * math.pi * ph) * np.sin(3 * ang + 2 * math.pi * 2 * ph + 1.3)
    band = np.exp(-((r - .955) / (.035 + .012 * flow)) ** 2)
    inner = np.exp(-((r - .9) / .12) ** 2) * .18
    return np.ones((S, S, 3), np.float32), np.clip(band * (.35 + .5 * flow) + inner, 0, 1)


# ------------------------------------------------------------------ registre
def _seq_single(n): return [[i] for i in range(n)]
REG = {
    # additifs (énergie, lumière)
    'glow':         dict(fn=lambda S: sh.glow(S), S=128, blend='add', desc='halo doux universel (cœur, aura, flash)'),
    'glow_hard':    dict(fn=lambda S: sh.glow(S, core=.12, power=4), S=128, blend='add', desc='point lumineux concentré'),
    'spark':        dict(fn=lambda S: sh.spark(S), S=128, blend='add', desc='étincelle allongée (traînées, pluie, éclats)'),
    'star':         dict(fn=lambda S: sh.pollen(S), S=64, blend='add', desc='scintillement / pollen / braise'),
    'flare':        dict(fn=lambda S: flare(S), S=128, blend='add', desc='éclat en croix (flash d\'impact)'),
    'ring':         dict(fn=lambda S: sh.ring(S), S=256, blend='add', desc='anneau fin (onde de choc, bordure de zone)'),
    'ring_soft':    dict(fn=lambda S: soft_ring(S), S=256, blend='add', desc='anneau épais et doux'),
    'veins':        dict(fn=lambda S: sh.veins_decal(S, seed=4), S=512, blend='add', desc='réseau de nervures/racines lumineuses (décal sol)'),
    'magic_circle': dict(fn=lambda S: magic_circle(S), S=512, blend='add', desc='cercle rituel / sceau (décal sol)'),
    'streak':       dict(fn=lambda S: streak(S), S=128, blend='add', desc='traînée de vitesse : tête brillante, queue fine'),
    'slash':        dict(fn=lambda S: slash(S), S=256, blend='add', desc='coup / arc en croissant (slash, fouet)'),
    'noise':        dict(fn=None, S=128, blend='add', grid=(2, 2), seqs=_seq_single(4), multi=lambda S, i: noise_puff(S, i),
                         desc='bouffée d\'énergie déchirée (4 variantes, volume secondaire)'),
    'energy':       dict(fn=None, S=128, blend='add', grid=(4, 2), seqs=[list(range(8))], rate=16, anim=energy_frame,
                         desc='flammèche d\'énergie animée 8 images (chakra, aura)'),
    'dust':         dict(fn=None, S=128, blend='alpha', grid=(2, 2), seqs=_seq_single(4), multi=lambda S, i: sh.dust(S, i),
                         desc='poussière / sable (4 variantes, à teinter)'),
    'chakra_tongue': dict(fn=None, S=128, blend='alpha', grid=(4, 2), seqs=[list(range(8))], rate=10, loop=True,
                          anim=chakra_tongue_frame, desc='flamme de chakra anime (3 bandes), translucide, animée'),
    'chakra_lick':  dict(fn=None, S=128, blend='add', grid=(4, 2), seqs=[list(range(8))], rate=10, loop=True,
                          anim=lambda S, k, n: chakra_tongue_frame(S, k, n, seed=1), desc='même flamme, additive (reflets)'),
    'chakra_body':  dict(fn=None, S=128, blend='alpha', grid=(2, 2), seqs=_seq_single(4), multi=lambda S, i: chakra_body(S, i),
                          desc='volume de chakra translucide (remplissage de silhouette)'),
    'softline':     dict(fn=lambda S: soft_line(S), S=64, blend='add', tiled=True, desc='ligne lumineuse douce tuilable (cordes, contours)'),
    'ink_spike':    dict(fn=None, S=256, blend='alpha', grid=(2, 2), seqs=_seq_single(4), multi=lambda S, i: ink_spike(S, i),
                         desc='flamme d\'encre noire à pointes déchirées, cœur rouge (couleurs intégrées, particule blanche)'),
    'miasma':       dict(fn=None, S=128, blend='alpha', grid=(4, 2), seqs=[list(range(8))], rate=6, loop=True,
                         anim=miasma_frame, desc='miasme démoniaque qui bouillonne (noir-violet, éclairé rouge par dessous)'),
    'crackle':      dict(fn=None, S=128, blend='add', grid=(2, 2), seqs=_seq_single(4), multi=lambda S, i: crackle(S, i),
                         desc='arc brisé ramifié (étincelle démoniaque), à teinter'),
    'sparkle':      dict(fn=None, S=128, blend='add', grid=(2, 2), seqs=_seq_single(4), multi=lambda S, i: sparkle(S, i),
                         desc='éclat à 4 branches (paillettes cosmiques), à teinter'),
    'nebula':       dict(fn=None, S=256, blend='add', grid=(2, 2), seqs=_seq_single(4), multi=lambda S, i: nebula(S, i),
                         desc='volute de nébuleuse filamenteuse, à teinter'),
    'curl':         dict(fn=None, S=128, blend='add', grid=(2, 2), seqs=_seq_single(4), multi=lambda S, i: curl(S, i),
                         desc='boucle d\'énergie fine en spirale, à teinter'),
    'black_bolt':   dict(fn=None, S=256, blend='alpha', grid=(2, 2), seqs=_seq_single(4), multi=lambda S, i: black_bolt(S, i),
                         desc='arc de foudre noire (encre + cœur blanc-bleu), couleurs intégrées'),
    'lightning_anim': dict(fn=None, S=128, blend='alpha', grid=(4, 4), seqs=[list(range(8)), list(range(8, 16))],
                           anim=lightning_anim_frame, desc='décharge de foudre noire animée (frappe, crépite, s\'éteint), 2 séquences'),
    'bolt_strand':  dict(fn=lambda S: bolt_strand(S), S=128, blend='add', tiled=True,
                         desc='éclair brisé tuilable pour cordes (cœur blanc, halo à teinter)'),
    'hex_cell':     dict(fn=None, S=128, blend='add', grid=(2, 1), seqs=[[0], [1]], multi=lambda S, i: hex_cell(S, i),
                         desc='alvéole de barrière hexagonale (bord net, remplissage léger), à teinter'),
    'hex_patch':    dict(fn=lambda S: hex_patch(S), S=256, blend='add', desc='plaque d\'alvéoles qui s\'illumine (impact sur bouclier)'),
    'hex_shard':    dict(fn=None, S=128, blend='add', grid=(2, 2), seqs=_seq_single(4), multi=lambda S, i: hex_shard(S, i),
                         desc='éclat d\'alvéole brisée (rupture de bouclier)'),
    'shield_film':  dict(fn=None, S=128, blend='add', grid=(2, 2), seqs=_seq_single(4), multi=lambda S, i: shield_film(S, i),
                         desc='peau de barrière liquide (masse douce + reflets ondulés), à superposer en grand nombre'),
    'shield_veins': dict(fn=None, S=128, blend='add', grid=(4, 4), seqs=[list(range(16))], rate=1, loop=True,
                         anim=shield_veins_frame, desc='veines d\'énergie liquides qui coulent (peau de bulle), animée en boucle'),
    'energy_cloud': dict(fn=None, S=128, blend='add', grid=(4, 4), seqs=[list(range(16))], rate=1, loop=True,
                         anim=energy_cloud_frame, desc='nuage d\'énergie qui bouillonne, bord lumineux, animé en boucle'),
    'mc_outer':     dict(fn=lambda S: mc_outer(S), S=512, blend='add', desc='cercle magique : double anneau extérieur gradué (36 graduations)'),
    'mc_orbit':     dict(fn=lambda S: mc_orbit(S), S=512, blend='add', desc='cercle magique : anneaux et 12 cercles satellites'),
    'mc_star':      dict(fn=lambda S: mc_star(S), S=512, blend='add', desc='cercle magique : étoile à 12 branches (4 triangles)'),
    'mc_inner':     dict(fn=lambda S: mc_inner(S), S=256, blend='add', desc='cercle magique : petits anneaux centraux et losanges'),
    'mc_edge':      dict(fn=None, S=256, blend='add', grid=(4, 2), seqs=[list(range(8))], rate=1, loop=True,
                         anim=mc_edge_frame, desc='cercle magique : énergie qui coule le long du contour, animée en boucle'),
    'shield_rim':   dict(fn=None, S=256, blend='add', grid=(4, 2), seqs=[list(range(8))], rate=1, loop=True,
                         anim=shield_rim_frame, desc='bulle de bouclier anime vue de face : contour net, intérieur en aplats, reflets qui montent'),
    'shield_wisp':  dict(fn=None, S=128, blend='add', grid=(2, 2), seqs=_seq_single(4), multi=lambda S, i: shield_wisp(S, i),
                         desc='nuage d\'énergie à bord lumineux (flux intérieur d\'une bulle de bouclier)'),
    'rune_line':    dict(fn=lambda S: rune_line(S), S=128, blend='add', tiled=True,
                         desc='trait de cercle magique (segments + nœuds) tuilable pour cordes, défile pour tourner'),
    'black_strand': dict(fn=lambda S: black_strand(S), S=64, blend='alpha', tiled=True,
                         desc='ligne de foudre noire tuilable pour cordes (cœur blanc-bleu)'),
    'strand':       dict(fn=lambda S: sh.thread(S), S=128, blend='add', desc='fil d\'énergie tressé tuilable (cordes, liens)'),
    'lightning':    dict(fn=lambda S: lightning_strand(S), S=128, blend='add', desc='brin d\'éclair tuilable (cordes)'),
    'flame':        dict(fn=None, S=128, blend='add', grid=(4, 4), seqs=[list(range(16))], rate=24, anim=flame_frame,
                         desc='flamme animée 16 images (feu, chakra ardent)'),
    # translucides (matière)
    'smoke':        dict(fn=None, S=128, blend='alpha', grid=(2, 2), seqs=_seq_single(4), multi=lambda S, i: smoke(S, i),
                         desc='fumée / poussière / brume (4 variantes, à teinter)'),
    'explosion':    dict(fn=None, S=128, blend='alpha', grid=(4, 4), seqs=[list(range(16))], rate=16, anim=explosion_frame,
                         desc='boule de feu qui se dissipe (16 images, jouer sur la vie)'),
    'shard':        dict(fn=None, S=128, blend='alpha', grid=(2, 2), seqs=_seq_single(4), multi=lambda S, i: shard(S, i),
                         desc='éclats anguleux roche/cristal/glace (4 variantes)'),
    'leaf':         dict(fn=None, S=256, blend='alpha', grid=(2, 2), seqs=_seq_single(4), multi=lambda S, i: sh.leaf(S, i, seed=i),
                         desc='feuilles vertes détaillées (4 variantes)'),
    'dryleaf':      dict(fn=None, S=256, blend='alpha', grid=(2, 2), seqs=_seq_single(4), multi=lambda S, i: sh.leaf(S, i, seed=10 + i, dry=True),
                         desc='feuilles mortes (4 variantes)'),
    'petal':        dict(fn=None, S=256, blend='alpha', grid=(2, 2), seqs=_seq_single(4), multi=lambda S, i: sh.petal(S, i, seed=i),
                         desc='pétales clairs à teinter (4 variantes)'),
    'feather':      dict(fn=None, S=128, blend='alpha', grid=(2, 2), seqs=_seq_single(4), multi=lambda S, i: feather(S, i),
                         desc='plumes claires à teinter'),
    'droplet':      dict(fn=lambda S: droplet(S), S=128, blend='alpha', desc='goutte (eau, sang, poison) à teinter'),
    'crack':        dict(fn=lambda S: crack_decal(S), S=512, blend='alpha', desc='fissures au sol (décal sombre)'),
    'seed':         dict(fn=lambda S: sh.seed_tex(S), S=256, blend='alpha', desc='graine à nervures lumineuses'),
    'flower':       dict(fn=None, S=256, blend='alpha', grid=(4, 4),
                         seqs=[[0], [0, 1, 2, 3, 4, 5], [5], [5, 6, 7, 8, 9, 10], [11], [12, 13, 14, 15], list(range(12))], rate=10,
                         anim=lambda S, k, n, seed=0: sh.flower_frame(S, min(1, k / 10.0)) if k < 12 else sh.flower_frame(S, 1, (k - 11) * .25),
                         desc='fleur qui éclot (seq 6 = éclosion complète, 5 = fanaison, 4 = pleine)'),
    'mimosa':       dict(fn=None, S=256, blend='alpha', grid=(2, 1), seqs=[[0], [1]], multi=lambda S, i: sh.mimosa(S, bool(i), seed=1),
                         desc='touffe végétale vue de dessus (seq 0 ouverte, 1 repliée)'),
    'stem':         dict(fn=None, S=256, blend='alpha', grid=(2, 1), seqs=[[0], [1]], multi=lambda S, i: sh.stem(S, i, seed=i),
                         desc='tige avec feuilles, verticale (orientation 1)'),
    'sprout':       dict(fn=lambda S: sh.sprout(S), S=128, blend='alpha', desc='jeune pousse verticale'),
    'cocoon':       dict(fn=None, S=256, blend='alpha', grid=(2, 2), seqs=[[0], [1], [2], [3], [0, 1, 2, 3]],
                         multi=lambda S, i: sh.cocoon_frame(S, i), desc='bouton/cocon vertical qui s\'ouvre (seq 4 = ouverture)'),
    'valve':        dict(fn=lambda S: sh.valve(S), S=256, blend='alpha', desc='coque/valve incurvée'),
    'pompom':       dict(fn=lambda S: sh.pompom(S, seed=3), S=128, blend='alpha', desc='houppe de filaments'),
}

def describe():
    return '\n'.join(f'{k:13s} {v["blend"]:5s}  {v["desc"]}' for k, v in REG.items())

# ------------------------------------------------------------------ fabrication
def _R(fn, S, *a, **k):
    c, al = fn(S * 2, *a, **k); return to_img(c, al, S)

def meta(name):
    """Texture info without rendering (for lint)."""
    t = REG[name]
    return dict(grid=t.get('grid', (1, 1)), seqs=t.get('seqs', [[0]]), blend=t['blend'], S=t['S'], rate=t.get('rate', 10))


def make(name, custom=None, size=None):
    """Retourne dict(img, grid, seqs, blend, S, rate). size: frame size override (power of two) to save memory."""
    with np.errstate(invalid='ignore', divide='ignore'):        # NaN are cleaned in shapes.to_img
        return _make(name, custom, size)


def _make(name, custom=None, size=None):
    if custom:                                                   # texture fournie : dossier/planche de PNG
        return load_custom(name, custom)
    t = REG[name]; S = int(size or t['S'])
    cols, rows = t.get('grid', (1, 1))
    if 'anim' in t:
        n = cols * rows; frames = [_R(t['anim'], S, k, n) for k in range(n)]
    elif 'multi' in t:
        frames = [_R(lambda SS, i=i: t['multi'](SS, i), S) for i in range(cols * rows)]
    else:
        frames = [_R(t['fn'], S)]
    big = Image.new('RGBA', (S * cols, S * rows), (0, 0, 0, 0))
    for i, fr in enumerate(frames): big.paste(fr, ((i % cols) * S, (i // cols) * S))
    return dict(img=big, grid=(cols, rows), seqs=t.get('seqs', [[0]]), blend=t['blend'], S=S, rate=t.get('rate', 10))

def load_custom(name, c):
    """c = {src: 'dossier/*.png' ou 'planche.png', blend: add|alpha, grid: [c, r], fps: 24, loop: false}"""
    files = sorted(glob.glob(c['src'])) if any(ch in c['src'] for ch in '*?') else [c['src']]
    if len(files) > 1:                                           # séquence d'images -> planche
        n = len(files); cols = int(math.ceil(math.sqrt(n))); rows = int(math.ceil(n / cols))
        S = c.get('size', 256)
        big = Image.new('RGBA', (S * cols, S * rows), (0, 0, 0, 0))
        for i, f in enumerate(files):
            im = Image.open(f).convert('RGBA').resize((S, S), Image.LANCZOS)
            big.paste(im, ((i % cols) * S, (i // cols) * S))
        seqs = [list(range(n))]
    else:
        big = Image.open(files[0]).convert('RGBA'); cols, rows = c.get('grid', [1, 1])
        S = big.size[0] // cols; n = cols * rows
        seqs = [list(range(n))] if c.get('animated', False) else [[i] for i in range(n)]
    return dict(img=big, grid=(cols, rows), seqs=seqs, blend=c.get('blend', 'alpha'), S=S, rate=c.get('fps', 10))

def export(name, t, matdir, pngdir, vmt_extra=None):
    """Écrit <matdir>/<name>.vtf/.vmt et <pngdir>/<name>.png (aperçu)."""
    os.makedirs(matdir, exist_ok=True); os.makedirs(pngdir, exist_ok=True)
    img = t['img']
    if t['blend'] == 'add':
        arr = np.asarray(img, np.float32) / 255; arr[..., :3] *= arr[..., 3:4]
        img_v = Image.fromarray((arr * 255 + .5).astype(np.uint8), 'RGBA')
    else:
        img_v = _dilate(img)
    W, H = img_v.size
    p2 = lambda n: 1 << (n - 1).bit_length()
    if (p2(W), p2(H)) != (W, H):
        cv = Image.new('RGBA', (p2(W), p2(H)), (0, 0, 0, 0)); cv.paste(img_v, (0, 0)); img_v = cv
    W2, H2 = img_v.size; cols, rows = t['grid']; S = t['S']
    tiled = name in ('strand', 'lightning') or t.get('tiled')
    path = os.path.join(matdir, name + '.vtf')
    if (cols, rows) != (1, 1):
        # Sheets: VTF 7.4 + sheet resource v1 (4 texcoord sets per frame), uncompressed. This layout is the one
        # verified in GMod; srctools' sheet v0 was drawn as the WHOLE sheet in game (leçon 30/09/2026).
        seqs = []
        for frames in t['seqs']:
            rects = [((f % cols) * S / W2, (f // cols) * S / H2, (f % cols + 1) * S / W2, (f // cols + 1) * S / H2)
                     for f in frames]
            seqs.append((rects, len(frames) > 1 and not (t.get('loop') or REG.get(name, {}).get('loop'))))
        VT.write_sheet(path, np.asarray(img_v, np.uint8), seqs, not tiled, not tiled)
    else:
        flags = VTFFlags.NO_LOD if tiled else (VTFFlags.CLAMP_S | VTFFlags.CLAMP_T | VTFFlags.NO_LOD)
        v = VTF(W2, H2, fmt=ImageFormats.DXT5, flags=flags)
        v.get().copy_from(img_v.tobytes()); v.compute_mipmaps()
        with open(path, 'wb') as f:
            v.save(f, version=(7, 4), asw_or_later=False)
    lines = ['"SpriteCard"', '{', f'\t"$basetexture" "{os.path.basename(matdir)}/{name}"', '\t"$vertexcolor" "1"', '\t"$vertexalpha" "1"',
             '\t"$additive" "1"' if t['blend'] == 'add' else '\t"$translucent" "1"']
    animated = any(len(s) > 1 for s in t['seqs'])
    if not animated: lines.append('\t"$blendframes" "0"')
    for k, val in (vmt_extra or {}).items(): lines.append(f'\t"{k}" "{val}"')
    lines.append('}')
    open(os.path.join(matdir, name + '.vmt'), 'w', newline='\r\n').write('\n'.join(lines) + '\n')
    t['img'].save(os.path.join(pngdir, name + '.png'))

def _dilate(img, it=6):
    """Étend les couleurs sous les zones transparentes (évite les bords noirs dans les mips)."""
    a = np.asarray(img, np.float32) / 255; rgb = a[..., :3].copy(); al = a[..., 3]
    m = (al > .02).astype(np.float32)
    for _ in range(it):
        acc = np.zeros_like(rgb); cnt = np.zeros_like(m)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            acc += np.roll(np.roll(rgb * m[..., None], dy, 0), dx, 1); cnt += np.roll(np.roll(m, dy, 0), dx, 1)
        fill = (m == 0) & (cnt > 0)
        rgb[fill] = acc[fill] / cnt[fill][:, None]; m = np.maximum(m, fill.astype(np.float32))
    return Image.fromarray((np.dstack([rgb, al]) * 255 + .5).astype(np.uint8), 'RGBA')


# ------------------------------------------------------------------ pack Sarada / Ōhirume (textures/sarada.py)
from . import sarada as _sarada                                    # noqa: E402
REG.update(_sarada.REG)
