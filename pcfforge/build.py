"""Build chain: spec file -> (compose) -> textures -> PCF -> lint -> ready-to-copy GMod addon.

out/<id>_fx/
  particles/<id>.pcf
  materials/<id>/*.vtf|vmt
  lua/pcfforge/runtime.lua            AttachEffect / DetachEffect / UpdateEffect (client)
  lua/autorun/pcfforge_<id>.lua       registers the PCF, precaches it, describes the attachment
  addon.json, LISEZMOI.txt, build_report.json
"""
import glob
import json
import os
import shutil

from srctools.dmx import Element

from . import dsl, effect as EF, layers as LY, compose as CO
from .textures import lib as TL

HERE = os.path.dirname(os.path.abspath(__file__))
RUNTIME = os.path.join(HERE, '..', 'gmod', 'pcfforge_runtime', 'lua', 'pcfforge', 'runtime.lua')


def paths(spec, out='out'):
    addon = spec.get('addon', spec['prefix'] + '_fx'); matdir = spec.get('materials', spec['prefix'])
    base = os.path.join(out, addon)
    return dict(addon=base, pcf=os.path.join(base, 'particles', spec.get('file', spec['prefix'] + '.pcf')),
                mat=os.path.join(base, 'materials', matdir), png=os.path.join(out, '.cache', matdir),
                prev=os.path.join(out, 'captures', spec['prefix']), matdir=matdir)


def used_textures(spec):
    out = set()
    for sdef in spec['systems'].values():
        for raw in (sdef['layers'] if isinstance(sdef, dict) else sdef):
            out.add(raw.get('tex') or LY.P[raw['preset']]['tex'])
    return out


def textures(spec, P, force=False):
    """Generates only the textures the spec uses (cached)."""
    info = {}
    custom = spec.get('textures', {})
    for name in sorted(used_textures(spec) | set(custom)):
        if name not in TL.REG and name not in custom:
            raise ValueError(f'texture inconnue : {name} (voir python -m pcfforge textures)')
        png = os.path.join(P['png'], name + '.png'); meta = png + '.json'
        size = spec.get('texture_size', {}).get(name)
        if not force and os.path.exists(png) and os.path.exists(meta) and os.path.exists(os.path.join(P['mat'], name + '.vtf')):
            cached = json.load(open(meta))
            if size is None or cached.get('S') == size:
                info[name] = cached; continue
        t = TL.make(name, custom.get(name), size)
        extra = dict(custom.get(name, {}).get('vmt', {}))
        if name in ('glow', 'glow_hard', 'smoke', 'explosion', 'noise'):      # big sprites: fade when screen-filling
            extra.setdefault('$minfadesize', '0.35'); extra.setdefault('$maxfadesize', '0.6')
        TL.export(name, t, P['mat'], P['png'], extra)
        m = {k: v for k, v in t.items() if k != 'img'}; json.dump(m, open(meta, 'w')); info[name] = m
    for f in glob.glob(os.path.join(P['mat'], '*.vtf')) + glob.glob(os.path.join(P['mat'], '*.vmt')):
        if os.path.splitext(os.path.basename(f))[0] not in info:             # textures an older version used
            os.remove(f)
    return info


def lint(spec, reg, roots, peaks, budget):
    errs, warns = [], []
    for n, s in reg.systems.items():
        fns = [fn for _, fn, _ in s.ops]
        pres = spec.get('prefixes', [spec['prefix']])
        if not any(n == p or n.startswith(p + '_') for p in pres): errs.append(f'{n}: nom non préfixé')
        if 'Lifespan Decay' not in fns: errs.append(f'{n}: pas de Lifespan Decay')
        if not any(k == 'renderers' for k, _, _ in s.ops): errs.append(f'{n}: pas de rendu')
        if not any(k == 'initializers' and fn.startswith('Position') for k, fn, _ in s.ops):
            errs.append(f'{n}: pas d\'initialiseur de position (Source réutilise la position d\'une particule morte)')
        if any('ollision' in f for f in fns): warns.append(f'{n}: collision (coûteux)')
        if fns.count('Color Fade') > 1: warns.append(f'{n}: plusieurs Color Fade')
        for c, _ in s.children:
            if c not in reg.systems: errs.append(f'{n}: enfant manquant {c}')
    for r in roots:
        tot = peaks.get(r, 0) + sum(peaks.get(c, 0) for c, _ in reg.systems[r].children)
        if tot > budget: warns.append(f'{r}: pic estimé {tot} > budget {budget}')
    return errs, warns


def write_pcf(P, reg):
    os.makedirs(os.path.dirname(P['pcf']), exist_ok=True)
    dsl.write_pcf(P['pcf'], reg)
    r, fmt, ver = Element.parse(open(P['pcf'], 'rb'))
    got = {d.name for d in r['particleSystemDefinitions'].iter_elem()}
    if (fmt, ver) != ('pcf', 1) or got != set(reg.systems):
        raise RuntimeError('relecture PCF incohérente')


def prepare(spec_path, analyze_model=True):
    """Loads any spec file -> (layer_spec, runtime_info, notes, effect_or_None)."""
    d = EF.load(spec_path, analyze_model)
    if EF.is_v2(d):
        return d, dict(attach={'type': 'entity'}, mode='standalone', systems=[LY.root_name(d['prefix'], k, d.get('exact_names', False)) for k in d['systems']]), [], None
    spec, runtime, notes = CO.compose(d)
    if d.get('textures'):
        spec['textures'] = d['textures']
    if d.get('preview'):
        spec['preview'] = d['preview']
    if d.get('texture_size'):
        spec['texture_size'] = d['texture_size']
    return spec, runtime, notes, d


def build(spec_path, out='out', force_tex=False):
    spec, runtime, notes, eff = prepare(spec_path)
    P = paths(spec, out)
    tex = textures(spec, P, force_tex)
    reg, roots, infos, peaks = LY.build(spec, tex)
    budget = int((eff or {}).get('performance', {}).get('max_particles', spec.get('budget', 400)))
    errs, warns = lint(spec, reg, roots, peaks, budget)
    if not errs:
        write_pcf(P, reg)
        write_lua(spec, P, runtime)
    os.makedirs(P['addon'], exist_ok=True)
    json.dump({'title': spec.get('title', spec['prefix']), 'type': 'effects', 'tags': ['fun'], 'ignore': []},
              open(os.path.join(P['addon'], 'addon.json'), 'w'), indent=1)
    rep = dict(pcf=P['pcf'], systems=len(reg.systems), roots={r: infos[r] for r in roots}, budget=budget,
               errors=errs, warnings=warns, notes=notes, textures=sorted(tex), mode=runtime['mode'],
               attach=runtime['attach'], segment={k: v for k, v in (runtime.get('segment') or {}).items() if k != 'profile'} or None,
               control_points=len(runtime.get('points', [])) + 2 if runtime.get('points') else None)
    write_readme(spec, P, rep)
    json.dump(rep, open(os.path.join(P['addon'], 'build_report.json'), 'w'), indent=1, ensure_ascii=False)
    return spec, P, tex, rep


def _vec(v):
    return 'Vector(%s)' % ', '.join(f'{float(x):.3f}' for x in v)


def write_lua(spec, P, runtime):
    ldir = os.path.join(P['addon'], 'lua')
    os.makedirs(os.path.join(ldir, 'pcfforge'), exist_ok=True)
    os.makedirs(os.path.join(ldir, 'autorun'), exist_ok=True)
    shutil.copy(RUNTIME, os.path.join(ldir, 'pcfforge', 'runtime.lua'))
    a = runtime['attach']
    fields = [f'type = "{a.get("type", "entity")}"']
    if a.get('name'): fields.append(f'name = "{a["name"]}"')
    seg = runtime.get('segment')
    if seg:
        fields += [f'bone = "{seg["bone"]}"', f'from = {_vec(seg["start"])}', f'to = {_vec(seg["end"])}']
    if a.get('offset'): fields.append(f'offset = {_vec(a["offset"])}')
    if runtime.get('points'):
        fields.append('points = { ' + ', '.join(_vec(p) for p in runtime['points']) + ' }')
    pcf = os.path.basename(P['pcf'])
    systems = runtime['systems']
    lua = [f'-- Généré par pcfforge : {spec["prefix"]}. Enregistre le PCF et décrit son attache.',
           'AddCSLuaFile()', 'AddCSLuaFile("pcfforge/runtime.lua")',
           f'game.AddParticles("particles/{pcf}")']
    lua += [f'PrecacheParticleSystem("{s}")' for s in systems]
    lua += ['if SERVER then return end', 'include("pcfforge/runtime.lua")']
    att = '{ ' + ', '.join(fields) + ' }'

    def persistent(sysname):                       # very long lives: StopEmission would leave it forever
        key = next((k for k in spec['systems'] if LY.root_name(spec['prefix'], k, spec.get('exact_names', False)) == sysname), None)
        sdef = spec['systems'].get(key, {})
        layers = sdef['layers'] if isinstance(sdef, dict) else sdef
        return any(float(LY._pair(l.get('life', LY.P.get(l.get('preset'), {}).get('life')), [1, 1])[1]) >= 600
                   for l in layers)
    flag = lambda s: ', persistent = true' if persistent(s) else ''
    if systems[0] != spec['prefix']:
        lua.append(f'PCFForge.Register("{spec["prefix"]}", {{ system = "{systems[0]}", attach = {att}{flag(systems[0])} }})')
    if len(systems) > 1 or systems[0] == spec['prefix']:
        for s in systems:
            lua.append(f'PCFForge.Register("{s}", {{ system = "{s}", attach = {att}{flag(s)} }})')
    lua.append('')
    open(os.path.join(ldir, 'autorun', f'pcfforge_{spec["prefix"]}.lua'), 'w', encoding='utf-8').write('\n'.join(lua))


def write_readme(spec, P, rep):
    L = [f"{spec.get('title', spec['prefix'])}", '=' * 40, '',
         'Installer : copier ce dossier dans garrysmod/addons/ puis relancer la carte.', '',
         f"Fichier : particles/{os.path.basename(P['pcf'])}  ({rep['systems']} systèmes)",
         f"Mode : {rep['mode']}   Attache : {rep['attach']}", '', 'Systèmes à appeler (racines) :']
    for r, i in rep['roots'].items():
        L.append(f"  {r:32s} pic ~{i['peak']:4d}  {i['about']}")
    L += ['', 'Test rapide en jeu (console, client) :',
          f"  pcfforge_attach {spec['prefix']}      attache l'effet à l'entité visée (ou à toi)",
          '  pcfforge_clear                 retire tous les effets de test', '',
          'Depuis du Lua client :',
          f"  local h = PCFForge.AttachEffect(ent, \"{spec['prefix']}\")",
          '  PCFForge.DetachEffect(h)', '']
    if rep.get('segment'):
        s = rep['segment']
        L += [f"Région : os {s['bone']}, CP0 {s['start']} -> CP1 {s['end']} (repère de l'os), longueur {s['length']} u", '']
    L += ['Statut : généré + vérifié (relecture PCF, lint). Le rendu réel se juge dans Garry\'s Mod.']
    open(os.path.join(P['addon'], 'LISEZMOI.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')


def summary(rep):
    s = [f"PCF : {rep['pcf']} ({rep['systems']} systèmes, budget {rep['budget']}, mode {rep['mode']})"]
    for r, i in rep['roots'].items(): s.append(f"  racine {r} : {i['layers']} couches, pic estimé {i['peak']}")
    for n in rep.get('notes', []): s.append('  note : ' + n)
    if rep['errors']: s.append('ERREURS : ' + ' | '.join(rep['errors']))
    if rep['warnings']: s.append('Avertissements : ' + ' | '.join(rep['warnings']))
    if not rep['errors'] and not rep['warnings']: s.append('Lint : OK')
    return '\n'.join(s)


def drop(spec, P, rep, dst):
    """PCF + materials only, laid out like garrysmod/ (particles/, materials/<dir>/), for particle tools that read
    garrysmod/particles directly. Effects that need the runtime (model-driven: CP1+ placed by Lua) are flagged."""
    os.makedirs(os.path.join(dst, 'particles'), exist_ok=True)
    shutil.copy(P['pcf'], os.path.join(dst, 'particles'))
    mdst = os.path.join(dst, 'materials', P['matdir'])
    shutil.rmtree(mdst, ignore_errors=True)
    shutil.copytree(P['mat'], mdst)
    # loader: particle tools only list PCFs the game has loaded (game.AddParticles); nothing else in it
    ldir = os.path.join(dst, 'lua', 'autorun'); os.makedirs(ldir, exist_ok=True)
    pcf = os.path.basename(P['pcf'])
    open(os.path.join(ldir, f'pcfforge_drop_{spec["prefix"]}.lua'), 'w', encoding='utf-8').write('\n'.join(
        [f'-- pcfforge (drop) : charge {pcf} pour les outils de particules. Aucune logique.',
         f'game.AddParticles("particles/{pcf}")'] + [f'PrecacheParticleSystem("{r}")' for r in rep['roots']]) + '\n')
    needs_runtime = rep.get('mode') == 'model_driven'
    note = os.path.join(dst, 'LISEZMOI_drop.txt')
    with open(note, 'a', encoding='utf-8') as f:
        f.write(f"{os.path.basename(P['pcf'])} : systèmes {', '.join(rep['roots'])}"
                + ("  [BESOIN DU RUNTIME : points de contrôle posés par le Lua, ne s'affiche pas correctement seul]\n"
                   if needs_runtime else "  [autonome : CP0 seul]\n"))
    return f"{os.path.basename(P['pcf'])} -> {dst}" + ('  (model-driven : nécessite le runtime)' if needs_runtime else '')


def pack(spec, P, rep, dst):
    """One shareable zip per effect: an addon folder to extract into garrysmod/addons/. Standalone effects get
    only the PCF, its materials and a loader (game.AddParticles + precache) so particle tools list them; effects
    that need the runtime (model-driven) ship the full generated addon."""
    import tempfile, zipfile
    pid = spec['prefix']
    needs_runtime = rep.get('mode') == 'model_driven'
    tmp = tempfile.mkdtemp()
    root = os.path.join(tmp, pid)
    if needs_runtime:
        shutil.copytree(P['addon'], root, ignore=shutil.ignore_patterns('build_report.json'))
    else:
        os.makedirs(os.path.join(root, 'particles'))
        shutil.copy(P['pcf'], os.path.join(root, 'particles'))
        shutil.copytree(P['mat'], os.path.join(root, 'materials', P['matdir']))
        ldir = os.path.join(root, 'lua', 'autorun'); os.makedirs(ldir)
        pcf = os.path.basename(P['pcf'])
        open(os.path.join(ldir, f'{pid}_particles.lua'), 'w', encoding='utf-8').write('\n'.join(
            [f'-- {pid} : charge {pcf} (aucune autre logique)', f'game.AddParticles("particles/{pcf}")']
            + [f'PrecacheParticleSystem("{r}")' for r in rep['roots']]) + '\n')
        json.dump({'title': spec.get('title', pid), 'type': 'effects', 'tags': ['fun'], 'ignore': []},
                  open(os.path.join(root, 'addon.json'), 'w'), indent=1)
        L = [spec.get('title', pid), '=' * 40, '',
             f'Installer : extraire le dossier "{pid}" dans garrysmod/addons/ puis relancer Garry\'s Mod.', '',
             f'Fichier : particles/{pcf}', 'Systèmes :']
        for r, i in rep['roots'].items():
            key = next((k for k in spec['systems'] if LY.root_name(pid, k, spec.get('exact_names', False)) == r), None)
            sd = spec['systems'].get(key)
            L.append(f"  {r:28s} {sd.get('about', '') if isinstance(sd, dict) else ''}")
        L += ['', 'Test : outil de particules (Particle Effects+, Advanced Particle Controller…) ou en Lua :',
              f'  ParticleEffect("{next(iter(rep["roots"]))}", pos, Angle(0, 0, 0))', '']
        L += list(spec.get('readme', [])) + ([''] if spec.get('readme') else [])     # mode d'emploi propre à l'effet
        L += ['Statut : généré et validé hors moteur (format identique à l\'éditeur de particules de Valve).']
        open(os.path.join(root, 'LISEZMOI.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    os.makedirs(dst, exist_ok=True)
    zpath = os.path.join(dst, f'{pid}.zip')
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        for base, _, files in os.walk(root):
            for f in files:
                full = os.path.join(base, f)
                z.write(full, os.path.relpath(full, tmp))
    shutil.rmtree(tmp, ignore_errors=True)
    return f"{zpath}  ({os.path.getsize(zpath) // 1024} Ko{', avec runtime' if needs_runtime else ''})"
