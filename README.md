# pcfforge — atelier de particules Garry's Mod

pcfforge transforme une description courte (une spec YAML ou un script Python) en particules prêtes pour Garry's Mod :
fichier `.pcf`, textures VTF/VMT et chargeur Lua. Les effets sont pensés pour un serveur Naruto RP : auras d'armes,
techniques en plusieurs temps (apparition, maintien, fin), packs autonomes à distribuer.

## Effets du dépôt

| Effet | Fichiers | Description | État en jeu |
|---|---|---|---|
| **Sarada — Mangekyō Sharingan / Ōhirume** | `examples/gen_sarada_ohirume.py` | pack autonome de 16 particules (aura, activation, œil, verrouillage, traînée d'attraction, sphères de gravité, projectile, attraction, impact, implosion, orbite de 4 sphères, lévitation) + motif du Mangekyō | non vu en jeu |
| **Bouclier Black Clover** | `examples/gen_bc_shield.py` | bulle ovale bleu-violet : un cercle s'ouvre au sol, le bouclier en sort, boucle animée, éclatement | v4 vue en jeu, v5 à valider |
| **Zone de protection Black Clover** | `examples/gen_bc_zone.py` | cercle magique géométrique au sol (rayon 150 u), anneaux qui tournent | non vu en jeu |
| **Aura Abyss** | `examples/abyss_aura.yaml` | nébuleuse violette sur la lame de `sword_persee` | **validée** (référence de qualité) |
| **Aura Darui** | `examples/darui_aura.yaml` | foudre noire qui fait le tour de la lame de `sword_darui` | à valider |
| **Aura Berserk** | `examples/berserk_aura.yaml` | miasme noir et pointes d'encre sur `sword_persee` | à valider |
| **Aura Hiramekarei** | `examples/hiramekarei_aura.yaml` | chakra le long de la silhouette de l'épée | à valider |
| Exemples simples | `examples/chakra_*.yaml`, `examples/energy_*.yaml` | aura, explosion, impact, projectile, traînée, vortex | exemples de base |

Les auras d'armes suivent le modèle réel de l'arme (lecture du `.mdl`) ; les autres effets sont autonomes.

## Installation

Python **3.11** (la bibliothèque `srctools` n'a pas de version compilée au-delà).

```
python -m venv venv
venv\Scripts\activate                 (Linux / macOS : . venv/bin/activate)
pip install -r requirements.txt pytest
python -m pytest -q tests
python -m pcfforge doctor
```

## Utilisation

| Commande | Résultat |
|---|---|
| `python -m pcfforge generate <spec>` | addon complet dans `out/<id>_fx/` |
| `python -m pcfforge pack <spec>` | zip à donner dans `out/share/<id>.zip`, à extraire dans `garrysmod/addons/` |
| `python -m pcfforge preview <spec> --chain 'start:0,loop:1:4!,end:4'` | GIF d'aperçu (simulation hors moteur) |
| `python -m pcfforge lint <spec>` / `validate <pcf>` | vérification d'une spec / d'un PCF |
| `python -m pcfforge analyze <pcf>` | lecture d'un PCF de référence (débits, tailles, couleurs) |
| `python -m pcfforge model inspect <mdl>` | os, attachements et hitboxes d'un modèle |

Les effets écrits en script se génèrent d'abord : `python examples/gen_<effet>.py`, puis `generate` ou `pack`.
Le pack Sarada a son propre assembleur : `python examples/package_sarada_ohirume.py` produit
`out/share/pcfforge_sarada_ohirume.zip` (PCF, matériaux, textures, documentation, aperçus).

## Organisation

| Dossier | Contenu |
|---|---|
| `pcfforge/` | l'outil : couches, textures procédurales, écriture du PCF (format de l'éditeur Valve), lint, aperçu |
| `pcfforge/model/` | lecture des modèles MDL/VVD (os, régions, silhouette d'une lame) |
| `examples/` | les effets (specs YAML et scripts de génération) |
| `gmod/` | runtime Lua client, captures en jeu, lanceur Windows |
| `references/` | PCF de référence et ce qu'on en a appris |
| `docs/` | `GUIDE.md` (mode d'emploi), `LIMITES.md` (journal : ce qui est vu en jeu ou non), `REPRISE.md` (état) |
| `tests/` | tests automatiques, modèles d'armes réels dans `fixtures/` |

## Statut

Les PCF sont générés et relus hors moteur, tous les tests passent. Le rendu réel se juge uniquement dans
Garry's Mod : l'état de chaque effet est suivi dans `docs/LIMITES.md`.
