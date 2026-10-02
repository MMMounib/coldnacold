"""Assemble l'archive AUTONOME du pack « Sarada — Mangekyō Sharingan / Ōhirume ».

    python examples/gen_sarada_ohirume.py
    python examples/package_sarada_ohirume.py            -> out/share/pcfforge_sarada_ohirume.zip

L'archive ne dépend ni de pcfforge, ni de Python : elle contient le PCF final, les matériaux VMT/VTF, les textures
PNG sources, le motif du Mangekyō, la documentation, les aperçus GIF (simulation hors moteur, annoncée comme telle) et
un chargeur Lua de 20 lignes pour Garry's Mod (game.AddParticles + précache + commande de test). Ce script vérifie
réellement le résultat (PCF relu, références de matériaux et de textures, structure de l'archive) et écrit les
statuts dans documentation/tests.md. Rien n'est déclaré testé s'il ne l'a pas été.
"""
import os
import re
import shutil
import sys
import zipfile

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'examples'))
os.chdir(ROOT)

from pcfforge import build as B, layers as LY                                   # noqa: E402
from pcfforge.preview import render                                            # noqa: E402
from pcfforge.textures import lib as TL, sarada as SA, vtf as VT               # noqa: E402
import gen_sarada_ohirume as G                                                  # noqa: E402

SPEC = 'examples/sarada_ohirume.yaml'
NAME = 'pcfforge_sarada_ohirume'
STAGE = os.path.join('out', 'pack', NAME)
ZIP = os.path.join('out', 'share', NAME + '.zip')

MAIN = ['sarada_aura', 'sarada_activate', 'sarada_eye', 'sarada_target', 'sarada_attract_trail',
        'ohirume_sphere', 'ohirume_projectile', 'ohirume_pull', 'ohirume_impact', 'ohirume_implosion',
        'ohirume_orbit', 'ohirume_float']
EXTRA = ['sarada_target_release', 'ohirume_sphere_s', 'ohirume_sphere_l', 'ohirume_sphere_end']
TEX_REQUIRED = ['sarada_core', 'sarada_glow', 'sarada_filament', 'sarada_spark', 'sarada_ring', 'sarada_void',
                'sarada_distort', 'sarada_fragment', 'sarada_streak', 'ohirume_core', 'ohirume_void', 'ohirume_ring',
                'ohirume_gravity', 'ohirume_streak', 'ohirume_fragment', 'ohirume_distort']

# aperçus GIF : (fichier, enchaînement, durée, caméra)
PREVIEWS = {
    'sarada_aura': dict(chain=[('sarada_aura', 0, None)], total=3, dist=130, target_z=36, figures=[(0, 0, 0)]),
    'sarada_activate': dict(chain=[('sarada_activate', 0, None), ('sarada_aura', .45, None)], total=1.8, dist=140,
                            target_z=36, figures=[(0, 0, 0)]),
    'sarada_eye': dict(chain=[('sarada_eye', 0, None)], total=1.6, dist=12, target_z=0),
    'sarada_target': dict(chain=[('sarada_target', 0, 2.2, 2.2), ('sarada_target_release', 2.2, None)], total=2.8,
                          dist=140, target_z=36, figures=[(0, 0, 0)]),
    'sarada_attract_trail': dict(chain=[('sarada_attract_trail', 0, None)], total=1.5, dist=170, target_z=36,
                                 cp0=(-120, 0, 36), cp0_vel=(180, 0, 0)),
    'ohirume_sphere': dict(chain=[('ohirume_sphere', 0, 2.4, 2.4), ('ohirume_sphere_end', 2.4, None)], total=2.9,
                           dist=110, target_z=0),
    'ohirume_projectile': dict(chain=[('ohirume_projectile', 0, None)], total=1.7, dist=200, target_z=40,
                               cp0=(-100, 0, 40), cp1=(100, 0, 40), figures=[(100, 0, 0)]),
    'ohirume_pull': dict(chain=[('ohirume_pull', 0, None), ('ohirume_sphere', 0, None)], total=2.2, dist=220,
                         target_z=40, cp0=(-80, 0, 50), cp1=(90, 0, 40), figures=[(90, 0, 0)]),
    'ohirume_impact': dict(chain=[('ohirume_impact', 0, None)], total=.8, dist=110, target_z=0),
    'ohirume_implosion': dict(chain=[('ohirume_implosion', 0, None)], total=1.3, dist=130, target_z=0),
    'ohirume_orbit': dict(chain=[('ohirume_orbit', 0, None)], total=4.2, dist=170, target_z=40, figures=[(0, 0, 0)]),
    'ohirume_float': dict(chain=[('ohirume_float', 0, None)], total=2.5, dist=110, target_z=20, figures=[(0, 0, 8)]),
}

LOADER = '''-- sarada_ohirume : charge le PCF du pack et le précache. Aucune autre logique de jeu.
game.AddParticles("particles/sarada_ohirume.pcf")
{precache}

if CLIENT then
	-- Test : sarada_ohirume_test <particule> [secondes]  (devant soi ; CP1 = 160 u plus loin pour pull / projectile)
	concommand.Add("sarada_ohirume_test", function(ply, _, args)
		local name = args[1] or "ohirume_sphere"
		local dur = tonumber(args[2] or "") or 4
		local tr = ply:GetEyeTrace()
		local pos = tr.HitPos + tr.HitNormal * 2
		local fwd = ply:GetAimVector(); fwd.z = 0; fwd:Normalize()
		local start = pos
		if name:find("^ohirume_") and not name:find("orbit") and not name:find("float") then start = pos + Vector(0, 0, 40) end
		local fx = CreateParticleSystemNoEntity(name, start, Angle(0, 0, 0))
		if not IsValid(fx) then print("sarada_ohirume : particule inconnue " .. name) return end
		fx:SetControlPoint(1, start + fwd * 160)
		timer.Simple(dur, function() if IsValid(fx) then fx:StopEmissionAndDestroyImmediately() end end)
	end, function(cmd) local t = {{}} for _, n in ipairs({{{names}}}) do t[#t + 1] = cmd .. " " .. n end return t end)
end
'''


def rm(p):
    shutil.rmtree(p, ignore_errors=True)


def build_pack():
    spec, P, tex, rep = B.build(SPEC)
    if rep['errors']:
        raise SystemExit('build : ' + ' | '.join(rep['errors']))
    rm(STAGE); os.makedirs(STAGE)
    # particules + matériaux (chemins Source réels)
    os.makedirs(os.path.join(STAGE, 'particles'))
    shutil.copy(P['pcf'], os.path.join(STAGE, 'particles', 'sarada_ohirume.pcf'))
    shutil.copytree(P['mat'], os.path.join(STAGE, 'materials', 'sarada_ohirume'))
    # textures PNG sources (planches telles qu'écrites dans les VTF)
    tdir = os.path.join(STAGE, 'textures', 'sarada_ohirume'); os.makedirs(tdir)
    for n in sorted(SA.REG):
        shutil.copy(os.path.join(P['png'], n + '.png'), tdir)
    mangekyo()
    # Hammer : manifeste d'exemple
    open(os.path.join(STAGE, 'particles', 'sarada_ohirume_manifest_example.txt'), 'w', encoding='utf-8').write(
        '// A fusionner dans garrysmod/particles/particles_manifest.txt (voir documentation/README.md)\n'
        'particles_manifest\n{\n\t"file"\t"particles/sarada_ohirume.pcf"\n}\n')
    # chargeur GMod (addon)
    ldir = os.path.join(STAGE, 'lua', 'autorun'); os.makedirs(ldir)
    roots = list(rep['roots'])
    open(os.path.join(ldir, 'sarada_ohirume_particles.lua'), 'w', encoding='utf-8').write(LOADER.format(
        precache='\n'.join(f'PrecacheParticleSystem("{r}")' for r in roots),
        names=', '.join(f'"{r}"' for r in roots)))
    open(os.path.join(STAGE, 'addon.json'), 'w', encoding='utf-8').write(
        '{\n\t"title": "Sarada - Mangekyou Sharingan / Ohirume (particules)",\n\t"type": "effects",\n'
        '\t"tags": ["fun"],\n\t"ignore": ["documentation/*", "preview/*", "textures/*"]\n}\n')
    previews()
    return spec, P, rep


def mangekyo():
    d = os.path.join(STAGE, 'textures', 'sarada'); os.makedirs(d, exist_ok=True)
    S = 1024
    for part, fname in (('color', 'mangekyo_sarada.png'), ('mask', 'mangekyo_sarada_mask.png'),
                        ('emissive', 'mangekyo_sarada_emissive.png')):
        c, a = SA.mangekyo(S * 2, part)
        rgba = np.dstack([np.clip(c, 0, 1), np.clip(a, 0, 1)])
        im = Image.fromarray((rgba * 255 + .5).astype(np.uint8), 'RGBA').resize((S, S), Image.LANCZOS)
        if part == 'mask':                                   # masque : niveaux de gris opaques
            g = np.asarray(im, np.float32)[..., 3]
            im = Image.fromarray(g.astype(np.uint8), 'L')
        im.save(os.path.join(d, fname))
    # version Source (512, VTF + VMT UnlitGeneric translucide) pour un usage direct (décal, overlay, test)
    c, a = SA.mangekyo(1024, 'color')
    rgba = (np.dstack([np.clip(c, 0, 1), np.clip(a, 0, 1)]) * 255 + .5).astype(np.uint8)
    rgba = np.asarray(Image.fromarray(rgba, 'RGBA').resize((512, 512), Image.LANCZOS))
    VT.write(os.path.join(STAGE, 'materials', 'sarada_ohirume', 'mangekyo_sarada.vtf'), rgba)
    open(os.path.join(STAGE, 'materials', 'sarada_ohirume', 'mangekyo_sarada.vmt'), 'w', newline='\r\n').write(
        '"UnlitGeneric"\n{\n\t"$basetexture" "sarada_ohirume/mangekyo_sarada"\n\t"$translucent" "1"\n}\n')


def previews():
    d = os.path.join(STAGE, 'preview'); os.makedirs(d)
    for name, c in PREVIEWS.items():
        c = dict(c); chain = c.pop('chain'); total = c.pop('total')
        render(SPEC, os.path.join(d, name + '.gif'), chain, total, elev_deg=14, size=320, fps=15,
               bg=(118, 120, 126), **c)
    open(os.path.join(d, 'README.md'), 'w', encoding='utf-8').write(
        '# Aperçus\n\nPreview Source Engine : **NOT EXECUTED** (aucun Garry\'s Mod / Source disponible ici).\n\n'
        'Les GIF de ce dossier sont une **simulation hors moteur** (outil interne `pcfforge preview`) : elle rejoue '
        'l\'émission, les durées de vie, les mouvements, les tailles, les fondus, les rotations et les planches '
        'animées avec les vraies textures, sur un fond gris moyen (proche d\'une map de jour). Elle ne reproduit ni l\'éclairage, ni le tri exact, ni '
        'les cordes texturées (dessinées en trait doux de la couleur de leur texture) de Source. Seul le jeu fait '
        'foi.\n')


# ------------------------------------------------------------------ vérifications réelles
def checks(spec, rep):
    from srctools.dmx import Element
    from pcfforge.validate import validate
    res = []
    pcf = os.path.join(STAGE, 'particles', 'sarada_ohirume.pcf')
    # 1. syntaxe : relu par srctools (DMX binaire) + validateur pcfforge (opérateurs connus, enfants, format)
    try:
        root, fmt, ver = Element.parse(open(pcf, 'rb'))
        errs, info = validate(pcf)
        ok = (fmt == 'pcf' and not errs)
        res.append(('PCF syntax', ok, f'DMX binaire v2, format {fmt} {ver} ; {info.splitlines()[0] if info else ""}'
                                      + (f' ; erreurs : {errs}' if errs else '')))
    except Exception as e:                                     # pragma: no cover
        res.append(('PCF syntax', False, repr(e))); return res
    systems = list(root['particleSystemDefinitions'].iter_elem())
    names = {s.name: s for s in systems}
    visible = sorted(s.name for s in systems if not s['preventNameBasedLookup'].val_bool)
    want = MAIN + EXTRA
    missing = [n for n in want if n not in names]
    bad = [s.name for s in systems if not any(True for _ in s['renderers'].iter_elem())]
    res.append(('Particle definitions', not missing and not bad and sorted(want) == visible,
                f'{len(systems)} systèmes, {len(visible)} appelables par nom : ' + ', '.join(visible)
                + (f' ; manquants : {missing}' if missing else '') + (f' ; sans rendu : {bad}' if bad else '')))
    # 2. matériaux référencés par le PCF -> VMT présents dans l'archive
    mats = sorted({s['material'].val_str.replace('\\', '/') for s in systems})
    miss_vmt = [m for m in mats if not os.path.exists(os.path.join(STAGE, 'materials', m))]
    res.append(('Material references', not miss_vmt, f'{len(mats)} matériaux référencés, tous présents'
                if not miss_vmt else f'manquants : {miss_vmt}'))
    # 3. VMT -> $basetexture -> VTF
    vmts = [os.path.join(dp, f) for dp, _, fs in os.walk(os.path.join(STAGE, 'materials')) for f in fs if f.endswith('.vmt')]
    bad_vmt, vtfs = [], []
    for v in vmts:
        txt = open(v, encoding='utf-8').read()
        m = re.search(r'"\$basetexture"\s+"([^"]+)"', txt, re.I)
        shader = txt.strip().split('\n')[0].strip('" \r')
        if not m or shader not in ('SpriteCard', 'UnlitGeneric'):
            bad_vmt.append(os.path.basename(v)); continue
        vt = os.path.join(STAGE, 'materials', m.group(1) + '.vtf')
        if not os.path.exists(vt):
            bad_vmt.append(os.path.basename(v) + ' -> ' + m.group(1)); continue
        vtfs.append(vt)
    res.append(('VMT references', not bad_vmt, f'{len(vmts)} VMT, shader et $basetexture valides'
                if not bad_vmt else f'défauts : {bad_vmt}'))
    # 4. textures : chaque VTF se relit (en-tête, dimensions, planche pour les planches)
    bad_vtf = []
    for vt in vtfs:
        try:
            w, h, fmt = read_vtf(vt)
            if w & (w - 1) or h & (h - 1):
                bad_vtf.append(os.path.basename(vt) + ' (pas une puissance de 2)')
        except Exception as e:
            bad_vtf.append(f'{os.path.basename(vt)} ({e!r})')
    pngs = os.listdir(os.path.join(STAGE, 'textures', 'sarada_ohirume'))
    miss_png = [n for n in SA.REG if n + '.png' not in pngs]
    miss_req = [n for n in TEX_REQUIRED if not os.path.exists(os.path.join(STAGE, 'materials', 'sarada_ohirume', n + '.vtf'))]
    res.append(('Texture references', not bad_vtf and not miss_png and not miss_req,
                f'{len(vtfs)} VTF relus (7.4, puissances de 2), {len(pngs)} PNG sources ; les 16 textures demandées sont '
                'présentes' if not (bad_vtf or miss_png or miss_req) else f'défauts : {bad_vtf} {miss_png} {miss_req}'))
    # 5. ressources manquantes : tout matériau / texture / fichier attendu
    expected = ['particles/sarada_ohirume.pcf', 'lua/autorun/sarada_ohirume_particles.lua', 'addon.json',
                'textures/sarada/mangekyo_sarada.png', 'textures/sarada/mangekyo_sarada_mask.png',
                'textures/sarada/mangekyo_sarada_emissive.png', 'documentation/README.md',
                'documentation/techniques.md', 'documentation/particle_list.md', 'preview/README.md']
    expected += [f'preview/{n}.gif' for n in PREVIEWS]
    miss = [e for e in expected if not os.path.exists(os.path.join(STAGE, e))]
    res.append(('Missing resources', not miss_vmt and not bad_vmt and not bad_vtf and not miss,
                'aucune' if not miss else f'manquants : {miss}'))
    return res


def read_vtf(path):
    """Relit réellement un VTF : planches BGRA8888 (lecteur pcfforge, avec la ressource de planche) ou DXT5
    (srctools, image décodée). Renvoie (largeur, hauteur, format)."""
    try:
        _, info = VT.read(path)
        return info['width'], info['height'], 'BGRA8888' + (' + planche' if info['sheet'] else '')
    except ValueError as e:
        if 'not supported' not in str(e):
            raise
    from srctools.vtf import VTF
    with open(path, 'rb') as f:
        v = VTF.read(f)
        v.load()
        v.get().to_PIL()                                   # décode réellement l'image
    return v.width, v.height, str(v.format)


def archive_check():
    with zipfile.ZipFile(ZIP) as z:
        names = z.namelist(); bad = z.testzip()
    need = [f'{NAME}/{p}' for p in ('particles/sarada_ohirume.pcf', 'materials/sarada_ohirume/ohirume_void.vmt',
                                     'textures/sarada/mangekyo_sarada.png', 'documentation/README.md',
                                     'documentation/techniques.md', 'documentation/particle_list.md',
                                     'documentation/tests.md', 'preview/ohirume_sphere.gif', 'addon.json',
                                     'lua/autorun/sarada_ohirume_particles.lua')]
    miss = [n for n in need if n not in names]
    return ('Archive structure', bad is None and not miss,
            f'{len(names)} fichiers, CRC OK, dossier racine {NAME}/' if not miss and bad is None
            else f'manquants : {miss}, CRC : {bad}')


def write_tests(res):
    L = ['# Résultats des tests', '', 'Vérifications exécutées par `examples/package_sarada_ohirume.py` sur les fichiers '
         'de cette archive (pas sur les sources).', '', '```text']
    for name, ok, _ in res:
        L.append(f'{name + " ":.<26} {"PASS" if ok else "FAIL"}')
    L += [f'{"GMod runtime ":.<26} NOT EXECUTED', f'{"Preview Source Engine ":.<26} NOT EXECUTED',
          f'{"Hammer++ ":.<26} NOT EXECUTED', '```', '', '## Détails', '']
    for name, ok, det in res:
        L.append(f'- **{name}** — {"PASS" if ok else "FAIL"} : {det}')
    L += ['- **GMod runtime** — NOT EXECUTED : aucun Garry\'s Mod dans l\'environnement de production. Le format du PCF '
          'est celui de l\'éditeur de particules de Valve (DMX binaire v2), relu sans erreur, mais l\'affichage réel '
          'n\'a pas été vu.',
          '- **Preview Source Engine** — NOT EXECUTED : les GIF de `preview/` sont une simulation hors moteur.',
          '- **Hammer++** — NOT EXECUTED.', '']
    open(os.path.join(STAGE, 'documentation', 'tests.md'), 'w', encoding='utf-8').write('\n'.join(L))


def zip_stage():
    os.makedirs(os.path.dirname(ZIP), exist_ok=True)
    if os.path.exists(ZIP):
        os.remove(ZIP)
    with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED) as z:
        for base, _, files in os.walk(STAGE):
            for f in sorted(files):
                full = os.path.join(base, f)
                z.write(full, os.path.relpath(full, os.path.dirname(STAGE)))


def main():
    spec, P, rep = build_pack()
    import docs_sarada_ohirume as D
    D.write(os.path.join(STAGE, 'documentation'), spec, rep)
    res = checks(spec, rep)
    write_tests(res + [('Archive structure', True, 'vérifiée après compression (voir ci-dessous)')])
    zip_stage()
    arch = archive_check()
    res.append(arch)
    write_tests(res)                                           # statut final, puis archive définitive
    zip_stage()
    for name, ok, det in res:
        print(f'{name + " ":.<26} {"PASS" if ok else "FAIL"}   {det[:110]}')
    print(f'{"GMod runtime ":.<26} NOT EXECUTED')
    print(ZIP, os.path.getsize(ZIP) // 1024, 'Ko')
    return 0 if all(ok for _, ok, _ in res) else 1


if __name__ == '__main__':
    sys.exit(main())
