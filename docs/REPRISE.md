# État du projet (02/10/2026)

Outil : **pcfforge** (Python). Mode d'emploi : `docs/GUIDE.md`. Journal des tests en jeu et des leçons :
`docs/LIMITES.md`. Références et ce qu'on en a tiré : `references/README.md`.

## Installation

```
python -m venv venv && . venv/bin/activate      (Windows : venv\Scripts\activate)
pip install -r requirements.txt pytest
python -m pytest -q tests                        # 138 tests attendus
python -m pcfforge doctor
```

**Python 3.11 maximum** : `srctools==2.3.13` n'a de version compilée que jusqu'à 3.11. En 3.12 / 3.13, pip installe
la version pur Python, qui ne sait pas écrire le DXT1 (« Saving DXT1 not implemented »).
Avec uv : `uv venv --python 3.11 venv && uv pip install --python venv/Scripts/python.exe -r requirements.txt pytest`.

## Effets

| Effet | Source | Particules | État en jeu |
|---|---|---|---|
| Sarada — Mangekyō / Ōhirume | `examples/gen_sarada_ohirume.py`, archive : `examples/package_sarada_ohirume.py` | 16 : `sarada_aura`, `_activate`, `_eye`, `_target(_release)`, `_attract_trail` ; `ohirume_sphere(_s/_l/_end)`, `_projectile`, `_pull`, `_impact`, `_implosion`, `_orbit`, `_float` | non vu en jeu |
| Bouclier Black Clover | `examples/gen_bc_shield.py` | `bc_shield_start` → `bc_shield_loop` (lancé à 1,1 s) → `bc_shield_end` | v4 vue en jeu, v5 à valider |
| Zone Black Clover | `examples/gen_bc_zone.py` | `bc_zone_start` → `bc_zone_loop` (lancé à 0,5 s) → `bc_zone_end` | non vue en jeu |
| Aura Abyss | `examples/abyss_aura.yaml` | aura sur `sword_persee` | **validée** : base de qualité |
| Aura Darui | `examples/darui_aura.yaml` | foudre noire sur `sword_darui` | v4 à valider |
| Aura Berserk | `examples/berserk_aura.yaml` | miasme et encre sur `sword_persee` | à valider |
| Aura Hiramekarei | `examples/hiramekarei_aura.yaml` | chakra sur la silhouette de l'épée | v3 à valider |
| Exemples simples | `examples/chakra_*`, `examples/energy_*` | effets de base | exemples |

Modèles d'armes réels (tests) : `tests/fixtures/{hiramekarei,berserk,darui}`.

## Commandes utiles

- `python -m pcfforge generate <spec>` : addon complet dans `out/<id>_fx/`.
- `python -m pcfforge pack <spec>` : zip à donner dans `out/share/<id>.zip`.
- `python -m pcfforge drop <spec...>` : PCF, matériaux et chargeur, à fusionner dans `garrysmod/`.
- `python -m pcfforge preview <spec> --chain 'start:0,loop:1.1:4.5!,end:4.5'` : GIF approximatif hors moteur
  (`!` = système détruit d'un coup). Options : `--cp0`, `--cp1`, `--cp0-vel`, `--bg`, `--size`, `--views`, `--figure`.
- `python -m pcfforge analyze <pcf>` : analyse lisible d'un PCF de référence.
- `python -m pcfforge model inspect <mdl>` : os, attachements, hitboxes d'un modèle.
- En jeu (runtime) : `pcfforge_attach <id>`, `pcfforge_debug 1`, `pcfforge_clear`.
- Pack Sarada : `sarada_ohirume_test <particule> [secondes]`.

## À valider en jeu

1. Pack Sarada / Ōhirume : lisibilité du noir et du carmin sur une map de jour, vol du projectile (0,55 s quelle
   que soit la distance), entonnoir de `ohirume_pull`, rubans de traînée.
2. Bouclier v5 et zone Black Clover.
3. Auras Darui, Berserk et Hiramekarei.

## Règles de travail

- Ne jamais décrire un rendu non vu : seul Garry's Mod fait foi.
- Base de qualité : `abyss_aura`, calibrée sur `references/fsc_aura2.pcf`.
- Chaque effet a son propre langage visuel. Pas de sprites ronds isolés, les traits suivent la géométrie.
- Matière sombre en mélange alpha, additif réservé aux lueurs faibles (sinon néon sur fond clair).
- Poser les questions de style (forme, couleur, taille, découpage) avant de générer quand c'est ambigu.
