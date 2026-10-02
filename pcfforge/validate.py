"""Re-reads a PCF file: DMX format, known operators and lists, children, materials."""
from srctools.dmx import Element

from .dsl import SCHEMA

LISTS = ('emitters', 'initializers', 'operators', 'renderers', 'forces', 'constraints')


def _load(path):
    root, fmt, ver = Element.parse(open(path, 'rb'))
    return root, fmt, ver, list(root['particleSystemDefinitions'].iter_elem())


def validate(path):
    errs = []
    try:
        root, fmt, ver, defs = _load(path)
    except Exception as e:                                   # noqa: BLE001 - any parse failure is a result
        return [f'illisible : {e}'], path
    if fmt != 'pcf':
        errs.append(f'format {fmt} (attendu pcf)')
    names = {d.name for d in defs}
    for s in defs:
        for k in LISTS:
            for o in (s[k].iter_elem() if k in s else []):
                fn = o['functionName'].val_str
                if fn not in SCHEMA:
                    errs.append(f'{s.name}: opérateur inconnu {fn!r}')
                elif k not in SCHEMA[fn]['__lists__']:
                    errs.append(f'{s.name}: {fn!r} placé dans {k}')
        for c in (s['children'].iter_elem() if 'children' in s else []):
            if c['child'].val_elem.name not in names:
                errs.append(f'{s.name}: enfant absent {c["child"].val_elem.name}')
    return errs, f'{path} : {fmt} v{ver}, {len(defs)} systèmes'


def describe(path, ops=False):
    root, fmt, ver, defs = _load(path)
    kids = {c['child'].val_elem.name for s in defs for c in (s['children'].iter_elem() if 'children' in s else [])}
    out = [f'{fmt} v{ver} — {len(defs)} systèmes, {len([d for d in defs if d.name not in kids])} racines']
    for s in defs:
        ch = [c['child'].val_elem.name for c in (s['children'].iter_elem() if 'children' in s else [])]
        tag = 'RACINE' if s.name not in kids else 'enfant'
        out.append(f"[{tag}] {s.name}  mat={s['material'].val_str}  max={s['max_particles'].val_int if 'max_particles' in s else '?'}"
                   + (f'  enfants={ch}' if ch else ''))
        if ops:
            out.append('    ' + str([o['functionName'].val_str for k in LISTS if k in s for o in s[k].iter_elem()]))
    return '\n'.join(out)
