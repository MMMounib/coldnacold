"""Visual parser: a natural request (FR / EN) -> EffectSpec dict (then `effect.normalize`).

Rule based and deterministic. It never invents a model: model-driven mode is chosen only when the
request talks about a model / bone / attachment (then the path must be given). Anything it could not
decide is listed in `unresolved` so the user can be asked instead of guessing.
"""
import re
import unicodedata

WORDS = {
    'shape': {
        'aura': ['aura', 'autour du joueur', 'autour du corps', 'around the player', 'enveloppe'],
        'burst': ['explosion', 'burst', 'eclat', 'déflagration', 'deflagration', 'libere', 'release'],
        'projectile': ['projectile', 'boule', 'ball', 'tir', 'fleche', 'arrow', 'missile'],
        'impact': ['impact', 'collision', 'hit'],
        'vortex': ['vortex', 'tornade', 'tourbillon', 'tornado', 'cyclone'],
        'trail': ['trainee', 'trail', 'sillage'],
        'beam': ['rayon', 'beam', 'laser', 'lien', 'link'],
        'ring': ['anneau', 'ring', 'onde de choc', 'shockwave'],
        'spiral': ['spirale', 'spiral'],
        'cloud': ['nuage', 'cloud', 'brume', 'mist'],
    },
    'energy': {
        'chakra': ['chakra'], 'fire': ['feu', 'fire', 'flamme', 'katon', 'braise'],
        'black_lightning': ['foudre noire', 'kuro kaminari', 'black lightning', 'eclair noir'],
        'lightning': ['foudre', 'eclair', 'lightning', 'raiton', 'electri'],
        'wind': ['vent', 'wind', 'futon', 'air'], 'water': ['eau', 'water', 'suiton', 'aqua'],
        'smoke': ['fumee', 'smoke'], 'demonic': ['demon', 'berserk', 'maudit', 'cursed', 'infernal'],
        'abyss': ['abysse', 'abyss', 'void', 'cosmique', 'cosmic', 'galaxie', 'nebuleuse', 'nebula'], 'magic': ['magie', 'magic', 'arcane', 'mystique'],
        'plasma': ['plasma'], 'dust': ['poussiere', 'sable', 'dust', 'sand'], 'ash': ['cendre', 'ash'],
    },
    'look': {
        'soft': ['doux', 'douce', 'soft'], 'sharp': ['net', 'nette', 'tranchant', 'sharp'],
        'anime': ['anime', 'manga'], 'cartoon': ['cartoon', 'dessin anime'],
        'energetic': ['energique', 'dynamique', 'energetic'], 'mystical': ['mystique', 'mystical', 'mysterieu'],
        'aggressive': ['agressi', 'violent', 'brutal', 'aggressive'], 'elegant': ['elegant', 'raffine', 'fin', 'subtil'],
        'dense': ['dense', 'massif', 'epais'], 'minimal': ['minimal', 'sobre', 'discret', 'leger', 'legere'],
    },
    'motion': {
        'orbit': ['tourne autour', 'orbite', 'orbit', 'tournent autour'], 'spiral': ['spirale', 'spiral'],
        'vortex': ['aspire', 'vortex'], 'converge': ['converge', 'se rassemble', 'charge'],
        'rise': ['monte', 'rise', 's echappe', 'qui s echappent'], 'fall': ['tombe', 'retombe', 'fall'],
        'flow': ['coule', 'circule', 'flow', 'ondule'], 'whip': ['fouet', 'whip'],
        'oscillate': ['oscille', 'pulse', 'respir', 'pulsation'],
    },
}
COLORS = {
    'bleu ciel': [120, 205, 255], 'sky blue': [120, 205, 255], 'bleu': [80, 160, 255], 'blue': [80, 160, 255],
    'cyan': [80, 230, 255], 'violet': [170, 90, 255], 'purple': [170, 90, 255], 'rouge': [255, 60, 50],
    'red': [255, 60, 50], 'orange': [255, 140, 40], 'jaune': [255, 220, 70], 'yellow': [255, 220, 70],
    'or': [255, 200, 80], 'dore': [255, 200, 80], 'gold': [255, 200, 80], 'vert': [90, 230, 120],
    'green': [90, 230, 120], 'rose': [255, 120, 200], 'pink': [255, 120, 200], 'blanc': [240, 245, 255],
    'white': [240, 245, 255], 'noir': [40, 30, 50], 'black': [40, 30, 50],
}
INTENSITY = [(('extreme', 'enorme', 'massive', 'extreme'), .95), (('fort', 'forte', 'puissant', 'strong', 'intense'), .8),
             (('moyen', 'moyenne', 'medium'), .6), (('faible', 'legere', 'leger', 'subtle', 'weak'), .35)]


def _plain(text):
    t = unicodedata.normalize('NFKD', text.lower())
    return ''.join(c for c in t if not unicodedata.combining(c)).replace("'", ' ').replace('-', ' ')


def _find(t, w):
    m = re.search(rf'\b{re.escape(w)}', t)          # word start: "air" must not match "eclair"
    return m.start() if m else -1


def _first(t, table):
    best, pos = None, None
    for key, words in table.items():
        for w in words:
            i = _find(t, w)
            if i >= 0 and (pos is None or i < pos):
                best, pos = key, i
    return best


def _all(t, table):
    return [k for k, words in table.items() if any(_find(t, w) >= 0 for w in words)]


def parse(text, effect_id=None):
    """Returns (spec_dict, unresolved_list)."""
    t = _plain(text)
    unresolved = []
    shape = _first(t, WORDS['shape'])
    energy = _first(t, WORDS['energy'])
    looks = _all(t, WORDS['look'])
    motions = _all(t, WORDS['motion'])
    color = next((c for name, c in sorted(COLORS.items(), key=lambda kv: -len(kv[0])) if re.search(rf'\b{name}\b', t)), None)
    intensity = next((v for words, v in INTENSITY if any(re.search(rf'\b{w}\b', t) for w in words)), None)

    spec = {'id': effect_id or re.sub(r'[^a-z0-9]+', '_', f"{energy or 'fx'}_{shape or 'effect'}").strip('_'),
            'prompt': text, 'mode': 'auto'}
    if not shape:
        unresolved.append('forme (aura, burst, projectile, impact, vortex, trail, beam…)')
    if not energy:
        unresolved.append('énergie (chakra, feu, foudre, vent, eau…)')
    if not color:
        unresolved.append('couleur')
    spec['style'] = {k: v for k, v in dict(type=energy or 'chakra', color=color, intensity=intensity,
                                            look=looks or None).items() if v is not None}
    spec['shape'] = {'type': shape or 'aura'}
    if motions:
        spec['behavior'] = {'motion': motions[0] if len(motions) == 1 else motions}
        if 'oscillate' in motions:
            spec['behavior']['pulse'] = 1.0
            spec['behavior']['motion'] = [m for m in motions if m != 'oscillate'] or None
            if spec['behavior']['motion'] is None:
                spec['behavior'].pop('motion')
    # model context: only when the request explicitly talks about it
    bone = re.search(r'\b(?:bone|os)\s+([a-z0-9_]+)', t)
    att = re.search(r'\battachment\s+([a-z0-9_]+)', t)
    if bone:
        spec['attachment'] = {'type': 'bone', 'name': bone.group(1)}
    elif att:
        spec['attachment'] = {'type': 'attachment', 'name': att.group(1)}
    elif re.search(r'\b(lame|blade)\b', t) and re.search(r'\b(modele|model|arme|weapon|epee|sword|katana)\b', t):
        spec['attachment'] = {'type': 'region', 'name': 'blade'}
    if spec.get('attachment'):
        unresolved.append('chemin du modèle .mdl (mode model_driven)')
    return spec, unresolved
