"""Pack Sarada — Mangekyō Sharingan / Ōhirume : un seul PCF, noms exacts, textures demandées, boucles propres."""
import os

import pytest

from pcfforge import build as B, layers as LY
from pcfforge.textures import lib as TL, sarada as SA

EX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'examples')
SPEC = os.path.join(EX, 'sarada_ohirume.yaml')
MAIN = ['sarada_aura', 'sarada_activate', 'sarada_eye', 'sarada_target', 'sarada_attract_trail', 'ohirume_sphere',
        'ohirume_projectile', 'ohirume_pull', 'ohirume_impact', 'ohirume_implosion', 'ohirume_orbit', 'ohirume_float']
REQUIRED_TEX = ['sarada_core', 'sarada_glow', 'sarada_filament', 'sarada_spark', 'sarada_ring', 'sarada_void',
                'sarada_distort', 'sarada_fragment', 'sarada_streak', 'ohirume_core', 'ohirume_void', 'ohirume_ring',
                'ohirume_gravity', 'ohirume_streak', 'ohirume_fragment', 'ohirume_distort']


@pytest.fixture(scope='module')
def built(tmp_path_factory):
    return B.build(SPEC, str(tmp_path_factory.mktemp('out')))


def test_exact_names_in_one_pcf(built):
    from srctools.dmx import Element
    spec, P, tex, rep = built
    assert rep['errors'] == [] and os.path.basename(P['pcf']) == 'sarada_ohirume.pcf'
    r, _, _ = Element.parse(open(P['pcf'], 'rb'))
    visible = {s.name for s in r['particleSystemDefinitions'].iter_elem() if not s['preventNameBasedLookup'].val_bool}
    assert set(MAIN) <= visible and all(len(n) <= 24 for n in visible)          # short, exact names
    assert all(n.startswith(('sarada_', 'ohirume_')) for n in visible)


def test_required_textures_exist_and_are_used(built):
    spec, P, tex, rep = built
    assert set(REQUIRED_TEX) <= set(SA.REG)
    used = B.used_textures(spec)
    assert set(REQUIRED_TEX) <= used                                               # every requested texture is used
    for n in used:
        assert os.path.exists(os.path.join(P['mat'], n + '.vmt')) and os.path.exists(os.path.join(P['mat'], n + '.vtf'))


def test_bright_red_and_additive_stay_rare():
    adds = [n for n, t in SA.REG.items() if t['blend'] == 'add']
    assert sorted(adds) == ['sarada_glow', 'sarada_spark']                         # matter is alpha-blended
    spec = LY.load(SPEC)
    for key, sd in spec['systems'].items():
        sparks = [L for L in sd['layers'] if L['tex'] == 'sarada_spark']
        assert sum(L.get('count', 0) + L.get('rate', 0) for L in sparks) <= 30, key


def test_loops_are_true_cycles_and_light():
    spec = LY.load(SPEC)
    for key in ('sarada_aura', 'sarada_eye', 'ohirume_sphere', 'ohirume_orbit', 'ohirume_float', 'ohirume_pull'):
        layers = spec['systems'][key]['layers']
        assert all(L['life'][1] < 40 for L in layers), key                          # nothing persistent
        assert sum(LY.estimate_peak(L) for L in layers) <= 110, key
    orbit = {L['id']: L for L in spec['systems']['ohirume_orbit']['layers']}
    for i in range(4):                                                             # a copy is born where the old one is
        run = orbit[f'void{i}']
        T = 1 / run['rate']
        assert run['motion'][0]['speed'] * 180 * T == pytest.approx(360, rel=.01)
    assert len({orbit[f'void{i}']['size'][0] for i in range(4)}) == 4             # 4 different scales


def test_projectile_flies_from_cp0_to_cp1_and_impacts_at_cp1():
    spec = LY.load(SPEC)
    P = {L['id']: L for L in spec['systems']['ohirume_projectile']['layers']}
    fly = [L for k, L in P.items() if k.endswith('_fly')]
    assert len(fly) == 4 and all(L['cp'] == 0 and L['cp_end'] == 1 and L['path_travel'][0] > 0 for L in fly)
    assert P['flash']['cp'] == 1 and P['flash']['delay'] >= fly[0]['delay'] + fly[0]['path_travel'][0] - .05


def test_mangekyo_pattern_is_centered():
    import numpy as np
    c, a = SA.mangekyo(256, 'mask')
    ys, xs = np.nonzero(a > .5)
    assert abs(xs.mean() - 127.5) < 2 and abs(ys.mean() - 127.5) < 2
