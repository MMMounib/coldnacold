"""Génère examples/bc_shield.yaml : bouclier Black Clover, bulle d'énergie ovale en style anime.

Trois particules (demande du 01/10) : bc_shield_start (la bulle naît aux pieds et gonfle), bc_shield_loop (bulle
formée, vivante, en vraie boucle : le sort renforce et protège la personne), bc_shield_end (la bulle éclate).
Retours du 01/10 : alvéoles « très moches », losange refusé -> OVALE ; v3 « pas animé, moche » -> tout ce qui
porte le rendu est une planche animée qui coule en boucle, et les mouvements sont plus francs ; couleur bleu-violet de la référence
(bulle translucide au bord lumineux, nuages d'énergie à bord brillant dans le bas), rendu anime.

Langage visuel :
  - contour : un sprite face caméra `shield_rim` (contour net, intérieur en aplats, reflets qui montent) : l'ovale
    est un corps de révolution, son contour reste le même de tous les côtés. Caché en vue à la 1re personne ;
  - peau : beaucoup de sprites `shield_film` qui se chevauchent sur la surface et tournent lentement, chaque étage
    à sa vitesse (cisaillement -> reflets qui coulent comme un liquide) ;
  - cœur : nuages `energy_cloud` (planche animée qui bouillonne) qui tournent et montent dans la moitié basse ;
  - veines : filaments `shield_veins` (planche animée) qui coulent sur la peau à contre-sens ;
  - douceur : vague de lumière qui monte, paillettes qui clignent, halo au sol.

Réglages : modifier les constantes ci-dessous, puis
    python examples/gen_bc_shield.py && python -m pcfforge pack examples/bc_shield.yaml
"""
import math
import os

import yaml

CENTER, A, B = 50.0, 40.0, 52.0                   # centre (hauteur), demi-largeur, demi-hauteur de l'ovale
RIM_R = 56.0                                      # rayon du sprite de contour (texture : ovale A x B dans RIM_R)
SKIN_STEP = 10.0                                  # écart entre deux sprites de peau (u, le long de la surface)
SKIN_SIZE = 11.0                                  # rayon d'un sprite de peau (se chevauchent ~4 fois)
SKIN_ALPHA = [40, 55]
LIGHT = [220, 225, 255]                           # blanc lilas (éclats)
RIM_COL = [155, 165, 255]
SKIN_COL = [[115, 120, 255], [160, 170, 255]]
CLOUD_COL = [[130, 135, 255], [175, 185, 255]]
FOLLOW = dict(attach=True)                         # tout suit le joueur (CP0), sans s'incliner


def radius(z):
    u = (z - CENTER) / B
    return A * math.sqrt(max(0.0, 1 - u * u))


def skin_rows():
    """Étages de peau [(z, r, n)] répartis régulièrement le long du profil de l'ovale (pôles et sol exclus)."""
    pts, acc, prev = [], 0.0, None
    for i in range(2001):
        t = math.pi * i / 2000                    # 0 = pôle bas, pi = pôle haut
        p = (A * math.sin(t), CENTER - B * math.cos(t))
        if prev:
            acc += math.dist(p, prev)
        pts.append((acc, p)); prev = p
    k = round(acc / SKIN_STEP); rows = []
    for j in range(k):
        s = (j + .5) * acc / k
        r, z = next(p for a, p in pts if a >= s)
        if z > 3 and r > 6:
            rows.append((round(z, 2), round(r, 2), max(3, round(2 * math.pi * r / SKIN_STEP))))
    return rows


ROWS = skin_rows() + [(round(CENTER + B - 3, 2), 1.0, 2)]     # + calotte au sommet


def skin(k, z, r, n, **kw):
    return dict(id=f'skin{k}', tex='shield_film', shape='ring', radius=r, ring_even=True, ring_count=n,
                ring_yaw=round(180 / n if k % 2 else 0, 2), size=[SKIN_SIZE * .9, SKIN_SIZE * 1.1], alpha=SKIN_ALPHA,
                color=SKIN_COL, rot=True, offset=[0, 0, z], **kw)


def rim(**kw):
    return dict(dict(id='rim', tex='shield_rim', shape='point', size=[RIM_R, RIM_R], alpha=255, color=RIM_COL,
                     offset=[0, 0, CENTER], anim_rate=.7, hide_in_first_person=True), **kw)


WAVE_EXTRA = [['O_rscale', .05, 1.0, 0.0, .5, .5], ['O_rscale', 1.0, .05, .5, 1.0, .5]]   # suit la largeur de l'ovale


def wave(**kw):
    """Anneau à plat qui monte du sol au sommet en suivant la largeur de l'ovale."""
    return dict(dict(id='wave', tex='ring', size=[A * .95, A * .95], orient='ground', alpha=150, color=LIGHT,
                     offset=[0, 0, 1], fade_in=.12, fade_out=.25, extra=WAVE_EXTRA), **kw)


CLOUD = dict(tex='energy_cloud', shape='disc', spread=[10, 27], height=[4, 30], size=[15, 22], up=[2, 5],
             alpha=[130, 180], color=CLOUD_COL, rot=True, spin=[-20, 20], anim_rate=.4,
             motion=[{'type': 'orbit', 'speed': .2, 'direction': 1}], attach=True)
VEINS = dict(tex='shield_veins', shape='ring', size=[15, 20], alpha=[120, 170], color=[[150, 160, 255], LIGHT],
             rot=True, anim_rate=.35, motion=[{'type': 'orbit', 'speed': .16, 'direction': -1}], attach=True)


# ------------------------------------------------------------------ start : le cercle s'ouvre, le bouclier en sort
# Demande du 01/10 : « le cercle doit faire en sorte que la particule s'ouvre comme si le bouclier s'activait à partir
# du petit cercle de départ ». 1) un petit cercle lumineux s'allume au sol et s'élargit jusqu'à la base de la bulle ;
# 2) le bouclier monte de ce cercle : chaque étage de peau naît au sol à son rayon final et monte à sa hauteur
# (vitesse verticale seulement, freinée par la traînée : v(t) = v0 (1 - drag)^(30 t), v0 = hauteur * K) ; le contour
# grandit depuis le cercle ; 3) éclats quand la bulle est fermée, le loop prend le relais.
OPEN = .35                                        # le cercle s'ouvre (s)
RISE = .75                                        # le bouclier monte (s)
DRAG = .12
K = 30 * -math.log(1 - DRAG)                      # 3,84 /s : ~95 % de la montée faite en RISE
LOOP_AT = round(OPEN + RISE, 3)                   # le loop prend le relais (fondu croisé court)
START_END = round(LOOP_AT + .25, 3)
BASE_R = round(A / .86, 2)                        # sprite du cercle ouvert : l'anneau de `ring` est à 86 % du rayon -> A


def fade_at_end(life, secs=.22):
    return round(min(.6, secs / max(life, 1e-3)), 3)


start = []
RISE_LIFE = round(START_END - OPEN, 3)
for k, (z, r, n) in enumerate(ROWS):
    start.append(skin(k, 1.0, r, n, count=n, delay=round(OPEN - .05, 3), life=[RISE_LIFE] * 2, drag=DRAG,
                      up=[round((z - 1) * K, 2)] * 2, fade_in_s=.15, fade_out=fade_at_end(RISE_LIFE)))
start += [
    # le cercle d'activation : petit, éclatant, il s'élargit au sol puis tient pendant que le bouclier en sort
    dict(id='circle', tex='ring', count=1, life=[START_END, START_END], size=[BASE_R, BASE_R],
         grow=[.08, 1.0, .35, round(OPEN / START_END, 3)], orient='ground', alpha=255, color=LIGHT, offset=[0, 0, 1],
         fade_out=fade_at_end(START_END, .3)),
    dict(id='circle_glow', tex='ring', count=1, life=[START_END, START_END], size=[round(BASE_R * 1.06, 2)] * 2,
         grow=[.08, 1.0, .35, round(OPEN / START_END, 3)], orient='ground', alpha=150, color=RIM_COL, offset=[0, 0, 1.5],
         pulse_alpha=[.3, 4], fade_out=fade_at_end(START_END, .3)),
    dict(id='seed', tex='sparkle', shape='point', count=1, life=[.45, .45], size=[6, 6], grow=[.3, 1.4, .4],
         alpha=255, color=LIGHT, offset=[0, 0, 2], fade_out=.6),
    # éclats qui jaillissent du cercle quand il s'ouvre
    dict(id='spray', tex='sparkle', shape='ring', radius=1.0, count=30, speed=[round(A * 2.2), round(A * 3)],
         up=[10, 35], drag=.1, life=[.4, .7], size=[1.2, 2.6], alpha=[220, 255], color=[LIGHT, [160, 170, 255]],
         rot=True, offset=[0, 0, 2], fade_out=.5),
    # le contour grandit depuis le cercle
    rim(count=1, delay=round(OPEN - .05, 3), life=[RISE_LIFE] * 2, drag=DRAG, up=[round((CENTER - 1) * K, 2)] * 2,
        offset=[0, 0, 1], grow=[.45, 1.0, .35, round(RISE / RISE_LIFE, 3)], fade_in_s=.25,
        fade_out=fade_at_end(RISE_LIFE)),
    dict(CLOUD, id='clouds', count=10, delay=round(OPEN + .2, 3), life=[round(START_END - OPEN - .2, 3)] * 2,
         fade_in=.4, fade_out=fade_at_end(START_END - OPEN - .2)),
    wave(count=1, delay=round(OPEN, 3), life=[RISE, RISE], up=[round((2 * B) / RISE, 2)] * 2),
    dict(id='pop', tex='sparkle', shape='sphere', spread=[A * .85, A * .95], count=26, delay=round(LOOP_AT - .1, 3),
         speed=[15, 35], drag=.1, life=[.4, .7], size=[1.4, 2.8], alpha=[220, 255], color=[LIGHT, [160, 170, 255]],
         rot=True, offset=[0, 0, CENTER], fade_out=.6),
    dict(id='star', tex='sparkle', shape='point', count=1, delay=round(LOOP_AT - .05, 3), life=[.5, .5], size=[8, 8],
         grow=[.3, 1.2, .3], alpha=255, color=LIGHT, offset=[0, 0, CENTER + B - 2], fade_out=.6),
]
for L_ in start:
    L_.update(FOLLOW)

# ------------------------------------------------------------------ loop : la bulle formée, fluide, en VRAIE boucle
# Tout est ré-émis en continu avec des vies courtes : l'effet tourne indéfiniment et s'éteint seul quand on l'arrête.
# Pour qu'il soit complet dès la 1re image, chaque étage a une « amorce » : la même forme émise d'un coup, dont la
# i-ème particule vit i/n d'un cycle (Remap Particle Count to Scalar) : elle s'éteint quand le cycle la remplace.
CYCLE = 1.4                                       # un étage de peau est entièrement renouvelé en CYCLE s (court :
                                                  # à l'arrêt, le loop s'éteint vite)
FLOW = .11                                        # rotation de la peau (x 180 °/s ≈ 20 °/s), différente à chaque étage
RIM_CYCLE = .9                                   # deux contours se relaient en fondu (somme constante)


def cycled(base, n, period, closing):
    """[couche en boucle, amorce] pour une forme de n emplacements réguliers (closing : +1 pour fermer une corde)."""
    run = dict(base, id=base['id'], rate=round(n / period, 3), life=[round(period * (n + closing) / n, 3)] * 2)
    prime = dict(base, id=base['id'] + '_prime', count=n + closing, life=[period, period],
                 extra=base.get('extra', []) + [['I_remap_count', 0, n, .02, period, 1]])
    return [run, prime]


loop = []
for k, (z, r, n) in enumerate(ROWS):
    flow = round(FLOW * (1 + .35 * math.sin(k * 1.7)), 3)
    base = skin(k, z, r, n, spin=[-6, 6], motion=[{'type': 'orbit', 'speed': flow, 'direction': 1}], **FOLLOW)
    run, prime = cycled(base, n, CYCLE, 0)
    run.update(fade_in=.25, fade_out=.25)          # chaque sprite se renouvelle en douceur sous ses voisins
    prime.update(fade_out=.25)
    loop += [run, prime]
TWINKLE = dict(tex='sparkle', shape='ring', size=[1.6, 3.0], alpha=[200, 255], color=[LIGHT, [160, 170, 255]],
               rot=True, grow=[0, 1, .5], fade_out=.5, **FOLLOW)
loop += [
    # contour : deux sprites se relaient (fondu entrant/sortant de moitié chacun) -> intensité constante
    rim(rate=round(1 / RIM_CYCLE, 3), life=[2 * RIM_CYCLE] * 2, fade_in=.5, fade_out=.5, **FOLLOW),
    # amorce : pleine jusqu'à la naissance du 1er contour (1 cycle), puis s'efface pendant qu'il apparaît
    rim(id='rim_prime', count=1, life=[2 * RIM_CYCLE] * 2, fade_out=.5, **FOLLOW),
    # cœur : nuages d'énergie qui bouillonnent (planche animée), tournent et montent dans la moitié basse
    dict(CLOUD, id='clouds', rate=10, life=[1.2, 1.6], fade_in=.3, fade_out=.35),
    dict(CLOUD, id='clouds_prime', count=14, life=[.4, 1.5], fade_out=.35),
    # veines : filaments d'énergie liquides qui coulent sur la peau, à contre-sens
    *[L_ for k, (z, r, n) in enumerate(ROWS[:-1]) for L_ in (
        dict(VEINS, id=f'veins{k}', radius=r, offset=[0, 0, z], rate=round(n / 3 / 1.1, 3), life=[.9, 1.3],
             fade_in=.3, fade_out=.3),
        dict(VEINS, id=f'veins{k}_prime', radius=r, offset=[0, 0, z], count=max(1, round(n / 3)), life=[.3, 1.2],
             fade_out=.3))],
    # vague : une bande de lumière douce monte du sol au sommet
    wave(rate=round(1 / 2.2, 3), life=[1.3, 1.3], up=[(2 * B) / 1.3] * 2, **FOLLOW),
    # paillettes qui clignent sur la peau (bas, milieu, haut)
    dict(TWINKLE, id='twinkle_low', radius=round(radius(25), 2), offset=[0, 0, 25], rate=5, life=[.6, 1.0]),
    dict(TWINKLE, id='twinkle_mid', radius=A, offset=[0, 0, CENTER], rate=7, life=[.6, 1.0]),
    dict(TWINKLE, id='twinkle_high', radius=round(radius(80), 2), offset=[0, 0, 80], rate=5, life=[.6, 1.0]),
    # poussière d'énergie qui monte dans la bulle
    dict(TWINKLE, id='motes', shape='disc', spread=[0, 30], height=[2, 60], rate=12, life=[1.0, 1.6], size=[.8, 1.6],
         up=[14, 26], fade_in=.2),
    dict(TWINKLE, id='motes_prime', shape='disc', spread=[0, 30], height=[2, 80], count=16, life=[.3, 1.5],
         size=[.8, 1.6], up=[14, 26]),
    # au sol : halo doux sous la bulle
    dict(id='halo', tex='ring', rate=1.0, life=[1.6, 1.6], size=[22, 22], grow=[.8, 1.15, .5], orient='ground',
         alpha=110, color=RIM_COL, offset=[0, 0, 1], fade_in=.3, fade_out=.4, **FOLLOW),
    dict(id='halo_prime', tex='ring', count=2, life=[.8, 1.6], size=[22, 22], orient='ground', alpha=110,
         color=RIM_COL, offset=[0, 0, 1], fade_out=.4, **FOLLOW),
]

# ------------------------------------------------------------------ end : la bulle éclate (flash) et se dissout
OUT_STEP = .035                                   # écart entre deux étages qui s'éteignent (du haut vers le bas)


def out_time(z):
    """Moment où l'étage à la hauteur z s'éteint : le haut d'abord."""
    return round(.12 + (CENTER + B - z) / (2 * B) * OUT_STEP * len(ROWS), 3)


fin = []
for k, (z, r, n) in enumerate(ROWS):
    t = out_time(z)
    fin.append(skin(k, z, r, n, count=n, life=[t + .05, t + .05], shrink_end=.6, fade_out=round(min(.6, .3 / (t + .05)), 3)))
    fin.append(dict(TWINKLE, id=f'motes{k}', radius=r, offset=[0, 0, z], count=max(3, n // 2), delay=t,
                    life=[.6, 1.0], up=[10, 28], size=[1.0, 2.0], drag=.05))
fin += [
    rim(count=1, life=[.4, .4], grow=[1.0, 1.2, .5], alpha=255, color=LIGHT, fade_out=.8),
    dict(id='shock', tex='ring', count=1, life=[.45, .45], size=[A * 1.3, A * 1.3], grow=[.8, 1.5, .3], orient='ground',
         alpha=255, color=LIGHT, offset=[0, 0, CENTER], fade_out=.8),
    dict(id='burst', tex='sparkle', shape='sphere', spread=[A * .8, A * .9], count=48, speed=[35, 80], drag=.08,
         life=[.5, .9], size=[1.2, 2.4], alpha=[210, 255], color=[LIGHT, [160, 170, 255]], rot=True,
         offset=[0, 0, CENTER], fade_out=.6),
    dict(CLOUD, id='clouds', count=10, life=[.4, .6], fade_out=.8),
    dict(id='ripple', tex='ring', count=1, delay=round(out_time(3), 3), life=[.6, .6], size=[A * .9] * 2,
         grow=[.3, 1.2, .3], orient='ground', alpha=130, color=LIGHT, offset=[0, 0, 1], fade_out=.7),
]
for L_ in fin:
    L_.update(FOLLOW)

spec = dict(prefix='bc_shield', title='Bouclier Black Clover', materials='bc_shield', file='bc_shield.pcf',
            budget=820, bbox=160,   # l'estimation additionne amorces et boucle, qui se relaient
            draw_distance=3000, hide_children=True,
            texture_size={'sparkle': 64},
            systems=dict(
                start=dict(about=f'apparition : un cercle s\'ouvre au sol et le bouclier en sort '
                                 f'({START_END} s) ; lancer loop à {LOOP_AT} s', layers=start),
                loop=dict(about='bulle ovale formée, fluide et animée, en boucle infinie (s\'éteint seule en ~1,5 s '
                                'quand on l\'arrête ; pour une fin nette, le détruire d\'un coup en lançant end)',
                          layers=loop),
                end=dict(about='disparition : la bulle éclate en flash puis se dissout en paillettes (lancer en détruisant '
                               'loop d\'un coup)', layers=fin)))
HEAD = ('# Généré par examples/gen_bc_shield.py — modifier le script plutôt que ce fichier.\n'
        "# Bouclier Black Clover, bulle ovale anime. 3 particules : bc_shield_start, bc_shield_loop, bc_shield_end.\n")
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bc_shield.yaml')
open(path, 'w', encoding='utf-8').write(HEAD + yaml.safe_dump(spec, allow_unicode=True, sort_keys=False, width=120))
print(path)
