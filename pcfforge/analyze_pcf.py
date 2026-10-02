"""Readable analysis of any PCF (a reference effect): what each system draws, how much, how it moves.

python -m pcfforge analyze <file.pcf> [--full]  -> Markdown report on stdout
Values are read from the file; attributes left out of the file use the engine default and are shown as such.
"""
from srctools.dmx import Element, ValueType

LISTS = ('emitters', 'initializers', 'operators', 'renderers', 'forces', 'constraints')
_SKIP = {'name', 'functionname'}
_BOILER = ('operator ', 'visibility ')                      # timing / visibility plumbing, rarely meaningful


def value(a):
    t = a.type
    try:
        if a.is_array:
            return f'[{len(a)} val.]'
        if t == ValueType.FLOAT:
            return round(a.val_float, 3)
        if t == ValueType.INT:
            return a.val_int
        if t == ValueType.BOOL:
            return a.val_bool
        if t == ValueType.STRING:
            return a.val_str
        if t == ValueType.COLOR:
            c = a.val_color
            return (c.r, c.g, c.b, c.a)
        if t == ValueType.VEC3:
            v = a.val_vec3
            return (round(v.x, 2), round(v.y, 2), round(v.z, 2))
        if t == ValueType.TIME:
            return round(float(a.val_time), 3)
        if t == ValueType.ELEMENT:
            e = a.val_elem
            return e.name if e is not None else None
    except (ValueError, TypeError, AttributeError):
        pass
    return str(t.name)


def params(o, full=False):
    return {k: value(o[k]) for k in o.keys()
            if k.lower() not in _SKIP and (full or not k.lower().startswith(_BOILER))}


def load(path):
    root, fmt, ver = Element.parse(open(path, 'rb'))
    defs = list(root['particleSystemDefinitions'].iter_elem())
    kids = {c['child'].val_elem.name for s in defs for c in (s['children'].iter_elem() if 'children' in s else [])}
    return defs, kids


def _get(p, *names, default=None):
    low = {k.lower(): v for k, v in p.items()}
    for n in names:
        if n.lower() in low:
            return low[n.lower()]
    return default


def summary(s):
    """Key numbers of one system (what matters when comparing with our own effects)."""
    ops = {k: [(o['functionName'].val_str, params(o)) for o in s[k].iter_elem()] if k in s else [] for k in LISTS}
    out = dict(material=s['material'].val_str if 'material' in s else '(défaut)',
               max=s['max_particles'].val_int if 'max_particles' in s else '(défaut)',
               children=[c['child'].val_elem.name for c in s['children'].iter_elem()] if 'children' in s else [])
    for fn, p in ops['emitters']:
        if fn == 'emit_continuously':
            out['emission'] = f"{_get(p, 'emission_rate', default='?')} /s, durée {_get(p, 'emission_duration', default=0)}"
        elif fn == 'emit_instantaneously':
            out['emission'] = f"{_get(p, 'num_to_emit', default='?')} d'un coup"
        else:
            out['emission'] = fn
    life, rad, pos, color, alpha, motion, look = None, None, [], [], None, [], []
    for fn, p in ops['initializers']:
        if fn in ('Lifetime Random',):
            life = (_get(p, 'lifetime_min'), _get(p, 'lifetime_max'))
        elif fn == 'Lifetime From Sequence':
            life = 'selon la séquence'
        elif fn == 'Radius Random':
            rad = (_get(p, 'radius_min'), _get(p, 'radius_max'))
        elif fn == 'Color Random':
            color = [_get(p, 'color1'), _get(p, 'color2')]
        elif fn == 'Alpha Random':
            alpha = (_get(p, 'alpha_min'), _get(p, 'alpha_max'))
        elif fn.startswith('Position') or fn in ('Set Hitbox Position on Model',):
            keep = {k: v for k, v in p.items() if k.lower() in (
                'distance_min', 'distance_max', 'distance_bias', 'speed_min', 'speed_max', 'offset min', 'offset max',
                'warp min', 'warp max', 'hitbox set', 'model hitbox scale', 'direction bias', 'control_point_number',
                'start control point number', 'end control point number', 'radius', 'offset in local space 0/1',
                'initial radius', 'thickness', 'even distribution', 'even distribution count', 'yaw', 'pitch', 'roll',
                'distance_bias_absolute_value', 'randomly select sequential cp pairs between start and end points',
                'use sequential cp pairs between start and end point', 'particles to map from start to end')}
            pos.append(f'{fn} {keep}')
        elif fn.startswith('Velocity') or fn.startswith('Rotation'):
            motion.append(f'{fn} {p}')
    for fn, p in ops['operators'] + ops['forces'] + ops['constraints']:
        if fn in ('Movement Basic',):
            motion.append(f"gravité {_get(p, 'gravity')} traînée {_get(p, 'drag')}")
        elif fn in ('Alpha Fade and Decay', 'Alpha Fade In Random', 'Alpha Fade Out Random', 'Lifespan Decay'):
            look.append(f'{fn} {p}' if fn != 'Lifespan Decay' else fn)
        elif fn.startswith('Movement Lock'):
            motion.append(f'VERROU {fn} {p}')
        else:
            motion.append(f'{fn} {p}')
    for fn, p in ops['renderers']:
        look.append(f'rendu {fn} {p}')
    out.update(life=life, radius=rad, color=color, alpha=alpha, position=pos, motion=motion, look=look)
    try:
        em = str(out.get('emission', '0'))
        rate = float(em.split()[0])
        lmax = life[1] if isinstance(life, tuple) and life[1] is not None else 1.0
        out['peak'] = int(rate) if "d'un coup" in em else int(rate * lmax)
    except (ValueError, TypeError):
        out['peak'] = None
    return out


def report(path, full=False):
    defs, kids = load(path)
    L = [f'# Analyse de {path.replace(chr(92), "/").split("/")[-1]}', '',
         f'{len(defs)} systèmes, dont {len([d for d in defs if d.name not in kids])} racines.', '']
    for s in defs:
        m = summary(s)
        L.append(f"## {'RACINE' if s.name not in kids else 'enfant'} `{s.name}`")
        L.append(f"- matériau `{m['material']}` · max {m['max']} · émission {m.get('emission', '-')}"
                 + (f" · pic estimé ~{m['peak']}" if m.get('peak') is not None else ''))
        if m['children']:
            L.append(f"- enfants : {', '.join(m['children'])}")
        L.append(f"- vie {m['life']} · rayon {m['radius']} · couleur {m['color']} · alpha {m['alpha']}")
        for x in m['position']:
            L.append(f'- position : {x}')
        for x in m['motion']:
            L.append(f'- mouvement : {x}')
        for x in m['look']:
            L.append(f'- aspect : {x}')
        if full:
            for k in LISTS:
                for o in (s[k].iter_elem() if k in s else []):
                    L.append(f"  - [{k}] {o['functionName'].val_str} {params(o, True)}")
        L.append('')
    return '\n'.join(L)
