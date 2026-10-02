"""EffectSpec (V3 DSL): load, normalize, validate, resolve the mode.

A V3 file has `style` / `shape` (and optionally `model` / `attachment`). A v2 file (prefix + systems)
is still accepted as is: see layers.py.
"""
import os
import re

import yaml

from . import compose as C
from .motions import normalize as norm_motion
from .variation import check as check_variation
from .layers import P as PRESETS, PHASES, PHASE_OVERRIDES

TOP_KEYS = {'id', 'title', 'prompt', 'mode', 'model', 'attachment', 'regions', 'style', 'shape', 'behavior', 'layers',
            'timeline', 'variation', 'performance', 'preview', 'textures', 'texture_size'}
MODES = ('auto', 'standalone', 'model_driven')


class SpecError(ValueError):
    pass


def is_v2(d):
    return isinstance(d, dict) and 'systems' in d and 'prefix' in d


def load_file(path):
    if not os.path.exists(path):
        raise SpecError(f'fichier introuvable : {path}')
    d = yaml.safe_load(open(path, encoding='utf-8'))
    if not isinstance(d, dict):
        raise SpecError('le fichier doit contenir un objet YAML')
    return d


def _num(d, key, where, lo=None, hi=None):
    v = d.get(key)
    if v is None:
        return
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        raise SpecError(f'{where}{key} doit être un nombre')
    if (lo is not None and v < lo) or (hi is not None and v > hi):
        raise SpecError(f'{where}{key} hors limites [{lo}, {hi}] : {v}')


def _color(v, where):
    if v is None:
        return
    if not (isinstance(v, list) and len(v) in (3, 4) and all(isinstance(x, int) and 0 <= x <= 255 for x in v)):
        raise SpecError(f'{where} doit être [r, g, b] (0-255)')


def resolve_mode(d, base_dir='.'):
    """auto -> model_driven when a model is given or an attachment names a bone / attachment / region."""
    mode = d.get('mode', 'auto')
    if mode not in MODES:
        raise SpecError(f'mode inconnu : {mode} (connus : {MODES})')
    if mode != 'auto':
        return mode
    att = (d.get('attachment') or {}).get('type', 'entity')
    return 'model_driven' if d.get('model') or att in ('bone', 'attachment', 'region') else 'standalone'


def normalize(d, base_dir='.', analyze_model=True):
    """Validates a V3 dict and returns a normalized copy. Raises SpecError with a clear message."""
    unknown = set(d) - TOP_KEYS
    if unknown:
        raise SpecError(f'clés inconnues : {sorted(unknown)}')
    if not d.get('id') or not re.fullmatch(r'[a-z0-9_]+', str(d['id'])):
        raise SpecError('id obligatoire, en minuscules / chiffres / _ (sert de préfixe aux systèmes)')
    out = dict(d)
    out['mode'] = resolve_mode(d, base_dir)

    st = dict(d.get('style') or {})
    st.setdefault('type', 'chakra')
    if st['type'] not in C.ENERGIES:
        raise SpecError(f"style.type inconnu : {st['type']} (connus : {', '.join(C.ENERGIES)})")
    _color(st.get('color'), 'style.color')
    _color(st.get('secondary_color'), 'style.secondary_color')
    _num(st, 'intensity', 'style.', 0, 1)
    for lk in C._looks(st):
        if lk not in C.LOOKS:
            raise SpecError(f"style.look inconnu : {lk} (connus : {', '.join(C.LOOKS)})")
    out['style'] = st

    sh = dict(d.get('shape') or {})
    sh.setdefault('type', 'aura')
    if sh['type'] not in C.SHAPES:
        raise SpecError(f"shape.type inconnu : {sh['type']} (connus : {', '.join(C.SHAPES)})")
    _num(sh, 'radius', 'shape.', 1, 2000)
    _num(sh, 'height', 'shape.', 1, 4000)
    _num(sh, 'scale', 'shape.', 1, 3)
    _num(sh, 'margin', 'shape.', 0, 100)
    _num(sh, 'rise', 'shape.', 0, 500)
    out['shape'] = sh

    beh = dict(d.get('behavior') or {})
    try:
        if 'motion' in beh:
            norm_motion(beh['motion'])
        check_variation(d.get('variation'))
    except ValueError as e:
        raise SpecError(str(e))
    _num(beh, 'turbulence', 'behavior.', 0, 1)
    _num(beh, 'pulse', 'behavior.', 0, 5)
    out['behavior'] = beh

    for i, L in enumerate(d.get('layers') or []):
        if not isinstance(L, dict) or not (L.get('preset') or L.get('tex')):
            raise SpecError(f'layers[{i}] : il faut preset ou tex')
        if L.get('preset') and L['preset'] not in PRESETS:
            raise SpecError(f"layers[{i}] : preset inconnu {L['preset']!r}")
        if 'motion' in L:
            try:
                norm_motion(L['motion'])
            except ValueError as e:
                raise SpecError(f'layers[{i}] : {e}')

    tl = d.get('timeline')
    if tl is not None:
        if not isinstance(tl, list):
            raise SpecError('timeline doit être une liste [{phase, duration}]')
        for p in tl:
            if not isinstance(p, dict) or p.get('phase') not in PHASES:
                raise SpecError(f"phase inconnue : {p.get('phase') if isinstance(p, dict) else p} (connues : {PHASES})")
            _num(p, 'duration', f"timeline.{p['phase']}.", 0, 60)
            if 'duration' not in p:
                raise SpecError(f"timeline.{p['phase']} : duration manquante")
            bad = set(p.get('scale', {})) - set(PHASE_OVERRIDES)
            if bad:
                raise SpecError(f"timeline.{p['phase']}.scale inconnu : {sorted(bad)}")

    perf = dict(d.get('performance') or {})
    perf.setdefault('quality', 'high')
    if perf['quality'] not in C.QUALITY:
        raise SpecError(f"performance.quality inconnue : {perf['quality']} (connues : {', '.join(C.QUALITY)})")
    _num(perf, 'max_particles', 'performance.', 1, 5000)
    _num(perf, 'max_active_systems', 'performance.', 1, 64)
    out['performance'] = perf

    att = dict(d.get('attachment') or {'type': 'entity'})
    if att.get('type', 'entity') not in ('entity', 'bone', 'attachment', 'region', 'bounds'):
        raise SpecError(f"attachment.type inconnu : {att.get('type')}")
    att.setdefault('type', 'entity')
    if att['type'] in ('bone', 'attachment', 'region') and not att.get('name'):
        raise SpecError(f"attachment {att['type']} : name obligatoire")
    out['attachment'] = att

    if out['mode'] == 'model_driven':
        m = d.get('model') or {}
        if att['type'] in ('bone', 'region') and not m.get('path'):
            raise SpecError('mode model_driven : model.path obligatoire pour une attache bone / region')
        if m.get('path') and m.get('analyze', True) and analyze_model:
            from .model import analyze as A, mdl
            path = m['path'] if os.path.isabs(m['path']) else os.path.join(base_dir, m['path'])
            try:
                info = A.resolve(path, att, d.get('regions'))
            except mdl.ModelError as e:
                raise SpecError(str(e))
            out['_model'] = info
            if 'segment' in info:
                out['_segment'] = info['segment']
    return out


def load(path, analyze_model=True):
    d = load_file(path)
    if is_v2(d):
        return d
    return normalize(d, os.path.dirname(os.path.abspath(path)), analyze_model)
