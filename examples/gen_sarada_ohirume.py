"""Génère examples/sarada_ohirume.yaml : pack « Sarada — Mangekyō Sharingan / Ōhirume » (un seul PCF).

Pack entièrement nouveau (02/10, cahier des charges de l'utilisateur) : rien n'est repris des versions Ohirume
précédentes. Livrable : out/share/pcfforge_sarada_ohirume.zip (voir examples/package_sarada_ohirume.py), autonome.

Langage visuel commun (textures pcfforge/textures/sarada.py) :
  - anime cel-shading, bords nets, couleurs intégrées aux textures (particules blanches) ;
  - palette BLACK / DARK CRIMSON / DEEP RED / CRIMSON / SCARLET, BRIGHT RED en accent rare (sarada_spark) ;
  - matière en mélange alpha (le noir est un vrai noir, le carmin reste carmin sur fond clair), additif réservé au
    halo très faible (sarada_glow) et aux micro-étincelles ;
  - motif signature : le Mangekyō (pupille + rayons triangulaires) -> éclats triangulaires, iris du target ;
  - mouvement : tout converge, s'enroule ou monte doucement ; rien d'aléatoire qui encombre.
Boucles : vraies boucles (copies relayées en phase, flux continus avec amorce), aucune particule persistante.

Points de contrôle :
  sarada_aura / sarada_activate / ohirume_orbit / ohirume_float : CP0 = pieds de Sarada
  sarada_eye : CP0 = l'œil          sarada_target(_release) : CP0 = pieds de la cible
  sarada_attract_trail : CP0 = centre (buste) du personnage attiré, en mouvement
  ohirume_sphere(_s/_l/_end), ohirume_implosion, ohirume_impact : CP0 = centre
  ohirume_projectile : CP0 = départ, CP1 = cible         ohirume_pull : CP0 = sphère, CP1 = cible

    python examples/gen_sarada_ohirume.py && python -m pcfforge generate examples/sarada_ohirume.yaml
"""
import math
import os

import yaml

W = [255, 255, 255]                               # couleurs intégrées aux textures : particules blanches
CHEST, HEAD = 40.0, 64.0                          # hauteurs sur un modèle joueur (~72 u), CP0 aux pieds
LOCK = dict(attach=True)


def r2(v):
    return round(float(v), 3)


def relay(base, T, alpha_blend=True, grow_in=None):
    """Pièce toujours présente, en VRAIE boucle : une copie neuve naît toutes les T s et vit 2T, à l'identique (même
    rotation de départ, planche en phase) ; pour une pièce qui tourne, T = un tour (ou une symétrie) exactement.
    Alpha : fondus d'un quart (une copie est toujours pleine : le noir ne faiblit pas). Additif : fondus de moitié
    (somme constante). Renvoie [cycle, amorce]. grow_in : l'amorce naît en grandissant (formation, s)."""
    f = .25 if alpha_blend else .5
    run = dict(base, rate=r2(1 / T), life=[r2(2 * T)] * 2, fade_in=f, fade_out=f)
    prime = dict(base, id=base['id'] + '_prime', count=1, life=[r2(2 * T)] * 2, fade_in_s=.06, fade_out=f)
    if grow_in:
        prime['grow'] = [.08, 1.0, .3, r2(grow_in / (2 * T))]
    for k in ('rate',):
        prime.pop(k, None)
    return [run, prime]


def primed(base, n, life_max, **over):
    """Amorce d'un flux continu : n particules d'un coup, vies réparties de 5 à 100 % (complet dès la 1re image)."""
    p = dict(base, id=base['id'] + '_prime', count=int(n), life=[r2(life_max)] * 2,
             extra=list(base.get('extra', [])) + [['I_remap_count', 0, int(n), r2(.05 * life_max), r2(life_max), 1]])
    for k in ('rate', 'duration', 'fade_in'):
        p.pop(k, None)
    p.update(over)
    return p


# ====================================================================== SARADA
def aura_layers():
    """Aura très légère : cœur sombre discret, halo rouge sombre qui respire, filaments fins qui montent en
    tournant, quelques éclats et micro-étincelles. Le personnage reste lisible (rien de dense sur le corps)."""
    fil = dict(id='filaments', tex='sarada_filament', shape='ring', radius=17, thickness=5, height=[17, 42],
               orient='vertical', rate=7, life=[1.4, 2.0], size=[12, 17], up=[10, 18], alpha=[210, 255], color=W,
               anim_rate=.8, motion=[{'type': 'orbit', 'speed': .12, 'direction': 1}], fade_in=.3, fade_out=.4, **LOCK)
    frag = dict(id='motes', tex='sarada_fragment', seq=[0, 3], shape='ring', radius=20, thickness=8,
                height=[6, 60], rate=4, life=[1.6, 2.4], size=[1.3, 2.3], up=[6, 12], alpha=[200, 250], color=W,
                rot=True, spin=[-70, 70], motion=[{'type': 'orbit', 'speed': .08, 'direction': 1}],
                fade_in=.25, fade_out=.35, **LOCK)
    spark = dict(id='sparks', tex='sarada_spark', shape='ring', radius=18, thickness=6, height=[10, 60], rate=2.5,
                 life=[.4, .7], size=[.5, .9], up=[8, 16], alpha=[150, 220], color=W, grow=[.2, 1.0, .4],
                 fade_out=.6, **LOCK)
    out = []
    out += relay(dict(id='core', tex='sarada_core', shape='point', offset=[0, 0, CHEST], size=[24, 24], alpha=120,
                      color=W, pulse_alpha=[.12, .4], **LOCK), 2.4)
    out += relay(dict(id='halo', tex='sarada_glow', shape='point', offset=[0, 0, CHEST + 2], size=[34, 34], alpha=38,
                      color=W, pulse_alpha=[.25, .4], **LOCK), 2.4, alpha_blend=False)
    out += [fil, primed(fil, 12, 2.0), frag, primed(frag, 8, 2.4), spark]
    return out


def activate_layers():
    """0,7 s. 0,00 : énergie de l'œil ; 0,10 : pulsation rouge ; 0,20 : l'aura sombre s'étend ; 0,35 : filaments ;
    0,50 : stabilisation (lancer sarada_aura à 0,45 s)."""
    return [
        dict(id='eye', tex='sarada_spark', shape='point', count=1, offset=[0, 0, HEAD], life=[.32, .32], size=[3, 3],
             grow=[.2, 1.3, .3], alpha=255, color=W, fade_out=.6, **LOCK),
        dict(id='pulse', tex='sarada_ring', seq=[0, 0], shape='point', count=1, delay=.1, offset=[0, 0, CHEST + 4],
             life=[.35, .35], size=[30, 30], grow=[.25, 1.25, .3], alpha=235, color=W, turn=60, fade_out=.7, **LOCK),
        dict(id='pulse_glow', tex='sarada_glow', shape='point', count=1, delay=.1, offset=[0, 0, CHEST + 4],
             life=[.35, .35], size=[38, 38], grow=[.3, 1.2, .3], alpha=110, color=W, fade_out=.8, **LOCK),
        dict(id='dark', tex='sarada_core', shape='point', count=1, delay=.2, offset=[0, 0, CHEST], life=[.5, .5],
             size=[30, 30], grow=[.2, 1.0, .3, .5], alpha=170, color=W, fade_in_s=.05, fade_out=.5, **LOCK),
        dict(id='ripple', tex='sarada_distort', seq=[0, 0], shape='point', count=1, delay=.2, offset=[0, 0, CHEST],
             life=[.4, .4], size=[40, 40], grow=[.25, 1.15, .3], alpha=220, color=W, fade_out=.6, **LOCK),
        dict(id='shards', tex='sarada_fragment', seq=[0, 3], shape='sphere', spread=[4, 8], count=8, delay=.12,
             offset=[0, 0, CHEST], life=[.4, .55], size=[1.2, 2.0], speed=[35, 60], drag=.12, alpha=245, color=W,
             rot=True, spin=[-200, 200], fade_out=.5, **LOCK),
        dict(id='filaments', tex='sarada_filament', shape='ring', radius=16, thickness=4, height=[4, 30], count=8,
             delay=.35, orient='vertical', life=[.4, .6], size=[10, 14], up=[25, 40], alpha=[170, 230], color=W,
             anim_rate=1.5, fade_in=.3, fade_out=.5, **LOCK),
    ]


def eye_layers():
    """Œil : le motif du Mangekyō (rouge qui respire, bord sombre intégré), une lueur minuscule. Pas de halo."""
    out = relay(dict(id='iris', tex='sarada_eye', shape='point', size=[.9, .9], alpha=255, color=W, anim_rate=.625,
                     **LOCK), 1.6)
    out += relay(dict(id='glint', tex='sarada_glow', shape='point', size=[1.8, 1.8], alpha=45, color=W,
                      pulse_alpha=[.25, .6], **LOCK), 1.6, alpha_blend=False)
    return out


# cible : centre du symbole à hauteur de buste
TGT = [0, 0, CHEST]


def target_layers():
    """acquire (0-0,35 s) : les éclats et lignes convergent ; lock (0,3-0,45) : les arcs se resserrent, l'iris se
    pose ; maintain (dès 0,35, en boucle) : arcs, iris et orbite tournent lentement en sens opposés, pupille sombre,
    matière attirée vers le centre. Une seule particule ; le relâchement est sarada_target_release."""
    M = .35
    out = [
        dict(id='converge', tex='sarada_fragment', seq=[0, 3], shape='ring', radius=46, ring_even=True, ring_count=6,
             count=6, offset=TGT, life=[.36, .36], size=[3.4, 3.4], speed=[-150, -150], drag=.06, alpha=250, color=W,
             rot=True, spin=[-120, 120], fade_in_s=.06, fade_out=.25, **LOCK),
        dict(id='lock', tex='sarada_ring', seq=[0, 0], shape='point', count=1, delay=.25, offset=TGT, life=[.22, .22],
             size=[22, 22], grow=[1.8, 1.0, .3], alpha=255, color=W, turn=30, fade_in_s=.05, fade_out=.3, **LOCK),
        dict(id='lock_spark', tex='sarada_spark', shape='point', count=1, delay=.33, offset=TGT, life=[.12, .12],
             size=[3.5, 3.5], grow=[.4, 1.2, .3], alpha=255, color=W, fade_out=.7, **LOCK),
    ]
    D = dict(delay=M)
    out += relay(dict(id='arcs', tex='sarada_ring', seq=[0, 0], shape='point', offset=TGT, size=[22, 22], alpha=240,
                      color=W, turn=30, pulse_alpha=[.12, .7], **LOCK, **D), 12.0)
    out += relay(dict(id='iris', tex='sarada_ring', seq=[1, 1], shape='point', offset=TGT, size=[16, 16], alpha=230,
                      color=W, turn=-40, **LOCK, **D), 3.0, grow_in=.15)
    out += relay(dict(id='ticks', tex='sarada_ring', seq=[2, 2], shape='point', offset=TGT, size=[24, 24], alpha=200,
                      color=W, turn=15, **LOCK, **D), 2.0)
    out += relay(dict(id='pupil', tex='sarada_void', shape='point', offset=TGT, size=[2.4, 2.4], alpha=230, color=W,
                      pulse=.3, **LOCK, **D), 2.0, grow_in=.12)
    pull = dict(id='pulled', tex='ohirume_gravity', render='trail', trail=[.1, .14], shape='sphere', spread=[15, 21],
                offset=TGT, speed=[-28, -20], rate=6, life=[.5, .6], size=[.5, .8], alpha=[200, 240], color=W,
                fade_in=.2, fade_out=.35, **LOCK, **D)
    out += [pull]
    return out


def target_release_layers():
    """0,4 s : les arcs s'ouvrent et s'éteignent, l'iris file, la pupille se résorbe, les éclats se dispersent."""
    return [
        dict(id='arcs', tex='sarada_ring', seq=[0, 0], shape='point', count=1, offset=TGT, life=[.4, .4],
             size=[22, 22], grow=[1.0, 1.6, .5], alpha=240, color=W, turn=90, fade_out=.8, **LOCK),
        dict(id='iris', tex='sarada_ring', seq=[1, 1], shape='point', count=1, offset=TGT, life=[.3, .3],
             size=[16, 16], grow=[1.0, .3, .5], alpha=230, color=W, turn=-260, fade_out=.7, **LOCK),
        dict(id='pupil', tex='sarada_void', shape='point', count=1, offset=TGT, life=[.25, .25], size=[2.4, 2.4],
             grow=[1.0, 0.0, .5], alpha=230, color=W, **LOCK),
        dict(id='ripple', tex='sarada_distort', seq=[1, 1], shape='point', count=1, offset=TGT, life=[.35, .35],
             size=[26, 26], grow=[.6, 1.3, .3], alpha=200, color=W, fade_out=.7, **LOCK),
        dict(id='scatter', tex='sarada_fragment', seq=[0, 3], shape='ring', radius=14, ring_even=True, ring_count=6,
             count=6, offset=TGT, life=[.35, .4], size=[1.6, 2.0], speed=[70, 100], drag=.1, alpha=240, color=W,
             rot=True, spin=[-200, 200], fade_out=.6, **LOCK),
    ]


def attract_trail_layers():
    """Traînée d'attraction (CP0 = centre du personnage attiré, qui bouge ; rien n'est verrouillé : la traînée reste dans le
    monde). Ruban sombre qui s'affine (compression), filaments-aiguilles tirés vers le personnage, éclats de vide qui
    se résorbent, rares étincelles rouges."""
    C = [0, 0, 0]                                 # CP0 = centre du personnage (buste), pas ses pieds
    return [
        dict(id='ribbon', tex='sarada_streak', render='rope', shape='point', offset=C, rate=40, life=[.38, .38],
             size=[8, 8], shrink=.05, alpha=235, color=W, texel=36, fade_out=.4),
        dict(id='filaments', tex='ohirume_gravity', render='trail', trail=[.12, .18], shape='sphere', spread=[10, 18],
             offset=C, rate=26, life=[.3, .45], size=[.7, 1.1], pull=900, drag=.05, alpha=[210, 250], color=W,
             fade_in=.2, fade_out=.4),
        dict(id='void', tex='sarada_fragment', seq=[0, 3], shape='sphere', spread=[6, 14], offset=C, rate=10,
             life=[.4, .6], size=[1.4, 2.4], shrink=0.0, alpha=240, color=W, rot=True, spin=[-160, 160]),
        dict(id='sparks', tex='sarada_spark', shape='sphere', spread=[4, 12], offset=C, rate=6, life=[.2, .3],
             size=[.7, 1.1], alpha=200, color=W, fade_out=.6),
    ]


# ====================================================================== ŌHIRUME
SIZES = {'': 16.0, '_s': 6.0, '_l': 36.0}         # rayon du noyau (u) ; 5 à 250 cm de diamètre dans le manga
VOID_K = 1 / .80                                  # sprite du noyau / de la coque : noyau à 80 % du rayon du sprite
RING_K = 1.25 / .94                               # anneau à 1,25 R (texture : anneau à 94 %)
RING2_K = 1.38 / .94
DIST_K = 2.3                                      # distorsion : creuse jusqu'à 0,6 x 2,3 R = 1,38 R


def sph(R, **kw):
    """Les pièces d'une sphère (sans émission) : noyau, coque, deux anneaux, distorsion."""
    return dict(
        void=dict(id='void', tex='ohirume_void', shape='point', size=[r2(R * VOID_K)] * 2, alpha=255, color=W, **kw),
        core=dict(id='shell', tex='ohirume_core', shape='point', size=[r2(R * VOID_K)] * 2, alpha=255, color=W, **kw),
        ring=dict(id='ring', tex='ohirume_ring', seq=[0, 0], shape='point', size=[r2(R * RING_K)] * 2, alpha=245,
                  color=W, turn=40, **kw),
        ring2=dict(id='ring2', tex='ohirume_ring', seq=[1, 1], shape='point', size=[r2(R * RING2_K)] * 2, alpha=170,
                   color=W, turn=-25, pulse_alpha=[.2, .5], **kw),
        dist=dict(id='distort', tex='ohirume_distort', shape='point', size=[r2(R * DIST_K)] * 2, alpha=150, color=W,
                  anim_rate=.625, **kw))


def gravity(R, k, **kw):
    """Matière attirée : aiguilles qui naissent autour de la sphère et filent vers son centre en accélérant,
    avalées au contact (fade_near)."""
    return dict(dict(id='gravity', tex='ohirume_gravity', render='trail', trail=[.16, .22], shape='sphere',
                     spread=[r2(2.2 * R), r2(2.9 * R)], speed=[r2(-2.4 * R), r2(-1.7 * R)], pull=r2(7 * R), drag=.04,
                     rate=r2(16 * k), life=[.45, .6], size=[r2(max(.5, .09 * R)), r2(max(.8, .14 * R))],
                     alpha=[200, 245], color=W, fade_in=.25, fade_near=[0, r2(.95 * R), r2(1.3 * R)]), **kw)


def debris(R, k, **kw):
    """Éclats de vide qui spiralent lentement vers le noyau."""
    return dict(dict(id='debris', tex='ohirume_fragment', seq=[0, 3], shape='sphere', spread=[r2(2.0 * R), r2(2.8 * R)],
                     speed=[r2(-1.1 * R), r2(-.7 * R)], twist=r2(3 * R), rate=r2(2.2 * k), life=[.9, 1.2],
                     size=[r2(max(.6, .1 * R)), r2(max(.9, .15 * R))], alpha=245, color=W, rot=True, spin=[-120, 120],
                     fade_in=.2, fade_near=[0, r2(.95 * R), r2(1.25 * R)]), **kw)


def sphere_layers(R):
    """Boucle (avec formation de 0,35 s) : distorsion -> anneau rouge -> coque d'énergie -> noyau noir ; matière
    attirée visible même immobile."""
    k = R / 16.0; P = sph(R, **LOCK); out = []
    out += relay(P['dist'], 1.6, grow_in=.35)
    out += relay(P['ring2'], 360 / 25)
    out += relay(P['ring'], 360 / 40, grow_in=.3)
    out += relay(P['core'], 2.0, grow_in=.3)
    out += relay(P['void'], 2.0, grow_in=.3)
    g = gravity(R, max(k, .5), **LOCK); d = debris(R, max(k, .5), **LOCK)
    out += [g, primed(g, round(16 * max(k, .5) * .5), .6), d, primed(d, round(2.2 * max(k, .5) * 1.1), 1.2)]
    return out


def sphere_end_layers(R):
    """0,35 s : la sphère se résorbe (noyau, coque, anneaux ensemble), quelques éclats relâchés."""
    P = sph(R, **LOCK); L = .35
    out = [dict(P[n], count=1, life=[L, L], grow=[1.0, 0.0, .65], fade_out=.3) for n in ('void', 'core', 'ring')]
    out.append(dict(P['dist'], count=1, life=[L * .8] * 2, grow=[1.0, .35, .5], anim_rate=2.5, fade_out=.7))
    out.append(dict(debris(R, 1, **LOCK), id='release', count=6, rate=0, spread=[r2(1.1 * R), r2(1.3 * R)],
                    speed=[r2(2 * R), r2(3 * R)], twist=0, life=[.3, .35], fade_near=None, fade_out=.6))
    for L_ in out:
        if L_.get('fade_near') is None:
            L_.pop('fade_near', None)
        if not L_.get('rate'):
            L_.pop('rate', None)
    return out


def impact_layers(R=12.0, t0=0.0, cp=0):
    """~0,5 s : compression (tout est aspiré) -> flash rouge bref -> onde de gravité fine -> effondrement du vide.
    Pas d'explosion classique."""
    C = .12 + t0
    P = sph(R, cp=cp)
    return [
        dict(P['ring'], id='squeeze', count=1, delay=t0, life=[.13, .13], size=[r2(R * 3)] * 2, grow=[1.0, .15, .6],
             turn=220, fade_in_s=.03),
        dict(P['dist'], id='suck', count=1, delay=t0, life=[.14, .14], size=[r2(R * 3.2)] * 2, grow=[1.0, .2, .6],
             anim_rate=5, fade_in_s=.03, fade_out=.2),
        dict(id='inrush', tex='ohirume_gravity', render='trail', trail=[.05, .07], shape='sphere', cp=cp,
             spread=[r2(2.2 * R), r2(2.8 * R)], speed=[r2(-20 * R), r2(-15 * R)], count=14, delay=t0,
             life=[.11, .12], size=[.6, .9], alpha=240, color=W),
        dict(id='flash', tex='sarada_spark', shape='point', cp=cp, count=1, delay=C, life=[.07, .07],
             size=[r2(R * .9)] * 2, grow=[.5, 1.2, .3], alpha=255, color=W, rot=True),
        dict(P['ring'], id='wave', count=1, delay=C + .01, life=[.3, .3], size=[r2(R * 2.4)] * 2,
             grow=[.2, 1.0, .25], turn=60, fade_out=.7),
        dict(P['ring2'], id='wave2', count=1, delay=C + .05, life=[.28, .28], size=[r2(R * 3.0)] * 2,
             grow=[.2, 1.0, .25], fade_out=.8),
        dict(id='needles', tex='ohirume_gravity', render='trail', trail=[.05, .08], shape='sphere', cp=cp,
             spread=[r2(.3 * R), r2(.5 * R)], speed=[r2(14 * R), r2(20 * R)], drag=.12, count=10, delay=C + .01,
             life=[.16, .22], size=[.5, .8], alpha=230, color=W, fade_out=.5),
        dict(P['void'], id='collapse', count=1, delay=C, life=[.36, .36], size=[r2(R * .6 * VOID_K)] * 2,
             grow=[1.4, 0.0, .55], fade_in_s=.02),
        dict(P['core'], id='collapse_shell', count=1, delay=C, life=[.36, .36], size=[r2(R * .6 * VOID_K)] * 2,
             grow=[1.4, 0.0, .55], fade_in_s=.02),
    ]


def implosion_layers(R=16.0):
    """~1,15 s : expansion (0-0,25) -> stabilisation (0,25-0,5, vibre) -> compression (0,5-0,84) -> implosion
    (0,84-0,9) -> flash rouge bref -> disparition. Tout va vers l'intérieur. À lancer en détruisant ohirume_sphere."""
    L = .9
    seq = [['O_rscale', 1.0, 1.35, 0.0, .28, .35], ['O_rscale', 1.35, .3, .55, .93, .7], ['O_rscale', .3, 0.0, .93, 1.0, .5]]
    P = sph(R, **LOCK)
    out = [dict(P[n], count=1, life=[L, L], extra=seq) for n in ('void', 'core')]
    out += [dict(P['ring'], count=1, life=[L, L], extra=seq, turn=90, pulse_alpha=[.6, 6]),
            dict(P['ring2'], count=1, life=[L * .95] * 2, extra=seq, turn=-70),
            dict(P['dist'], count=1, life=[L, L], extra=seq, anim_rate=1.8)]
    g = gravity(R, 1.0, **LOCK)
    out += [dict(g, id='gravity', rate=10, duration=.5),
            dict(g, id='rush', delay=.48, duration=.36, rate=55, speed=[r2(-5 * R), r2(-4 * R)], pull=r2(18 * R),
                 life=[.22, .3], trail=[.06, .1])]
    F = .84
    out += [
        dict(id='flash', tex='sarada_spark', shape='point', count=1, delay=F, life=[.07, .07], size=[r2(R * .8)] * 2,
             grow=[.4, 1.2, .3], alpha=255, color=W, rot=True, **LOCK),
        dict(P['ring'], id='snap', count=1, delay=F, life=[.14, .14], size=[r2(R * 1.6)] * 2, grow=[.1, 1.0, .3],
             fade_out=.7),
        dict(debris(R, 1, **LOCK), id='remains', count=6, delay=F + .02, spread=[1, 3], speed=[r2(.6 * R), r2(1.2 * R)],
             twist=0, life=[.25, .32], fade_out=.6),
    ]
    for L_ in out:
        if L_.get('id') == 'remains':
            L_.pop('rate', None); L_.pop('fade_near', None)
    return out


TRAVEL = .55                                      # vol CP0 -> CP1 (s)
LAUNCH = .45                                      # fin de la charge


def projectile_layers(R=10.0):
    """Spawn (0-0,25) -> charge (matière aspirée, 0,15-0,45) -> départ (onde fine) -> vol CP0 -> CP1 en 0,55 s
    (la sphère garde ses pièces ; sillage en ruban qui s'affine, débris happés) -> impact à CP1 (ohirume_impact)."""
    P = sph(R, **LOCK); k = R / 16
    out = [dict(P[n], count=1, life=[LAUNCH, LAUNCH], grow=[.08, 1.0, .3, .6], fade_out_s=.03)
           for n in ('void', 'core', 'ring', 'dist')]
    g = gravity(R, 1.0, **LOCK)
    out += [dict(g, id='charge', delay=.12, duration=.33, rate=40, life=[.25, .32], pull=r2(14 * R)),
            dict(P['ring2'], id='launch_wave', count=1, delay=LAUNCH - .02, life=[.22, .22], size=[r2(R * 3)] * 2,
                 grow=[.3, 1.0, .3], fade_out=.7)]
    fly = dict(delay=LAUNCH, life=[TRAVEL + .02] * 2, path_travel=[TRAVEL, 0, 0, 0, 0], cp=0, cp_end=1)
    for n in ('dist', 'ring', 'core', 'void'):
        L_ = dict(P[n], count=1, **fly); L_['id'] += '_fly'; L_.pop('attach', None); out.append(L_)
    n_wake = int(70 * TRAVEL)
    out += [
        dict(id='wake', tex='ohirume_streak', render='rope', shape='chain_seq', cp=0, cp_end=1, path_count=n_wake,
             spread=[0, 0], rate=70, duration=TRAVEL, delay=LAUNCH, life=[.3, .3], size=[r2(R * .55)] * 2, shrink=.05,
             alpha=235, color=W, texel=r2(R * 3), fade_out=.4),
        dict(id='swallowed', tex='ohirume_fragment', seq=[0, 3], shape='chain_seq', cp=0, cp_end=1,
             path_count=int(40 * TRAVEL), spread=[0, r2(1.8 * R)], rate=40, duration=TRAVEL, delay=LAUNCH,
             life=[.22, .3], size=[r2(.14 * R), r2(.22 * R)], shrink=0.0, alpha=240, color=W, rot=True,
             spin=[-200, 200]),
    ]
    out += impact_layers(R=max(10.0, R), t0=LAUNCH + TRAVEL - .02, cp=1)
    return out


def pull_layers():
    """Attraction (CP0 = sphère, CP1 = cible) : tout converge vers la sphère le long du trajet, en entonnoir large
    autour de la cible (l'espace y est tiré) et serré à la sphère : longues aiguilles-filaments, traînées plus
    épaisses, éclats de vide qui tournoient, rares étincelles. Avalés au contact de la sphère."""
    path = dict(cp=1, cp_end=0, path_travel=[.6, 26, 12, 0, 8])
    base = dict(shape='sphere', spread=[6, 26], color=W, fade_near=[0, 12, 20], **path)
    return [
        dict(base, id='filaments', tex='ohirume_gravity', render='trail', trail=[.3, .42], rate=30, life=[.6, .66],
             size=[.4, .6], alpha=[200, 240], fade_in=.15),
        dict(base, id='streaks', tex='ohirume_gravity', render='trail', trail=[.12, .18], rate=18, life=[.6, .66],
             size=[.8, 1.2], alpha=[225, 255], fade_in=.12),
        dict(base, id='fragments', tex='ohirume_fragment', seq=[0, 3], rate=7, life=[.6, .66], size=[1.2, 2.0],
             alpha=245, rot=True, spin=[-200, 200], fade_in=.15),
        dict(base, id='sparks', tex='sarada_spark', rate=4, life=[.6, .66], size=[.6, 1.0], alpha=210, fade_in=.3),
    ]


def orbit_layers():
    """4 sphères en orbite autour de Sarada (90 °/s : un tour en 4 s = la période de relais, donc chaque copie neuve
    naît exactement où est l'ancienne). Tailles et hauteurs différentes, pièces de la sphère (distorsion, anneaux,
    coque, noyau) +
    sillage d'orbite en aiguilles. ~48 particules pour les 4."""
    T = 4.0; out = []
    spheres = [(0, 6.5, 50), (90, 4.5, 40), (180, 8.0, 58), (270, 5.5, 44)]
    for i, (yaw, R, z) in enumerate(spheres):
        pos = dict(shape='ring', radius=34, ring_even=True, ring_count=1, ring_yaw=yaw, offset=[0, 0, z],
                   motion=[{'type': 'orbit', 'speed': .5, 'direction': 1}], **LOCK)
        P = sph(R)
        for n in ('dist', 'ring2', 'ring', 'core', 'void'):
            piece = dict(P[n], **pos, id=f'{n}{i}')
            piece.pop('shape', None); piece['shape'] = 'ring'
            if n == 'ring':
                piece['turn'] = 90                       # un tour par période : la copie neuve recouvre l'ancienne
            if n == 'ring2':
                piece['turn'] = -90
            if n == 'dist':
                piece['anim_rate'] = .5                  # 2 cycles de planche par période
            out += relay(piece, T, grow_in=.3)
    trail = dict(id='trail', tex='ohirume_gravity', render='trail', trail=[.2, .28], shape='ring', radius=34,
                 thickness=3, height=[40, 58], rate=20, life=[.35, .45], size=[.6, .9], alpha=[180, 230], color=W,
                 motion=[{'type': 'orbit', 'speed': .5, 'direction': 1}], fade_in=.2, fade_out=.5, **LOCK)
    out += [trail, primed(trail, 5, .45)]
    return out


def float_layers():
    """Lévitation : deux anneaux fins posés sous les pieds qui tournent en sens opposés, micro-éclats et petits
    filaments qui montent. Très léger."""
    out = []
    out += relay(dict(id='ring', tex='ohirume_ring', seq=[0, 0], shape='point', orient='ground', offset=[0, 0, 1],
                      size=[14, 14], alpha=200, color=W, turn=20, **LOCK), 18.0, grow_in=.25)
    out += relay(dict(id='ring_in', tex='ohirume_ring', seq=[1, 1], shape='point', orient='ground', offset=[0, 0, 1.5],
                      size=[9, 9], alpha=170, color=W, turn=-30, **LOCK), 12.0, grow_in=.25)
    frag = dict(id='rise', tex='sarada_fragment', seq=[0, 3], shape='disc', spread=[3, 12], height=[0, 4], rate=6,
                life=[.6, 1.0], size=[.5, 1.0], up=[14, 24], alpha=230, color=W, rot=True, spin=[-120, 120],
                fade_in=.2, fade_out=.5, **LOCK)
    fil = dict(id='filaments', tex='sarada_filament', shape='ring', radius=8, thickness=4, height=[0, 6], rate=3,
               orient='vertical', life=[.5, .8], size=[3, 5], up=[18, 28], alpha=[160, 220], color=W, anim_rate=1.5,
               fade_in=.3, fade_out=.5, **LOCK)
    out += [frag, primed(frag, 5, 1.0), fil, primed(fil, 2, .8)]
    return out


def systems():
    S = {}
    S['sarada_aura'] = dict(about='aura sombre et carmin très légère, en boucle (CP0 = pieds)', layers=aura_layers())
    S['sarada_activate'] = dict(about='activation du Mangekyō, 0,7 s (lancer sarada_aura à 0,45 s)',
                                layers=activate_layers())
    S['sarada_eye'] = dict(about='Mangekyō sur l\'œil, rouge qui respire, en boucle (CP0 = l\'œil)', layers=eye_layers())
    S['sarada_target'] = dict(about='verrouillage d\'une cible : acquire -> lock -> maintain en boucle (CP0 = pieds '
                                    'de la cible)', layers=target_layers())
    S['sarada_target_release'] = dict(about='relâchement de la cible, 0,4 s (détruire sarada_target)',
                                      layers=target_release_layers())
    S['sarada_attract_trail'] = dict(about='traînée gravitationnelle du personnage attiré (CP0 = son buste, en mouvement)',
                                     layers=attract_trail_layers())
    for suf, R in SIZES.items():
        S[f'ohirume_sphere{suf}'] = dict(about=f'sphère de gravité (noyau {int(R)} u), se forme en 0,35 s puis boucle '
                                               f'(CP0 = centre)', layers=sphere_layers(R))
    S['ohirume_sphere_end'] = dict(about='la sphère (taille normale) se résorbe, 0,35 s', layers=sphere_end_layers(16.0))
    S['ohirume_projectile'] = dict(about=f'sphère lancée : charge 0,45 s, vol {TRAVEL} s CP0 -> CP1, impact à CP1',
                                   layers=projectile_layers())
    S['ohirume_pull'] = dict(about='attraction de la cible (CP1) vers la sphère (CP0), en boucle', layers=pull_layers())
    S['ohirume_impact'] = dict(about='compression gravitationnelle, ~0,5 s (CP0 = point d\'impact)',
                               layers=impact_layers())
    S['ohirume_implosion'] = dict(about='la sphère s\'effondre sur elle-même, ~1,15 s (CP0 = centre)',
                                  layers=implosion_layers())
    S['ohirume_orbit'] = dict(about='4 sphères en orbite autour de Sarada, en boucle (CP0 = pieds)',
                              layers=orbit_layers())
    S['ohirume_float'] = dict(about='lévitation discrète sous les pieds, en boucle (CP0 = pieds)', layers=float_layers())
    return S


def build():
    return dict(prefix='sarada_ohirume', prefixes=['sarada', 'ohirume'], exact_names=True,
                title='Sarada — Mangekyō Sharingan / Ōhirume', materials='sarada_ohirume', file='sarada_ohirume.pcf',
                budget=200, bbox=220, draw_distance=4000, hide_children=True,
                texture_size={'sarada_spark': 64, 'ohirume_gravity': 64}, systems=systems())


HEAD_ = ('# Généré par examples/gen_sarada_ohirume.py — modifier le script plutôt que ce fichier.\n'
         '# Pack Sarada — Mangekyō Sharingan / Ōhirume : un seul PCF, systèmes sarada_* et ohirume_*.\n')

if __name__ == '__main__':
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sarada_ohirume.yaml')
    open(path, 'w', encoding='utf-8').write(HEAD_ + yaml.safe_dump(build(), allow_unicode=True, sort_keys=False,
                                                                    width=120))
    print(path)
