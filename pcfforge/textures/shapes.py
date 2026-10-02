"""Formes procédurales de base (dessin suréchantillonné, bords propres).
Chaque texture est dessinée en suréchantillonnage (x2) puis réduite, pour des bords propres.
Sorties : PNG (aperçu / simulateur), VTF (DXT5 + mipmaps, planche de sprites si besoin), VMT SpriteCard.
"""
import numpy as np, io, os, math
from PIL import Image, ImageFilter
from srctools.vtf import VTF, ImageFormats, SheetSequence, VTFFlags, TexCoord

RNG = np.random.default_rng(7)

# ---------------------------------------------------------------- utilitaires
def grid(S):
    y, x = np.mgrid[0:S, 0:S].astype(np.float32)
    return (x + .5) / S * 2 - 1, (y + .5) / S * 2 - 1          # [-1,1], y vers le bas

def sstep(a, b, x):
    t = np.clip((x - a) / (b - a + 1e-9), 0, 1); return t * t * (3 - 2 * t)

def fbm(S, octaves=5, seed=0, base=4):
    r = np.random.default_rng(seed); acc = np.zeros((S, S), np.float32); amp = 1; tot = 0
    for o in range(octaves):
        n = base * 2 ** o
        g = r.random((n + 1, n + 1)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC)
        acc += amp * (np.asarray(im, np.float32) / 255); tot += amp; amp *= .5
    return acc / tot

def rot(x, y, a):
    c, s = math.cos(a), math.sin(a); return x * c - y * s, x * s + y * c

def to_img(rgb, a, S_out):
    rgb, a = np.nan_to_num(rgb), np.nan_to_num(a)          # powers of negative bases must not leak NaN
    arr = np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)[..., None]])
    im = Image.fromarray((arr * 255 + .5).astype(np.uint8), 'RGBA')
    # réduction avec alpha prémultiplié pour éviter les franges sombres
    pm = arr.copy(); pm[..., :3] *= pm[..., 3:4]
    pim = Image.fromarray((pm * 255 + .5).astype(np.uint8), 'RGBA').resize((S_out, S_out), Image.LANCZOS)
    p = np.asarray(pim, np.float32) / 255
    rgb2 = np.where(p[..., 3:4] > 1e-3, p[..., :3] / np.maximum(p[..., 3:4], 1e-3), 0)
    return Image.fromarray((np.dstack([np.clip(rgb2, 0, 1), p[..., 3:4]]) * 255 + .5).astype(np.uint8), 'RGBA')

def mix(c1, c2, t):
    t = np.asarray(t)[..., None]; return np.asarray(c1) * (1 - t) + np.asarray(c2) * t

def hexc(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)

# ---------------------------------------------------------------- formes
def leaf(S, variant=0, seed=0, dry=False):
    x, y = grid(S)
    x, y = rot(x, y, -math.pi / 4)                       # feuille en diagonale : utilise toute la carte
    u = x / .95                                           # axe longitudinal [-1,1] base->pointe
    t = np.clip((u + 1) / 2, 0, 1)
    if variant == 0:   wid = .34 * np.sin(np.pi * t) ** .8 * (1 - .35 * t)          # lancéolée
    elif variant == 1: wid = .42 * np.sin(np.pi * t) ** .6 * (1 - .2 * t)           # ovale
    elif variant == 2: wid = .30 * np.sin(np.pi * t) ** .9                            # fine
    else:              wid = .38 * np.sin(np.pi * t) ** .7 * (1 - .3 * t)
    bend = .10 * np.sin(np.pi * t) * (1 if variant % 2 else -1)                        # légère courbure
    yy = y - bend
    if variant == 2 or dry:                                                          # dentelure
        wid = wid * (1 - .10 * (np.abs(np.sin(t * 38)) ** 2) * (t > .12))
    if dry:                                                                           # feuille recroquevillée
        wid = wid * (1 - .45 * sstep(.3, 1, t) * (yy > 0))
    d = wid - np.abs(yy)
    a = sstep(0, .012, d) * (np.abs(u) < 1)
    stem = (np.abs(yy) < .012) & (u < -.95) & (u > -1.15)
    a = np.maximum(a, stem * 1.0)
    edge = 1 - sstep(0, .08, d)                           # assombrit le bord
    mid = np.exp(-(yy / .012) ** 2) * (t < .97)           # nervure centrale
    lat = np.abs(((u - 1.7 * np.abs(yy)) * 7.5) % 1 - .5)
    veins = np.exp(-(lat / .06) ** 2) * sstep(.02, .10, d) * (np.abs(yy) > .01)
    n = fbm(S, 5, seed)
    if dry:
        base, tip, vc = hexc('#5a3a1e'), hexc('#a8783f'), hexc('#d9b47a')
    else:
        base, tip, vc = hexc('#15431f'), hexc('#4fae57'), hexc('#b9f5a0')
    col = mix(base, tip, np.clip(t * .8 + (n - .5) * .5, 0, 1))
    shade = .80 + .35 * (yy < 0)                           # moitié éclairée / moitié ombre (volume)
    col = col * shade[..., None]
    col = mix(col, col * .55, edge * .7)
    col = mix(col, vc, np.clip(mid * .75 + veins * .35, 0, 1))
    return col, a

def petal(S, variant=0, seed=0):
    """Pétale clair (teinté par la couleur de vertex) : base sombre, stries, bord dentelé."""
    x, y = grid(S)
    x, y = rot(x, y, -math.pi / 4)
    u = x / .95; t = np.clip((u + 1) / 2, 0, 1)
    if variant == 0: wid = .40 * np.sin(np.pi * t ** .75) ** .7                     # large
    elif variant == 1: wid = .28 * np.sin(np.pi * t ** .8) ** .8                    # étroit
    elif variant == 2: wid = .44 * np.sin(np.pi * t ** .6) ** .5 * (1 - .15 * t)     # rond
    else: wid = .36 * np.sin(np.pi * t ** .7) ** .7
    curl = .08 * t ** 2 * (1 if variant % 2 else -1); yy = y - curl
    notch = 1 - .22 * np.exp(-((yy) / .05) ** 2) * sstep(.85, 1, t) if variant != 1 else 1
    wid = wid * notch * (1 - .06 * np.abs(np.sin(t * 30 + variant)) * sstep(.6, 1, t))
    d = wid - np.abs(yy)
    a = sstep(0, .015, d) * (u > -1) * (u < 1)
    n = fbm(S, 5, seed + 11)
    stri = .5 + .5 * np.cos((yy / (wid + 1e-3)) * 9 + n * 3)
    lum = .45 + .55 * sstep(-.1, .8, t)                    # base sombre -> pointe claire
    lum = lum * (.88 + .12 * stri) * (.9 + .2 * n)
    rim = np.exp(-(d / .03) ** 2) * .25                   # liseré clair
    col = np.dstack([lum, lum * .93, lum * .96]) + rim[..., None]
    col = col * (.85 + .25 * (yy > 0))[..., None]
    return col, a

def seed_tex(S):
    x, y = grid(S); x, y = rot(x, y, -math.pi / 4)
    e = (x / .78) ** 2 + (y / .46) ** 2
    a = sstep(1, .96, e)
    n = fbm(S, 5, 3)
    col = mix(hexc('#2b1b0e'), hexc('#8a5a2b'), np.clip(1 - e + (n - .5) * .4, 0, 1))
    hl = np.exp(-(((x + .25) / .35) ** 2 + ((y + .18) / .15) ** 2)) * .55    # reflet
    vein = 0
    for k in range(-3, 4):
        vein = np.maximum(vein, np.exp(-((y - k * .11 * (1 - (x / .8) ** 2)) / .012) ** 2))
    vein = vein * (e < .93)
    col = col + hl[..., None] * .8
    col = mix(col, hexc('#8dffae'), np.clip(vein * .9, 0, 1))
    return col, a

def valve(S, seed=0):
    """Valve de gousse enroulée (croissant épais, vert->brun)."""
    x, y = grid(S)
    r = np.hypot(x + .15, y - .1); th = np.arctan2(y - .1, x + .15)
    band = .62 - .18 * sstep(-2.6, 1.2, th)
    thick = .16 * np.sin(np.clip((th + 2.6) / 3.8, 0, 1) * np.pi) ** .6
    d = thick - np.abs(r - band)
    a = sstep(0, .02, d) * (th > -2.6) * (th < 1.2)
    n = fbm(S, 5, seed + 21)
    t = np.clip((th + 2.6) / 3.8, 0, 1)
    col = mix(hexc('#2f6b2c'), hexc('#8a6a2e'), np.clip(t + (n - .5) * .4, 0, 1))
    inner = sstep(0, .1, (r - band))                         # face interne plus claire
    col = mix(col, hexc('#d9e8a0'), inner * .45)
    col = col * (.7 + .5 * sstep(0, .12, d))[..., None]
    return col, a

def mimosa(S, closed=False, seed=0):
    """Touffe de sensitive vue de dessus : 7 frondes pennées en rosette ; closed = folioles repliées."""
    x, y = grid(S); a = np.zeros_like(x); lum = np.zeros_like(x); vein = np.zeros_like(x); shade = np.zeros_like(x)
    rr = np.random.default_rng(seed + 3)
    nf = 7
    for k in range(nf):
        ang = k / nf * 2 * np.pi + rr.normal() * .22
        L = rr.uniform(.62, .95) * (.86 if closed else 1)
        bend = rr.normal() * .25
        u, v = rot(x, y, -ang)
        v = v - bend * (u / L) ** 2 * .3
        on = (u > .04) & (u < L)
        vein = np.maximum(vein, np.exp(-(v / .009) ** 2) * on)
        a = np.maximum(a, sstep(.016, .004, np.abs(v)) * on)
        n_leaf = 12
        for i in range(n_leaf):
            p = .09 + i * (L - .11) / n_leaf
            taper = 1 - .5 * i / n_leaf
            for side in (-1, 1):
                if closed:
                    th, ln, wd = side * .22, .045 * taper + .02, .017 * taper + .008
                else:
                    th, ln, wd = side * 1.15, .075 * taper + .025, .021 * taper + .008
                cu, cv = p + math.cos(th) * ln, math.sin(th) * ln
                c, sn = math.cos(th), math.sin(th)
                a1 = (u - cu) * c + (v - cv) * sn; a2 = -(u - cu) * sn + (v - cv) * c
                e = (a1 / ln) ** 2 + (a2 / wd) ** 2
                m = sstep(1, .75, e)
                a = np.maximum(a, m)
                lum = np.maximum(lum, m * (.45 + .55 * (a2 * side < 0)) * (.8 + .2 * taper))
        shade = np.maximum(shade, sstep(.10, 0, np.abs(v)) * on)
    n = fbm(S, 4, seed + 5)
    c1, c2 = (hexc('#17401f'), hexc('#58ad57')) if not closed else (hexc('#1c3a1c'), hexc('#4d7a3d'))
    col = mix(c1, c2, np.clip(lum * .9 + (n - .5) * .45, 0, 1))
    col = mix(col, hexc('#b6f0a6') if not closed else hexc('#8fae78'), vein * .5)
    r = np.hypot(x, y)
    col = col * (.75 + .25 * np.clip(r * 1.4, 0, 1))[..., None]      # cœur de touffe plus sombre (volume)
    return col, a

def pompom(S, seed=0):
    x, y = grid(S); r = np.hypot(x, y); th = np.arctan2(y, x)
    rr = np.random.default_rng(seed)
    fil = np.zeros_like(x)
    for k in range(90):
        a0 = rr.random() * 2 * np.pi; L = .55 + rr.random() * .35
        u, v = rot(x, y, -a0)
        fil = np.maximum(fil, np.exp(-(v / .012) ** 2) * (u > 0) * (u < L) * (1 - u / L * .3))
        tipd = (u - L) ** 2 + v ** 2
        fil = np.maximum(fil, np.exp(-tipd / .0012))
    core = sstep(.25, .1, r)
    a = np.clip(fil * .9 + core, 0, 1)
    col = mix(hexc('#ff8fc4'), hexc('#ffe1ef'), np.clip(r, 0, 1))
    col = mix(col, hexc('#fff3a8'), np.exp(-((r - .8) / .08) ** 2) * .6)
    return col, a

def glow(S, core=.25, power=2.2):
    x, y = grid(S); r = np.hypot(x, y)
    a = np.clip(1 - r, 0, 1) ** power + np.exp(-(r / core) ** 2) * .6
    return np.ones((S, S, 3), np.float32), np.clip(a, 0, 1)

def pollen(S):
    x, y = grid(S); r = np.hypot(x, y)
    a = np.clip(1 - r, 0, 1) ** 3 * .6 + np.exp(-(r / .12) ** 2)
    th = np.arctan2(y, x)
    star = np.exp(-(r / .6) ** 2) * (np.abs(np.cos(th * 2)) ** 30) * .5         # petite croix scintillante
    return np.ones((S, S, 3), np.float32), np.clip(a + star, 0, 1)

def ring(S, width=.06):
    x, y = grid(S); r = np.hypot(x, y)
    a = np.exp(-((r - .86) / width) ** 2) + .25 * np.exp(-((r - .8) / .15) ** 2) * (r < .86)
    return np.ones((S, S, 3), np.float32), np.clip(a, 0, 1)

def spark(S):
    x, y = grid(S)
    a = np.exp(-(y / .08) ** 2) * np.clip(1 - np.abs(x), 0, 1) ** 1.5 + np.exp(-((x / .5) ** 2 + (y / .03) ** 2)) * .6
    return np.ones((S, S, 3), np.float32), np.clip(a, 0, 1)

def veins_decal(S, seed=0, branches=9):
    """Réseau de nervures radiales ramifiées (décal au sol, additif)."""
    rr = np.random.default_rng(seed)
    im = Image.new('L', (S, S), 0)
    from PIL import ImageDraw
    dr = ImageDraw.Draw(im)
    c = S / 2
    def grow(x, y, ang, length, w, depth):
        steps = int(length / (S * .012))
        for i in range(steps):
            ang += rr.normal() * .18
            nx, ny = x + math.cos(ang) * S * .012, y + math.sin(ang) * S * .012
            if math.hypot(nx - c, ny - c) > S * .48: return
            ww = max(1, w * (1 - i / steps * .6))
            dr.line([(x, y), (nx, ny)], fill=255, width=int(ww))
            x, y = nx, ny
            if depth < 3 and rr.random() < .07:
                grow(x, y, ang + rr.choice([-1, 1]) * (.5 + rr.random() * .5), length * .45, ww * .7, depth + 1)
    for k in range(branches):
        grow(c, c, k / branches * 2 * np.pi + rr.normal() * .2, S * .6, S * .012, 0)
    im = im.filter(ImageFilter.GaussianBlur(S * .002))
    core = np.asarray(im, np.float32) / 255
    halo = np.asarray(im.filter(ImageFilter.GaussianBlur(S * .012)), np.float32) / 255
    x, y = grid(S); r = np.hypot(x, y)
    a = np.clip(core + halo * 1.2, 0, 1) * sstep(1, .75, r)
    return np.ones((S, S, 3), np.float32), a

def dust(S, seed=0):
    x, y = grid(S); r = np.hypot(x, y)
    n = fbm(S, 5, seed + 40, base=3)
    a = np.clip(1 - (r + (n - .5) * .5) / .95, 0, 1) ** 1.6 * (.55 + .45 * n)
    lum = .75 + .25 * n
    return np.dstack([lum] * 3), a

def thread(S):
    """Brin de chakra tressé, tuilable horizontalement (corde)."""
    y, x = np.mgrid[0:S, 0:S].astype(np.float32); u = x / S; v = (y + .5) / S * 2 - 1
    a = np.exp(-(v / .12) ** 2)
    for k in range(3):
        ph = u * 2 * np.pi * 2 + k * 2.1
        c = .35 * np.sin(ph)
        a = np.maximum(a, np.exp(-((v - c) / .06) ** 2) * (.6 + .4 * np.cos(ph)))
    a = np.clip(a + np.exp(-(v / .45) ** 2) * .25, 0, 1)
    return np.ones((S, S, 3), np.float32), a

# ---- fleur carnivore (face caméra), animation d'éclosion -----------------------------
def flower_frame(S, openness, wilt=0.0, seed=0):
    """Fleur carnivore face caméra. openness 0 = bourgeon, 1 = ouverte ; wilt 0..1 = fanaison."""
    x, y = grid(S)
    col = np.zeros((S, S, 3), np.float32); a = np.zeros((S, S), np.float32)
    n = fbm(S, 5, seed + 60)
    def over(c2, a2):
        nonlocal col, a
        col = col * (1 - a2[..., None]) + c2 * a2[..., None]; a = a2 + a * (1 - a2)
    o = openness; drop = wilt * .25
    # couronne arrière : sépales verts effilés
    for k in range(5):
        ang = k / 5 * 2 * np.pi + .63 - np.pi / 2
        ang = -np.pi / 2 + (ang + np.pi / 2) * (.2 + .8 * o)
        u, v = rot(x, y - drop * .3, -ang)
        L = (.45 + .5 * o) * (1 - .2 * wilt); t = np.clip(u / L, 0, 1)
        wid = .09 * np.sin(np.pi * t ** .6) ** .8
        m = sstep(0, .015, wid - np.abs(v)) * (u > 0) * (u < L) * sstep(.05, .4, o)
        over(mix(hexc('#10351a'), hexc('#3d8d45'), t) * (.8 + .3 * (v > 0))[..., None], m)
    # 5 pétales épais et pointus
    for k in range(5):
        base = k / 5 * 2 * np.pi - np.pi / 2
        ang = -np.pi / 2 + (base + np.pi / 2) * (.14 + .86 * o)
        L = (.42 + .52 * o) * (1 - .22 * wilt)
        u, v = rot(x, y - drop * (.2 + .3 * (k % 2)), -ang)
        v = v + wilt * .12 * np.clip(u / L, 0, 1) ** 2
        t = np.clip(u / L, 0, 1)
        wid = (.16 + .13 * o) * np.sin(np.pi * t ** .62) ** .55 * (1 - .45 * wilt * t)
        wid = wid * (1 - .10 * np.abs(np.sin(t * 26 + k)) * sstep(.5, 1, t))
        d = wid - np.abs(v)
        m = sstep(0, .014, d) * (u > -.03) * (u < L)
        lum = .30 + .70 * sstep(.05, .95, t)
        pc = mix(hexc('#4a0a24'), hexc('#ff4f8f'), lum * (.85 + .3 * (n - .5)))
        pc = mix(pc, hexc('#ffc3da'), np.exp(-(d / .022) ** 2) * .45 * (t > .25))
        sp = ((np.sin(u * 46 + k * 3) * np.sin(v * 46)) > .72) * (t > .18) * (t < .55)
        pc = mix(pc, hexc('#2e0515'), sp * .7)
        pc = mix(pc, hexc('#5e4652'), wilt * .75)
        over(pc * (.78 + .32 * (v > 0))[..., None], m)
    r = np.hypot(x, y - drop * .2); th = np.arctan2(y, x)
    # gorge sombre + dents
    throat = sstep(.30, .22, r) * sstep(.25, .65, o)
    over(mix(hexc('#1c030c'), hexc('#6a1030'), np.clip(r / .3, 0, 1)), throat)
    teeth_r = .22 + .09 * np.abs(np.cos(th * 9)) ** 6
    teeth = sstep(0, .012, teeth_r - r) * (r > .19) * sstep(.35, .8, o) * (1 - wilt)
    over(np.ones((S, S, 3)) * hexc('#f3e9d8'), teeth)
    heart = sstep(.13, .06, r) * sstep(.3, .7, o)
    over(mix(hexc('#ffb040'), hexc('#fff3b0'), np.clip(1 - r / .13, 0, 1)) * (1 - .6 * wilt), heart)
    bud = sstep(.4, 0, o)
    if bud > 0:
        e = (x / .26) ** 2 + ((y + .02) / .46) ** 2
        m = sstep(1, .9, e) * bud
        bc = mix(hexc('#3e0a21'), hexc('#e0457f'), np.clip(.5 - y * .7 + (n - .5) * .3, 0, 1))
        seam = np.exp(-((x + .03 * np.sin(y * 7)) / .014) ** 2) * .6
        bc = bc * (.8 + .3 * (x > 0))[..., None]
        over(mix(bc, hexc('#1a040d'), seam), m)
    return col, a

def cocoon_frame(S, k):
    """Cocon floral (vertical) : 0 fermé, 1 fissuré, 2 s'ouvre, 3 pétales rabattus."""
    x, y = grid(S)
    col = np.zeros((S, S, 3), np.float32); a = np.zeros((S, S), np.float32)
    n = fbm(S, 5, 77 + k)
    def over(c2, a2):
        nonlocal col, a
        col = col * (1 - a2[..., None]) + c2 * a2[..., None]; a = a2 + a * (1 - a2)
    open_ = [0, .15, .55, 1.0][k]
    for i, side in enumerate([-2, -1, 1, 2, 0]):
        tilt = side * (.08 + .55 * open_)
        u, v = rot(x, y - .95, tilt)          # pivot en bas
        u, v = v, u                            # axe vertical
        L = 1.75 - .35 * open_ * (abs(side) > 0)
        t = np.clip(-u / L, 0, 1)
        wid = (.30 - .06 * abs(side)) * np.sin(np.pi * t ** .8) ** .55
        m = sstep(0, .02, wid - np.abs(v)) * (u < 0) * (-u < L)
        lum = .3 + .7 * t
        c = mix(hexc('#3d0a22'), hexc('#c93a74'), lum * (.85 + .3 * (n - .5)))
        c = mix(c, hexc('#f6a2c4'), np.exp(-((wid - np.abs(v)) / .03) ** 2) * .3)
        c = c * (.75 + .35 * (v * np.sign(side + .01) > 0))[..., None]
        if side == 0 and k < 2:
            over(c, m)
        elif side != 0:
            over(c, m)
    if k >= 1:  # lueur intérieure dorée
        r = np.hypot(x / .35, (y - .25) / .6)
        g = np.exp(-r ** 2) * [0, .35, .8, .5][k]
        col = col + g[..., None] * hexc('#ffe27a'); a = np.clip(a + g * .5, 0, 1)
    return col, a

def stem(S, variant=0, seed=0):
    """Tige verticale avec feuilles alternées (vue latérale, pour orientation Z)."""
    x, y = grid(S)
    col = np.zeros((S, S, 3), np.float32); a = np.zeros((S, S), np.float32)
    def over(c2, a2):
        nonlocal col, a
        col = col * (1 - a2[..., None]) + c2 * a2[..., None]; a = a2 + a * (1 - a2)
    t = np.clip((1 - y) / 2, 0, 1)                  # 0 en bas, 1 en haut
    cx = .08 * np.sin(t * 3.2 + variant) * t
    w = .035 * (1 - .6 * t)
    m = sstep(0, .012, w - np.abs(x - cx)) * (t < .92)
    over(mix(hexc('#173f1e'), hexc('#4b9a4c'), t)[..., :] * (.8 + .3 * (x > cx))[..., None], m)
    rr = np.random.default_rng(seed)
    for i in range(4):
        tp = .25 + i * .18; side = 1 if (i + variant) % 2 else -1
        py = 1 - 2 * tp; px = .08 * math.sin(tp * 3.2 + variant) * tp
        u, v = rot(x - px, y - py, -(side * .6 - (np.pi / 2 if side < 0 else -np.pi / 2) * 0))
        ang = -.5 if side > 0 else np.pi + .5
        u, v = rot(x - px, y - py, -ang)
        L = .42 - i * .05; tt = np.clip(u / L, 0, 1)
        wid = .11 * np.sin(np.pi * tt) ** .7
        d = wid - np.abs(v - .06 * tt ** 2)
        mm = sstep(0, .012, d) * (u > 0) * (u < L)
        c = mix(hexc('#1a4a22'), hexc('#6bd06b'), tt * .9) * (.8 + .3 * (v > 0))[..., None]
        c = mix(c, hexc('#b8f5a8'), np.exp(-(v / .01) ** 2) * .5)
        over(c, mm)
    # bourgeon en tête
    e = (x / .09) ** 2 + ((y + .88) / .12) ** 2
    over(mix(hexc('#5a1030'), hexc('#e5508a'), np.clip(-y - .8, 0, 1) * 4), sstep(1, .85, e))
    return col, a

def sprout(S):
    x, y = grid(S)
    col = np.zeros((S, S, 3), np.float32); a = np.zeros((S, S), np.float32)
    def over(c2, a2):
        nonlocal col, a
        col = col * (1 - a2[..., None]) + c2 * a2[..., None]; a = a2 + a * (1 - a2)
    m = sstep(0, .015, .03 - np.abs(x)) * (y > -.1) * (y < .95)
    over(np.ones((S, S, 3)) * hexc('#2d6b2f'), m)
    for side in (-1, 1):
        u, v = rot(x, y + .1, -(np.pi + .5 if side < 0 else -.5))
        L = .75; tt = np.clip(u / L, 0, 1)
        wid = .26 * np.sin(np.pi * tt) ** .6
        d = wid - np.abs(v)
        mm = sstep(0, .015, d) * (u > 0) * (u < L)
        c = mix(hexc('#2b7a34'), hexc('#8cf58f'), tt) * (.8 + .3 * (v > 0))[..., None]
        c = mix(c, hexc('#d6ffd0'), np.exp(-(v / .012) ** 2) * .6)
        over(c, mm)
    return col, a

