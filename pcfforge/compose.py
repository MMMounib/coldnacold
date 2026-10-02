"""Composer: EffectSpec (effect.py) -> layered low-level spec (layers.py) + runtime attachment info.

An effect is a hierarchy of roles, each with one visual job:
  core       the main energy, small and bright          halo       soft volume of light, low alpha
  filaments  motion (ropes / wisps)                     sparks     sharp details that escape
  secondary  depth and variation (motes, puffs)         accents    ring / flash / smoke, per shape
Shape recipes place the roles; the energy picks textures and colours; the style changes timing,
density, silhouette and motion (not only colours); intensity and quality scale the result; the
performance budget trims the least important roles first.
"""
import copy
import math

from . import layers as LY
from .motions import normalize as norm_motion

SHAPES = ('aura', 'burst', 'projectile', 'impact', 'vortex', 'trail', 'beam', 'sphere', 'ring', 'spiral', 'cone',
          'ribbon', 'cloud', 'radial', 'line', 'custom')
ENERGIES = ('chakra', 'fire', 'lightning', 'wind', 'smoke', 'magic', 'plasma', 'water', 'dust', 'ash', 'particles',
            'impact', 'energy', 'demonic', 'abyss', 'black_lightning')
LOOKS = ('soft', 'sharp', 'anime', 'cartoon', 'energetic', 'mystical', 'aggressive', 'elegant', 'dense', 'minimal')
QUALITY = {'low': .45, 'medium': .7, 'high': 1.0, 'ultra': 1.3}
ROLE_PRIORITY = ('core', 'halo', 'filaments', 'accents', 'sparks', 'secondary')   # cut from the end

# ------------------------------------------------------------------ energies: textures + default colours
ENERGY = {
    'chakra':    dict(color=[110, 205, 255], color2=[225, 248, 255], core='glow_hard', halo='glow', fil='strand',
                      wisp='energy', spark='spark', mote='star'),
    'fire':      dict(color=[255, 120, 35], color2=[255, 225, 150], core='glow_hard', halo='glow', fil='flame',
                      wisp='flame', spark='streak', mote='star', smoke=[70, 60, 55]),
    'lightning': dict(color=[140, 170, 255], color2=[240, 245, 255], core='flare', halo='glow', fil='lightning',
                      wisp='lightning', spark='spark', mote='star'),
    'wind':      dict(color=[200, 235, 225], color2=[255, 255, 255], core='glow', halo='noise', fil='strand',
                      wisp='slash', spark='streak', mote='dust'),
    'water':     dict(color=[70, 180, 240], color2=[210, 245, 255], core='glow', halo='glow', fil='strand',
                      wisp='energy', spark='droplet', mote='star'),
    'smoke':     dict(color=[120, 115, 110], color2=[170, 165, 160], core='smoke', halo='smoke', fil='smoke',
                      wisp='smoke', spark='dust', mote='dust'),
    'magic':     dict(color=[190, 120, 255], color2=[245, 225, 255], core='glow_hard', halo='glow', fil='strand',
                      wisp='energy', spark='star', mote='star'),
    'plasma':    dict(color=[255, 90, 210], color2=[255, 220, 250], core='glow_hard', halo='glow', fil='lightning',
                      wisp='energy', spark='spark', mote='star'),
    'dust':      dict(color=[190, 165, 125], color2=[230, 215, 185], core='dust', halo='dust', fil='dust',
                      wisp='dust', spark='dust', mote='dust'),
    'ash':       dict(color=[90, 85, 80], color2=[150, 140, 130], core='smoke', halo='smoke', fil='smoke',
                      wisp='smoke', spark='star', mote='dust'),
}
for _k in ('particles', 'impact', 'energy'):
    ENERGY[_k] = dict(ENERGY['chakra'])
# dark fantasy (Berserk): black ink dominant, blood-red core, purple rim. color = red core, color2 = purple rim
ENERGY['demonic'] = dict(color=[165, 12, 22], color2=[105, 25, 150], ink=[14, 6, 16], core='glow', halo='glow',
                         fil='lightning', wisp='chakra_tongue', spark='star', mote='star', recipe='demonic')
# cosmic demonic (violet nebula): color = violet, color2 = magenta highlights
ENERGY['abyss'] = dict(color=[120, 45, 235], color2=[235, 120, 255], core='glow', halo='nebula', fil='curl',
                       wisp='curl', spark='sparkle', mote='sparkle', recipe='abyss')
# Kuro Kaminari (Darui): black ink discharges with an electric-blue core; color = pale electric blue light
ENERGY['black_lightning'] = dict(color=[120, 170, 255], color2=[220, 235, 255], core='glow', halo='glow',
                                 fil='black_strand', wisp='black_bolt', spark='spark', mote='spark',
                                 recipe='black_lightning')
# anime flame set (cel-shaded tongues + translucent body): energies that burn like chakra
for _k in ('chakra', 'fire', 'magic', 'plasma', 'particles', 'impact', 'energy', 'demonic'):
    ENERGY[_k].update(tongue='chakra_tongue', lick='chakra_lick', body='chakra_body')
ALPHA_TEX = {'smoke', 'dust', 'droplet', 'shard'}

# ------------------------------------------------------------------ styles: structural changes, not colours
# m_*: multipliers; hold: fade style; spin; add/drop roles; motion speed; variation defaults
LOOK = {
    'soft':       dict(m_size=1.2, m_alpha=.8, m_life=1.2, hold=None, var=.2),
    'sharp':      dict(m_size=.8, m_life=.75, m_alpha=1.1, hold=.75, core='glow_hard', spark_trail=True, var=.15),
    'anime':      dict(m_life=.85, hold=.72, m_alpha=1.15, add=('ring',), spin=True, var=.12, m_rate=.8),
    'cartoon':    dict(m_life=.85, hold=.7, m_alpha=1.2, m_size=1.15, add=('ring',), var=.1, m_rate=.7),
    'energetic':  dict(m_speed=1.35, m_rate=1.2, pulse=1.5, var=.25),
    'mystical':   dict(m_speed=.7, m_life=1.35, m_alpha=.85, pulse=.8, add=('secondary',), var=.25),
    'aggressive': dict(m_speed=1.5, m_rate=1.35, m_life=.75, m_spark=1.7, hold=.8, spark_trail=True, var=.3),
    'elegant':    dict(m_rate=.65, m_size=.85, m_life=1.2, m_alpha=.85, m_spark=.5, m_speed=.8, var=.15),
    'dense':      dict(m_rate=1.6, m_spark=1.4, var=.2),
    'minimal':    dict(m_rate=.55, drop=('secondary',), m_spark=.5, var=.1),
}


def _looks(style):
    look = style.get('look', [])
    return [look] if isinstance(look, str) else list(look)


def _merge_look(names):
    out = dict(m_size=1, m_alpha=1, m_life=1, m_rate=1, m_speed=1, m_spark=1, hold=None, add=(), drop=(), spin=False,
               spark_trail=False, pulse=None, var=.2, core=None)
    for n in names:
        lk = LOOK[n]
        for k, v in lk.items():
            if k.startswith('m_'):
                out[k] *= v
            elif k in ('add', 'drop'):
                out[k] = tuple(out[k]) + tuple(v)
            else:
                out[k] = v
    return out


# ------------------------------------------------------------------ shape recipes -> role layers
def _aura(g, E, c1, c2):
    R, H = g['radius'], g['height']
    if 'tongue' in E:                                   # anime aura: the body of chakra carries the silhouette
        body = [int(c * .85) for c in c1]
        return [
            dict(role='core', id='body', tex=E['body'], rate=30, shape='ring', radius=R * .6, thickness=R * .35,
                 height=[H * .05, H * .9], life=[.6, .9], size=[R * .45, R * .7], alpha=[45, 75], color=body,
                 attach=True, rot=True, spin=[-15, 15], fade_in=.3, fade_out=.45),
            dict(role='filaments', id='flames', tex=E['tongue'], rate=26, attach=True, anim_rate=1.5, shape='ring', radius=R * .8, thickness=R * .2,
                 height=[0, H * .85], up=[H * .45, H * .8], drag=.12, life=[.45, .7], size=[R * .35, R * .55],
                 grow=[.55, 1.0, .35], shrink_end=.5, alpha=[160, 215], color=[c1, c2], rot=True, spin=[-15, 15],
                 motion=[{'type': 'orbit', 'speed': .25}], fade_in=.12, fade_out=.35),
            dict(role='accents', id='licks', tex=E['lick'], rate=10, attach=True, anim_rate=1.5, shape='ring', radius=R * .75, thickness=R * .2,
                 height=[H * .1, H * .9], up=[H * .55, H * .9], drag=.12, life=[.3, .5], size=[R * .2, R * .32],
                 grow=[.5, 1.0, .35], alpha=[80, 130], color=c2, rot=True, spin=[-15, 15], fade_in=.1, fade_out=.4),
            dict(role='secondary', tex=E['mote'], rate=6, shape='ring', radius=R * .9, thickness=R * .3,
                 height=[0, H], up=[H * .5, H * .9], life=[.8, 1.2], size=[.8, 1.4], alpha=[150, 220], color=c2,
                 drag=.08, motion=[{'type': 'flow', 'speed': .5}], fade_in=.2, fade_out=.5),
        ]
    return [
        dict(role='core', tex=E['core'], count=1, life=[60, 60], size=[R * .22, R * .26], attach=True, alpha=235,
             offset=[0, 0, H * .5], color=c2, fade_in=.02, pulse=6),
        dict(role='halo', tex=E['halo'], count=1, life=[60, 60], size=[R * 1.1, R * 1.25], attach=True, alpha=70,
             offset=[0, 0, H * .5], color=c1, fade_in=.03, pulse=10),
        dict(role='filaments', tex=E['wisp'], rate=14, shape='ring', radius=R * .7, thickness=R * .3,
             height=[H * .05, H * .6], life=[.7, 1.0], size=[R * .22, R * .32], alpha=[150, 200], color=[c1, c2],
             attach=True, motion=[{'type': 'orbit', 'speed': 1.0}, {'type': 'rise', 'height': H * .6}],
             fade_in=.2, fade_out=.45),
        dict(role='sparks', tex=E['spark'], count=0, rate=10, shape='sphere', spread=[R * .3, R * .9],
             height=[H * .2, H * .8], speed=[20, 60], up=[40, 90], life=[.4, .7], size=[1.0, 1.8], alpha=[200, 255],
             color=c2, drag=.08, fade_out=.4, render='trail', trail=[.03, .06]),
        dict(role='secondary', tex=E['mote'], rate=6, shape='sphere', spread=[R * .4, R * 1.1], height=[0, H],
             up=[10, 30], life=[1.0, 1.6], size=[1.2, 2.2], alpha=[120, 200], color=c1, drag=.1,
             motion=[{'type': 'flow', 'speed': .6}], fade_in=.3, fade_out=.5),
    ]


def _burst(g, E, c1, c2):
    R = g['radius']
    return [
        dict(role='core', tex=E['core'], count=1, life=[.9, .9], size=[R * .15, R * .15], grow=[.3, 1.4, .3],
             alpha=240, color=c2, phase='charge', fade_out=.2),
        dict(role='secondary', id='gather', tex=E['mote'], rate=40, shape='sphere', spread=[R * .8, R * 1.2],
             life=[.4, .55], size=[1.2, 2.0], color=c1, motion=[{'type': 'vortex', 'speed': 1.0, 'radius': R}],
             fade_in=.3, fade_out=.3, phase='charge'),
        dict(role='accents', id='flash', tex='flare', count=1, life=[.18, .18], size=[R * .9, R * .9],
             grow=[.4, 1.2, .3], alpha=255, color=c2, phase='release', fade_out=.6),
        dict(role='accents', id='ring', tex='ring_soft', count=1, life=[.45, .45], size=[R * 1.6, R * 1.6],
             grow=[.08, 1.0, .45], alpha=200, color=c1, orient='ground', offset=[0, 0, 2], phase='release',
             fade_out=.6),
        dict(role='sparks', tex=E['spark'], count=28, shape='sphere', spread=[0, 4], speed=[R * 5, R * 11],
             life=[.25, .5], size=[1.4, 2.6], color=[c1, c2], drag=.06, render='trail', trail=[.03, .06],
             motion=[{'type': 'radial_burst'}], phase='release', fade_out=.4),
        dict(role='filaments', tex=E['wisp'], count=10, shape='sphere', spread=[0, R * .2], speed=[R * 1.5, R * 3],
             life=[.4, .6], size=[R * .3, R * .45], color=[c1, c2], alpha=[160, 220], drag=.15, rot=True,
             spin=[-120, 120], phase='release', fade_out=.5),
        dict(role='secondary', id='residue', tex=E['mote'], count=16, shape='sphere', spread=[R * .2, R * .8],
             up=[10, 40], life=[.8, 1.3], size=[1.0, 1.8], color=c1, drag=.1, motion=[{'type': 'flow', 'speed': .5}],
             phase='aftermath', fade_out=.5),
    ]


def _projectile(g, E, c1, c2):
    R = g['radius']
    return [
        dict(role='core', tex=E['core'], count=1, life=[60, 60], size=[R * .35, R * .4], attach=True, alpha=245,
             color=c2, pulse=4),
        dict(role='halo', tex=E['halo'], count=1, life=[60, 60], size=[R * 1.1, R * 1.3], attach=True, alpha=110,
             color=c1),
        dict(role='filaments', id='trail', tex=E['fil'], render='rope', rate=70, life=[.22, .28], size=[R * .25, R * .3],
             shrink=.1, alpha=200, color=[c1, c2], motion=[{'type': 'flow', 'speed': .6}], fade_out=.6),
        dict(role='filaments', id='wisps', tex=E['wisp'], rate=30, shape='sphere', spread=[0, R * .3],
             life=[.2, .3], size=[R * .35, R * .5], color=[c1, c2], alpha=[150, 210], rot=True, fade_out=.5),
        dict(role='sparks', tex=E['spark'], rate=18, shape='sphere', spread=[0, R * .4], speed=[20, 80],
             life=[.25, .4], size=[.8, 1.5], color=c2, drag=.08, fade_out=.4),
    ]


def _impact(g, E, c1, c2):
    R = g['radius']
    L = _burst(g, E, c1, c2)
    L = [l for l in L if l.get('phase') != 'charge']
    for l in L:
        if l.get('phase') == 'release':
            l['phase'] = 'impact'
    L.append(dict(role='secondary', id='smoke', tex='smoke', count=6, shape='sphere', spread=[0, R * .3],
                  speed=[R * .3, R * .8], up=[10, 30], size=[R * .4, R * .6], grow=[.6, 1.6, .5], life=[.9, 1.3],
                  alpha=[70, 110], color=[110, 105, 100], drag=.1, rot=True, spin=[-20, 20], phase='aftermath',
                  fade_in=.15, fade_out=.6))
    return L


def _vortex(g, E, c1, c2):
    R, H = g['radius'], g['height']
    return [
        dict(role='core', tex=E['core'], count=1, life=[60, 60], size=[R * .25, R * .3], attach=True,
             offset=[0, 0, H * .15], alpha=230, color=c2, pulse=5),
        dict(role='filaments', tex=E['fil'], render='rope', rate=45, shape='ring', radius=R, ring_even=True,
             count=0, life=[.8, .8], size=[2, 3], alpha=190, color=[c1, c2],
             motion=[{'type': 'spiral', 'speed': 1.0, 'height': H}], fade_out=.5),
        dict(role='filaments', id='wisps', tex=E['wisp'], rate=22, shape='ring', radius=R * .8, thickness=R * .3,
             life=[.6, .9], size=[R * .25, R * .35], color=[c1, c2], alpha=[140, 200],
             motion=[{'type': 'spiral', 'speed': 1.1, 'height': H}], fade_in=.2, fade_out=.45),
        dict(role='secondary', tex=E['mote'], rate=30, shape='ring', radius=R * 1.6, thickness=R * .6,
             height=[0, H * .5], life=[.5, .7], size=[1.2, 2.2], color=c1, motion=[{'type': 'vortex', 'radius': R}],
             fade_in=.2, fade_out=.3),
        dict(role='sparks', tex=E['spark'], rate=12, shape='ring', radius=R, speed=[20, 60], up=[H * .8, H * 1.4],
             life=[.4, .6], size=[1, 1.8], color=c2, render='trail', trail=[.03, .05], fade_out=.4),
    ]


def _trail(g, E, c1, c2):
    R = g['radius']
    return [
        dict(role='core', tex=E['fil'], render='rope', rate=80, life=[.35, .4], size=[R * .2, R * .2], shrink=.05,
             alpha=230, color=c2, fade_out=.5),
        dict(role='halo', tex=E['halo'], rate=30, life=[.25, .35], size=[R * .6, R * .8], alpha=60, color=c1,
             fade_out=.6),
        dict(role='filaments', tex=E['wisp'], rate=25, shape='sphere', spread=[0, R * .3], life=[.3, .45],
             size=[R * .3, R * .45], color=[c1, c2], alpha=[140, 200], motion=[{'type': 'flow', 'speed': .8}],
             rot=True, fade_out=.5),
        dict(role='sparks', tex=E['spark'], rate=14, shape='sphere', spread=[0, R * .3], speed=[20, 60],
             life=[.3, .5], size=[.8, 1.4], color=c2, drag=.1, fade_out=.4),
    ]


def _beam(g, E, c1, c2):
    R = g['radius']
    return [
        dict(role='core', tex=E['fil'], render='rope', count=24, shape='path', life=[60, 60], size=[R * .15, R * .15],
             alpha=235, color=c2, scroll=40),
        dict(role='halo', tex=E['halo'], rate=20, shape='segment', spread=[0, R * .1], life=[.3, .4],
             size=[R * .5, R * .7], alpha=60, color=c1, fade_in=.3, fade_out=.5),
        dict(role='sparks', tex=E['spark'], rate=16, shape='segment', spread=[0, R * .2], speed=[10, 40],
             life=[.25, .4], size=[.8, 1.4], color=c2, drag=.1, fade_out=.4),
    ]


RECIPES = dict(aura=_aura, burst=_burst, projectile=_projectile, impact=_impact, vortex=_vortex, trail=_trail,
               beam=_beam, sphere=_aura, cloud=_aura, ring=_burst, radial=_burst, spiral=_vortex, cone=_vortex,
               ribbon=_trail, line=_beam, custom=_aura)
DEFAULT_TIMELINE = dict(burst=[('charge', .6), ('release', .2), ('aftermath', 1.0)],
                        ring=[('charge', .3), ('release', .2), ('aftermath', .8)],
                        radial=[('charge', .3), ('release', .2), ('aftermath', .8)],
                        impact=[('impact', .3), ('aftermath', 1.2)])


# ------------------------------------------------------------------ model-driven: roles along a segment (CP0 -> CP1)
def _segment_roles(seg, E, c1, c2):
    """Layers for a region such as a blade. CP0 = region start, CP1 = region end (set by the runtime)."""
    Ln, W = seg['length'], max(seg['radius'], 1.0)
    n = max(8, int(Ln / 3))
    return [
        dict(role='core', tex=E['fil'], render='rope', count=n, shape='path', life=[60, 60], size=[.6, .9],
             alpha=235, color=c2, scroll=60, fade_in=.02),
        dict(role='halo', tex=E['halo'], rate=max(6, Ln * .35), shape='segment', spread=[0, W * .15],
             life=[.35, .5], size=[W * .5, W * .7], alpha=[35, 55], color=c1, fade_in=.3, fade_out=.5, pulse=3),
        dict(role='filaments', tex=E['wisp'], rate=max(8, Ln * .5), shape='segment', spread=[0, W * .2],
             life=[.3, .45], size=[W * .18, W * .28], alpha=[130, 190], color=[c1, c2], rot=True,
             motion=[{'type': 'flow', 'speed': .5}], fade_in=.15, fade_out=.45),
        dict(role='sparks', tex=E['spark'], rate=max(4, Ln * .12), shape='sphere', cp=1, spread=[0, W * .3],
             speed=[15, 45], up=[5, 25], life=[.25, .45], size=[.6, 1.1], alpha=[200, 255], color=c2, drag=.1,
             fade_out=.4),
        dict(role='secondary', tex=E['mote'], rate=max(3, Ln * .08), shape='segment', spread=[W * .3, W * .7],
             up=[5, 15], life=[.6, 1.0], size=[.8, 1.4], alpha=[120, 180], color=c1, drag=.1,
             motion=[{'type': 'flow', 'speed': .4}], fade_in=.3, fade_out=.5),
    ]


def _local_axis(seg):
    """Blade direction in the bone frame (CP0 carries the bone orientation)."""
    return [round(x, 4) for x in seg['axis']]


def envelope(seg, scale=1.35, margin=3.0, fill=True, faces=False):
    """Scales the model silhouette (analyze.profile) into an envelope, in bone space.

    Returns (points, ranges): points become control points 2, 3, ... (set by the runtime every frame);
    ranges['outline'] is the closed contour, ranges['fill'] a zigzag between the upper and lower edges
    (every segment of it lies inside the shape, so emitting along it fills the silhouette).
    """
    import numpy as np
    sl = seg['profile']['slices']
    ax = np.array(seg['axis'], float)
    cs = [np.array(s['center'], float) for s in sl]
    mid = cs[0]                                          # anchored at the grip side: the envelope grows forward
    k_ax = 1 + (scale - 1) * .5                         # grows less along the length than across it

    def grow(p, c, k, m):
        p, c = np.asarray(p, float), np.asarray(c, float)
        c2 = mid + (c - mid) * k_ax
        d = p - c
        n = np.linalg.norm(d)
        return c2 + d * k + (d / n * m if n > 1e-6 else 0)

    up = [grow(s['upper'], s['center'], scale, margin) for s in sl]
    lo = [grow(s['lower'], s['center'], scale, margin) for s in sl]
    tail = mid + (cs[0] - mid) * k_ax - ax * margin
    tip = mid + (cs[-1] - mid) * k_ax + ax * margin * 1.5
    outline = [tail] + up + [tip] + lo[::-1] + [tail]
    inner = [grow(s['upper'], s['center'], scale * .8, 0) for s in sl], [grow(s['lower'], s['center'], scale * .8, 0) for s in sl]
    groups = [('outline', outline)]
    if fill:
        groups.append(('fill', [p for pair in zip(*inner) for p in pair]))
    if faces:                                            # just in front of each face of the blade (cracks, runes)
        th = np.array(seg['profile']['thickness_axis'], float)
        for name, key, sgn in (('front', 'front', 1), ('back', 'back', -1)):
            line = [np.array(s[key], float) + th * sgn * .35 for s in sl]
            groups.append((name, line + line[-2::-1]))      # closed loop base->tip->base: a rope has no seam
    pts, ranges = [], {}
    for name, g in groups:
        ranges[name] = (2 + len(pts), 1 + len(pts) + len(g))
        pts += g
    half = float(np.mean([np.linalg.norm(u - l) / 2 for u, l in zip(up, lo)]))
    return [p.round(3).tolist() for p in pts], ranges, half


def _envelope_roles(env, E, c1, c2, rise):
    """Chakra wrapping a model part (e.g. Hiramekarei's blade), following its real silhouette.

    GMod tests 30/09/2026: (1) big, dense, free-floating flames read as noise -> everything that draws the
    shape is locked to the blade (CP0 position + rotation); (2) the blade hides whatever is inside its
    outline -> the chakra mass lives on the contour band, and two light streaks run along the contour.
    """
    pts, R, W = env
    o0, o1 = R['outline']; f0, f1 = R['fill']
    deep = [int(c * .65) for c in c1]
    lock = dict(attach='rotation', lock_cp=0)
    lap = 1.8                                           # seconds for a streak to go round the blade
    streak = dict(role='accents', tex='softline', render='rope', shape='chain_seq', cp=o0, cp_end=o1, path_count=64,
                  rate=64 / lap, life=[lap * .3, lap * .3], size=[1.1, 1.1], alpha=220, color=c2, texel=12,
                  fade_out=.9, fixed=True, **lock)
    return [
        dict(role='core', id='band', tex=E.get('body', 'chakra_body'), rate=30, shape='chain', cp=o0, cp_end=o1,
             spread=[0, W * .18], life=[.6, .9], size=[W * .45, W * .65], alpha=[60, 90], color=deep, rot=True,
             spin=[-10, 10], fade_in=.3, fade_out=.45, pulse=1.2, **lock),
        dict(role='halo', id='haze', tex=E.get('body', 'chakra_body'), rate=12, shape='chain', cp=o0, cp_end=o1,
             spread=[0, W * .1], life=[.7, 1.0], size=[W * .8, W * 1.1], alpha=[22, 36], color=c1, rot=True,
             fade_in=.35, fade_out=.5, **lock),
        dict(role='filaments', id='flames', tex=E.get('tongue', 'chakra_tongue'), rate=40, shape='chain', cp=o0,
             cp_end=o1, spread=[0, W * .05], up=[rise * .6, rise], drag=.1, life=[.35, .55],
             size=[W * .28, W * .42], grow=[.5, 1.0, .35], shrink_end=.4, alpha=[170, 220], color=c1,
             color_end=c2, color_end_at=[.3, 1], rot=True, spin=[-8, 8], anim_rate=1.5, fade_in=.15, fade_out=.4,
             **lock),
        dict(role='accents', id='licks', tex=E.get('lick', 'chakra_lick'), rate=12, shape='chain', cp=o0, cp_end=o1,
             spread=[0, W * .04], up=[rise * .7, rise * 1.1], drag=.1, life=[.3, .45], size=[W * .18, W * .26],
             grow=[.5, 1.0, .35], alpha=[80, 120], color=c2, rot=True, spin=[-8, 8], anim_rate=1.5,
             fade_in=.1, fade_out=.4, **lock),
        dict(streak, id='streak'),
        dict(streak, id='streak2', delay=lap / 2),
        dict(role='secondary', id='motes', tex=E['mote'], rate=3, shape='chain', cp=o0, cp_end=o1, spread=[0, W * .1],
             up=[rise * .8, rise * 1.3], life=[.5, .8], size=[.6, 1.0], alpha=[140, 200], color=c2, drag=.1,
             fade_in=.2, fade_out=.5),
    ]


def _demonic_roles(env, E, c1, c2, rise):
    """Berserk-like demonic aura: its own visual language, not a recoloured chakra.

    GMod test 30/09/2026: the chakra recipe in black/red read as "cute". Here the silhouette is carried by a column
    of boiling black miasma that climbs well above the sword (free, not locked: it trails behind a swing), ink
    spikes with a blood-red heart on the edges, a pulsing blood-red underglow (keeps the shape readable on dark
    maps), short branching red crackles, a crack on each face, and embers + ash carried up by the miasma.
    Textures carry their own colours (white particle colour) except the additive ones.
    """
    pts, R, W = env
    o0, o1 = R['outline']
    lock = dict(attach='rotation', lock_cp=0)
    white = [255, 255, 255]
    lap = 2.4
    crack = dict(role='accents', tex='lightning', render='rope', shape='chain_seq', path_count=44, rate=44 / lap,
                 life=[lap, lap], size=[1.4, 1.4], alpha=200, color=c1, texel=10, pulse_alpha=[.45, .6],
                 fade_in=.05, fade_out=.1, fixed=True, **lock)
    return [
        dict(role='core', id='miasma', tex='miasma', rate=12, shape='chain', cp=o0, cp_end=o1, spread=[0, W * .2],
             up=[rise * .8, rise * 1.35], drag=.12, life=[1.4, 2.0], size=[W * .9, W * 1.3], grow=[1.0, 2.6, .5],
             alpha=[150, 200], color=white, rot=True, spin=[-20, 20], anim_rate=.5,
             motion=[{'type': 'flow', 'speed': .6}], fade_in=.12, fade_out=.55),
        dict(role='filaments', id='spikes', tex='ink_spike', rate=34, shape='chain', cp=o0, cp_end=o1,
             spread=[0, W * .05], up=[8, 16], life=[.35, .6], size=[W * .9, W * 1.4], grow=[.6, 1.0, .3],
             alpha=[200, 245], color=white, fade_in=.1, fade_out=.35, **lock),
        dict(role='halo', id='blood_glow', tex='glow', rate=14, shape='chain', cp=o0, cp_end=o1, spread=[0, W * .08],
             life=[.8, 1.2], size=[W * 1.0, W * 1.4], alpha=[45, 70], color=c1, fade_in=.35, fade_out=.5, **lock),
        dict(role='accents', id='crackles', tex='crackle', rate=7, shape='chain', cp=o0, cp_end=o1, spread=[0, W * .15],
             life=[.08, .16], size=[W * 1.2, W * 2.0], alpha=[200, 255], color=[255, 40, 30], rot=True,
             fade_out=.5, fixed=True, **lock),
        dict(crack, id='crack', cp=R['front'][0], cp_end=R['front'][1]),
        dict(crack, id='crack_back', cp=R['back'][0], cp_end=R['back'][1]),
        dict(role='secondary', id='embers', tex='star', rate=12, shape='chain', cp=o0, cp_end=o1, spread=[0, W * .2],
             up=[rise * .9, rise * 1.6], life=[1.2, 2.2], size=[.7, 1.3], alpha=[190, 250], color=[255, 70, 35],
             color_end=[120, 10, 10], drag=.08, motion=[{'type': 'flow', 'speed': .5}], fade_in=.1, fade_out=.5),
        dict(role='secondary', id='ash', tex='dust', rate=6, shape='chain', cp=o0, cp_end=o1, spread=[0, W * .2],
             up=[rise * .7, rise * 1.2], life=[1.4, 2.2], size=[1.0, 2.0], alpha=[160, 220], color=[22, 12, 18],
             rot=True, spin=[-90, 90], drag=.1, motion=[{'type': 'flow', 'speed': .5}], fade_in=.2, fade_out=.5),
    ]


def _abyss_roles(env, E, c1, c2, rise, axis=(0, 0, 1)):
    """Cosmic demonic aura (violet nebula), user's reference image + calibration on fsc_aura2.pcf (30/09/2026).

    GMod test v1: too light, and the blade glow read as separate round pink balls. Calibration from the
    reference PCF (python -m pcfforge analyze references/fsc_aura2.pcf): 60-160 particles/s per layer, ~1 s
    lives, saturated DARK violets (no near-white), big textured sprites that keep growing, locked to the
    weapon then released at ~70 % of their life so they peel away, gentle random force + swirl.
    Layers: inner light strip (rope along each face: smooth, never balls), dense violet smoke body, filament
    nebula, swirling flecks, dense twinkling glints, curls, dark void behind.
    """
    pts, R, W = env
    o0, o1 = R['outline']
    deep = [88, 0, 186]; dark = [30, 0, 107]                     # reference violets (fsc_aura2 akuma*)
    lock = dict(attach='rotation', lock_cp=0)
    peel = dict(attach='rotation', lock_cp=0, release=.7)
    strips = [dict(role='core', id=f'blade_{k}', tex='softline', render='rope', shape='chain_seq', cp=R[k][0],
                   cp_end=R[k][1], path_count=34, rate=34 / 1.2, life=[1.2, 1.2], size=[W * .8, W * .8], alpha=90,
                   color=c1, texel=W * 3, fade_in=.1, fade_out=.1, fixed=True, **lock) for k in ('front', 'back')]
    return strips + [
        dict(role='halo', id='void', tex='smoke', rate=10, shape='chain', cp=o0, cp_end=o1, spread=[0, W * .5],
             life=[1.4, 2.0], size=[W * 1.8, W * 2.6], grow=[.8, 1.4, .5], alpha=[70, 100], color=[14, 2, 28],
             rot=True, spin=[-10, 10], fade_in=.3, fade_out=.5, fixed=True, **peel),
        dict(role='core', id='smoke', tex='smoke', rate=80, shape='chain', cp=o0, cp_end=o1, spread=[0, W * .35],
             up=[2, 6], life=[.8, 1.2], size=[W * .7, W * 1.0], grow=[.8, 2.2, .5], alpha=[150, 200],
             color=[deep, dark], rot=True, spin=[-25, 25], noise=15, fade_in=.15, fade_out=.3, fixed=True, **peel),
        dict(role='halo', id='nebula', tex='nebula', rate=24, shape='chain', cp=o0, cp_end=o1, spread=[0, W * .5],
             life=[1.0, 1.6], size=[W * 1.4, W * 2.2], grow=[.8, 1.3, .5], alpha=[80, 120], color=[c1, [150, 20, 230]],
             rot=True, spin=[-12, 12], fade_in=.3, fade_out=.45, fixed=True, **peel),
        dict(role='accents', id='flecks', tex='star', rate=60, shape='chain', cp=o0, cp_end=o1, spread=[W * .2, W * .9],
             life=[.8, 1.2], size=[.8, 1.4], alpha=[200, 255], color=[[180, 0, 255], [110, 30, 240]], noise=15,
             twist_axis=[64, list(axis)], fade_in=.15, fade_out=.3, fixed=True, **peel),
        dict(role='sparks', id='glitter', tex='sparkle', rate=70, shape='chain', cp=o0, cp_end=o1, spread=[0, W * 1.3],
             life=[.6, 1.3], size=[.8, 2.6], alpha=[210, 255], color=[[245, 190, 255], c2], rot=True,
             pulse_alpha=[.9, 3.0], fade_in=.2, fade_out=.4, fixed=True, **lock),
        dict(role='filaments', id='curls', tex='curl', rate=10, shape='chain', cp=o0, cp_end=o1, spread=[0, W * .7],
             life=[1.0, 1.5], size=[W * .9, W * 1.5], alpha=[140, 190], color=[c1, c2], rot=True, spin=[-45, 45],
             grow=[.7, 1.1, .4], fade_in=.3, fade_out=.5, fixed=True, **peel),
    ]


def _black_lightning_roles(env, E, c1, c2, rise, axis=(0, 0, 1)):
    """Darui's black lightning (Kuro Kaminari) on the validated abyss structure (GMod tests 30/09/2026).

    v1 (lightning sprites + round glows, no volume) was rejected: ugly crackle, no aura, "balls". Lessons:
    'sober' still means an aura body (volume calibrated on fsc_aura2, just lighter), lightning must FOLLOW the
    geometry (ropes along the outline, re-drawn with jitter), and no isolated glow sprites.
    v2 feedback: tighten the aura so it draws real contours, and make the lightning animated particles.
    v3 feedback: randomly oriented bolt sprites looked like scribbles spinning around the blade, not lightning,
    and did not go round the weapon; the blue was dull. Now three discharges RUN round the exact outline (ropes
    in order along the contour, jagged by jitter, black ink under a white-hot electric core), at three speeds so
    they overtake each other; vivid electric blue.
    Layers: electric strip inside each face, dark storm smoke hugging the edges (sticks then peels),
    electric-blue haze close to the blade, the running discharges, swirling static flecks, a few sparks.
    """
    pts, R, W = env
    o0, o1 = R['outline']
    lock = dict(attach='rotation', lock_cp=0)
    peel = dict(attach='rotation', lock_cp=0, release=.7)
    elec = [40, 120, 255]                                   # vivid electric blue (v3: "le bleu doit être plus éclatant")
    bright = [90, 175, 255]

    def runner(idn, tex, width, alpha, color, lap, n=90, seg=.17):
        """A discharge running round the blade: a rope along the outline, in order (chain_seq), whose particles
        live for `seg` of a lap -> a jagged segment (jitter) that travels along the edge, one lap in `lap` s."""
        return dict(role='accents', id=idn, tex=tex, render='rope', shape='chain_seq', cp=o0, cp_end=o1,
                    path_count=n, rate=n / lap, life=[lap * seg, lap * seg], size=[width, width], spread=[0, 1.8],
                    alpha=alpha, color=color, texel=8, scroll=40, fade_in=.15, fade_out=.35, fixed=True, **lock)
    strips = [dict(role='core', id=f'blade_{k}', tex='softline', render='rope', shape='chain_seq', cp=R[k][0],
                   cp_end=R[k][1], path_count=34, rate=34 / 1.2, life=[1.2, 1.2], size=[W * .7, W * .7], alpha=120,
                   color=elec, texel=W * 3, fade_in=.1, fade_out=.1, fixed=True, **lock) for k in ('front', 'back')]

    return strips + [
        dict(role='core', id='storm', tex='smoke', rate=45, shape='chain', cp=o0, cp_end=o1, spread=[0, W * .15],
             up=[1, 4], life=[.7, 1.0], size=[W * .5, W * .7], grow=[.8, 1.5, .5], alpha=[120, 160],
             color=[[18, 20, 32], [42, 52, 90]], rot=True, spin=[-25, 25], noise=10, fade_in=.15, fade_out=.3,
             fixed=True, **peel),
        dict(role='halo', id='charge', tex='nebula', rate=14, shape='chain', cp=o0, cp_end=o1, spread=[0, W * .2],
             life=[.8, 1.2], size=[W * .9, W * 1.3], grow=[.8, 1.2, .5], alpha=[95, 140],
             color=[elec, [110, 190, 255]], rot=True, spin=[-15, 15], fade_in=.3, fade_out=.45, fixed=True, **peel),
        *[dict(runner(f'run{i}', 'black_strand', 2.2, 200, [255, 255, 255], lap), delay=d)
          for i, (lap, d) in enumerate(((.8, 0), (1.1, .35), (1.4, .7)))],
        *[dict(runner(f'bolt{i}', 'bolt_strand', 1.3, 255, bright, lap), delay=d)
          for i, (lap, d) in enumerate(((.8, 0), (1.1, .35), (1.4, .7)))],
        dict(role='accents', id='static', tex='star', rate=34, shape='chain', cp=o0, cp_end=o1, spread=[W * .1, W * .45],
             life=[.6, 1.0], size=[.6, 1.2], alpha=[200, 255], color=[[130, 205, 255], [50, 130, 255]], noise=15,
             twist_axis=[64, list(axis)], fade_in=.15, fade_out=.3, fixed=True, **peel),
        dict(role='sparks', id='sparks', tex='spark', render='trail', trail=[.02, .04], rate=10, shape='chain', cp=o0,
             cp_end=o1, spread=[0, W * .1], speed=[60, 160], life=[.1, .25], size=[.5, .9], alpha=[220, 255],
             color=[c2, c1], drag=.08, fade_out=.4, fixed=True),
    ]


# ------------------------------------------------------------------ main
def _scale_layer(L, lk, intensity, quality):
    k_count = lk['m_rate'] * (.6 + .8 * intensity) * quality
    if L['role'] == 'sparks':
        k_count *= lk['m_spark']
    for key in ('rate',):
        if L.get(key):
            L[key] = round(L[key] * k_count, 2)
    if L.get('count') and L.get('life', [0, 0])[1] < 30:        # persistent single sprites keep count 1
        L['count'] = max(1, int(round(L['count'] * k_count)))
    if 'life' in L and L['life'][1] < 30:
        L['life'] = [round(x * lk['m_life'] * (1.0 if quality >= .7 else .9), 3) for x in L['life']]
    if 'size' in L:
        L['size'] = [round(x * lk['m_size'] * (.85 + .3 * intensity), 3) for x in L['size']]
    if 'alpha' in L:
        a = L['alpha'] if isinstance(L['alpha'], list) else [L['alpha'], L['alpha']]
        L['alpha'] = [min(255, int(x * lk['m_alpha'])) for x in a]
    if 'speed' in L:
        L['speed'] = [x * lk['m_speed'] for x in L['speed']]
    for m in L.get('motion', []) or []:
        if isinstance(m, dict):
            m['speed'] = m.get('speed', 1.0) * lk['m_speed']
    if lk['hold'] and 'fade_out' in L and L['role'] != 'halo':
        L.pop('fade_out')
        L['hold'] = lk['hold']
    if lk['spin'] and L['role'] in ('filaments', 'secondary') and L.get('render', 'sprite') == 'sprite':
        L['rot'] = True
        L.setdefault('spin', [-90, 90])
    if lk['pulse'] and 'pulse' in L:
        L['pulse'] = L['pulse'] * lk['pulse']
    if lk['spark_trail'] and L['role'] == 'sparks' and L.get('render', 'sprite') == 'sprite':
        L.update(render='trail', trail=[.03, .06])
    if lk['core'] and L['role'] == 'core' and L.get('render', 'sprite') == 'sprite':
        L['tex'] = lk['core']


def _peak(L):
    return LY.estimate_peak(dict(L, _phase_duration=None))


def compose(effect):
    """effect: normalized dict from effect.load(). Returns (layer_spec, runtime_info, notes)."""
    notes = []
    style, shape = effect['style'], effect['shape']
    energy = style.get('type', 'chakra')
    E = ENERGY[energy]
    c1 = list(style.get('color') or E['color'])
    c2 = list(style.get('secondary_color') or E['color2'])
    intensity = float(style.get('intensity', .6))
    lk = _merge_look(_looks(style))
    perf = effect['performance']
    q = QUALITY[perf.get('quality', 'high')]
    g = dict(radius=float(shape.get('radius', 32)), height=float(shape.get('height', 72)))
    runtime = dict(attach=effect['attachment'], mode=effect['mode'])

    seg = effect.get('_segment')
    env = None
    if seg:                                             # model-driven along a real segment
        runtime['segment'] = seg
        notes.append(f"segment {seg['bone']} : {seg['length']} u, rayon {seg['radius']} u ({seg['source']})")
        if seg.get('profile') and shape.get('silhouette', True):
            recipe = {'demonic': _demonic_roles, 'abyss': _abyss_roles,
                      'black_lightning': _black_lightning_roles}.get(E.get('recipe'), _envelope_roles)
            own = recipe is not _envelope_roles                   # own recipes use the faces, not the inner fill
            env = envelope(seg, float(shape.get('scale', 1.25)), float(shape.get('margin', 2)),
                           fill=not own, faces=own)
            kw = {'axis': _local_axis(seg)} if recipe in (_abyss_roles, _black_lightning_roles) else {}
            roles = recipe(env, E, c1, c2, float(shape.get('rise', 16)), **kw)
            runtime['points'] = env[0]
            notes.append(f"silhouette : {len(env[0])} points de contrôle (CP2-CP{1 + len(env[0])}), "
                         f"demi-largeur moyenne {env[2]:.1f} u")
        else:
            roles = _segment_roles(seg, E, c1, c2)
    else:
        roles = RECIPES[shape['type']](g, E, c1, c2)
    roles = copy.deepcopy(roles)

    # style: structural adds / drops
    if 'ring' in lk['add'] and shape['type'] in ('burst', 'impact', 'ring', 'radial') and not any(
            l.get('id') == 'ring' for l in roles):
        roles.append(dict(role='accents', id='ring', tex='ring', count=1, life=[.35, .35], size=[g['radius'] * 1.6] * 2,
                          grow=[.1, 1, .4], alpha=230, color=c2, orient='ground', offset=[0, 0, 2]))
    roles = [l for l in roles if l['role'] not in lk['drop']]
    if q < .5:
        roles = [l for l in roles if l['role'] != 'secondary']
        notes.append('qualité low : couche secondary retirée')

    # user layer list (presets) replaces / extends the recipe
    if effect.get('layers'):
        roles = [dict(copy.deepcopy(l), role=l.get('role', 'custom')) for l in effect['layers']]

    behavior = effect.get('behavior', {})
    for L in roles:
        L.setdefault('role', 'custom')
        if L.pop('fixed', False):                      # timed layers (e.g. contour streaks): no style / variation
            L['_fixed'] = True
            continue
        if behavior.get('motion') and L['role'] in ('filaments', 'secondary'):
            L['motion'] = norm_motion(behavior['motion']) + (norm_motion(L.get('motion')) if L.get('motion') else [])
        if behavior.get('turbulence') and L['role'] in ('filaments', 'secondary', 'sparks'):
            L['motion'] = (norm_motion(L.get('motion')) or [{'type': 'static'}])
            L['motion'][0]['turbulence'] = float(behavior['turbulence']) * (0 if q < .5 else 1)
        if behavior.get('pulse') is not None and 'pulse' in L:
            L['pulse'] = L['pulse'] * float(behavior['pulse'])
        var = dict(effect.get('variation') or {})
        if not var:
            v = lk['var']
            var = dict(scale=v, lifetime=v * .8, alpha=v * .6, velocity=v)
        L['variation'] = var
        if L.get('tex') in ALPHA_TEX and L['role'] == 'core':
            L['alpha'] = [min(200, a) for a in (L.get('alpha') if isinstance(L.get('alpha'), list) else [200, 200])]
        if 'preset' not in L:
            _scale_layer(L, lk, intensity, q)
        if seg and L['role'] != 'sparks':
            L.setdefault('cp', 0)
            if L.get('shape') in ('segment', 'path'):
                L['cp_end'] = 1

    # performance budget: trim the least important roles first
    budget = int(perf.get('max_particles', 400))
    total = sum(_peak(L) for L in roles if 'preset' not in L)
    for role in reversed(ROLE_PRIORITY):
        if total <= budget:
            break
        for L in roles:
            if L['role'] == role and L.get('rate') and not L.get('_fixed'):
                before = _peak(L)
                L['rate'] = max(1.0, L['rate'] * budget / max(total, 1))
                total -= before - _peak(L)
    if total > budget:
        notes.append(f'budget {budget} dépassé ({total}) même après réduction : alléger la composition')

    # phases / timeline
    tl = effect.get('timeline')
    if not tl and shape['type'] in DEFAULT_TIMELINE and not seg:
        tl = [dict(phase=p, duration=d) for p, d in DEFAULT_TIMELINE[shape['type']]]
    phases = {}
    if tl:
        for p in tl:
            phases[p['phase']] = {k: v for k, v in p.items() if k != 'phase'}
        used = {L.get('phase') for L in roles} - {None}
        missing = used - set(phases)
        if missing:
            raise ValueError(f'phases utilisées mais absentes de la timeline : {sorted(missing)}')
    else:
        for L in roles:
            L.pop('phase', None)

    # the root must be the core (persistent roles need it first)
    roles.sort(key=lambda L: 0 if L['role'] == 'core' else 1)
    layer_list, seen = [], {}
    for L in roles:
        L.pop('_fixed', None)
        base = L.pop('id', None) or L['role']
        seen[base] = seen.get(base, 0) + 1
        L['id'] = base if seen[base] == 1 else f'{base}{seen[base]}'
        if L.get('count') == 0:
            L.pop('count')
        if not L.get('rate'):
            L.pop('rate', None)
        layer_list.append(L)
    system = dict(about=effect.get('title', ''), layers=layer_list)
    if phases:
        system['phases'] = phases
    spec = dict(prefix=effect['id'], title=effect.get('title', effect['id']), materials=effect['id'],
                file=effect['id'] + '.pcf', systems={'main': system},
                draw_distance=float(perf.get('draw_distance', 3000)),
                bbox=max(128, int(g['radius'] * 6), int(seg['length'] * 3) if seg else 0))
    runtime['systems'] = [f"{effect['id']}_main"]
    return spec, runtime, notes
