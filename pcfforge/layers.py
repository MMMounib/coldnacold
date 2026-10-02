"""Layer engine: low-level spec (prefix / systems / layers) -> particle systems.

This is the v2 format, kept as the compiler back end. The V3 composer (compose.py) produces it from an
EffectSpec, and hand-written v2 specs still build as before.
A spec describes callable SYSTEMS (roots), each made of LAYERS. A layer starts from a PRESET and
overrides a few keys. The first layer is the root `<prefix>_<system>`, the others are its children.
"""
import math, copy, yaml
from . import dsl, motions, variation
from .dsl import *

PERF_GUARD = 400   # pic par racine au-delà duquel on AVERTIT (surdessin à vérifier) ; la qualité n'est jamais réduite

# ------------------------------------------------------------------ presets (valeurs par défaut)
# shape : point | sphere | disc | ring | model | path | segment | chain (polyline cp..cp_end, random) |
#         chain_seq (same polyline, in order: a rope that runs along it) | parent
# render: sprite | trail | rope      orient: camera | vertical | ground | normal
P = {
 'flash':      dict(tex='glow', count=1, life=[.15, .15], size=[40, 40], grow=[.4, 1.2, .3], fade_out=.7, alpha=255),
 'flare':      dict(tex='flare', count=1, life=[.2, .2], size=[50, 50], grow=[.3, 1.1, .3], fade_out=.7, spin=[-40, 40]),
 'glow':       dict(tex='glow', count=1, life=[60, 60], size=[20, 20], attach=True, alpha=140, fade_in=.01),
 'pulse':      dict(tex='glow', rate=2, life=[.5, .5], size=[20, 20], grow=[.5, 1.2, .4], fade_in=.2, fade_out=.7, alpha=150, attach=True),
 'shockwave':  dict(tex='ring', count=1, life=[.4, .4], size=[120, 120], grow=[.08, 1, .45], fade_out=.6, orient='ground', offset=[0, 0, 2], alpha=220),
 'decal':      dict(tex='veins', count=1, life=[2, 2], size=[150, 150], grow=[.1, 1, .3, .35], fade_in=.05, fade_out=.4, orient='ground',
                    offset=[0, 0, 1], rot=True, alpha=220),
 'sparks':     dict(tex='spark', render='trail', count=20, shape='sphere', spread=[0, 4], speed=[200, 600], life=[.2, .45], size=[1.5, 2.5],
                    gravity=-500, drag=.05, fade_out=.4, trail=[.03, .06]),
 'debris':     dict(tex='shard', count=12, shape='sphere', spread=[0, 6], speed=[100, 300], up=[80, 200], gravity=-600, drag=.03,
                    spin=[200, 600], life=[.6, 1.1], size=[2, 4], fade_out=.3, rot=True),
 'petals':     dict(tex='petal', count=14, shape='sphere', spread=[0, 6], speed=[60, 200], up=[40, 160], gravity=-160, drag=.08, noise=150,
                    spin=[150, 450], life=[1.0, 1.6], size=[3, 5], fade_in=.05, fade_out=.35, rot=True),
 'leaves':     dict(tex='leaf', count=12, shape='sphere', spread=[0, 6], speed=[60, 200], up=[40, 160], gravity=-160, drag=.08, noise=150,
                    spin=[150, 450], life=[1.0, 1.6], size=[3, 5], fade_in=.05, fade_out=.35, rot=True),
 'smoke':      dict(tex='smoke', count=6, shape='sphere', spread=[0, 10], speed=[20, 60], up=[10, 30], size=[15, 25], grow=[.6, 1.6, .5],
                    life=[1.0, 1.6], fade_in=.15, fade_out=.6, alpha=120, drag=.1, spin=[-20, 20], rot=True, color=[140, 135, 130]),
 'smoke_trail': dict(tex='smoke', rate=20, shape='sphere', spread=[0, 3], speed=[5, 15], size=[6, 10], grow=[.6, 2, .5], life=[.6, 1.0],
                    fade_in=.1, fade_out=.6, alpha=90, drag=.1, rot=True, color=[140, 135, 130]),
 'embers':     dict(tex='star', count=20, shape='sphere', spread=[0, 10], speed=[20, 80], up=[20, 70], noise=40, drag=.05,
                    life=[.8, 1.6], size=[1.2, 2.2], fade_in=.1, fade_out=.5),
 'motes':      dict(tex='star', rate=15, shape='model', up=[20, 45], life=[.5, .8], size=[1.4, 2.2], attach=True, drag=.05,
                    fade_in=.2, fade_out=.5),
 'orbit':      dict(tex='star', count=8, shape='ring', radius=20, ring_even=True, orbit=900, attach=True, life=[60, 60], size=[2, 3],
                    offset=[0, 0, 30], fade_in=.005),
 'converge':   dict(tex='star', rate=40, shape='ring', radius=80, thickness=60, pull=1800, twist=300, life=[.5, .7], size=[1.6, 2.4],
                    drag=.06, fade_in=.2, fade_out=.3, offset=[0, 0, 0]),
 'column':     dict(tex='glow', rate=20, height=[0, 300], life=[.4, .5], size=[30, 50], alpha=60, fade_in=.3, fade_out=.5),
 'beam':       dict(tex='strand', render='rope', count=16, shape='path', bulge=0, life=[60, 60], size=[2, 2], alpha=220, scroll=30),
 'ribbon':     dict(tex='strand', render='rope', rate=80, life=[.22, .26], size=[2.5, 2.5], shrink=.1, noise=120, drag=.15, alpha=200),
 'core':       dict(tex='glow_hard', count=1, life=[60, 60], size=[6, 6], attach=True, spin=[300, 600]),
 'rain':       dict(tex='spark', render='trail', rate=100, shape='disc', spread=[0, 400], height=[560, 620], vel=[[-40, -40, -1100], [40, 40, -980]],
                    life=[.55, .6], trail=[.06, .09], size=[1.8, 2.6], fade_in=.05, alpha=230),
 'scatter':    dict(tex='flower', count=20, shape='disc', spread=[20, 300], seq=6, anim_fps=34, grow=[0, 1, .3, .03], life=[3, 3.5],
                    offset=[0, 0, 20], size=[14, 20], fade_out=.15),
 'sprouts':    dict(tex='stem', rate=40, duration=1.5, shape='disc', spread=[20, 300], orient='vertical', grow=[0, 1, .35, .1],
                    life=[4, 4.5], size=[20, 30], fade_out=.12, seq=[0, 1]),
 'fire':       dict(tex='flame', rate=24, shape='disc', spread=[0, 8], up=[40, 80], life=[.6, .9], size=[10, 16], grow=[1, .4, .5],
                    fade_in=.1, fade_out=.4, alpha=230, drag=.05, noise=60),
 'burst_anim': dict(tex='explosion', count=1, life=[1.0, 1.0], size=[60, 60], alpha=255, fade_out=.2, rot=True),
 'drops':      dict(tex='droplet', count=12, shape='sphere', spread=[0, 4], speed=[80, 220], up=[60, 160], gravity=-700, life=[.5, .8],
                    size=[1.5, 3], fade_out=.3),
 'energy_core': dict(tex='glow_hard', count=1, life=[60, 60], size=[5, 7], attach=True, alpha=255),
 'energy_halo': dict(tex='glow', count=1, life=[60, 60], size=[18, 24], attach=True, alpha=110, fade_in=.02),
 'energy_sparks': dict(tex='spark', render='trail', count=18, shape='sphere', spread=[0, 6], speed=[120, 420],
                    life=[.18, .42], size=[1.2, 2.4], fade_out=.35, trail=[.025, .055]),
 'energy_filaments': dict(tex='strand', render='rope', rate=45, life=[.28, .42], size=[1.5, 2.5],
                    shrink=.15, noise=90, drag=.12, alpha=170),
 'energy_ring': dict(tex='ring_soft', count=1, life=[.35, .5], size=[70, 90], grow=[.08, 1.15, .45],
                    fade_out=.65, orient='camera', alpha=150),
 'impact_spikes': dict(tex='spark', render='trail', count=14, shape='sphere', spread=[0, 5], speed=[280, 650],
                    life=[.16, .3], size=[1.5, 3], gravity=-120, fade_out=.45, trail=[.035, .07]),
}
ORIENT = {'camera': 0, 'vertical': 1, 'ground': 2, 'normal': 3}
LAYER_KEYS = set().union(*[set(v) for v in P.values()]) | {
    'preset', 'id', 'delay', 'color', 'color_end', 'color_end_at', 'cp', 'duration', 'max', 'render', 'orient', 'extra',
    'loop', 'about', 'shrink_end', 'vel', 'radius', 'thickness', 'ring_even', 'seq', 'anim_fps', 'fit', 'height', 'bias',
    'phase', 'motion', 'scale', 'variation', 'seed', 'cp_end', 'path_count', 'hold', 'pulse', 'role', 'draw_distance', 'lock_cp', 'anim_rate', 'pulse_alpha', 'release', 'twist_axis', 'ring_count', 'ring_yaw', 'fade_in_s', 'hide_in_first_person', 'turn', 'turn_from',
    'path_live', 'path_travel', 'fade_near', 'spin_one_way', 'fade_out_s'}

def _pair(v, default=None):
    if v is None: return default
    return list(v) if isinstance(v, (list, tuple)) else [v, v]

def _color(v, pal):
    if v is None: return None
    if isinstance(v, str): return tuple(pal[v])
    if isinstance(v, (list, tuple)) and len(v) == 2 and not isinstance(v[0], (int, float)):
        return (_color(v[0], pal), _color(v[1], pal))
    return tuple(v)

def layer_ops(L, pal, textures, emission_delay=0.0, phase_duration=None):
    """Construit la liste d'opérateurs d'une couche à partir de ses paramètres."""
    L = variation.apply(copy.deepcopy(L))
    tex = L['tex']; info = textures[tex]
    ops = []
    cp = L.get('cp', 0)
    if 'count' in L and not L.get('rate'): ops.append(E_inst(L['count'], emission_delay))
    else:
        dur = phase_duration if phase_duration is not None and 'duration' not in L else L.get('duration', 0)
        if L.get('_emit_noise'):
            k = L['_emit_noise']
            ops.append(op('emitters', 'emit noise', emission_start_time=float(emission_delay), emission_duration=float(dur or 0),
                          **{'emission minimum': float(L['rate'] * (1 - k)), 'emission maximum': float(L['rate'] * (1 + k)),
                             'time noise coordinate scale': 2.0}))
        else: ops.append(E_cont(L['rate'], dur, emission_delay))
    life = _pair(L.get('life'), [1, 1])
    ops.append(I_life(*life))
    size = _pair(L.get('size'), [5, 5])
    if 'scale' in L:
        sc = L['scale']; size = [float(size[0]) * float(sc[0]), float(size[1]) * float(sc[1])] if isinstance(sc, (list, tuple)) else [float(size[0]) * float(sc), float(size[1]) * float(sc)]
    ops.append(I_rad(*size))
    col = _color(L.get('color'), pal)
    if col is not None:
        if isinstance(col[0], tuple): ops.append(I_col(col[0], col[1]))
        else: ops.append(I_col(col))
    if 'alpha' in L:
        ops.append(I_alpha(*_pair(L['alpha'])))
    # séquence : variantes aléatoires si la texture en a plusieurs d'une image
    seqs = info['seqs']
    if 'seq' in L: ops.append(I_seq(*_pair(L['seq'])))
    elif len(seqs) > 1: ops.append(I_seq(0, len(seqs) - 1))          # variants or several animations
    if 'turn' in L:                       # fixed rotation (deg/s) from a fixed start angle: symmetric pieces loop seamlessly
        ops.append(I_rot(0, 0, float(L.get('turn_from', 0)))); ops.append(I_rotspd(L['turn'], L['turn'], flip=False))
    elif L.get('rot') or 'spin' in L: ops.append(I_rot())
    if 'spin' in L and 'turn' not in L: ops.append(I_rotspd(*_pair(L['spin']), flip=not L.get('spin_one_way')))
    # position
    shape = L.get('shape', 'point'); spread = _pair(L.get('spread'), [0, 0]); speed = _pair(L.get('speed'), [0, 0])
    if shape == 'sphere': ops.append(I_sphere(spread[0], spread[1], speed[0], speed[1], cp=cp))
    elif shape == 'disc': ops.append(I_sphere(spread[0], spread[1], speed[0], speed[1], (1, 1, 0), cp=cp))
    elif shape == 'ring': ops.append(I_ring(L.get('radius', 20), L.get('thickness', 0), speed[0], speed[1], L.get('ring_even', False),
                                            L.get('ring_count', L.get('count', -1)) if L.get('ring_even') else -1, cp=cp,
                                            yaw=L.get('ring_yaw', 0.0)))
    elif shape == 'dome': ops.append(I_sphere(L.get('radius', 40), L.get('radius', 40), speed[0], speed[1], cp=cp, upper=True))
    elif shape == 'model': ops.append(I_model(cp))
    elif shape == 'path':
        n = L.get('count', L.get('path_count', 16)); ops.append(I_path_seq(n, cp, L.get('cp_end', cp + 1), L.get('bulge', 0)))
    elif shape == 'segment': ops.append(I_path_rand(cp, L.get('cp_end', cp + 1), spread[1]))
    elif shape == 'chain': ops.append(I_path_rand(cp, L['cp_end'], spread[1], chain=True))
    elif shape == 'chain_seq': ops.append(I_path_seq(L.get('path_count', 48), cp, L['cp_end'], 0, chain=True, jitter=spread[1]))
    elif shape == 'parent': ops.append(I_parent())
    elif shape == 'point':
        # always an explicit position: without one, Source keeps the dead particle's position in that slot and
        # `offset` adds to it again (seen in game 01/10: shield rims stacked higher at every emission)
        ops.append(I_sphere(0, 0, cp=cp))
    off = L.get('offset'); h = L.get('height')
    if h is not None:
        o = list(off or [0, 0, 0]); ops.append(I_offset((o[0], o[1], o[2] + h[0]), (o[0], o[1], o[2] + h[1]), cp=cp))
    elif off is not None: ops.append(I_offset(tuple(off), tuple(off), cp=cp))
    vel = L.get('vel'); up = L.get('up')
    if vel is not None: ops.append(I_vel(tuple(vel[0]), tuple(vel[1])))
    elif up is not None: ops.append(I_vel((0, 0, up[0]), (0, 0, up[1])))
    if L.get('render') == 'trail': ops.append(I_trail(*_pair(L.get('trail'), [.04, .06])))
    # forces
    if 'twist' in L: ops.append(F_twist(L['twist']))
    if 'twist_axis' in L: ops.append(F_twist(L['twist_axis'][0], tuple(L['twist_axis'][1]), True))
    if 'orbit' in L: ops.append(F_twist(L['orbit']))
    if 'pull' in L: ops.append(F_pull(L['pull'], L.get('pull_cp', cp)))
    if 'noise' in L: n = L['noise']; ops.append(F_rand((-n, -n, -n * .5), (n, n, n * .5)))
    if 'orbit' in L:
        r = L.get('radius', 20); ops.append(C_dist(r * .85, r * 1.15, cp))
    mops, m_moving = motions.ops(L, cp)
    ops += mops
    if 'path_travel' in L:                # [travel s, max dist at start, middle, end, random bulge]: cp -> cp_end
        pt = list(L['path_travel']) + [0] * (5 - len(L['path_travel']))
        ops.append(C_path(pt[0], (pt[1], pt[2], pt[3]), cp, L.get('cp_end', 0), pt[4]))
    # opérateurs
    moving = shape != 'path' and (speed[1] or vel is not None or up is not None or 'gravity' in L or 'noise' in L or 'twist' in L
                                  or 'pull' in L or 'orbit' in L or L.get('render') == 'rope' or m_moving
                                  or 'path_travel' in L)
    if L.get('attach'): ops.append(O_lock(L.get('lock_cp', cp), L.get('attach') == 'rotation', L.get('release')))
    if shape == 'path': ops.append(O_path(L.get('count', L.get('path_count', 16)), cp, L.get('cp_end', cp + 1),
                                          L.get('bulge', 0), L.get('path_live', False)))
    if moving: ops.append(O_move((0, 0, L.get('gravity', 0)), L.get('drag', 0)))
    if 'spin' in L or 'turn' in L: ops.append(O_rotbasic())
    g = L.get('grow')
    if g:   # [début, fin, biais, fin_fenêtre]
        ops.append(O_rscale(g[0], g[1], 0, g[3] if len(g) > 3 else 1, g[2] if len(g) > 2 else .5, len(g) > 3))
    if 'shrink' in L: ops.append(O_rscale(1, L['shrink'], 0, 1, .5))
    if 'shrink_end' in L: ops.append(O_rscale(1, L['shrink_end'], .85, 1, .5))
    ce = _color(L.get('color_end'), pal)
    if ce is not None:
        a0 = L.get('color_end_at', [.5, 1]); ops.append(O_cfade(ce, a0[0], a0[1]))
    if 'pulse' in L: ops.append(O_osc_scalar(3, L['pulse'], (.8, 1.4)))
    if 'pulse_alpha' in L:                                          # [rate, frequency Hz], on the age in seconds
        pa = L['pulse_alpha']; f = (pa[1], pa[2] if len(pa) > 2 else pa[1])     # [rate, freq] or [rate, fmin, fmax]
        ops.append(O_osc_scalar(7, pa[0], f, 0, 1, proportional=False))
    if 'hold' in L: ops.append(O_hold_cut(L['hold']))
    if 'fade_in' in L: ops.append(O_fadein(L['fade_in']))
    if 'fade_in_s' in L: ops.append(O_fadein(L['fade_in_s'], prop=False))
    if 'fade_out' in L: ops.append(O_fadeout(L['fade_out']))
    if 'fade_out_s' in L: ops.append(O_fadeout(L['fade_out_s'], prop=False))
    if 'fade_near' in L:                  # [cp, d0, d1]: invisible at d0 or closer, full alpha from d1 (swallowed)
        fcp, d0, d1 = L['fade_near']; ops.append(O_remap_dist(d0, d1, 7, 0.0, 1.0, int(fcp)))
    ops.append(O_decay())
    for e in L.get('extra', []):                                   # raw operators, restricted to the DSL helpers
        fn = getattr(dsl, e[0], None) if e and e[0][:2] in ('I_', 'O_', 'F_', 'C_', 'E_') else None
        if fn is None: raise ValueError(f'extra : helper inconnu {e[0] if e else e!r}')
        ops.append(fn(*e[1:]))
    # rendu
    r = L.get('render', 'sprite')
    if r == 'trail': ops.append(R_trail(2, L.get('trail_max', 120)))
    elif r == 'rope': ops.append(R_rope(L.get('texel', 20), L.get('scroll', 0), 3))
    else:
        orient = ORIENT[L.get('orient', 'camera')]
        s = seqs[int(_pair(L.get('seq'), [0])[0]) % len(seqs)] if seqs else [0]
        if 'anim_fps' in L: ops.append(R_sprite(orient, False, L['anim_fps'], True))
        elif len(s) > 1:
            # measured in GMod: rate r (not FPS) = r full cycles per second, and fit-to-lifetime has no effect.
            # One cycle over the mean life by default; `anim_rate` overrides (loops: flames).
            ops.append(R_sprite(orient, False, float(L.get('anim_rate', 2.0 / (life[0] + life[1])))))
        else: ops.append(R_sprite(orient, False))
    return ops

def estimate_peak(L):
    life = _pair(L.get('life'), [1, 1])[1]
    if 'count' in L and not L.get('rate'): return L['count']
    dur = L.get('duration', L.get('_phase_duration', 0)) or 1e9
    return int(math.ceil(L['rate'] * min(life, dur))) + 1

def load(path):
    return yaml.safe_load(open(path, encoding='utf-8'))

PHASES = ('charge', 'release', 'travel', 'impact', 'aftermath', 'persistent')
PHASE_OVERRIDES = ('rate', 'count', 'size', 'life', 'alpha', 'speed')   # multipliers a phase may apply


def timeline(phases, where=''):
    """dict {name: {duration, ...}} or list [{phase, duration, ...}] -> ordered {name: {start, duration, over}}."""
    items = phases.items() if isinstance(phases, dict) else [(p.get('phase'), p) for p in phases or []]
    out, clock = {}, 0.0
    for name, pdef in items:
        if not name:
            raise ValueError(f'{where}phase sans nom')
        if not isinstance(pdef, dict) or 'duration' not in pdef:
            raise ValueError(f'{where}phase {name} doit avoir duration')
        d = float(pdef['duration'])
        if d < 0:
            raise ValueError(f'{where}durée de phase négative : {name}')
        over = pdef.get('scale', {})
        bad = set(over) - set(PHASE_OVERRIDES)
        if bad:
            raise ValueError(f'{where}phase {name} : scale inconnu {bad} (connus : {PHASE_OVERRIDES})')
        out[name] = dict(start=clock, duration=d, over=over, color=pdef.get('color'))
        clock += d
    return out


def _apply_phase(L, ph):
    for k, f in ph['over'].items():
        if k in L and not isinstance(L[k], bool):
            v = L[k]
            L[k] = [x * f for x in v] if isinstance(v, (list, tuple)) else v * f
    if 'count' in L and not isinstance(L['count'], int):
        L['count'] = max(1, int(round(L['count'])))
    if ph['color'] is not None:
        L['color'] = ph['color']


def root_name(pre, sname, exact=False):
    """A system keyed with the effect's own prefix is called exactly that (e.g. `bc_shield`), else prefix_name.
    exact (spec `exact_names: true`): the key is the full name (a pack mixing several families, e.g. sarada_* and
    ohirume_* in one PCF)."""
    if exact:
        return sname
    return pre if sname == pre else f'{pre}_{sname}'


def build(spec, textures, registry=None):
    """Registers the spec's systems. Returns (registry, roots, infos, peaks)."""
    reg = registry or dsl.Registry()
    pre = spec['prefix']; pal = spec.get('palette', {}); matdir = spec.get('materials', pre)
    roots, infos, peaks = [], {}, {}
    for sname, sdef in spec['systems'].items():
        layers = sdef['layers'] if isinstance(sdef, dict) else sdef
        root = root_name(pre, sname, spec.get('exact_names', False)); roots.append(root)
        phases = timeline(sdef.get('phases', {}) if isinstance(sdef, dict) else {}, f'{sname}: ')
        names = []
        for i, raw in enumerate(layers):
            unknown = set(raw) - LAYER_KEYS - {'pull_cp', 'trail_max', 'texel'}
            if unknown: raise ValueError(f'{sname}[{i}] clés inconnues : {unknown}')
            if raw.get('preset') and raw['preset'] not in P and 'tex' not in raw:
                raise ValueError(f'{sname}[{i}] preset inconnu : {raw["preset"]}')
            L = copy.deepcopy(P.get(raw.get('preset'), {})); L.update(raw)
            if 'rate' in raw and 'count' in L and 'count' not in raw: L.pop('count')
            if 'count' in raw and 'rate' in L and 'rate' not in raw: L.pop('rate')
            if L.get('phase'):
                if L['phase'] not in phases: raise ValueError(f'{sname}[{i}]: phase inconnue {L["phase"]}')
                ph = phases[L['phase']]; _apply_phase(L, ph)
                L['_phase_delay'] = ph['start']; L['_phase_duration'] = None if L['phase'] == 'persistent' else ph['duration']
            else: L['_phase_delay'] = 0.0; L['_phase_duration'] = None
            nm = root if i == 0 else f'{root}_{raw.get("id", raw.get("preset", "l") + str(i))}'
            names.append((nm, L))
        for i, (nm, L) in enumerate(names):
            effective_delay = float(L.get('delay', 0)) + float(L.get('_phase_delay', 0))
            ops = layer_ops(L, pal, textures, emission_delay=effective_delay if i == 0 else 0.0, phase_duration=L.get('_phase_duration'))
            peak = estimate_peak(L); peaks[nm] = peak
            maxp = L.get('max', int(math.ceil(max(peak, 1) * 1.1 / 4) * 4))
            kids = [(n2, float(L2.get('delay', 0)) + float(L2.get('_phase_delay', 0))) for n2, L2 in names[1:]] if i == 0 else []
            reg.add(Sys(nm, f'{matdir}/{L["tex"]}', maxp, ops, children=kids, bbox=spec.get('bbox', 600),
                        draw_distance=spec.get('draw_distance', 4000.0),
                        hidden=bool(spec.get('hide_children')) and i > 0,
                        camera_cp=L.get('cp', 0) if L.get('hide_in_first_person') else -1))
        infos[root] = dict(about=sdef.get('about', '') if isinstance(sdef, dict) else '', layers=len(names),
                           peak=sum(peaks[n] for n, _ in names))
    return reg, roots, infos, peaks

def used_textures(spec):
    out = set()
    for sdef in spec['systems'].values():
        for raw in (sdef['layers'] if isinstance(sdef, dict) else sdef):
            out.add(raw.get('tex') or P[raw['preset']]['tex'])
    return out
