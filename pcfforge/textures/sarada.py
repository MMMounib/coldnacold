"""Textures du pack « Sarada — Mangekyō Sharingan / Ōhirume » (sarada_ohirume.pcf).

Langage visuel commun : anime cel-shading, bords nets (anticrénelés), 2 à 3 tons, couleurs INTÉGRÉES (la particule
reste blanche) pour tenir la palette au pixel près :
  BLACK #070405 · DARK CRIMSON #3a0610 · DEEP RED #6e0a18 · CRIMSON #a3101f · SCARLET #d4202a · BRIGHT RED #ff3c3c (rare)
Matière (noir, carmin) = mélange alpha : elle reste sombre et lisible sur fond clair comme sur fond sombre.
Additif = seulement sarada_glow (halo très faible) et sarada_spark (minuscule accent rouge vif).

Motif signature partagé : le Mangekyō de Sarada (pupille sombre + rayons triangulaires en soleil) -> les fragments
sont des triangles, le target est un iris, l'œil porte le motif.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from .shapes import grid, sstep, fbm, hexc

BLACK = hexc('#070405')
DKCRIM = hexc('#3a0610')
DEEP = hexc('#6e0a18')
CRIM = hexc('#a3101f')
SCAR = hexc('#d4202a')
BRIGHT = hexc('#ff3c3c')


def _mix(a, b, t):
    t = np.clip(t, 0, 1)[..., None] if np.ndim(t) else t
    return a * (1 - t) + b * t


def _col(c, S):
    return np.ones((S, S, 3), np.float32) * c


def _edge(d, S, w=1.2):
    """Hard but anti-aliased edge of a signed distance d (> 0 inside, in sprite units)."""
    e = w * 2.0 / S
    return np.clip(.5 + d / (2 * e), 0, 1)


def _wave(x, y, ph, seed, n=6, k=3.0, drift=(0.0, -1.0)):
    """Looping travelling-wave field in about [-1, 1] (whole turns per loop -> seamless flipbooks)."""
    r_ = np.random.default_rng(seed); acc = np.zeros_like(x)
    for i in range(n):
        a = r_.uniform(0, 2 * math.pi); kk = k * r_.uniform(.6, 1.4)
        kx, ky = kk * math.cos(a), kk * math.sin(a)
        sgn = 1 if (kx * drift[0] + ky * drift[1]) <= 0 else -1
        acc += np.sin(kx * x + ky * y + sgn * 2 * math.pi * (1 + i % 2) * ph + r_.uniform(0, 6.28))
    return acc / math.sqrt(n)


def _angle_noise(ang, seed, k=5, amp=1.0):
    """Smooth periodic noise along the angle (for irregular rings)."""
    r_ = np.random.default_rng(seed); acc = np.zeros_like(ang)
    for i in range(1, k + 1):
        acc += r_.uniform(-1, 1) / i * np.sin(i * ang + r_.uniform(0, 6.28))
    return acc * amp


# ------------------------------------------------------------------ Ōhirume : la sphère
def ohirume_void(S):
    """Black core: deep, clean, dense. Darkest at the centre, a hair lifted toward the edge (reads as a ball that
    swallows light), thin dark-crimson inner rim so it never melts into a black background."""
    x, y = grid(S); r = np.hypot(x, y); R = .80
    inside = _edge(R - r, S)
    t = (r / R) ** 3
    col = _mix(hexc('#020101'), hexc('#1a0508'), t)
    col = _mix(col, DKCRIM, sstep(R - .05, R - .01, r) * .9)            # inner rim
    return col, inside


def ohirume_core(S):
    """Dark energy shell: a cel-shaded band hugging the void (hollow centre), deep red to dark crimson, with a hard
    crimson crescent highlight on the upper-left and a black outline. Same scale as ohirume_void (core at .80)."""
    x, y = grid(S); r = np.hypot(x, y); ang = np.arctan2(y, x)
    r0, r1 = .78, .90 + .012 * np.sin(3 * ang + 1.1)
    band = _edge(r - r0, S) * _edge(r1 - r, S)
    u = np.clip((r - r0) / (r1 - r0), 0, 1)
    col = _mix(DKCRIM, BLACK, u ** 1.5)
    light = np.cos(ang - math.radians(-135))                           # light from the upper left (y down)
    cres = _edge(light - .55, S, 3) * _edge(.55 - abs(u - .45), S, 2)
    col = _mix(col, CRIM, cres * .85)
    col = _mix(col, BLACK, _edge(r - (r1 - .018), S))                  # outline
    return col, band * .92


def ohirume_ring(S, v=0):
    """Red gravity ring: very thin, broken into tapered arcs, thickness varying along the angle (not a perfect
    circle). Crimson with a scarlet core line. 2 variants (3 or 4 arcs)."""
    x, y = grid(S); r = np.hypot(x, y); ang = np.arctan2(y, x)
    n_arc = 3 + v
    r_c = .94 + .012 * _angle_noise(ang, 300 + v, 4)
    ph = (ang / (2 * math.pi) * n_arc + .17 * v) % 1
    gap = .1 + .05 * np.sin(ang * 2 + v)
    seg = np.clip(np.minimum(ph - gap / 2, 1 - gap / 2 - ph) / .12, 0, 1)   # tapered arc ends
    th = (.006 + .012 * (.5 + .5 * _angle_noise(ang, 310 + v, 3))) * seg
    d = th - np.abs(r - r_c)
    a = _edge(d, S, 1.0) * (seg > 0)
    core = _edge(th * .35 - np.abs(r - r_c), S, .8)
    col = _mix(CRIM, SCAR, core)
    return col, a


def ohirume_distort_frame(S, k, n=16):
    """Outer distortion (looped flipbook): a few thin anime warp strokes spiralling INTO the sphere (3 long arms +
    3 faint ones), tapered toward the core. Hollow centre (nothing inside .46 of the sprite = inside the gravity ring
    when the sprite is 2.1 x the core). Dark crimson -> black: space being bent toward the core."""
    x, y = grid(S); r = np.hypot(x, y) + 1e-6; ang = np.arctan2(y, x); ph = k / n
    def arms(m, pitch, ph_off, width):
        f = m * ang + pitch * np.log(r) + 2 * math.pi * (ph + ph_off)
        return sstep(1 - width, 1 - width * .25, np.cos(f))
    w = .02 + .05 * sstep(.46, 1.0, r)                                  # thicker outside, needle-thin near the core
    main = arms(5, 5.0, 0, w * .7) * (.55 + .45 * np.cos(ang * 2 + 1.0) ** 2)    # uneven arms: no pinwheel
    faint = arms(5, 5.0, .5, w * .45) * .35
    band = sstep(.46, .6, r) * sstep(.99, .78, r)
    a = np.clip(main + faint, 0, 1) * band
    col = _mix(BLACK, DEEP, sstep(.5, .85, r))
    return col, a * .85


def ohirume_gravity(S):
    """Matter drawn into the sphere: a round mote, crimson heart and black rim, stretched into a needle by the trail
    renderer along its velocity (toward the core)."""
    x, y = grid(S); r = np.hypot(x, y)
    a = _edge(.62 - r, S, 2)
    col = _mix(CRIM, BLACK, sstep(.15, .5, r))
    return col, a


def ohirume_streak(S):
    """Tileable ribbon for ropes (projectile wake, pull filaments): black band, crimson edges, a scarlet thread
    that breaks along the length (tiles along U)."""
    x, y = grid(S); u = (x + 1) / 2
    w = .32 + .06 * np.sin(2 * math.pi * u * 2)
    band = _edge(w - np.abs(y), S, 1.5)
    edge = _edge(.05 - np.abs(np.abs(y) - (w - .05)), S, 1)
    thread = _edge(.02 - np.abs(y - .04 * np.sin(2 * math.pi * u * 2 + .7)), S, .8)
    col = _mix(BLACK, DEEP, edge)
    col = _mix(col, CRIM, thread * (.6 + .4 * np.sin(2 * math.pi * u) ** 2))
    return col, np.clip(band, 0, 1) * .95


def _poly(S, pts, fill=255):
    im = Image.new('L', (S, S), 0); ImageDraw.Draw(im).polygon([((px + 1) * S / 2, (py + 1) * S / 2) for px, py in pts],
                                                               fill=fill)
    return np.asarray(im, np.float32) / 255


def ohirume_fragment(S, v=0):
    """Void shards: irregular angular splinters (4 variants), black with one lit crimson edge."""
    r_ = np.random.default_rng(330 + v)
    n = 4 + v % 2
    angs = np.sort(r_.uniform(0, 2 * math.pi, n))
    rad = r_.uniform(.45, .9, n) * np.array([1.0 if i % 2 == 0 else .55 for i in range(n)])
    pts = [(rad[i] * math.cos(angs[i]), rad[i] * math.sin(angs[i]) * .7) for i in range(n)]
    m = _poly(S, pts)
    lit = _poly(S, [(0, 0)] + pts[:2]) * m
    col = _mix(_col(BLACK, S), _col(CRIM, S), lit * .9)
    return col, m


# ------------------------------------------------------------------ Sarada : aura, œil, cible, traînée
def sarada_core(S):
    """Dense dark centre of the aura: a very soft dark-crimson-black presence, faint (no fog)."""
    x, y = grid(S); r = np.hypot(x, y)
    a = np.clip(1 - r, 0, 1) ** 2.2 * .55
    return _col(_mix(DKCRIM, BLACK, .6), S), a


def sarada_glow(S):
    """Red halo (ADDITIVE, very faint): brighter toward a soft ring than at the centre, so it never reads as a
    uniform glow disc. Deep red."""
    x, y = grid(S); r = np.hypot(x, y)
    a = np.exp(-((r - .55) / .25) ** 2) * .8 + np.exp(-(r / .4) ** 2) * .15
    return _col(DEEP * 1.4, S), np.clip(a * np.clip(1 - r, 0, 1) * 1.6, 0, 1)


def sarada_filament_frame(S, k, n=8):
    """Energy filament (looped flipbook): one very thin vertical line, tapered at both ends, a small wave running
    up it (the energy is alive). Crimson core, dark crimson sheath."""
    x, y = grid(S); ph = k / n
    yy = -y                                                           # up
    cx = .12 * np.sin(4.2 * yy - 2 * math.pi * ph) * (1 - yy ** 2)
    taper = np.clip(1 - np.abs(yy) ** 2, 0, 1)
    d = np.abs(x - cx)
    core = _edge(.018 * taper - d, S, .8)
    sheath = _edge(.05 * taper - d, S, 1.2)
    col = _mix(DKCRIM, CRIM, core)
    return col, np.clip(sheath * .55 + core, 0, 1) * taper ** .5


def sarada_spark(S):
    """Micro spark (ADDITIVE): tiny 4-point star, bright red heart. The only bright red of the pack: use sparingly."""
    x, y = grid(S); r = np.hypot(x, y)
    rays = np.maximum(np.exp(-(np.abs(x) / .05) ** 2) * np.clip(1 - np.abs(y), 0, 1) ** 3,
                      np.exp(-(np.abs(y) / .05) ** 2) * np.clip(1 - np.abs(x), 0, 1) ** 3)
    core = np.exp(-(r / .12) ** 2)
    return _col(BRIGHT, S), np.clip(rays * .8 + core, 0, 1)


def sarada_ring(S, v=0):
    """Target / iris pieces (3 sequences, same scale):
      0  outer lock arcs: 3 incomplete arcs of uneven length, tapered, a bright point at one end of each;
      1  iris: thin ring with 3 inward triangular teeth (the Mangekyō sun rays), black outline;
      2  inner orbit: hairline ring with 12 small points (an eye's ticks), very light."""
    x, y = grid(S); r = np.hypot(x, y); ang = np.arctan2(y, x)
    if v == 0:
        R = .92; spans = [(.05, 1.6), (2.3, 3.6), (4.2, 5.75)]
        a = np.zeros_like(r); pt = np.zeros_like(r)
        for i, (a0, a1) in enumerate(spans):
            t = ((ang - a0) % (2 * math.pi)) / (a1 - a0)
            on = (t >= 0) & (t <= 1)
            th = .022 * np.clip(np.sin(np.clip(t, 0, 1) * math.pi), 0, 1) ** .6 + .004
            a = np.maximum(a, _edge(th - np.abs(r - R), S, 1) * on)
            ex, ey = R * math.cos(a1), R * math.sin(a1)
            pt = np.maximum(pt, _edge(.03 - np.hypot(x - ex, y - ey), S, 1))
        col = _mix(_col(CRIM, S), _col(SCAR, S), pt)
        return col, np.clip(a + pt, 0, 1)
    if v == 1:
        R = .66
        ring = _edge(.012 - np.abs(r - R), S, 1)
        teeth = np.zeros_like(r)
        for i in range(3):
            t0 = 2 * math.pi * i / 3 + math.pi / 2
            p = [(R * math.cos(t0 - .16), R * math.sin(t0 - .16)), (R * math.cos(t0 + .16), R * math.sin(t0 + .16)),
                 (.44 * math.cos(t0), .44 * math.sin(t0))]
            teeth = np.maximum(teeth, _poly(S, p))
        m = np.clip(ring + teeth, 0, 1)
        col = _mix(_col(DEEP, S), _col(BLACK, S), teeth * .65)
        outline = _edge(.022 - np.abs(r - R), S, 1) * (1 - ring)
        return col * (1 - outline[..., None]) + BLACK * outline[..., None], np.clip(m + outline, 0, 1)
    R = .5
    ring = _edge(.005 - np.abs(r - R), S, .8) * .7
    k = 12; ph = (ang / (2 * math.pi) * k) % 1
    dots = _edge(.018 - np.hypot(np.minimum(ph, 1 - ph) * 2 * math.pi * R / k, r - R), S, .8)
    return _col(CRIM, S), np.clip(ring + dots, 0, 1)


def sarada_void(S):
    """Small pupil-like void (target core, eye dark edge): black disc, thin dark-crimson rim, soft outer fade."""
    x, y = grid(S); r = np.hypot(x, y)
    disc = _edge(.5 - r, S, 1.2)
    rim = _edge(.04 - np.abs(r - .52), S, 1)
    halo = np.exp(-((r - .55) / .15) ** 2) * (r > .55) * .35
    col = _mix(_col(BLACK, S), _col(DKCRIM, S), rim)
    return col, np.clip(disc + rim + halo, 0, 1)


def sarada_distort(S, v=0):
    """Space-bending ripple (4 variants): a wobbly double ring, thicker on one side, broken in two places — the air
    bent by an expanding pulse. Dark crimson to black, never a perfect circle."""
    x, y = grid(S); r = np.hypot(x, y); ang = np.arctan2(y, x)
    wob = .025 * _angle_noise(ang, 360 + v, 5)
    th = .012 + .02 * (.5 + .5 * np.cos(ang - v * 1.7))
    gap = sstep(.05, .25, np.abs(np.sin((ang - v) * 1.0)))             # two soft breaks
    outer = _edge(th - np.abs(r - (.88 + wob)), S, 1) * gap
    inner = _edge(th * .5 - np.abs(r - (.78 + wob * 1.3)), S, 1) * gap * .7
    col = _mix(_col(BLACK, S), _col(DEEP, S), np.clip(outer, 0, 1))
    return col, np.clip(outer + inner, 0, 1) * .9


def sarada_fragment(S, v=0):
    """Mangekyō shards: sharp blade-like triangles (the sun rays), black, one side lit by a thin crimson cel band
    (4 proportions)."""
    r_ = np.random.default_rng(370 + v)
    h = r_.uniform(.75, .95); w = r_.uniform(.22, .4); sk = r_.uniform(-.15, .15)
    tip, bl, br = (sk, -h), (-w, h * .7), (w, h * .7)
    m = _poly(S, [tip, bl, br])
    lit = _poly(S, [tip, bl, (bl[0] + .12 * (br[0] - bl[0]), bl[1])])   # thin band along the left edge
    col = _mix(_col(BLACK, S), _col(CRIM, S), lit * .95)
    return col, m


def sarada_streak(S):
    """Tileable ribbon for the attraction trail: wispy black edges, dark crimson body, a thin crimson line that
    flickers along its length (tiles along U)."""
    x, y = grid(S); u = (x + 1) / 2
    n = .5 + .5 * np.sin(2 * math.pi * (u * 2)) * np.sin(2 * math.pi * (u * 3) + 1.0)
    w = .38 + .08 * n
    band = sstep(w, w - .12, np.abs(y))
    line = _edge(.018 - np.abs(y - .05 * np.sin(2 * math.pi * u * 2)), S, .8) * (.45 + .55 * n)
    col = _mix(_col(BLACK, S), _col(DKCRIM, S), sstep(w, .05, np.abs(y)))
    col = _mix(col, CRIM, line)
    return col, np.clip(band * .85 + line, 0, 1)


# ------------------------------------------------------------------ Mangekyō Sharingan de Sarada
def mangekyo(S, part='color'):
    """Sarada's Mangekyō Sharingan — ARTISTIC INTERPRETATION from published descriptions (« sun-like pattern: a dark
    round pupil with triangular rays stemming from it », 8 rays per several sources); not traced from an official
    image. part: 'color' (RGBA eye), 'mask' (white = black pattern), 'emissive' (glow map of the red iris)."""
    x, y = grid(S); r = np.hypot(x, y); ang = np.arctan2(y, x)
    iris = _edge(.96 - r, S, 1.2)
    limbus = _edge(r - .9, S, 1.2) * iris
    pupil = _edge(.17 - r, S, 1.2)
    rays = np.zeros_like(r)
    for i in range(8):
        t = 2 * math.pi * i / 8 - math.pi / 2
        hw = .36                                                         # half-angle of the ray base (rad)
        base = .15                                                       # broad triangular rays from the pupil
        p = [(base * math.cos(t - hw), base * math.sin(t - hw)), (base * math.cos(t + hw), base * math.sin(t + hw)),
             (.68 * math.cos(t), .68 * math.sin(t))]
        rays = np.maximum(rays, _poly(S, p))
    pattern = np.clip(pupil + rays + limbus, 0, 1)
    red = _mix(hexc('#e0242c'), hexc('#8a0a14'), sstep(.2, .9, r))
    col = _mix(red, hexc('#0a0304'), pattern)
    if part == 'mask':
        return np.ones((S, S, 3), np.float32), pattern * iris
    if part == 'emissive':
        e = iris * (1 - pattern) * (.55 + .45 * sstep(.9, .2, r))
        return _col(hexc('#ff2a2a'), S), e
    return col, iris


def sarada_eye_frame(S, k, n=8):
    """Eye effect (looped flipbook): the Mangekyō motif, its red breathing slightly (subtle pulse). Alpha blend:
    red emissive look + dark edge without any halo."""
    c, a = mangekyo(S)
    puls = .9 + .1 * math.cos(2 * math.pi * k / n)
    return np.clip(c * puls, 0, 1), a


REG = {
    'ohirume_void':     dict(fn=lambda S: ohirume_void(S), S=256, blend='alpha',
                             desc='Ōhirume : noyau noir profond, propre, dense (absorbe la lumière)'),
    'ohirume_core':     dict(fn=lambda S: ohirume_core(S), S=256, blend='alpha',
                             desc='Ōhirume : coque d\'énergie sombre en cel-shading (bande creuse autour du noyau)'),
    'ohirume_ring':     dict(fn=None, S=256, blend='alpha', grid=(2, 1), seqs=[[0], [1]], multi=lambda S, i: ohirume_ring(S, i),
                             desc='Ōhirume : anneau de gravité rouge très fin, irrégulier, en arcs (2 variantes)'),
    'ohirume_distort':  dict(fn=None, S=256, blend='alpha', grid=(4, 4), seqs=[list(range(16))], rate=1, loop=True,
                             anim=ohirume_distort_frame, desc='Ōhirume : lignes de distorsion aspirées en spirale (boucle)'),
    'ohirume_gravity':  dict(fn=lambda S: ohirume_gravity(S), S=64, blend='alpha',
                             desc='Ōhirume : matière attirée (étirée en aiguille par la traînée)'),
    'ohirume_streak':   dict(fn=lambda S: ohirume_streak(S), S=128, blend='alpha', tiled=True,
                             desc='Ōhirume : ruban tuilable (sillage, filaments d\'attraction)'),
    'ohirume_fragment': dict(fn=None, S=128, blend='alpha', grid=(2, 2), seqs=[[0], [1], [2], [3]],
                             multi=lambda S, i: ohirume_fragment(S, i), desc='Ōhirume : éclats de vide (4 variantes)'),
    'sarada_core':      dict(fn=lambda S: sarada_core(S), S=128, blend='alpha', desc='Sarada : cœur sombre très discret'),
    'sarada_glow':      dict(fn=lambda S: sarada_glow(S), S=128, blend='add', desc='Sarada : halo rouge sombre très faible (additif)'),
    'sarada_filament':  dict(fn=None, S=128, blend='alpha', grid=(4, 2), seqs=[list(range(8))], rate=1, loop=True,
                             anim=sarada_filament_frame, desc='Sarada : filament d\'énergie vertical, onde qui monte (boucle)'),
    'sarada_spark':     dict(fn=lambda S: sarada_spark(S), S=64, blend='add', desc='Sarada : micro-étincelle rouge vif (accent rare, additif)'),
    'sarada_ring':      dict(fn=None, S=256, blend='alpha', grid=(2, 2), seqs=[[0], [1], [2]], multi=lambda S, i: sarada_ring(S, i % 3),
                             desc='Sarada : pièces d\'iris (arcs de verrouillage, iris à 3 rayons, orbite pointée)'),
    'sarada_void':      dict(fn=lambda S: sarada_void(S), S=128, blend='alpha', desc='Sarada : petite pupille sombre cerclée de carmin'),
    'sarada_distort':   dict(fn=None, S=128, blend='alpha', grid=(2, 2), seqs=[[0], [1], [2], [3]],
                             multi=lambda S, i: sarada_distort(S, i), desc='Sarada : onde qui plie l\'espace (double anneau ondulé, 4 variantes)'),
    'sarada_fragment':  dict(fn=None, S=128, blend='alpha', grid=(2, 2), seqs=[[0], [1], [2], [3]],
                             multi=lambda S, i: sarada_fragment(S, i), desc='Sarada : éclats triangulaires du Mangekyō (4 variantes)'),
    'sarada_streak':    dict(fn=lambda S: sarada_streak(S), S=128, blend='alpha', tiled=True,
                             desc='Sarada : ruban tuilable de la traînée d\'attraction'),
    'sarada_eye':       dict(fn=None, S=128, blend='alpha', grid=(4, 2), seqs=[list(range(8))], rate=1, loop=True,
                             anim=sarada_eye_frame, desc='Sarada : motif du Mangekyō pour l\'œil, rouge qui respire (boucle)'),
}
