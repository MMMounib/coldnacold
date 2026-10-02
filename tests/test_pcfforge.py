"""pcfforge V3 tests (positive and negative). Run: python -m pytest -q tests"""
import copy
import glob
import os
import shutil

import pytest

from pcfforge import build as B, compose as CO, dsl, effect as EF, layers as LY, motions as MO, parse as PA
from pcfforge import variation as VA, validate as VL
from pcfforge.model import analyze as AN, mdl
from pcfforge.textures import lib as TL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EX = os.path.join(ROOT, 'examples')
MDL = os.path.join(ROOT, 'tests', 'fixtures', 'hiramekarei', 'models', 'models', 'naruto', 'unique_props',
                   'unique_props', 'fsc', 'hiramekarai.mdl')
V3 = ['chakra_aura', 'chakra_burst', 'chakra_projectile', 'chakra_impact', 'energy_vortex', 'energy_trail',
      'hiramekarei_aura']


def base(**kw):
    d = dict(id='t_fx', style={'type': 'chakra', 'color': [100, 200, 255]}, shape={'type': 'aura'})
    d.update(kw)
    return d


@pytest.fixture(scope='session')
def built(tmp_path_factory):
    out = str(tmp_path_factory.mktemp('out'))
    return {n: B.build(os.path.join(EX, n + '.yaml'), out) for n in V3}


# ------------------------------------------------------------------ DSL / schema
def test_schema_loaded():
    assert len(dsl.SCHEMA) >= 99
    assert all(v['__lists__'] for v in dsl.SCHEMA.values())


def test_op_element_ok_and_case_insensitive():
    el = dsl.op_element('operators', 'Lifespan Decay', {})
    assert el['functionName'].val_str == 'Lifespan Decay'


def test_op_element_unknown_operator():
    with pytest.raises(KeyError):
        dsl.op_element('operators', 'Made Up Operator', {})


def test_op_element_wrong_list():
    with pytest.raises(ValueError):
        dsl.op_element('renderers', 'Lifespan Decay', {})


def test_op_element_unknown_attribute():
    with pytest.raises(KeyError):
        dsl.op_element('operators', 'Lifespan Decay', {'not an attribute': 1})


def test_registry_rejects_duplicates():
    reg = dsl.Registry()
    s = dsl.Sys('x_a', 'm/t', 4, [])
    reg.add(s)
    with pytest.raises(Exception):
        reg.add(s)


# ------------------------------------------------------------------ spec validation (negative)
@pytest.mark.parametrize('patch, msg', [
    ({'id': 'Bad-Id'}, 'id'),
    ({'unknown_key': 1}, 'clés inconnues'),
    ({'mode': 'magic'}, 'mode inconnu'),
    ({'style': {'type': 'goo'}}, 'style.type'),
    ({'style': {'type': 'chakra', 'color': [300, 0, 0]}}, 'style.color'),
    ({'style': {'type': 'chakra', 'look': ['weird']}}, 'style.look'),
    ({'style': {'type': 'chakra', 'intensity': 2}}, 'hors limites'),
    ({'shape': {'type': 'cube'}}, 'shape.type'),
    ({'behavior': {'motion': 'teleport'}}, 'motion inconnue'),
    ({'variation': {'wobble': .2}}, 'variation inconnue'),
    ({'variation': {'scale': 3}}, 'entre 0 et 1'),
    ({'layers': [{'preset': 'nope'}]}, 'preset inconnu'),
    ({'layers': [{'size': 3}]}, 'preset ou tex'),
    ({'timeline': [{'phase': 'dance', 'duration': 1}]}, 'phase inconnue'),
    ({'timeline': [{'phase': 'charge'}]}, 'duration manquante'),
    ({'timeline': [{'phase': 'charge', 'duration': 1, 'scale': {'mass': 2}}]}, 'scale inconnu'),
    ({'performance': {'quality': 'insane'}}, 'quality'),
    ({'attachment': {'type': 'socket'}}, 'attachment.type'),
    ({'attachment': {'type': 'bone'}}, 'name obligatoire'),
    ({'attachment': {'type': 'bone', 'name': 'RightHand'}}, 'model.path obligatoire'),
])
def test_normalize_rejects(patch, msg):
    with pytest.raises(EF.SpecError, match=msg):
        EF.normalize(base(**patch))


def test_missing_file():
    with pytest.raises(EF.SpecError):
        EF.load('does/not/exist.yaml')


# ------------------------------------------------------------------ auto mode
def test_auto_mode():
    assert EF.resolve_mode(base()) == 'standalone'
    assert EF.resolve_mode(base(attachment={'type': 'bone', 'name': 'x'})) == 'model_driven'
    assert EF.resolve_mode(base(model={'path': 'a.mdl'})) == 'model_driven'
    assert EF.resolve_mode(base(attachment={'type': 'bounds'})) == 'standalone'


# ------------------------------------------------------------------ standalone composition + PCF
@pytest.mark.parametrize('name', V3)
def test_examples_build_and_validate(built, name):
    spec, P, tex, rep = built[name]
    assert rep['errors'] == []
    errs, _ = VL.validate(P['pcf'])
    assert errs == []
    assert os.path.exists(os.path.join(P['addon'], 'lua', 'autorun', f'pcfforge_{name}.lua'))
    assert os.path.exists(os.path.join(P['addon'], 'lua', 'pcfforge', 'runtime.lua'))
    for t in tex:
        assert os.path.exists(os.path.join(P['mat'], t + '.vtf'))
        assert os.path.exists(os.path.join(P['mat'], t + '.vmt'))


def test_standalone_needs_no_model(built):
    rep = built['chakra_aura'][3]
    assert rep['mode'] == 'standalone' and rep['segment'] is None


def test_composition_hierarchy():
    spec, runtime, notes = CO.compose(EF.normalize(base()))
    layers = spec['systems']['main']['layers']
    assert layers[0]['role'] == 'core'
    roles = {L['role'] for L in layers}
    assert {'core', 'filaments'} <= roles and len(roles) >= 3


@pytest.mark.parametrize('shape', ['aura', 'burst', 'projectile', 'impact', 'vortex', 'trail', 'beam'])
def test_every_shape_composes(shape):
    spec, _, _ = CO.compose(EF.normalize(base(shape={'type': shape})))
    reg, roots, infos, peaks = LY.build(spec, {n: TL.meta(n) for n in B.used_textures(spec)})
    errs, _ = B.lint(spec, reg, roots, peaks, 400)
    assert errs == []


def test_budget_trims():
    big, _, _ = CO.compose(EF.normalize(base(shape={'type': 'vortex'}, performance={'max_particles': 5000})))
    small, _, notes = CO.compose(EF.normalize(base(shape={'type': 'vortex'}, performance={'max_particles': 40})))
    peak = lambda s: sum(CO._peak(L) for L in s['systems']['main']['layers'])
    assert peak(small) < peak(big)


def test_quality_changes_density():
    lo, _, _ = CO.compose(EF.normalize(base(performance={'quality': 'low'})))
    hi, _, _ = CO.compose(EF.normalize(base(performance={'quality': 'ultra'})))
    assert len(lo['systems']['main']['layers']) <= len(hi['systems']['main']['layers'])


def test_look_changes_structure():
    ids = lambda look: [L['role'] for L in CO.compose(EF.normalize(base(style={'type': 'chakra', 'look': look})))[0]
                        ['systems']['main']['layers']]
    assert 'secondary' in ids(['mystical']) and 'secondary' not in ids(['minimal'])
    held = CO.compose(EF.normalize(base(shape={'type': 'burst'}, style={'type': 'chakra', 'look': ['anime']})))[0]
    assert any(L.get('hold') for L in held['systems']['main']['layers'])   # anime: hold then cut


# ------------------------------------------------------------------ phases
def test_phases_in_burst(built):
    spec = built['chakra_burst'][0]
    ph = spec['systems']['main']['phases']
    assert list(ph) == ['charge', 'release', 'aftermath']


def test_timeline_order_and_start():
    t = LY.timeline([{'phase': 'charge', 'duration': .3}, {'phase': 'release', 'duration': .2}])
    assert t['release']['start'] == pytest.approx(.3)


def test_timeline_negative_duration():
    with pytest.raises(ValueError):
        LY.timeline([{'phase': 'charge', 'duration': -1}])


def test_phase_used_but_missing():
    d = base(shape={'type': 'burst'}, timeline=[{'phase': 'charge', 'duration': .3}])
    with pytest.raises(ValueError, match='absentes de la timeline'):
        CO.compose(EF.normalize(d))


# ------------------------------------------------------------------ motions
@pytest.mark.parametrize('m', [m for m in MO.MOTIONS if m not in ('static', 'follow')])
def test_every_motion_emits_operators(m):
    ops, moving = MO.ops({'motion': m, 'radius': 20, 'speed': [60, 90]})
    assert ops or (m == 'radial_burst' and moving)     # radial_burst reuses the layer's own velocity
    for kind, fn, params in ops:
        dsl.op_element(kind, fn, params)             # real, correctly placed operators


def test_motion_composition_and_turbulence():
    ops, _ = MO.ops({'motion': ['orbit', {'type': 'rise', 'speed': 2, 'turbulence': .5}]})
    fns = {fn for _, fn, _ in ops}
    assert len(fns) >= 2


def test_unknown_motion():
    with pytest.raises(ValueError):
        MO.normalize(['orbit', 'teleport'])


# ------------------------------------------------------------------ variation
def test_widen():
    assert VA.widen([10, 10], .2) == pytest.approx([8, 12])   # 0.2 = ±20 %
    assert VA.widen([10, 20], 0) == [10, 20]


def test_variation_apply():
    L = dict(size=[10, 10], life=[1, 1], alpha=[200, 200], variation={'scale': .3, 'lifetime': .2, 'rotation': .5,
                                                                        'emission': .4})
    VA.apply(L)
    assert L['size'][0] < 10 < L['size'][1] and L['life'][1] > 1 and L['rot'] and L['alpha'][1] <= 255


@pytest.mark.parametrize('v', [{'x': .1}, {'scale': -1}, 'a'])
def test_variation_rejects(v):
    with pytest.raises(ValueError):
        VA.check(v)


# ------------------------------------------------------------------ textures
@pytest.mark.parametrize('name', ['glow', 'glow_hard', 'spark', 'smoke', 'flame', 'streak', 'ring',
                                  'slash', 'dust', 'noise', 'energy'])
def test_texture_families(name):
    if name not in TL.REG:
        pytest.skip(f'{name} absent de la bibliothèque')
    t = TL.make(name)
    cols, rows = t['grid']
    assert t['img'].size == (t['S'] * cols, t['S'] * rows)
    assert t['img'].getextrema()[3][1] > 0             # not empty


def test_energy_is_flipbook():
    m = TL.meta('energy')
    assert m['grid'][0] * m['grid'][1] == 8 and len(m['seqs'][0]) == 8


def test_unknown_texture(tmp_path):
    spec = {'prefix': 'x', 'systems': {'a': [{'tex': 'no_such_texture'}]}}
    with pytest.raises(ValueError, match='texture inconnue'):
        B.textures(spec, B.paths(spec, str(tmp_path)))


# ------------------------------------------------------------------ model (real Hiramekarei file)
def test_real_mdl_parse():
    m = mdl.read(MDL)
    assert m.version == 48
    assert [b.name for b in m.bones][-1] == 'RightHand' and len(m.bones) == 8
    assert len(m.attachments) == 0 and len(m.hitboxes) == 1
    assert len(m.vertices) == 714


def test_real_mdl_blade_region():
    seg = AN.region(mdl.read(MDL), {'hitbox_bone': 'RightHand', 'start': 0.05, 'end': 0.98})
    assert seg['bone'] == 'RightHand' and seg['source'] == 'vertices'
    assert 45 < seg['length'] < 60


def test_region_adapts_to_fraction():
    m = mdl.read(MDL)
    full = AN.region(m, {'bone': 'RightHand'})['length']
    half = AN.region(m, {'bone': 'RightHand', 'start': 0, 'end': .5})['length']
    assert half == pytest.approx(full / 2, rel=.02)


def test_hiramekarei_model_driven(built):
    spec, P, tex, rep = built['hiramekarei_aura']
    assert rep['mode'] == 'model_driven' and rep['segment']['bone'] == 'RightHand'
    lua = open(os.path.join(P['addon'], 'lua', 'autorun', 'pcfforge_hiramekarei_aura.lua'), encoding='utf-8').read()
    assert 'bone = "RightHand"' in lua and 'type = "region"' in lua


@pytest.mark.parametrize('att, regions, msg', [
    ({'type': 'bone', 'name': 'Blade'}, None, 'os introuvable'),
    ({'type': 'attachment', 'name': 'muzzle'}, None, 'attachment introuvable'),
    ({'type': 'region', 'name': 'blade'}, None, 'région non définie'),
    ({'type': 'region', 'name': 'blade'}, {'blade': {'bone': 'RightHand', 'start': .8, 'end': .2}}, 'start < end'),
])
def test_model_negative(att, regions, msg):
    with pytest.raises(mdl.ModelError, match=msg):
        AN.resolve(MDL, att, regions)


def test_model_errors(tmp_path):
    with pytest.raises(mdl.ModelError, match='introuvable'):
        mdl.read(str(tmp_path / 'none.mdl'))
    bad = tmp_path / 'bad.mdl'
    bad.write_bytes(b'NOPE' + b'\0' * 400)
    with pytest.raises(mdl.ModelError, match='pas un fichier MDL'):
        mdl.read(str(bad))
    trunc = tmp_path / 'trunc.mdl'
    trunc.write_bytes(open(MDL, 'rb').read()[:600])
    with pytest.raises(mdl.ModelError):
        mdl.read(str(trunc))


def test_spec_with_missing_model():
    d = base(attachment={'type': 'bone', 'name': 'RightHand'}, model={'path': 'missing.mdl'})
    with pytest.raises(EF.SpecError, match='introuvable'):
        EF.normalize(d)


# ------------------------------------------------------------------ parser
def test_parse_simple():
    spec, unresolved = PA.parse('aura de chakra bleu qui tourne autour du joueur, élégant')
    assert spec['shape']['type'] == 'aura' and spec['style']['type'] == 'chakra'
    assert spec['style']['color'] == [80, 160, 255] and 'elegant' in spec['style']['look']
    assert spec['behavior']['motion'] == 'orbit' and unresolved == []
    EF.normalize(spec)


def test_parse_word_start_only():
    spec, _ = PA.parse('un eclair rouge')
    assert spec['style']['type'] == 'lightning'


def test_parse_reports_unknowns():
    spec, unresolved = PA.parse('un truc stylé')
    assert any('forme' in u for u in unresolved) and any('couleur' in u for u in unresolved)


def test_parse_model_words():
    spec, unresolved = PA.parse("aura sur la lame de l'arme, chakra bleu")
    assert spec['attachment'] == {'type': 'region', 'name': 'blade'}
    assert any('.mdl' in u for u in unresolved)


# ------------------------------------------------------------------ PCF validator
def test_validator_detects_bad_pcf(tmp_path):
    p = tmp_path / 'x.pcf'
    p.write_bytes(b'garbage')
    errs, _ = VL.validate(str(p))
    assert errs


# ------------------------------------------------------------------ silhouette (real Hiramekarei geometry)
def test_profile_follows_blade_shape():
    seg = AN.region(mdl.read(MDL), {'hitbox_bone': 'RightHand', 'start': .15, 'end': .99})
    sl = seg['profile']['slices']
    assert len(sl) == 9
    widths = [s['half_width'] for s in sl]
    assert max(widths) > 12 and widths[-1] < max(widths)          # fins / body wider than the head tip


def test_envelope_scales_and_counts():
    seg = AN.region(mdl.read(MDL), {'hitbox_bone': 'RightHand', 'start': .15, 'end': .99})
    pts, ranges, half = CO.envelope(seg, 1.5, 4)
    o0, o1 = ranges['outline']
    f0, f1 = ranges['fill']
    assert o0 == 2 and f1 == 1 + len(pts) <= 63                    # GMod control points 0-63
    assert pts[0] == pts[o1 - 2]                                   # closed outline
    base = sum(s['half_width'] for s in seg['profile']['slices']) / len(seg['profile']['slices'])
    assert half > base * 1.4


def test_chain_shape_uses_random_cp_pairs():
    ops = LY.layer_ops(dict(tex='glow', rate=5, shape='chain', cp=2, cp_end=10), {}, {'glow': TL.meta('glow')})
    path = [p for k, fn, p in ops if fn == 'Position Along Path Random'][0]
    assert path['randomly select sequential CP pairs between start and end points'] is True
    assert path['end control point number'] == 10


def test_hiramekarei_uses_silhouette(built):
    spec, P, tex, rep = built['hiramekarei_aura']
    assert rep['control_points'] and rep['control_points'] <= 64
    assert {'chakra_tongue', 'chakra_body'} <= set(tex)
    lua = open(os.path.join(P['addon'], 'lua', 'autorun', 'pcfforge_hiramekarei_aura.lua'), encoding='utf-8').read()
    assert 'points = { Vector(' in lua


def test_silhouette_can_be_disabled():
    d = EF.load(os.path.join(EX, 'hiramekarei_aura.yaml'))
    d['shape'] = dict(d['shape'], silhouette=False)
    spec, runtime, _ = CO.compose(d)
    assert 'points' not in runtime


def test_anime_aura_has_no_glow_disc():
    spec, _, _ = CO.compose(EF.normalize(base()))
    core = spec['systems']['main']['layers'][0]
    assert core['tex'] == 'chakra_body' and core.get('count') is None


# ------------------------------------------------------------------ in-game lessons (30/09/2026)
def test_sheet_vtf_uses_validated_layout(tmp_path):
    t = TL.make('chakra_tongue')
    TL.export('chakra_tongue', t, str(tmp_path / 'm'), str(tmp_path / 'p'))
    from pcfforge.textures import vtf as VT
    _, info = VT.read(str(tmp_path / 'm' / 'chakra_tongue.vtf'))
    assert info['version'] == '7.4' and info['sheet'] is not None
    clamp, frames = info['sheet'][0]
    assert clamp == 0 and len(frames) == 8                        # flames loop


def test_flipbook_rate_not_fit_lifetime():
    ops = LY.layer_ops(dict(tex='energy', rate=5, life=[.4, .6]), {}, {'energy': TL.meta('energy')})
    r = [p for k, fn, p in ops if fn == 'render_animated_sprites'][0]
    assert r['animation_fit_lifetime'] is False and r['animation rate'] == pytest.approx(2.0)


def test_hiramekarei_is_attached_and_sober(built):
    spec = built['hiramekarei_aura'][0]
    layers = spec['systems']['main']['layers']
    for L in layers:
        if L['id'] != 'motes':
            assert L.get('attach') == 'rotation' and L.get('lock_cp') == 0
    assert built['hiramekarei_aura'][3]['roots']['hiramekarei_aura_main']['peak'] <= 120


def test_contour_streaks_keep_their_timing(built):
    layers = {L['id']: L for L in built['hiramekarei_aura'][0]['systems']['main']['layers']}
    a, b = layers['streak'], layers['streak2']
    assert a['shape'] == 'chain_seq' and a['render'] == 'rope' and 'variation' not in a
    assert a['rate'] == pytest.approx(64 / 1.8) and b['delay'] == pytest.approx(.9)


# ------------------------------------------------------------------ Berserk sword (real MDL v49, low-poly blade)
BERSERK = os.path.join(ROOT, 'tests', 'fixtures', 'berserk', 'models', 'face', 'sword_persee.mdl')


def test_real_mdl_v49():
    m = mdl.read(BERSERK)
    assert m.version == 49 and [b.name for b in m.bones] == ['root'] and len(m.vertices) == 7703


def test_lowpoly_blade_profile_is_interpolated_not_guessed():
    seg = AN.region(mdl.read(BERSERK), {'bone': 'root', 'start': .32, 'end': 1.0})
    sl = seg['profile']['slices']
    assert sl[0]['half_width'] < 3.5                 # narrow base, not the guard nor the wide blade
    assert max(s['half_width'] for s in sl) > 5.5    # broad blade
    assert all(s['thickness'] > 0 for s in sl)


def test_berserk_demonic_aura():
    spec, P, tex, rep = B.build(os.path.join(EX, 'berserk_aura.yaml'), os.path.join(ROOT, 'out'))
    assert rep['errors'] == [] and rep['control_points'] <= 64
    layers = {L['id']: L for L in spec['systems']['main']['layers']}
    assert {'miasma', 'spikes', 'crackles'} <= set(layers)                                # its own language
    assert layers['miasma']['tex'] == 'miasma' and layers['spikes']['tex'] == 'ink_spike'
    assert layers['crack']['render'] == 'rope' and 'pulse_alpha' in layers['crack']
    assert layers['crack']['cp'] != layers['crack_back']['cp']                           # one crack per face
    free = {'miasma', 'embers', 'ash'}                                                    # trail behind a swing
    assert all(L.get('attach') == 'rotation' for k, L in layers.items() if k not in free)
    assert all('attach' not in layers[k] for k in free)
    assert not {'chakra_tongue', 'chakra_body'} & set(tex)                                # not a recoloured chakra


def test_parse_demonic():
    spec, _ = PA.parse('aura démoniaque rouge sang style berserk')
    assert spec['style']['type'] == 'demonic'


def test_abyss_has_its_own_language():
    spec, P, tex, rep = B.build(os.path.join(EX, 'abyss_aura.yaml'), os.path.join(ROOT, 'out'))
    assert rep['errors'] == []
    layers = {L['id']: L for L in spec['systems']['main']['layers']}
    assert {'sparkle', 'nebula', 'curl'} <= set(tex) and not {'ink_spike', 'miasma', 'chakra_tongue'} & set(tex)
    assert layers['blade_front']['cp'] != layers['blade_back']['cp']       # blade lit from inside, both faces
    assert layers['glitter']['rate'] >= 40                                 # dense glints, untouched by style


def test_analyze_reference_pcf():
    from pcfforge.analyze_pcf import report, load, summary
    path = os.path.join(ROOT, 'references', 'fsc_aura2.pcf')
    defs, kids = load(path)
    s = {d.name: summary(d) for d in defs}
    assert s['[99]_akuma3']['emission'].startswith('160') and s['[99]_akuma1']['color'][0][:3] == (89, 5, 138)
    assert '[99]_akuma1' in report(path)


def test_lock_release():
    ops = LY.layer_ops(dict(tex='glow', rate=5, attach='rotation', release=.7), {}, {'glow': TL.meta('glow')})
    lock = [p for k, fn, p in ops if fn == 'Movement Lock to Control Point'][0]
    assert lock['start_fadeout_min'] == pytest.approx(.6) and lock['end_fadeout_max'] == pytest.approx(.8)


def test_abyss_calibrated_on_reference(built):
    spec, P, tex, rep = B.build(os.path.join(EX, 'abyss_aura.yaml'), os.path.join(ROOT, 'out'))
    layers = {L['id']: L for L in spec['systems']['main']['layers']}
    assert rep['roots']['abyss_aura_main']['peak'] >= 300                     # dense like fsc_aura2
    assert layers['blade_front']['render'] == 'rope'                          # no round balls on the blade
    assert layers['smoke']['release'] == pytest.approx(.7)


def test_black_lightning_recipe():
    d = EF.load(os.path.join(EX, 'abyss_aura.yaml'))
    d['style'] = {'type': 'black_lightning', 'intensity': .7}
    spec, runtime, _ = CO.compose(d)
    layers = {L['id']: L for L in spec['systems']['main']['layers']}
    assert layers['storm']['release'] == pytest.approx(.7)                              # an aura body
    runs = [layers[f'bolt{i}'] for i in range(3)]                                       # discharges run round
    assert all(L['shape'] == 'chain_seq' and L['render'] == 'rope' and L['tex'] == 'bolt_strand' for L in runs)
    assert len({round(L['path_count'] / L['rate'], 2) for L in runs}) == 3              # three lap speeds
    assert all(layers[f'run{i}']['tex'] == 'black_strand' for i in range(3))            # black ink underneath
    assert not any(L['tex'] == 'lightning_anim' for L in layers.values())               # no spinning sprites
    assert layers['storm']['spread'][1] <= layers['storm']['size'][0] * .5              # tight: draws contours
    assert not any(L['tex'] == 'glow' for L in layers.values())                          # no round glows
    assert 'attach' not in layers['sparks']
    assert PA.parse('épée de foudre noire')[0]['style']['type'] == 'black_lightning'


# ------------------------------------------------------------------ Darui (real MDL v49, very low-poly blade)
DARUI = os.path.join(ROOT, 'tests', 'fixtures', 'darui', 'models', 'face', 'sword_darui.mdl')


def test_lowpoly_uses_hull_and_follows_straight_edges():
    seg = AN.region(mdl.read(DARUI), {'bone': 'root', 'start': .25, 'end': 1.0})
    prof = seg['profile']
    assert prof['method'] == 'hull'
    mid = [s['half_width'] for s in prof['slices'][2:7]]
    assert min(mid) > 8.5 and max(mid) - min(mid) < 1.0          # no zigzag between vertex columns
    assert prof['slices'][-1]['half_width'] < 2                  # tapers to the tip


def test_dense_model_keeps_slices():
    seg = AN.region(mdl.read(MDL), {'hitbox_bone': 'RightHand', 'start': .15, 'end': .99})
    assert seg['profile'].get('method', 'slices') == 'slices'


def test_darui_black_lightning(built):
    spec, P, tex, rep = B.build(os.path.join(EX, 'darui_aura.yaml'), os.path.join(ROOT, 'out'))
    assert rep['errors'] == [] and rep['mode'] == 'model_driven' and rep['control_points'] <= 64
    assert {'bolt_strand', 'black_strand', 'smoke', 'nebula'} <= set(tex) and 'black_bolt' not in tex
    assert 150 <= rep['roots']['darui_aura_main']['peak'] <= 360             # validated base, a bit lighter


# ------------------------------------------------------------------ Black Clover shield (standalone, 4 systems)
def test_bc_shield_systems_and_lua(tmp_path):
    spec, P, tex, rep = B.build(os.path.join(EX, 'bc_shield.yaml'), str(tmp_path))
    assert rep['errors'] == [] and set(rep['roots']) == {'bc_shield_start', 'bc_shield_loop', 'bc_shield_end'}
    assert {'shield_rim', 'shield_film', 'energy_cloud', 'shield_veins'} <= set(tex)
    lua = open(os.path.join(P['addon'], 'lua', 'autorun', 'pcfforge_bc_shield.lua'), encoding='utf-8').read()
    assert 'PCFForge.Register("bc_shield_loop", { system = "bc_shield_loop", attach = { type = "entity" } })' in lua
    assert 'Register("bc_shield_end"' in lua and 'persistent' not in lua.split('Register("bc_shield_end"')[-1]
    assert 'persistent' not in lua.split('Register("bc_shield_start"')[1].split('\n')[0]
    errs, _ = VL.validate(P['pcf'])
    assert errs == []


def test_bc_shield_opens_from_the_ground_circle():
    spec = LY.load(os.path.join(EX, 'bc_shield.yaml'))
    L = {l['id']: l for l in spec['systems']['start']['layers']}
    circle = L['circle']
    assert circle['orient'] == 'ground' and circle['grow'][0] < .2                          # small circle opens
    skins = [L[k] for k in L if k.startswith('skin')]
    assert len(skins) >= 8 and all(s['offset'][2] == 1.0 for s in skins)                   # rise out of the circle
    assert all(s['delay'] >= .3 and s['drag'] > 0 and s['up'][0] > 0 for s in skins)       # after it has opened
    assert L['rim']['hide_in_first_person'] and L['rim']['offset'][2] == 1.0               # from the floor, not 50
    ops = LY.layer_ops(dict(L['rim']), {}, {'shield_rim': TL.meta('shield_rim')})
    assert any(fn == 'Movement Basic' for k, fn, p in ops)


def test_point_layers_always_set_a_position():
    """Without a position initializer Source reuses the dead particle's position and `offset` adds up (seen in game)."""
    ops = LY.layer_ops(dict(id='p', tex='ring', count=1, offset=[0, 0, 50]), {}, {'ring': TL.meta('ring')})
    fns = [fn for k, fn, p in ops if k == 'initializers']
    assert fns.index('Position Within Sphere Random') < fns.index('Position Modify Offset Random')


def test_drop_layout(tmp_path):
    spec, P, tex, rep = B.build(os.path.join(EX, 'bc_shield.yaml'), str(tmp_path / 'out'))
    dst = str(tmp_path / 'drop')
    B.drop(spec, P, rep, dst)
    assert os.path.exists(os.path.join(dst, 'particles', 'bc_shield.pcf'))
    assert os.path.exists(os.path.join(dst, 'materials', 'bc_shield', 'shield_rim.vtf'))
    assert 'autonome' in open(os.path.join(dst, 'LISEZMOI_drop.txt'), encoding='utf-8').read()
    lua = open(os.path.join(dst, 'lua', 'autorun', 'pcfforge_drop_bc_shield.lua'), encoding='utf-8').read()
    assert 'game.AddParticles("particles/bc_shield.pcf")' in lua and 'PrecacheParticleSystem("bc_shield_start")' in lua


# ------------------------------------------------------------------ editor-identical PCF + shareable zip
def test_pcf_layout_matches_valve_editor(tmp_path):
    import struct
    spec, P, tex, rep = B.build(os.path.join(EX, 'bc_shield.yaml'), str(tmp_path / 'out'))
    d = open(P['pcf'], 'rb').read()
    assert d.startswith(b'<!-- dmx encoding binary 2 format pcf 1 -->\n\0')
    from srctools.dmx import Element
    r, fmt, ver = Element.parse(open(P['pcf'], 'rb'))
    s0 = next(r['particleSystemDefinitions'].iter_elem())
    assert 'Sort particles' in [a.name for a in s0.values()]                 # exact editor spelling
    op = next(s0['renderers'].iter_elem())
    names = [a.name for a in op.values()]
    assert 'Visibility Alpha Scale maximum' in names or op['functionName'].val_str == 'render_rope'  # defaults written
    assert [a.name for a in op.values()][0] in ('name', 'functionName')


def test_pack_standalone_zip(tmp_path):
    import zipfile
    spec, P, tex, rep = B.build(os.path.join(EX, 'bc_shield.yaml'), str(tmp_path / 'out'))
    z = B.pack(spec, P, rep, str(tmp_path / 'share')).split()[0]
    names = zipfile.ZipFile(z).namelist()
    assert 'bc_shield/particles/bc_shield.pcf' in names and 'bc_shield/addon.json' in names
    assert 'bc_shield/lua/autorun/bc_shield_particles.lua' in names
    assert not any('runtime.lua' in n for n in names)                        # standalone: loader only



def test_bc_shield_three_listed_effects(tmp_path):
    from srctools.dmx import Element
    spec, P, tex, rep = B.build(os.path.join(EX, 'bc_shield.yaml'), str(tmp_path))
    r, _, _ = Element.parse(open(P['pcf'], 'rb'))
    visible = [s.name for s in r['particleSystemDefinitions'].iter_elem() if not s['preventNameBasedLookup'].val_bool]
    assert sorted(visible) == ['bc_shield_end', 'bc_shield_loop', 'bc_shield_start']  # sub-parts hidden from tools
    fin = {l['id']: l for l in LY.load(os.path.join(EX, 'bc_shield.yaml'))['systems']['end']['layers']}
    rows = sorted((l for l in fin.values() if l['id'].startswith('skin')), key=lambda l: l['offset'][2])
    lives = [l['life'][0] for l in rows]
    assert lives == sorted(lives, reverse=True)                               # top dissolves first



def test_bc_shield_loop_is_a_true_cycle():
    loop = {l['id']: l for l in LY.load(os.path.join(EX, 'bc_shield.yaml'))['systems']['loop']['layers']}
    assert all(l['life'][1] < 10 for l in loop.values())                       # no persistent particle: it loops
    skins = [k for k in loop if k.startswith('skin') and not k.endswith('_prime')]
    for k in skins:
        run, prime = loop[k], loop[k + '_prime']
        n = run['ring_count']
        assert run['rate'] * run['life'][0] == pytest.approx(n, abs=.05)       # the row is always full
        assert prime['count'] == n and prime['extra'][-1][0] == 'I_remap_count'   # complete from frame 1
    ops = LY.layer_ops(dict(loop[skins[0] + '_prime']), {}, {'shield_film': TL.meta('shield_film')})
    remap = [p for k, fn, p in ops if fn == 'Remap Particle Count to Scalar'][0]
    assert remap['output field'] == 1 and remap['output maximum'] == pytest.approx(1.4)
    rim = loop['rim']                                                          # two rims cross-fade: constant
    assert rim['life'][0] * rim['rate'] == pytest.approx(2, abs=.01) and rim['fade_in'] == rim['fade_out'] == .5
    assert loop['rim_prime']['count'] == 1


def test_bc_shield_follows_player_and_loop_is_alive():
    spec = LY.load(os.path.join(EX, 'bc_shield.yaml'))
    for key in ('start', 'loop', 'end'):
        assert all(L.get('attach') for L in spec['systems'][key]['layers']), key      # stays on the player
    loop = {l['id']: l for l in spec['systems']['loop']['layers']}
    flows = {l['motion'][0]['speed'] for k, l in loop.items() if k.startswith('skin')}
    assert len(flows) > 3                                                              # shear: liquid flow
    assert loop['wave']['rate'] > 0 and len(loop['wave']['extra']) == 2                # rising light band
    assert loop['clouds']['up'][0] > 0 and loop['clouds']['tex'] == 'energy_cloud'    # inner clouds rise
    assert all(loop[k].get('anim_rate') for k in ('rim', 'clouds', 'veins0'))          # animated sheets
    assert not any('hex' in l['tex'] for l in loop.values())                          # no cells any more


def test_hide_in_first_person_sets_camera_cp(tmp_path):
    from srctools.dmx import Element
    spec, P, tex, rep = B.build(os.path.join(EX, 'bc_shield.yaml'), str(tmp_path))
    r, _, _ = Element.parse(open(P['pcf'], 'rb'))
    cps = {s.name: s['control point to disable rendering if it is the camera'].val_int
           for s in r['particleSystemDefinitions'].iter_elem()}
    assert cps['bc_shield_loop_rim'] == 0 and cps['bc_shield_loop'] == -1


def test_preview_plays_the_chain(tmp_path):
    from pcfforge.preview import render
    from PIL import Image
    out = str(tmp_path / 'p.gif')
    n = render(os.path.join(EX, 'bc_shield.yaml'), out, [('start', 0, None), ('loop', .85, 1.5), ('end', 1.5, None)],
               2.0, size=96, fps=10)
    assert n == 20 and Image.open(out).n_frames == 20


# ------------------------------------------------------------------ Black Clover protection zone (ground magic circle)
def test_bc_zone_timings_and_seamless_loop(tmp_path):
    spec, P, tex, rep = B.build(os.path.join(EX, 'bc_zone.yaml'), str(tmp_path))
    assert rep['errors'] == [] and set(rep['roots']) == {'bc_zone_start', 'bc_zone_loop', 'bc_zone_end'}
    S = {k: {l['id']: l for l in v['layers']} for k, v in spec['systems'].items()}
    st = max(l.get('delay', 0) + l['life'][1] for l in S['start'].values())
    en = max(l.get('delay', 0) + l['life'][1] for l in S['end'].values())
    assert .4 <= st <= .7 and en <= .5                                     # short start / quick clean end
    sym = {'mc_outer': 10, 'mc_orbit': 30, 'mc_star': 30, 'mc_inner': 30}
    turns = []
    for k in ('outer', 'orbit', 'star', 'inner', 'edge'):
        run, prime = S['loop'][k], S['loop'][k + '_prime']
        T = 1 / run['rate']
        assert run['life'][0] == pytest.approx(2 * T, rel=.01) and run['fade_in'] == run['fade_out'] == .5
        assert prime['count'] == 1 and prime['life'][0] == pytest.approx(2 * T, rel=.01)
        if 'turn' in run:                                                   # a copy covers the old one exactly
            assert abs(run['turn']) * T == pytest.approx(sym[run['tex']], rel=.01); turns.append(run['turn'])
    assert min(turns) < 0 < max(turns)                                     # rings turn in different directions
    assert all(l['orient'] == 'ground' for k, l in S['loop'].items() if l['tex'].startswith('mc_'))
    ops = LY.layer_ops(dict(S['loop']['outer']), {}, {'mc_outer': TL.meta('mc_outer')})
    spd = [p for k, fn, p in ops if fn == 'Rotation Speed Random'][0]
    rot = [p for k, fn, p in ops if fn == 'Rotation Random'][0]
    assert spd['randomly_flip_direction'] is False and rot['rotation_offset_max'] == 0
    errs, _ = VL.validate(P['pcf'])
    assert errs == []
