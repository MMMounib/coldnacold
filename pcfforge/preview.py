"""Aperçu APPROXIMATIF hors moteur d'une spec à systèmes (prefix / systems / layers) : GIF animé.

Ce n'est PAS le rendu Source : la simulation rejoue l'émission (count, rate, delay, duration, amorces
I_remap_count), les formes (ring, disc, sphere, dome, point, path / segment entre deux CP), offset/height,
speed/up/vel, drag (1 - drag toutes les 1/30 s), gravité, attraction (pull), tourbillon (twist, autour de l'axe Z de
CP0), orbite, verrouillage sur un CP qui bouge (attach), trajet contraint CP -> CP (path_travel), fondu près d'un CP
(fade_near), rotation, tailles (grow, O_rscale, shrink, shrink_end), fondus, couleurs et planches animées (anim_rate).
Les textures additives s'ajoutent, les translucides (alpha) recouvrent dans l'ordre de profondeur : on peut juger du
noir. Les traînées (trail) sont étirées le long de la vitesse ; les cordes sont un trait doux (sans la texture qui
défile). Sert à vérifier un enchaînement, une position, un rythme, avant le test en jeu, qui seul fait foi.
"""
import math
import random

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFilter

from .textures import lib as TL


def _vec(v, d=(0, 0, 0)):
    return np.array(v if v is not None else d, float)


def _figure_mask(px_per_u):
    """Grey stand-in for a player model (72 u, seen from the front), to judge what an effect covers."""
    k = px_per_u * 2                                         # drawn at 2x, then reduced
    w, h = max(2, int(30 * k)), max(2, int(74 * k))
    im = Image.new('L', (w, h), 0); d = ImageDraw.Draw(im)
    X = lambda u: w / 2 + u * k; Y = lambda z: h - z * k
    d.ellipse([X(-4.5), Y(71), X(4.5), Y(61)], fill=255)                                   # head
    d.polygon([(X(-9), Y(58)), (X(9), Y(58)), (X(6.5), Y(34)), (X(-6.5), Y(34))], fill=255)  # torso
    for s in (-1, 1):
        d.polygon([(X(s * 6.5), Y(35)), (X(s * 1), Y(35)), (X(s * 1.5), Y(0)), (X(s * 5.5), Y(0))], fill=255)  # legs
        d.polygon([(X(s * 9), Y(57)), (X(s * 11.5), Y(55)), (X(s * 10.5), Y(32)), (X(s * 8), Y(33))], fill=255)  # arms
    return im.resize((max(1, w // 2), max(1, h // 2)), Image.LANCZOS)


_RGB = {}


def _tex_rgb(name):
    """Mean colour of a texture weighted by its alpha (ropes are drawn as a soft line in that colour)."""
    if name not in _RGB:
        arr = np.asarray(TL.make(name, size=64)['img'], np.float32) / 255
        w = arr[..., 3:4]
        _RGB[name] = (arr[..., :3] * w).sum((0, 1)) / max(1e-6, float(w.sum()))
    return _RGB[name]


def render(spec_path, out, chain, total, elev_deg=12.0, size=360, fps=20, seed=3, dist=240.0, target_z=50.0,
           cp0=(0, 0, 0), cp1=(160, 0, 40), cp0_vel=(0, 0, 0), bg=(70, 72, 78), azim_deg=0.0, figures=()):
    """chain = [(clé, début s, fin d'émission s ou None[, destruction immédiate s])]. Écrit un GIF, renvoie le
    nombre d'images. cp0 / cp1 : points de contrôle (CP0 bouge à cp0_vel u/s). azim_deg : la caméra tourne autour
    de la cible. figures : pieds de silhouettes grises (un modèle joueur de 72 u) pour juger ce que l'effet couvre."""
    spec = yaml.safe_load(open(spec_path, encoding='utf-8'))
    W = H = size; FPS = fps; TOTAL = total; ELEV = math.radians(elev_deg); AZ = math.radians(azim_deg)
    DIST, TGT = float(dist), np.array([0, 0, float(target_z)])
    cam = TGT + DIST * np.array([math.sin(AZ) * math.cos(ELEV), -math.cos(AZ) * math.cos(ELEV), math.sin(ELEV)])
    fwd = (TGT - cam) / DIST; right = np.array([math.cos(AZ), math.sin(AZ), 0]); up = np.cross(right, fwd)
    F = 330 * size / 360
    CP0, CP1, V0 = _vec(cp0), _vec(cp1), _vec(cp0_vel)
    cps = lambda t: {0: CP0 + V0 * t, 1: CP1}
    random.seed(seed)
    TEX = {}

    def frames(name):
        """[(rgb, a)] per frame, as float arrays (rgb is the texture's own colour, white when it is to be tinted)."""
        if name not in TEX:
            t = TL.REG[name]; S = 256 if name.startswith('mc_') else (128 if name != 'shield_rim' else 192)
            f = lambda res: (np.clip(np.nan_to_num(res[0]), 0, 1).astype(np.float32),
                             np.clip(np.nan_to_num(res[1]), 0, 1).astype(np.float32))
            with np.errstate(invalid='ignore', divide='ignore'):
                if 'anim' in t:
                    c, r = t.get('grid', (1, 1)); n = c * r
                    TEX[name] = ('anim', [f(t['anim'](S, k, n)) for k in range(n)], t.get('loop', False))
                elif t.get('multi'):
                    TEX[name] = ('multi', [f(t['multi'](S, i)) for i in range(len(t['seqs']))], False)
                else:
                    TEX[name] = ('one', [f(t['fn'](S))], False)
        return TEX[name]

    def pair(v, d):
        if v is None: return list(d)
        return list(v) if isinstance(v, (list, tuple)) else [v, v]

    def col(c):
        if c is None: return [np.array([255, 255, 255.])] * 2
        if isinstance(c[0], (list, tuple)): return [np.array(c[0], float), np.array(c[1], float)]
        return [np.array(c, float)] * 2

    def unit(v):
        n = np.linalg.norm(v)
        return v / n if n > 1e-9 else np.array([0, 0, 1.0])

    class P: pass
    parts = []

    def spawn(L, t0, idx, kill=None, order=0):
        p = P(); p.L = L; p.t0 = t0; p.order = order; p.idx = idx
        l = pair(L.get('life'), [1, 1]); p.life = random.uniform(*l)
        remap_rot = None
        for e in L.get('extra', []):
            if e[0] == 'I_remap_count':                            # field 1 = lifetime, 4 = rotation (radians)
                v = e[3] + (e[4] - e[3]) * min(1, max(0, idx - e[1]) / max(1, e[2] - e[1]))
                if (e[5] if len(e) > 5 else 1) == 4: remap_rot = math.degrees(v)
                else: p.life = v
        C = cps(t0); cp = int(L.get('cp', 0)); base = C.get(cp, CP0)
        s = L.get('shape', 'point'); pos = np.zeros(3); vel = np.zeros(3)
        sp = random.uniform(*pair(L.get('speed'), [0, 0]))
        if s == 'ring':
            if L.get('ring_even'):
                n = L.get('ring_count', L.get('count', 12)); a = 2 * math.pi * (idx % n) / n + math.radians(L.get('ring_yaw', 0))
            else: a = random.uniform(0, 2 * math.pi)
            d = np.array([math.cos(a), math.sin(a), 0]); pos = d * L.get('radius', 20); vel = d * sp
        elif s in ('disc', 'sphere', 'dome'):
            sr = pair(L.get('spread'), [0, 0]) if s != 'dome' else [L.get('radius', 40)] * 2
            a = random.uniform(0, 2 * math.pi)
            if s == 'disc': d = np.array([math.cos(a), math.sin(a), 0])
            else:
                z = random.uniform(-1, 1) if s == 'sphere' else random.uniform(0, 1)
                d = np.array([math.sqrt(1 - z * z) * math.cos(a), math.sqrt(1 - z * z) * math.sin(a), z])
            pos = d * random.uniform(*sr); vel = d * sp
        elif s in ('path', 'segment'):
            end = C.get(int(L.get('cp_end', cp + 1)), CP0)
            n = L.get('count', L.get('path_count', 16))
            f = (idx % max(1, n)) / max(1, n - 1) if s == 'path' else random.random()
            pos = (end - base) * f
            if s == 'segment':
                j = pair(L.get('spread'), [0, 0])[1]; pos = pos + np.random.uniform(-j, j, 3)
        off = np.array(L.get('offset', [0, 0, 0]), float)
        if L.get('height'): off[2] += random.uniform(*L['height'])
        pos = base + pos + off
        if L.get('vel') is not None:
            vmin, vmax = L['vel']; vel = vel + np.array([random.uniform(a, b) for a, b in zip(vmin, vmax)])
        elif L.get('up'): vel[2] += random.uniform(*L['up'])
        p.pos, p.vel = pos, vel
        p.size = random.uniform(*pair(L.get('size'), [5, 5])); p.alpha = random.uniform(*pair(L.get('alpha'), [255, 255]))
        c = col(L.get('color')); k = random.random(); p.col = c[0] * (1 - k) + c[1] * k
        p.rot = random.uniform(0, 360) if (L.get('rot') or 'spin' in L) else 0
        p.spin = random.uniform(*pair(L.get('spin'), [0, 0])) * (1 if L.get('spin_one_way') else random.choice([-1, 1]))
        if 'turn' in L: p.rot, p.spin = float(L.get('turn_from', 0)), float(L['turn'])
        if remap_rot is not None: p.rot = remap_rot
        kind, fr, _ = frames(L['tex'])
        p.var = (int(pair(L['seq'], [0])[0]) % len(fr) if 'seq' in L else random.randrange(len(fr))) if kind == 'multi' else 0
        p.orbit = sum(180 * m.get('speed', 1) * m.get('direction', 1) for m in L.get('motion', [])
                      if isinstance(m, dict) and m.get('type') == 'orbit')
        p.bulge = np.random.normal(0, 1, 3) * (L.get('path_travel', [0] * 5) + [0] * 5)[4] if 'path_travel' in L else 0
        p.kill = kill; p.sc = 1.0
        g = L.get('grow')
        if g: p.sc = g[0]
        parts.append(p)

    emitters = []
    for item in chain:
        key, t_on, t_off = item[:3]; kill = item[3] if len(item) > 3 else None
        for i, L in enumerate(spec['systems'][key]['layers']):
            emitters.append(dict(L=L, t=t_on + float(L.get('delay', 0)), off=t_off, kill=kill, done=False, acc=0.0,
                                 idx=0, order=len(emitters)))
    dt = 1 / FPS; t = 0.0; out_path = out; out = []
    bgimg = Image.new('RGB', (W, H), tuple(int(c) for c in bg)); dr = ImageDraw.Draw(bgimg)

    def proj(p):
        d = p - cam; z = d @ fwd
        return W / 2 + F * (d @ right) / z, H * .55 - F * (d @ up) / z, z
    line = tuple(min(255, int(c) + 25) for c in bg)
    for gx in range(-200, 201, 40):
        for a, b in (((gx, -200, 0), (gx, 200, 0)), ((-200, gx, 0), (200, gx, 0))):
            pa, pb = proj(np.array(a, float)), proj(np.array(b, float))
            if pa[2] > 5 and pb[2] > 5: dr.line([pa[:2], pb[:2]], fill=line)
    bgarr = np.asarray(bgimg, np.float32) / 255
    prevC = cps(0)
    while t < TOTAL:
        C = cps(t)
        for e in emitters:
            L = e['L']
            if t < e['t']: continue
            if 'count' in L and not L.get('rate'):
                if not e['done']:
                    for i in range(int(L['count'])): spawn(L, t, i, e['kill'], e['order'])
                    e['done'] = True
            elif L.get('rate'):
                stop = e['off'] if e['off'] is not None else 1e9
                if L.get('duration'): stop = min(stop, e['t'] + L['duration'])
                if t < stop:
                    e['acc'] += L['rate'] * dt
                    while e['acc'] >= 1:
                        e['acc'] -= 1; spawn(L, t, e['idx'], e['kill'], e['order']); e['idx'] += 1
        img = bgarr.copy(); keep = []; draws = []; ropes = {}
        for p in parts:
            age = t - p.t0; L = p.L
            if age > p.life or (p.kill is not None and t >= p.kill): continue
            keep.append(p); x = age / p.life
            cp = int(L.get('cp', 0)); prev = p.pos.copy()
            # forces (accelerations, u/s²) then Source-like drag and integration
            acc = np.array([0, 0, float(L.get('gravity', 0))])
            if 'pull' in L:
                acc += float(L['pull']) * unit(C.get(int(L.get('pull_cp', cp)), CP0) - p.pos)
            if 'twist' in L:
                rel = p.pos - C[0]; rel[2] = 0
                acc += float(L['twist']) * unit(np.cross([0, 0, 1.0], rel)) if np.linalg.norm(rel) > 1e-6 else 0
            for m in L.get('motion', []):
                if isinstance(m, dict) and m.get('type') in ('converge', 'diverge', 'vortex'):
                    k_ = float(m.get('speed', 1)); tgt = C.get(int(m.get('cp', cp)), CP0)
                    acc += {'converge': 900, 'diverge': -500, 'vortex': 700}[m['type']] * k_ * unit(tgt - p.pos)
            p.vel = p.vel + acc * dt
            if L.get('drag'): p.vel *= (1 - L['drag']) ** (30 * dt)
            p.pos = p.pos + p.vel * dt
            if L.get('attach'):                                    # locked: follows its CP
                lc = int(L.get('lock_cp', cp)); p.pos = p.pos + (C[lc] - prevC[lc])
            if p.orbit:
                a = math.radians(p.orbit * dt); c_, s_ = math.cos(a), math.sin(a); o = C[cp]
                rx, ry = p.pos[0] - o[0], p.pos[1] - o[1]
                p.pos[0], p.pos[1] = o[0] + c_ * rx - s_ * ry, o[1] + s_ * rx + c_ * ry
            if 'path_travel' in L:                                 # dragged along CP cp -> CP cp_end
                pt = list(L['path_travel']) + [0] * 5
                a_, b_ = C.get(cp, CP0), C.get(int(L.get('cp_end', 0)), CP0)
                u = min(1.0, age / max(1e-3, pt[0]))
                q = a_ + (b_ - a_) * u + p.bulge * 4 * u * (1 - u)
                dmax = pt[1] + (pt[2] - pt[1]) * min(1, 2 * u) if u < .5 else pt[2] + (pt[3] - pt[2]) * (2 * u - 1)
                d = p.pos - q; n = np.linalg.norm(d)
                if n > dmax:
                    newp = q + d / n * dmax; p.vel = (newp - (p.pos - p.vel * dt)) / dt * .5; p.pos = newp
            p.disp = (p.pos - prev) / dt                          # real motion (forces, orbit, lock, path)
            p.rot += p.spin * dt
            # Radius Scale operators, in layer order: each one sets radius = initial x its scale inside its time
            # window; outside every window the radius keeps its last value (as in Source)
            g = L.get('grow'); rs = []
            if g: rs.append((g[0], g[1], 0.0, g[3] if len(g) > 3 else 1.0, True))
            if 'shrink' in L: rs.append((1.0, L['shrink'], 0.0, 1.0, False))
            if 'shrink_end' in L: rs.append((1.0, L['shrink_end'], .85, 1.0, False))
            rs += [(e2[1], e2[2], e2[3], e2[4], False) for e2 in L.get('extra', []) if e2[0] == 'O_rscale']
            for s0, s1, w0, w1, ease in rs:
                if w0 <= x <= w1:
                    u = (x - w0) / max(1e-6, w1 - w0); u = 1 - (1 - u) ** 2 if ease else u
                    p.sc = s0 + (s1 - s0) * u
            sc = p.sc
            al = p.alpha
            if 'fade_in' in L: al *= min(1, x / max(1e-6, L['fade_in']))
            if 'fade_in_s' in L: al *= min(1, age / L['fade_in_s'])
            if 'fade_out' in L: al *= min(1, (1 - x) / max(1e-6, L['fade_out']))
            if 'fade_out_s' in L: al *= min(1, (p.life - age) / max(1e-6, L['fade_out_s']))
            if 'pulse_alpha' in L: al *= 1 + .3 * math.sin(2 * math.pi * L['pulse_alpha'][1] * age)
            if 'fade_near' in L:
                fcp, d0, d1 = L['fade_near']
                al *= min(1, max(0, (np.linalg.norm(p.pos - C.get(int(fcp), CP0)) - d0) / max(1e-6, d1 - d0)))
            if al < 2: continue
            c_ = p.col
            if L.get('color_end') is not None:
                ce = np.array(L['color_end'], float); a0 = L.get('color_end_at', [.5, 1])
                k_ = min(1, max(0, (x - a0[0]) / max(1e-6, a0[1] - a0[0]))); c_ = c_ * (1 - k_) + ce * k_
            if L.get('render') == 'rope':
                ropes.setdefault(id(L), (L, []))[1].append((p, al, c_)); continue
            kind, fr, loops = frames(L['tex'])
            if kind == 'anim':
                rate = L.get('anim_rate', 2.0 / sum(pair(L.get('life'), [1, 1])))
                ph = age * rate * len(fr)
                if loops: i0 = int(ph) % len(fr); i1 = (i0 + 1) % len(fr)
                else: i0 = min(int(ph), len(fr) - 1); i1 = min(i0 + 1, len(fr) - 1)
                k_ = ph - int(ph)
                rgb = fr[i0][0] * (1 - k_) + fr[i1][0] * k_; ta = fr[i0][1] * (1 - k_) + fr[i1][1] * k_
            else: rgb, ta = fr[p.var]
            X, Y, Z = proj(p.pos)
            if Z < 10: continue
            draws.append((Z, p.order, p, X, Y, sc, al, c_, rgb, ta))
        # ropes: a soft line through the live nodes (in path order), no scrolling texture
        for L, nodes in ropes.values():
            if len(nodes) < 2: continue
            if L.get('path_live'):                                 # live nodes spread from cp to cp_end
                nodes.sort(key=lambda n: n[0].idx)
                a_, b_ = C.get(int(L.get('cp', 0)), CP0), C.get(int(L.get('cp_end', 1)), CP0)
                for i, n in enumerate(nodes): n[0].pos = a_ + (b_ - a_) * i / (len(nodes) - 1)
            nodes.sort(key=lambda n: (np.linalg.norm(n[0].pos - cps(t)[int(L.get('cp', 0))]), n[0].idx))
            pts = [proj(n[0].pos) for n in nodes]
            if min(pq[2] for pq in pts) < 10: continue
            wpx = max(1, int(2 * F * nodes[0][0].size / np.mean([pq[2] for pq in pts])))
            m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).line([pq[:2] for pq in pts], fill=255, width=wpx)
            m = np.asarray(m.filter(ImageFilter.GaussianBlur(max(1, wpx / 3))), np.float32)[..., None] / 255
            al = np.mean([n[1] for n in nodes]) / 255; c_ = np.mean([n[2] for n in nodes], axis=0) / 255
            if TL.REG[L['tex']]['blend'] == 'add': img += m * c_ * al
            else: img = img * (1 - m * al) + m * al * c_ * _tex_rgb(L['tex'])     # texture's own colour
        for fpos in figures:                                        # grey stand-ins, depth-sorted with the sprites
            fp = np.array(fpos, float); Xf, Yf, Zf = proj(fp); Zc = proj(fp + [0, 0, 36])[2]
            if Zf > 10: draws.append((Zc, -1, None, Xf, Yf, F / Zf, 0, 0, 0, 0))
        draws.sort(key=lambda d: (-d[0], d[1]))                     # far first: alpha sprites cover what is behind
        for Z, order, p, X, Y, sc, al, c_, rgb, ta in draws:
            if p is None:                                          # figure
                m = np.asarray(_figure_mask(sc), np.float32)[..., None] / 255
                fh, fw = m.shape[:2]; x0, y0 = int(X - fw / 2), int(Y - fh)
                xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + fw), min(H, y0 + fh)
                if xb > xa and yb > ya:
                    sub = m[ya - y0:yb - y0, xa - x0:xb - x0]
                    img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - sub) + sub * np.array([.47, .48, .52])
                continue
            L = p.L
            r = F * p.size * sc / Z
            if r < .7: continue
            im = Image.fromarray((np.dstack([rgb, ta]) * 255).astype(np.uint8), 'RGBA')
            if L.get('render') == 'trail':                          # stretched along the screen-space velocity
                tl = np.mean(pair(L.get('trail'), [.04, .06]))
                X2, Y2, Z2 = proj(p.pos - getattr(p, 'disp', p.vel) * tl)
                L_px = math.hypot(X2 - X, Y2 - Y)
                sw, sh = max(1, int(2 * r + L_px)), max(1, int(2 * r))
                im = im.resize((sw, sh)).rotate(-math.degrees(math.atan2(Y2 - Y, X2 - X)), expand=True)
                X, Y = (X + X2) / 2, (Y + Y2) / 2
                sw, sh = im.size
            else:
                if p.rot and L.get('orient') == 'ground': im = im.rotate(p.rot)
                sw, sh = max(1, int(2 * r)), max(1, int(2 * r))
                if L.get('orient') == 'ground': sh = max(1, int(2 * r * math.sin(ELEV + .05)))
                im = im.resize((sw, sh))
                if p.rot and L.get('orient') != 'ground': im = im.rotate(p.rot)
            a = np.asarray(im, np.float32) / 255
            x0, y0 = int(X - sw / 2), int(Y - sh / 2)
            xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + sw), min(H, y0 + sh)
            if xb <= xa or yb <= ya: continue
            sub = a[ya - y0:yb - y0, xa - x0:xb - x0]
            k_ = sub[..., 3:4] * (al / 255)
            src = sub[..., :3] * (c_ / 255)
            if TL.REG[L['tex']]['blend'] == 'add': img[ya:yb, xa:xb] += src * k_
            else: img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - k_) + src * k_
        parts[:] = keep
        prevC = C
        out.append(Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)))
        t += dt
    out[0].save(out_path, save_all=True, append_images=out[1:], duration=int(1000 / FPS), loop=0)
    return len(out)


# the four views every effect must pass (fond clair / fond sombre, angle 1 à hauteur d'yeux / angle 2 en hauteur)
VIEWS = (('clair', (196, 196, 200), 10.0, 0.0), ('sombre', (22, 20, 26), 10.0, 0.0),
         ('clair_haut', (196, 196, 200), 40.0, 35.0), ('sombre_haut', (22, 20, 26), 40.0, 35.0))


def render_views(spec_path, base, chain, total, times, **kw):
    """Renders the 4 test views (base_<vue>.gif) and a contact sheet base_planche.png: one row per view, one column
    per time in `times` (s). Returns the sheet path."""
    from PIL import ImageFont
    fps = kw.get('fps', 20); rows = []
    for name, bg, elev, azim in VIEWS:
        gif = f'{base}_{name}.gif'
        render(spec_path, gif, chain, total, elev_deg=elev, bg=bg, azim_deg=azim, **kw)
        im = Image.open(gif); row = []
        for t in times:
            im.seek(min(im.n_frames - 1, int(round(t * fps)))); row.append(im.convert('RGB').copy())
        rows.append((name, row))
    w, h = rows[0][1][0].size
    sheet = Image.new('RGB', (w * len(times), h * len(rows)), (0, 0, 0)); dr = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for r, (name, row) in enumerate(rows):
        for c, fr in enumerate(row):
            sheet.paste(fr, (c * w, r * h))
            dr.text((c * w + 4, r * h + 4), f'{name}  {times[c]:.2f} s', fill=(255, 60, 60), font=font)
    out = f'{base}_planche.png'
    sheet.save(out)
    return out
