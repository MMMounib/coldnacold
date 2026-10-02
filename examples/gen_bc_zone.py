"""Génère examples/bc_zone.yaml : zone magique de protection au sol (Black Clover), 3 particules.

Demande de l'utilisateur (01/10) : cercle magique au sol, violet principal, bleu-violet sombre en secondaire, blanc
légèrement lumineux pour le tracé, glow subtil, centre plus transparent que les contours. Pas le bouclier lui-même :
seulement son aire d'effet. Choix : rayon 150 u ; pas de runes (« un cercle qui fait anneau, cercle magique avec
forme géométrique »).

Construction : chaque pièce du cercle est un grand sprite à plat au sol (orientation 2), toutes à la même échelle :
  mc_edge  énergie qui coule le long du contour (planche animée)      bleu-violet sombre
  mc_outer double anneau extérieur gradué, 36 graduations (10°)       violet
  mc_orbit anneaux + 12 cercles satellites (30°)                      bleu-violet
  mc_star  étoile à 12 branches, 4 triangles (30°)                    blanc lilas, pulse doucement
  mc_inner petits anneaux centraux + 12 losanges (30°)                violet
Boucle sans raccord : une pièce tourne à `turn` °/s ; une copie neuve à rotation 0 naît toutes les T = symétrie / turn
secondes et vit 2T (fondu entrant puis sortant de moitié : intensité constante). Elle recouvre exactement l'ancienne,
qui a tourné d'une symétrie entière.

Réglages : modifier les constantes, puis
    python examples/gen_bc_zone.py && python -m pcfforge pack examples/bc_zone.yaml
"""
import os

import yaml

R = 150.0                                         # rayon de la zone (anneau extérieur)
SPRITE = round(R / .955, 2)                       # rayon des sprites (l'anneau extérieur est à 95,5 % du sprite)
Z = 1.5                                           # juste au-dessus du sol
VIOLET = [160, 115, 250]
DEEP = [95, 75, 205]                              # bleu/violet sombre
LINE = [222, 212, 255]                            # blanc légèrement lumineux
FOLLOW = dict(attach=True)                         # la zone suit le lanceur (CP0)

# pièce : (texture, couleur, alpha, symétrie °, vitesse °/s, pulse)
PIECES = {
    'edge':  ('mc_edge', DEEP, 150, None, 0, None),
    'outer': ('mc_outer', VIOLET, 235, 10, 4.0, None),
    'orbit': ('mc_orbit', DEEP, 215, 30, -9.0, None),
    'star':  ('mc_star', LINE, 150, 30, 6.0, [.25, .5]),
    'inner': ('mc_inner', VIOLET, 200, 30, -8.0, None),
}
EDGE_T = 2.0                                      # période de la planche du contour (s)


def piece(key, **kw):
    tex, col, alpha, sym, turn, pulse = PIECES[key]
    L = dict(id=key, tex=tex, shape='point', size=[SPRITE, SPRITE], orient='ground', alpha=alpha, color=col,
             offset=[0, 0, Z])
    if tex == 'mc_edge':
        L['anim_rate'] = round(1 / EDGE_T, 3)
    if pulse:
        L['pulse_alpha'] = pulse
    L.update(FOLLOW)
    return dict(L, **kw)


def period(key):
    tex, col, alpha, sym, turn, pulse = PIECES[key]
    return EDGE_T if sym is None else round(sym / abs(turn), 3)


# ------------------------------------------------------------------ start (0,6 s) : le cercle s'ouvre
# Un petit cercle s'allume au centre, le contour s'étend jusqu'au rayon final, les anneaux apparaissent du centre vers
# l'extérieur, la géométrie s'allume en dernier, des étincelles montent du sol. Tout reste à rotation 0 : le loop
# démarre exactement sur la même image (fondu croisé de 0,1 s).
EXPAND = .22                                      # le contour atteint le rayon final
START_END = .6
LOOP_AT = round(START_END - .1, 3)


def appear(key, t0, grow_from, grow_time, fade_in):
    life = round(START_END - t0, 3)
    return piece(key, count=1, delay=t0, life=[life, life], grow=[grow_from, 1.0, .3, round(grow_time / life, 3)],
                 fade_in_s=fade_in, fade_out=round(.1 / life, 3))


start = [
    dict(id='seed', tex='ring', shape='point', count=1, life=[.25, .25], size=[14, 14], grow=[.3, 1.6, .3],
         orient='ground', alpha=255, color=LINE, offset=[0, 0, Z + .3], fade_out=.6, **FOLLOW),
    appear('inner', 0.0, .5, .1, .04),
    appear('outer', 0.0, .06, EXPAND, .03),
    appear('edge', .05, .06, EXPAND - .05, .08),
    appear('orbit', .12, .85, .12, .12),
    appear('star', .22, .95, .15, .22),
    # le front d'expansion : un anneau vif qui file vers l'extérieur et s'éteint au bord
    dict(id='front', tex='ring', shape='point', count=1, life=[EXPAND + .08] * 2, size=[R / .86] * 2,
         grow=[.06, 1.04, .3, round(EXPAND / (EXPAND + .08), 3)], orient='ground', alpha=255, color=LINE,
         offset=[0, 0, Z + .4], fade_out=.35, **FOLLOW),
    # énergie qui remonte légèrement du sol, le long du contour puis de l'anneau des satellites
    dict(id='rise', tex='sparkle', shape='ring', radius=round(R * .95, 2), count=26, delay=.12, life=[.3, .48],
         size=[1.4, 2.6], up=[18, 40], alpha=[200, 255], color=[LINE, VIOLET], rot=True, offset=[0, 0, Z],
         fade_out=.6, **FOLLOW),
    dict(id='rise_mid', tex='sparkle', shape='ring', radius=round(R * .66, 2), count=14, delay=.2, life=[.25, .4],
         size=[1.2, 2.2], up=[14, 30], alpha=[200, 255], color=[LINE, VIOLET], rot=True, offset=[0, 0, Z],
         fade_out=.6, **FOLLOW),
]

# ------------------------------------------------------------------ loop : la zone active, en vraie boucle
loop = []
for key in PIECES:
    T = period(key); turn = PIECES[key][4]
    rot = dict(turn=turn) if turn else {}
    loop.append(piece(key, rate=round(1 / T, 4), life=[2 * T, 2 * T], fade_in=.5, fade_out=.5, **rot))
    # amorce : pleine pendant un cycle (jusqu'à la 1re copie), puis s'efface pendant qu'elle apparaît
    loop.append(piece(key, id=key + '_prime', count=1, life=[2 * T, 2 * T], fade_in_s=.05, fade_out=.5, **rot))
MOTE = dict(tex='sparkle', shape='ring', size=[.9, 1.8], alpha=[150, 220], color=[LINE, VIOLET], rot=True,
            fade_in=.3, fade_out=.4, **FOLLOW)
loop += [
    # petites particules qui flottent au-dessus du contour et de l'anneau des satellites
    dict(MOTE, id='motes', radius=round(R * .95, 2), offset=[0, 0, Z + 2], rate=9, life=[1.4, 2.2], up=[5, 12]),
    dict(MOTE, id='motes_prime', radius=round(R * .95, 2), offset=[0, 0, Z + 2], count=14, life=[.3, 2.0],
         up=[5, 12], fade_in=.1),
    dict(MOTE, id='motes_mid', radius=round(R * .66, 2), offset=[0, 0, Z + 2], rate=4, life=[1.2, 1.8], up=[4, 9]),
    dict(MOTE, id='motes_mid_prime', radius=round(R * .66, 2), offset=[0, 0, Z + 2], count=6, life=[.3, 1.6],
         up=[4, 9], fade_in=.1),
]

# ------------------------------------------------------------------ end (0,45 s) : la zone s'éteint
# La géométrie s'éteint d'abord, les anneaux ralentissent (moitié de leur vitesse), se rétractent un peu vers le centre
# et disparaissent, des étincelles se détachent du contour. Lancer en détruisant loop d'un coup.
END = .45


def vanish(key, life, shrink, turn_k=.4):
    turn = PIECES[key][4]
    rot = dict(turn=round(turn * turn_k, 2)) if turn else {}
    return piece(key, count=1, life=[life, life], grow=[1.0, shrink, .5], fade_out=.8, **rot)


fin = [
    vanish('star', .2, .97),
    vanish('inner', .25, .9),
    vanish('orbit', .32, .93),
    vanish('edge', .4, .9),
    vanish('outer', END, .9),
    dict(id='sparks', tex='sparkle', shape='ring', radius=round(R * .93, 2), count=30, delay=.05, life=[.25, .4],
         size=[1.2, 2.4], speed=[-25, -8], up=[15, 35], alpha=[200, 255], color=[LINE, VIOLET], rot=True,
         offset=[0, 0, Z], fade_out=.6, **FOLLOW),
]

spec = dict(prefix='bc_zone', title='Zone magique Black Clover', materials='bc_zone', file='bc_zone.pcf',
            budget=160, bbox=220, draw_distance=4000, hide_children=True,
            texture_size={'sparkle': 64},
            systems=dict(
                start=dict(about=f'apparition : le cercle s\'ouvre du centre au rayon {int(R)} u ({START_END} s) ; '
                                 f'lancer loop à {LOOP_AT} s', layers=start),
                loop=dict(about='zone active : anneaux qui tournent en sens opposés, géométrie qui pulse, contour qui '
                                'ondule, en boucle infinie', layers=loop),
                end=dict(about=f'disparition ({END} s) : la géométrie s\'éteint, les anneaux ralentissent et se '
                               f'rétractent (lancer en détruisant loop d\'un coup)', layers=fin)))
HEAD = ('# Généré par examples/gen_bc_zone.py — modifier le script plutôt que ce fichier.\n'
        "# Zone magique de protection au sol (Black Clover). 3 particules : bc_zone_start, bc_zone_loop, bc_zone_end.\n")
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bc_zone.yaml')
open(path, 'w', encoding='utf-8').write(HEAD + yaml.safe_dump(spec, allow_unicode=True, sort_keys=False, width=120))
print(path)
