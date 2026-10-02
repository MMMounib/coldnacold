"""DSL bas niveau des systèmes de particules (écriture PCF).
Les noms de paramètres sont EXACTEMENT les noms d'attributs PCF relevés dans le pack (schema.json),
garantissant des PCF identiques à ceux produits par le Particle Editor.
"""
import json, os, io
from srctools.dmx import Element, Attribute, ValueType, Color
from srctools.math import Vec

SCHEMA = json.load(open(os.path.join(os.path.dirname(__file__), 'schema.json')))['ops']
DEFAULTS = json.load(open(os.path.join(os.path.dirname(__file__), 'defaults.json')))
# attribute names are matched without case (the corpus spells some of them differently)
_CANON = {fn: {k.lower(): k for k in attrs if k != '__lists__'} for fn, attrs in SCHEMA.items()}


class Registry:
    """Systems of one build (no global state between builds)."""
    def __init__(self):
        self.systems = {}

    def add(self, sys):
        if sys.name in self.systems:
            raise ValueError(f'système en double : {sys.name}')
        self.systems[sys.name] = sys
        return sys


class Sys:
    def __init__(self, name, mat, maxp, ops, children=(), radius=5, color=(255, 255, 255, 255),
                 sort=True, bbox=64, draw_distance=4000.0, hidden=False, camera_cp=-1):
        self.name, self.mat, self.maxp, self.ops = name, mat, maxp, list(ops)
        self.hidden = hidden                 # child only: not listed / not callable by name (preventNameBasedLookup)
        self.children = list(children)       # [(nom_enfant, délai)]
        self.radius, self.color, self.sort, self.bbox = radius, color, sort, bbox
        self.draw_distance = draw_distance
        self.camera_cp = camera_cp           # not drawn when this CP's entity is the camera (first person)

def op(kind, fn, **p):
    return (kind, fn, {k.replace('__', ' ').replace('_S_', '/'): v for k, v in p.items()})

# ------------------------------------------------------------------ émetteurs
def E_inst(n, t=0.0):
    return op('emitters', 'emit_instantaneously', num_to_emit=int(n), emission_start_time=float(t))
def E_cont(rate, dur=0.0, t=0.0):
    return op('emitters', 'emit_continuously', emission_rate=float(rate), emission_duration=float(dur),
              emission_start_time=float(t))
# ------------------------------------------------------------------ initialiseurs
def I_life(a, b): return op('initializers', 'Lifetime Random', lifetime_min=a, lifetime_max=b)
def I_rad(a, b, exp=1.0): return op('initializers', 'Radius Random', radius_min=a, radius_max=b, radius_random_exponent=exp)
def I_col(c1, c2=None):
    c2 = c2 or c1
    return op('initializers', 'Color Random', color1=tuple(c1) + (255,) * (4 - len(c1)), color2=tuple(c2) + (255,) * (4 - len(c2)))
def I_alpha(a, b=None): return op('initializers', 'Alpha Random', alpha_min=int(a), alpha_max=int(b if b is not None else a))
def I_rot(a=0, b=360, init=0): return op('initializers', 'Rotation Random', rotation_initial=float(init),
                                         rotation_offset_min=float(a), rotation_offset_max=float(b), randomly_flip_direction=False)
def I_rotspd(a, b, flip=True): return op('initializers', 'Rotation Speed Random', rotation_speed_constant=0.0,
                                         rotation_speed_random_min=float(a), rotation_speed_random_max=float(b),
                                         randomly_flip_direction=flip)
def I_seq(a, b=None): return op('initializers', 'Sequence Random', sequence_min=int(a), sequence_max=int(b if b is not None else a))
def I_sphere(dmin, dmax, smin=0, smax=0, bias=(1, 1, 1), lmin=(0, 0, 0), lmax=(0, 0, 0), cp=0, upper=False):
    """upper=True: only the upper half (|z|), e.g. a dome resting on the ground."""
    return op('initializers', 'Position Within Sphere Random', distance_min=float(dmin), distance_max=float(dmax),
              distance_bias=tuple(bias), distance_bias_absolute_value=(0.0, 0.0, 1.0 if upper else 0.0),
              speed_min=float(smin), speed_max=float(smax),
              speed_in_local_coordinate_system_min=tuple(lmin), speed_in_local_coordinate_system_max=tuple(lmax),
              control_point_number=cp)
def I_ring(r, thick=0, smin=0, smax=0, even=False, count=-1, cp=0, yaw=0.0):
    """Ring around CP (XY plane). even: `count` evenly spaced slots; yaw (degrees) rotates the ring (stagger rows)."""
    return op('initializers', 'Position Along Ring', **{'initial radius': float(r), 'thickness': float(thick),
              'min initial speed': float(smin), 'max initial speed': float(smax), 'even distribution': even,
              'even distribution count': float(count), 'control point number': cp, 'pitch': 0.0, 'yaw': float(yaw),
              'roll': 0.0, 'xy velocity only': True})
def I_offset(mn, mx, cp=0, local=False):
    return op('initializers', 'Position Modify Offset Random', **{'offset min': tuple(mn), 'offset max': tuple(mx),
              'control_point_number': cp, 'offset in local space 0/1': local})
def I_vel(lmin=(0, 0, 0), lmax=(0, 0, 0), smin=0, smax=0, cp=0):
    return op('initializers', 'Velocity Random', speed_in_local_coordinate_system_min=tuple(lmin),
              speed_in_local_coordinate_system_max=tuple(lmax), random_speed_min=float(smin),
              random_speed_max=float(smax), control_point_number=cp)
def I_trail(a, b): return op('initializers', 'Trail Length Random', length_min=a, length_max=b)
def I_path_seq(n, start=0, end=1, bulge=0.0, chain=False, jitter=0.0):
    """n particles mapped in order from CP start to CP end (loops). chain=True: along the polyline start..end."""
    return op('initializers', 'Position Along Path Sequential', **{'particles to map from start to end': float(n),
              'start control point number': start, 'end control point number': end, 'bulge': float(bulge),
              'mid point position': .5, 'maximum distance': float(jitter), 'restart behavior (0 = bounce, 1 = loop )': True,
              'Use sequential CP pairs between start and end point': bool(chain)})
def I_model(cp=0, scale=1.0):
    return op('initializers', 'Position on Model Random', control_point_number=cp, **{'model hitbox scale': float(scale),
              'hitbox set': 'effects', 'force to be inside model': 0, 'direction bias': (0, 0, 0), 'desired hitbox': -1})
def I_parent(vel=0.0, rnd=True):
    return op('initializers', 'Position From Parent Particles', **{'inherited velocity scale': float(vel),
              'random parent particle distribution': rnd, 'particle increment amount': 1})
# ------------------------------------------------------------------ opérateurs
def O_move(g=(0, 0, 0), drag=0.0): return op('operators', 'Movement Basic', gravity=tuple(g), drag=float(drag))
def O_decay(): return op('operators', 'Lifespan Decay')
def O_fadein(a, b=None, prop=True):
    """prop=False: fade-in time in seconds (needed for persistent particles, whose lifetime is huge)."""
    return op('operators', 'Alpha Fade In Random', **{'fade in time min': a, 'fade in time max': b if b else a,
              'proportional 0/1': prop, 'fade in time exponent': 1.0})
def O_fadeout(a, b=None, bias=.5, ease=True, prop=True):
    """prop=False: fade-out time in seconds before death (a staggered prime hands over exactly to its cycle)."""
    return op('operators', 'Alpha Fade Out Random', **{'fade out time min': a, 'fade out time max': b if b else a,
              'proportional 0/1': prop, 'ease in and out': ease, 'fade bias': bias, 'fade out time exponent': 1.0})
def O_rscale(s0, s1, t0=0.0, t1=1.0, bias=.5, ease=False):
    return op('operators', 'Radius Scale', radius_start_scale=float(s0), radius_end_scale=float(s1),
              start_time=float(t0), end_time=float(t1), scale_bias=float(bias), ease_in_and_out=ease)
def O_cfade(c, t0, t1, ease=True):
    return op('operators', 'Color Fade', color_fade=tuple(c) + (255,) * (4 - len(c)), fade_start_time=float(t0),
              fade_end_time=float(t1), ease_in_and_out=ease)
def O_rotbasic(): return op('operators', 'Rotation Basic')
def I_remap_count(in_min, in_max, out_min, out_max, field=1):
    """Sets a field from the particle's index in the system (field 1 = lifetime): e.g. the i-th particle of a burst
    lives i/n of a cycle. Not in the corpus, but part of the GMod particle editor (defaults.json)."""
    return op('initializers', 'Remap Particle Count to Scalar', **{'input minimum': int(in_min),
              'input maximum': int(in_max), 'output minimum': float(out_min), 'output maximum': float(out_max),
              'output field': int(field)})
def O_lock(cp=0, rotation=False, release=None):
    """Keeps particles attached to a CP. release (0..1 of life): the lock fades out around that point, so particles
    stick first then peel away and trail behind a moving weapon (as in reference auras, e.g. fsc_aura2: 0.7)."""
    a, b = (1.0, 1.0) if release is None else (max(0.0, release - .1), min(1.0, release + .1))
    return op('operators', 'Movement Lock to Control Point', control_point_number=cp, start_fadeout_min=a,
              start_fadeout_max=a, end_fadeout_min=b, end_fadeout_max=b, **{'lock rotation': bool(rotation)})
def I_path_rand(start=0, end=1, jitter=0.0, bulge=0.0, chain=False):
    """Random point on the segment CP start -> CP end (e.g. along a blade).
    chain=True: random point on the polyline start, start+1, ..., end (e.g. a silhouette outline)."""
    return op('initializers', 'Position Along Path Random', **{'start control point number': start,
              'end control point number': end, 'maximum distance': float(jitter), 'bulge': float(bulge),
              'mid point position': .5, 'bulge control 0=random 1=orientation of start pnt 2=orientation of end point': 0,
              'randomly select sequential CP pairs between start and end points': bool(chain)})
def O_path(n, start=0, end=1, bulge=0.0, live=False):
    """live=True: spread the particles alive right now from start to end (use existing particle count), so a rope
    that is re-emitted continuously stays one clean line between the two CPs."""
    return op('operators', 'Movement Maintain Position Along Path', **{'particles to map from start to end': float(n),
              'start control point number': start, 'end control point number': end, 'bulge': float(bulge),
              'mid point position': .5, 'cohesion strength': 1.0, 'maximum distance': 0.0,
              'restart behavior (0 = bounce, 1 = loop )': True, 'use existing particle count': bool(live)})
def C_path(travel, dmax=(8.0, 8.0, 8.0), start=1, end=0, bulge=0.0, dmin=0.0):
    """Particles travel from CP start to CP end in `travel` seconds, kept within dmax (at start, middle, end) of the
    moving point on the path; it follows the CPs every frame (a link that follows its target). bulge: random
    curve per particle."""
    return op('constraints', 'Constrain distance to path between two control points', **{
        'minimum distance': float(dmin), 'maximum distance': float(dmax[0]), 'maximum distance middle': float(dmax[1]),
        'maximum distance end': float(dmax[2]), 'travel time': float(travel), 'random bulge': float(bulge),
        'start control point number': int(start), 'end control point number': int(end),
        'bulge control 0=random 1=orientation of start pnt 2=orientation of end point': 0, 'mid point position': .5})
def O_remap_dist(dmin, dmax, field=7, omin=0.0, omax=1.0, cp=0):
    """Scales a field by the distance to a CP (7 = alpha, 3 = radius): omin at dmin or closer, omax at dmax or
    farther, e.g. matter fades as it is swallowed by a sphere. Multiplies the current value (set every frame by the
    fade / radius operators placed before it)."""
    return op('operators', 'Remap Distance to Control Point to Scalar', **{'distance minimum': float(dmin),
              'distance maximum': float(dmax), 'output field': int(field), 'output minimum': float(omin),
              'output maximum': float(omax), 'control point': int(cp), 'output is scalar of current value': True})
def F_pull(force, cp=0, falloff=0.0):
    return op('forces', 'Pull towards control point', **{'amount of force': float(force), 'falloff power': float(falloff),
              'control point number': cp})
def F_twist(force, axis=(0, 0, 1), local=False):
    """Swirl around an axis through CP0 (local=True: axis in CP0's frame, e.g. along a blade)."""
    return op('forces', 'twist around axis', **{'amount of force': float(force), 'twist axis': tuple(axis),
              'object local space axis 0/1': bool(local)})
def F_rand(mn, mx): return op('forces', 'random force', **{'min force': tuple(mn), 'max force': tuple(mx)})
def C_dist(mn, mx, cp=0):
    return op('constraints', 'Constrain distance to control point', **{'minimum distance': float(mn),
              'maximum distance': float(mx), 'control point number': cp, 'offset of center': (0, 0, 0),
              'global center point': False})
def O_axis_spin(rate, cp=0, axis=(0, 0, 1)):
    """Rotates particles around an axis through a (possibly moving) control point."""
    return op('operators', 'Movement Rotate Particle Around Axis', **{'Rotation Axis': tuple(axis),
              'Rotation Rate': float(rate), 'Control Point': cp, 'Use Local Space': False})
def O_osc_scalar(field, rate, freq=(.5, 1.0), t0=0.0, t1=1.0, proportional=True):
    """Oscillates a particle field (3 = radius, 7 = alpha) over its life (proportional) or its age in seconds."""
    r = _pair2(rate)
    return op('operators', 'Oscillate Scalar', **{'oscillation field': int(field), 'oscillation rate min': float(r[0]),
              'oscillation rate max': float(r[1]), 'oscillation frequency min': float(freq[0]),
              'oscillation frequency max': float(freq[1]), 'proportional 0/1': bool(proportional), 'start time min': float(t0),
              'start time max': float(t0), 'end time min': float(t1), 'end time max': float(t1),
              'start/end proportional': True, 'oscillation multiplier': 2.0, 'oscillation start phase': 0.5})
def O_osc_position(amp, freq=(.6, 1.2)):
    """Sways particle positions (oscillation field 0) — a soft wobble, not noise."""
    a = tuple(amp)
    return op('operators', 'Oscillate Vector', **{'oscillation field': 0, 'oscillation rate min': tuple(-x for x in a),
              'oscillation rate max': a, 'oscillation frequency min': (freq[0],) * 3,
              'oscillation frequency max': (freq[1],) * 3, 'proportional 0/1': True, 'start time min': 0.0,
              'start time max': 0.0, 'end time min': 1.0, 'end time max': 1.0, 'start/end proportional': True,
              'oscillation multiplier': 2.0, 'oscillation start phase': 0.5})
def I_vnoise(amount, up=(0.0, 0.0), time_scale=1.0, space_scale=0.01, cp=0):
    """Smooth coherent velocity (world noise): particles born close together move alike."""
    return op('initializers', 'Velocity Noise', **{'Control Point Number': cp, 'Time Noise Coordinate Scale': float(time_scale),
              'Spatial Noise Coordinate Scale': float(space_scale), 'Time Coordinate Offset': 0.0,
              'Spatial Coordinate Offset': (0, 0, 0), 'Absolute Value': (0, 0, 0), 'Invert Abs Value': (0, 0, 0),
              'output minimum': (-amount, -amount, up[0]), 'output maximum': (amount, amount, up[1]),
              'Apply Velocity in Local Space (0/1)': False})
def O_hold_cut(cut=.75, fade_in=0.0):
    """Stays fully visible, then fades out quickly: the anime/cartoon timing."""
    return op('operators', 'Alpha Fade and Decay', start_alpha=1.0, end_alpha=0.0, start_fade_in_time=0.0,
              end_fade_in_time=float(fade_in), start_fade_out_time=float(cut), end_fade_out_time=1.0)
def O_spin_roll(deg, min_deg=0):
    return op('operators', 'Rotation Spin Roll', spin_rate_degrees=int(deg), spin_rate_min=int(min_deg), spin_stop_time=0.0)
def _pair2(v): return list(v) if isinstance(v, (list, tuple)) else [v, v]

# ------------------------------------------------------------------ rendus
def R_sprite(orient=0, fit=True, rate=1.0, fps=False):
    return op('renderers', 'render_animated_sprites', orientation_type=orient, animation_fit_lifetime=fit,
              **{'animation rate': float(rate), 'use animation rate as fps': fps})
def R_trail(minl=0, maxl=512, fadein=.1):
    return op('renderers', 'render_sprite_trail', **{'min length': float(minl), 'max length': float(maxl),
              'length fade in time': float(fadein), 'animation rate': .1, 'constrain radius to length': True})
def R_rope(texel=24.0, scroll=0.0, subdiv=3):
    return op('renderers', 'render_rope', texel_size=float(texel), texture_scroll_rate=float(scroll), subdivision_count=subdiv)

# ================================================================== écriture PCF
TYPEMAP = {'FLOAT': ValueType.FLOAT, 'INTEGER': ValueType.INT, 'BOOL': ValueType.BOOL, 'VEC3': ValueType.VEC3,
           'VEC4': ValueType.VEC4, 'COLOR': ValueType.COLOR, 'STRING': ValueType.STRING}
COMMON = {'operator start fadein': 0.0, 'operator end fadein': 0.0, 'operator start fadeout': 0.0,
          'operator end fadeout': 0.0, 'operator fade oscillate': 0.0, 'operator end cap state': -1,
          'operator strength random scale max': 1.0, 'operator strength random scale min': 1.0,
          'operator strength scale seed': 0, 'operator time strength random scale max': 1.0,
          'operator time scale max': 1.0, 'operator time scale min': 1.0, 'operator time scale seed': 0,
          'operator time offset max': 0.0, 'operator time offset min': 0.0, 'operator time offset seed': 0}

def _attr(name, tname, val):
    t = TYPEMAP[tname]
    if t == ValueType.VEC3: val = Vec(*val)
    elif t == ValueType.COLOR: val = Color(*[int(v) for v in val])
    elif t == ValueType.VEC4:
        from srctools.dmx import Vec4
        val = Vec4(*val)
    elif t == ValueType.FLOAT: val = float(val)
    elif t == ValueType.INT: val = int(val)
    elif t == ValueType.BOOL: val = bool(val)
    return name, t, val

def op_element(kind, fn, params):
    if fn not in SCHEMA:
        raise KeyError(f'opérateur inconnu du corpus : {fn}')
    sch, canon = SCHEMA[fn], _CANON[fn]
    if kind not in sch.get('__lists__', [kind]):
        raise ValueError(f'{fn} n\'est pas un {kind} (vu dans : {sch["__lists__"]})')
    given = {}
    for k, v in params.items():
        if k.lower() not in canon:
            raise KeyError(f'{fn}: attribut inconnu {k!r}')
        given[canon[k.lower()]] = v
    common = {k.lower(): v for k, v in COMMON.items()}
    # Like Valve's editor (and every PCF tools read reliably): write EVERY attribute, defaults included.
    # Defaults: values from the GMod particle editor (pcfforge/defaults.json, via Particle Effects+, MIT).
    dflt = {k.lower(): v for k, v in {**DEFAULTS.get(kind, {}).get('_generic', {}),
                                         **DEFAULTS.get(kind, {}).get(fn, {})}.items()}
    el = Element(fn, 'DmeParticleOperator')
    el['functionName'] = fn
    for k, spec in sch.items():
        if k in ('__lists__', 'name', 'functionName', 'functionname'):
            continue
        tname = spec[0]
        if k in given: v = given[k]
        elif k.lower() in dflt: v = _dflt(dflt[k.lower()])
        elif k.lower() in common: v = common[k.lower()]
        else: continue                      # attribute this operator does not really have
        n, t, vv = _attr(k, tname, v)
        el[n] = Attribute(n, t, vv)
    return el


def _dflt(v):
    if isinstance(v, dict):
        return tuple(v.get('vec') or v.get('color') or v.get('vec4'))
    return v

def write_pcf(path, registry):
    systems = registry.systems
    names = list(systems)
    root = Element('untitled', 'DmElement')
    elems = {n: Element(n, 'DmeParticleSystemDefinition') for n in names}
    for n in names:
        s = systems[n]; e = elems[n]
        groups = {k: [] for k in ('renderers', 'operators', 'initializers', 'emitters', 'forces', 'constraints')}
        for kind, fn, params in s.ops:
            groups[kind].append(op_element(kind, fn, params))
        for k, lst in groups.items():
            e[k] = Attribute.array(k, ValueType.ELEMENT, lst)
        ch = []
        for cname, delay in s.children:
            c = Element(cname, 'DmeParticleChild')
            c['child'] = elems[cname]; c['delay'] = float(delay); c['end cap effect'] = False
            ch.append(c)
        e['children'] = Attribute.array('children', ValueType.ELEMENT, ch)
        e['preventNameBasedLookup'] = bool(getattr(s, 'hidden', False))
        e['max_particles'] = int(s.maxp); e['initial_particles'] = 0
        e['material'] = s.mat.replace('/', '\\') + '.vmt' if not s.mat.endswith('.vmt') else s.mat
        e['bounding_box_min'] = Vec(-s.bbox, -s.bbox, -s.bbox); e['bounding_box_max'] = Vec(s.bbox, s.bbox, s.bbox)
        e['cull_radius'] = 0.0; e['cull_cost'] = 1.0; e['cull_control_point'] = 0; e['cull_replacement_definition'] = ''
        e['radius'] = float(s.radius); e['color'] = Color(*s.color); e['rotation'] = 0.0; e['rotation_speed'] = 0.0
        e['normal'] = Vec(0, 0, 1); e['sequence_number'] = 0; e['sequence_number 1'] = 0; e['group id'] = 0
        e['maximum time step'] = 0.1; e['maximum sim tick rate'] = 0.0; e['minimum sim tick rate'] = 0.0
        e['minimum rendered frames'] = 0; e['control point to disable rendering if it is the camera'] = int(s.camera_cp)
        e['maximum draw distance'] = float(s.draw_distance); e['time to sleep when not drawn'] = 8.0
        e['Sort particles'] = bool(s.sort); e['batch particle systems'] = False
        e['view model effect'] = False; e['screen space effect'] = False
    root['particleSystemDefinitions'] = Attribute.array('particleSystemDefinitions', ValueType.ELEMENT, [elems[n] for n in names])
    from .dmx2 import write as write_dmx2
    write_dmx2(path, root)
