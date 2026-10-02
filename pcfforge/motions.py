"""Reusable motions. A layer can combine several: motion: [orbit, {type: flow, speed: .5}]

Each motion turns a few intent parameters into real PCF operators (all present in the corpus schema):
  speed       overall intensity multiplier (1 = default)
  radius      distance from the control point (u)
  height      vertical travel (u) for rise / fall / spiral
  turbulence  0..1, coherent wobble added on top (Velocity Noise, never white noise)
  direction   1 or -1 (turning direction)
"""
from .dsl import (F_pull, F_twist, F_rand, C_dist, O_axis_spin, O_osc_position, I_vnoise, I_vel)

MOTIONS = ('static', 'orbit', 'spiral', 'vortex', 'converge', 'diverge', 'radial_burst', 'flow', 'whip',
           'oscillate', 'rise', 'fall', 'follow', 'swirl')


def normalize(m):
    """str | dict | list -> list of dicts (validated)."""
    if m is None:
        return []
    items = m if isinstance(m, list) else [m]
    out = []
    for it in items:
        d = {'type': it} if isinstance(it, str) else dict(it)
        if d.get('type') not in MOTIONS:
            raise ValueError(f"motion inconnue : {d.get('type')!r} (connues : {', '.join(MOTIONS)})")
        out.append(d)
    return out


def ops(layer, cp=0):
    """Operators for all motions of a layer. Also returns whether the layer needs Movement Basic."""
    res, moving = [], False
    for m in normalize(layer.get('motion')):
        t = m['type']
        k = float(m.get('speed', 1.0))
        r = float(m.get('radius', layer.get('radius', 30)))
        h = float(m.get('height', 60))
        d = 1 if float(m.get('direction', 1)) >= 0 else -1
        mcp = int(m.get('cp', cp))
        if t in ('static', 'follow'):
            pass                                            # follow = lock handled by the composer (attach)
        elif t == 'orbit':
            res.append(O_axis_spin(d * 180 * k, mcp))       # turns around the CP even when it moves
        elif t == 'swirl':
            res += [O_axis_spin(d * 260 * k, mcp), I_vnoise(12 * k, (4, 18 * k))]
            moving = True
        elif t == 'spiral':
            res += [O_axis_spin(d * 220 * k, mcp), I_vel((0, 0, h * .8 * k), (0, 0, h * 1.2 * k))]
            moving = True
        elif t == 'vortex':
            res += [F_pull(700 * k, mcp), F_twist(d * 380 * k), C_dist(r * .45, r * 1.5, mcp)]
            moving = True
        elif t == 'converge':
            res.append(F_pull(900 * k, mcp))
            moving = True
        elif t == 'diverge':
            res.append(F_pull(-500 * k, mcp))
            moving = True
        elif t == 'radial_burst':
            if not (layer.get('speed') or layer.get('vel')):
                raise ValueError('motion radial_burst : la couche doit définir speed ou vel')
            moving = True
        elif t == 'flow':
            res.append(I_vnoise(25 * k, (0, 0)))
            moving = True
        elif t == 'whip':
            n = 180 * k
            res += [F_rand((-n, -n, -n * .5), (n, n, n * .5)), F_twist(d * 300 * k)]
            moving = True
        elif t == 'oscillate':
            a = float(m.get('amplitude', 6)) * k
            res.append(O_osc_position((a, a, a * .5)))
        elif t == 'rise':
            res.append(I_vel((0, 0, h * .8 * k), (0, 0, h * 1.2 * k)))
            moving = True
        elif t == 'fall':
            res.append(I_vel((0, 0, -h * 1.2 * k), (0, 0, -h * .8 * k)))
            moving = True
        turb = float(m.get('turbulence', 0))
        if turb > 0 and t not in ('flow', 'swirl'):
            res.append(I_vnoise(40 * turb * k, (0, 0)))
            moving = True
    return res, moving
