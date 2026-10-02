"""Controlled variation: every particle differs a little, never chaotically.

variation: {scale: .25, lifetime: .18, rotation: 1, position: .15, velocity: .2, alpha: .15, color: .1, emission: .3}
Values are 0..1. Ranges are widened around the layer's own values; the style sets sensible defaults.
"""
KEYS = ('scale', 'size', 'lifetime', 'velocity', 'alpha', 'brightness', 'rotation', 'angle', 'position', 'color',
        'emission')


def _pair(v):
    return [float(v[0]), float(v[1])] if isinstance(v, (list, tuple)) else [float(v), float(v)]


def widen(pair, amount, floor=0.0):
    lo, hi = _pair(pair)
    if amount <= 0:
        return [lo, hi]
    mid = (lo + hi) / 2
    span = max(hi - lo, abs(mid) * 2 * amount)
    return [max(floor, mid - span / 2), mid + span / 2]


def check(v, where=''):
    if v is None:
        return {}
    if not isinstance(v, dict):
        raise ValueError(f'{where}variation doit être un objet')
    for k, x in v.items():
        if k not in KEYS:
            raise ValueError(f'{where}variation inconnue : {k!r} (connues : {", ".join(KEYS)})')
        if not 0 <= float(x) <= 1:
            raise ValueError(f'{where}variation {k} doit être entre 0 et 1')
    return v


def apply(L):
    """Mutates a layer dict in place from L['variation']."""
    v = check(L.get('variation'))
    if not v:
        return L
    g = lambda *ks: max(float(v.get(k, 0)) for k in ks)
    if 'size' in L:
        L['size'] = widen(L['size'], g('scale', 'size'), .1)
    if 'life' in L:
        L['life'] = widen(L['life'], g('lifetime'), .02)
    if 'speed' in L:
        L['speed'] = widen(L['speed'], g('velocity'))
    if 'up' in L:
        L['up'] = widen(L['up'], g('velocity'))
    if 'alpha' in L:
        a = widen(L['alpha'], g('alpha', 'brightness'))
        L['alpha'] = [min(255, a[0]), min(255, a[1])]
    if g('rotation', 'angle') > 0:
        L['rot'] = True
        s = _pair(L.get('spin', [0, 0]))
        amp = 60 * g('rotation', 'angle')
        L['spin'] = [s[0] - amp, s[1] + amp]
    if g('position') > 0:
        sp = _pair(L.get('spread', [0, 0]))
        L['spread'] = [sp[0], sp[1] + max(2.0, sp[1] * g('position'))]
    if g('color') > 0 and isinstance(L.get('color'), (list, tuple)) and L['color'] and isinstance(L['color'][0], (int, float)):
        c, k = L['color'], g('color') * .35
        L['color'] = ([max(0, int(x * (1 - k))) for x in c[:3]], [min(255, int(x + (255 - x) * k)) for x in c[:3]])
    if g('emission') > 0 and L.get('rate'):
        L['_emit_noise'] = g('emission')
    return L
