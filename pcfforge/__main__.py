"""CLI : python -m pcfforge <commande> ...
  generate <spec> [--retex]     (alias build) spec V3 ou v2 -> textures + PCF + lint + addon GMod (out/)
  lint <spec>                   valide la spec et le PCF qu'elle produirait, sans rien écrire
  validate <fichier.pcf>        relit un PCF : format, opérateurs connus, enfants, matériaux
  parse "<texte>" [--id ID]     demande en langage naturel -> spec YAML + points non résolus
  model inspect <fichier.mdl>   os, hiérarchie, attachments, hitboxes, axe principal (lecture réelle du .mdl)
  textures | presets            bibliothèques disponibles
  new <nom>                     crée specs/<nom>.yaml depuis le modèle
  inspect <fichier.pcf> [--ops] résumé d'un PCF existant
  analyze <fichier.pcf> [--full] analyse lisible d'un PCF de référence (quantités, tailles, mouvement, rendu)
  install <spec> [--gmod DIR]   copie l'addon généré dans garrysmod/addons
  drop <spec...> [--out DIR]    PCF + matériaux seuls, à déposer dans garrysmod/ (test avec un outil de particules)
  pack <spec...> [--out DIR]    un zip par effet, à donner : extraire dans garrysmod/addons/ et c'est prêt
  preview <spec> [--chain start:0,loop:1.1:4.5!,end:4.5] [--total 7] [--elev 12] [--dist 240] [--target 50] [--out f.gif]
          [--cp0 0,0,60] [--cp1 160,0,40] [--cp0-vel 0,0,0] [--bg 70,72,78] [--size 360] [--azim 0]
          [--figure 0,0,0;110,0,5]   (silhouettes grises de 72 u, pieds aux points donnés)
          [--views 0.3,1,2.5]        4 vues (fond clair / sombre, angle bas / haut) + planche PNG à ces instants
                                (! = détruit d'un coup ; CP1 = 2e point de contrôle, ex. la cible d'un lien)
                                aperçu APPROXIMATIF hors moteur (GIF) d'un enchaînement de systèmes
  capture <spec> [--video] ...  captures DANS Garry's Mod (Windows + GMod requis)
  doctor                        état de l'environnement
"""
import sys, os, json, shutil, glob, platform


def _fail(msg):
    print('ERREUR : ' + str(msg)); sys.exit(1)


def main(a):
    if not a or a[0] in ('-h', '--help', 'help'): print(__doc__); return
    cmd = a[0]
    from . import effect as EF
    try:
        run(cmd, a)
    except (EF.SpecError, ValueError, KeyError) as e:
        _fail(e)


def run(cmd, a):
    if cmd == 'textures':
        from .textures.lib import describe; print(describe())
    elif cmd == 'presets':
        from .layers import P
        for k, v in P.items(): print(f'{k:12s} ' + ', '.join(f'{kk}={vv}' for kk, vv in v.items()))
    elif cmd == 'new':
        name = a[1]; os.makedirs('specs', exist_ok=True); dst = f'specs/{name}.yaml'
        src = open(os.path.join(os.path.dirname(__file__), '..', 'templates', 'spec_template.yaml'), encoding='utf-8').read()
        open(dst, 'w', encoding='utf-8').write(src.replace('__NAME__', name)); print(dst)
    elif cmd in ('generate', 'build'):
        from . import build as B
        spec, P, tex, rep = B.build(a[1], force_tex='--retex' in a)
        print(B.summary(rep))
        if rep['errors']: sys.exit(1)
    elif cmd == 'lint':
        from . import build as B, layers as LY
        from .textures import lib as TL
        spec, runtime, notes, eff = B.prepare(a[1])
        missing = sorted(t for t in B.used_textures(spec) if t not in TL.REG and t not in spec.get('textures', {}))
        if missing: _fail(f'textures inconnues : {missing}')
        tex = {n: TL.meta(n) for n in B.used_textures(spec) if n in TL.REG}
        reg, roots, infos, peaks = LY.build(spec, tex)
        budget = int((eff or {}).get('performance', {}).get('max_particles', spec.get('budget', 400)))
        errs, warns = B.lint(spec, reg, roots, peaks, budget)
        for n in notes: print('note : ' + n)
        for w in warns: print('avertissement : ' + w)
        for e in errs: print('erreur : ' + e)
        print(f"{'FAIL' if errs else 'OK'} — {len(reg.systems)} systèmes, mode {runtime['mode']}")
        if errs: sys.exit(1)
    elif cmd == 'validate':
        from .validate import validate
        errs, info = validate(a[1])
        print(info)
        for e in errs: print('erreur : ' + e)
        print('FAIL' if errs else 'OK'); sys.exit(1 if errs else 0)
    elif cmd == 'parse':
        import yaml
        from .parse import parse
        spec, unresolved = parse(a[1], a[a.index('--id') + 1] if '--id' in a else None)
        print(yaml.safe_dump(spec, allow_unicode=True, sort_keys=False))
        for u in unresolved: print('# à préciser : ' + u)
    elif cmd == 'model':
        if len(a) < 3 or a[1] != 'inspect': _fail('usage : model inspect <fichier.mdl>')
        from .model import mdl, analyze
        try:
            print(json.dumps(analyze.summary(mdl.read(a[2])), indent=1, ensure_ascii=False))
        except mdl.ModelError as e:
            _fail(e)
    elif cmd == 'capture':
        from . import capture as C
        g = a[a.index('--gmod') + 1] if '--gmod' in a else None
        to = int(a[a.index('--timeout') + 1]) if '--timeout' in a else 300
        r = C.capture(a[1], g, video='--video' in a, keep_open='--keep-open' in a, timeout=to)
        if r:
            print(f"Captures moteur : {r.get('sheet_small', '(aucune image)')}" + (f"\nVidéo : {r['video']}" if 'video' in r else ''))
    elif cmd == 'capture-clean':
        from . import capture as C
        C.remove_harness(a[a.index('--gmod') + 1] if '--gmod' in a else None)
    elif cmd == 'drop':
        from . import build as B
        dst = a[a.index('--out') + 1] if '--out' in a else os.path.join('out', 'drop')
        for spec_path in [x for x in a[1:] if not x.startswith('--') and x != dst]:
            spec, P, tex, rep = B.build(spec_path)
            if rep['errors']: _fail(f'{spec_path} : ' + ' | '.join(rep['errors']))
            print(B.drop(spec, P, rep, dst))
        print(f'À copier tel quel dans garrysmod/ : {dst}/particles et {dst}/materials')
    elif cmd == 'pack':
        from . import build as B
        dst = a[a.index('--out') + 1] if '--out' in a else os.path.join('out', 'share')
        for spec_path in [x for x in a[1:] if not x.startswith('--') and x != dst]:
            spec, P, tex, rep = B.build(spec_path)
            if rep['errors']: _fail(f'{spec_path} : ' + ' | '.join(rep['errors']))
            print(B.pack(spec, P, rep, dst))
    elif cmd == 'preview':
        import yaml
        from .preview import render
        opt = lambda k, d: a[a.index(k) + 1] if k in a else d
        keys = list(yaml.safe_load(open(a[1], encoding='utf-8'))['systems'])
        chain = []
        for item in opt('--chain', ','.join(f'{k}:0' for k in keys)).split(','):
            parts = item.split(':')
            kill = parts[2].endswith('!') if len(parts) > 2 else False      # loop:1.1:4.5! = détruit d'un coup
            stop = float(parts[2].rstrip('!')) if len(parts) > 2 else None
            chain.append((parts[0], float(parts[1]), stop, stop if kill else None))
        out = opt('--out', os.path.join('out', 'preview', os.path.splitext(os.path.basename(a[1]))[0] + '.gif'))
        os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
        v3 = lambda k, d: tuple(float(x) for x in opt(k, d).split(','))
        if '--views' in a:                                    # 4 test views + contact sheet at the given times
            from .preview import render_views
            base = os.path.splitext(out)[0]
            sheet = render_views(a[1], base, chain, float(opt('--total', 6)),
                                 [float(x) for x in opt('--views', '1').split(',')], size=int(opt('--size', 300)),
                                 dist=float(opt('--dist', 240)), target_z=float(opt('--target', 50)),
                                 cp0=v3('--cp0', '0,0,0'), cp1=v3('--cp1', '160,0,40'), cp0_vel=v3('--cp0-vel', '0,0,0'),
                                 figures=[tuple(float(x) for x in f.split(',')) for f in opt('--figure', '').split(';') if f])
            print(f'{sheet} + 4 GIF ({base}_clair.gif, _sombre, _clair_haut, _sombre_haut) — aperçu approximatif, '
                  f'PAS le rendu Source : seul GMod fait foi')
            return
        n = render(a[1], out, chain, float(opt('--total', 6)), float(opt('--elev', 12)), size=int(opt('--size', 360)),
                   dist=float(opt('--dist', 240)), target_z=float(opt('--target', 50)), cp0=v3('--cp0', '0,0,0'),
                   cp1=v3('--cp1', '160,0,40'), cp0_vel=v3('--cp0-vel', '0,0,0'), bg=v3('--bg', '70,72,78'),
                   azim_deg=float(opt('--azim', 0)),
                   figures=[tuple(float(x) for x in f.split(',')) for f in opt('--figure', '').split(';') if f])
        print(f'{out} ({n} images) — aperçu approximatif, PAS le rendu Source : seul GMod fait foi')
    elif cmd == 'analyze':
        from .analyze_pcf import report
        print(report(a[1], '--full' in a))
    elif cmd == 'inspect':
        from .validate import describe
        print(describe(a[1], '--ops' in a))
    elif cmd == 'install':
        from . import build as B
        spec = B.prepare(a[1], analyze_model=False)[0]; P = B.paths(spec)
        if not os.path.isdir(P['addon']): _fail(f"addon non généré : lancer d'abord generate {a[1]}")
        gm = a[a.index('--gmod') + 1] if '--gmod' in a else find_gmod()
        if not gm: _fail('GMod introuvable : relancer avec --gmod "<...>/GarrysMod/garrysmod"')
        dst = os.path.join(gm, 'addons', os.path.basename(P['addon']))
        shutil.rmtree(dst, ignore_errors=True); shutil.copytree(P['addon'], dst)
        print(f'Installé : {dst}')
    elif cmd == 'doctor':
        doctor()
    else:
        print(__doc__)


def find_gmod():
    cands = []
    if platform.system() == 'Windows':
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam'); steam = winreg.QueryValueEx(k, 'SteamPath')[0]
        except Exception: steam = r'C:\Program Files (x86)\Steam'
    else:
        steam = os.path.expanduser('~/.local/share/Steam')
    libs = [steam]; vdf = os.path.join(steam, 'steamapps', 'libraryfolders.vdf')
    if os.path.exists(vdf):
        import re
        libs += [p.replace('\\\\', '\\') for p in re.findall(r'"path"\s+"([^"]+)"', open(vdf, encoding='utf-8', errors='ignore').read())]
    for l in libs:
        g = os.path.join(l, 'steamapps', 'common', 'GarrysMod', 'garrysmod')
        if os.path.isdir(g): return g
    return None

def doctor():
    """Statuses: OK / MISSING / OPTIONAL (absent but not needed) / NOT TESTED."""
    def row(name, status, detail=''): print(f'{name:22s} {status:11s} {detail}')
    print(f'{"Python":22s} {"OK":11s} {platform.python_version()}')
    for mod, why in (('numpy', 'textures'), ('PIL', 'textures'), ('yaml', 'specs'), ('srctools', 'écriture PCF')):
        try: __import__(mod); row(mod, 'OK', why)
        except ImportError: row(mod, 'MISSING', 'pip install -r requirements.txt')
    try:
        from . import dsl
        row('Compilateur PCF', 'OK', f'{len(dsl.SCHEMA)} opérateurs connus (schema.json)')
    except Exception as e:
        row('Compilateur PCF', 'MISSING', str(e))
    try:
        from .textures import lib as TL
        row('Textures', 'OK', f'{len(TL.REG)} textures procédurales')
    except Exception as e:
        row('Textures', 'MISSING', str(e))
    row('Parseur MDL', 'OK', 'lecture studiohdr v44-49 + VVD (pcfforge/model)')
    row('ffmpeg', 'OK' if shutil.which('ffmpeg') else 'OPTIONAL', 'vidéo des captures')
    gm = find_gmod()
    row("Garry's Mod", 'OK' if gm else 'NOT FOUND', gm or 'requis seulement pour install / capture')
    row('Runtime GMod', 'NOT TESTED', 'runtime.lua non exécuté par pcfforge ; à tester en jeu')
    row('Captures', 'OK' if gm and platform.system() == 'Windows' else 'UNAVAILABLE', 'Windows + GMod requis')


if __name__ == '__main__':
    main(sys.argv[1:])
