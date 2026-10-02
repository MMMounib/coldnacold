# pcfforge V3 — guide

Toutes les commandes : `python -m pcfforge <commande>` depuis la racine du dépôt.

## 1. Installation
```
python -m venv venv && venv\Scripts\activate        (Linux : . venv/bin/activate)
pip install -r requirements.txt
python -m pcfforge doctor
```
`doctor` affiche un statut par élément : OK, MISSING, OPTIONAL, NOT FOUND, NOT TESTED ou UNAVAILABLE.
Garry's Mod n'est nécessaire que pour `install` et `capture`.

## 2. Effet simple
```yaml
id: chakra_aura                 # minuscules : sert de préfixe aux systèmes
style: {type: chakra, color: [90, 190, 255], intensity: 0.7, look: [elegant]}
shape: {type: aura, radius: 34, height: 72}
```
`python -m pcfforge generate specs/chakra_aura.yaml` → `out/chakra_aura_fx/` (addon à copier dans `garrysmod/addons`).
Système à appeler : `chakra_aura_main`. Aucun modèle n'est requis (mode standalone).

Depuis une phrase : `python -m pcfforge parse "aura de chakra bleu élégante qui tourne autour du joueur"`.
La commande affiche une spec, puis les points non résolus (`# à préciser`), qu'il faut compléter au lieu de les deviner.

## 3. Effet complexe
Le composeur crée des couches hiérarchisées à partir de `shape` + `style` :
`core` (énergie principale) → `halo` → `filaments` → `sparks` → `secondary` → `accents` (anneau, flash…).
- `style.type` : chakra, fire, lightning, wind, water, smoke, magic, plasma, dust, ash…
- `style.look` : soft, sharp, anime, cartoon, energetic, mystical, aggressive, elegant, dense, minimal.
  Chaque look change le timing, la densité et la structure (couches ajoutées ou retirées), pas seulement la couleur.
- `shape.type` : aura, burst, projectile, impact, vortex, trail, beam, ring, spiral, cloud…
- Pour un contrôle total, `layers:` remplace la recette par une liste de presets
  (`python -m pcfforge presets`), chacun surchargeable (size, life, rate, color, motion…).

### Effet à plusieurs systèmes (format bas niveau)
Pour un sort en plusieurs moments (ex. `examples/bc_shield.yaml`), on utilise le format `prefix / systems / layers`.
Chaque système devient `<prefix>_<nom>`, est préchargé, et s'appelle par son nom :
`pcfforge_attach bc_shield_form`, ou `PCFForge.AttachEffect(ent, "bc_shield_loop")`.
Un système à particules persistantes (vie ≥ 600 s) est marqué `persistent` : `DetachEffect` le détruit tout de suite.
Formes utiles :
- `ring` + `ring_even` / `ring_count` / `ring_yaw` : anneau régulier. Avec `ring_yaw`, les rangées sont décalées.
  En corde avec `count = ring_count + 1`, le cercle est fermé.
- `dome` : surface d'une demi-sphère de rayon `radius`.
- `fade_in_s` : fondu d'entrée en secondes, indispensable quand la vie est très longue.
- `hide_in_first_person: true` : la couche n'est pas dessinée quand son point de contrôle est la caméra (gros sprite
  autour du joueur, qui couvrirait son écran). Non testé en jeu.
- `hide_children: true` (spec) : marque les sous-parties `preventNameBasedLookup`, pour que les outils de particules
  ne listent que les effets à appeler.
- Une clé de système égale au préfixe donne ce nom exact (`bc_shield`), sinon le nom est `<prefix>_<clé>`.
- `cp` / `cp_end` + `path_travel: [durée, dist. max départ, milieu, fin, courbe]` : la particule voyage de CP `cp` à
  CP `cp_end` en `durée` s, tenue près du trajet, qui suit les deux CP à chaque image (lien vers une cible : CP1 -> CP0).
- `fade_near: [cp, d0, d1]` : invisible à d0 du CP ou plus près, pleine à partir de d1 (matière avalée par une sphère).
- `render: rope` + `shape: path` + `path_live: true` : corde ré-émise en continu, toujours étalée d'un CP à l'autre.
- `spin_one_way: true` : `spin` tourne toujours dans le même sens. `fade_out_s` : fondu de sortie en secondes.
- Texture translucide (`blend: alpha`, ex. `oh_orb`) pour tout ce qui doit être NOIR : l'additif ne fait qu'éclaircir.
- Spec : `readme: [lignes]` est ajouté au LISEZMOI du zip (`pack`), par exemple pour expliquer les points de contrôle.
- **Additif seul = néon sans contraste sur fond clair.** Faire porter la matière par des textures translucides et
  garder l'additif pour des lueurs faibles. Vérifier chaque effet avec
  `preview <spec> --chain ... --views 0.3,1,2 [--figure 0,0,0]` : fond clair et fond sombre, angle bas et angle haut,
  planche PNG ; `--figure` pose une silhouette de 72 u pour voir ce que l'effet couvre.

## 4. Phases
```yaml
timeline:
  - {phase: charge, duration: 0.35}
  - {phase: release, duration: 0.25, scale: {rate: 1.5}}
  - {phase: aftermath, duration: 0.8}
```
Phases : charge, release, travel, impact, aftermath, persistent. Chaque phase a un début (cumulé) et une durée.
Elle peut multiplier `rate, count, size, life, alpha, speed` et imposer une `color`.
Une couche qui utilise une phase absente de la timeline provoque une erreur.
Les formes burst / impact / projectile ont une timeline par défaut.

## 5. Motions
`behavior: {motion: [orbit, {type: rise, speed: 1.5, turbulence: 0.3}]}`
Motions disponibles : static, orbit, spiral, vortex, converge, diverge, radial_burst, flow, whip, oscillate, rise, fall, follow, swirl.
Paramètres : speed, radius, height, turbulence (0..1), direction (1 / -1).
Chaque motion est traduite en opérateurs Source réels (voir `pcfforge/motions.py`). La turbulence est un bruit
de vitesse cohérent, pas un bruit blanc.

## 6. Variation
`variation: {scale: .25, lifetime: .2, rotation: .5, position: .15, velocity: .2, alpha: .15, color: .1, emission: .3}`
Valeurs 0..1 : 0,2 = ±20 % autour de la valeur de la couche. `emission` rend le débit irrégulier.
Si la variation est absente, le look fixe une valeur modérée.

## 7. Textures
`python -m pcfforge textures` liste les textures procédurales. Familles : glow / glow_hard, energy
(flipbook 8 images), spark, smoke, flame, streak, ring, slash, dust, noise, star, strand, lightning…
Seules les textures utilisées sont générées (cache dans `out/.cache`). Texture personnalisée :
`textures: {ma_tex: {src: "dossier/*.png", blend: add, fps: 24}}`.

## 8. Model-driven
Ce mode est optionnel. Il s'active si `model` est fourni, ou si `attachment.type` vaut bone / attachment / region.
```yaml
model: {path: chemin/vers/modele.mdl}
attachment: {type: region, name: blade}
```
Le `.mdl` (et son `.vvd` s'il est présent) est **réellement lu**. Voir `python -m pcfforge model inspect <mdl>`.
Modes d'attache : `entity` (origine), `bounds` (centre de la bounding box), `attachment` (attachment nommé),
`bone` (segment le long de l'os), `region` (portion de ce segment).

## 9. Bones
`attachment: {type: bone, name: RightHand}`. L'os doit exister : sinon, l'erreur liste les os du modèle.
L'axe principal est calculé sur les vertices pondérés à l'os (VVD), ou sur la hitbox à défaut.
CP0 = début et CP1 = fin, dans le repère de l'os. En jeu, le runtime les suit chaque frame.

### Silhouette (enveloppe)
Quand l'os a de la géométrie, l'analyseur mesure aussi la **silhouette** de la pièce : 9 tranches le long de l'axe,
avec les bords haut et bas dans le plan le plus large (lame plate). Le composeur agrandit cette silhouette avec
`shape.scale` (1 à 3, défaut 1,15), `shape.margin` (u, défaut 1,5), et `shape.rise` (défaut 16) (vitesse de montée des flammes, u/s). Il la transforme
ensuite en chaîne de points de contrôle :
- CP2… : contour fermé → flammes, reflets, particules ;
- points suivants : zigzag intérieur → remplissage translucide qui porte la forme.
Le runtime place ces points dans le repère de l'os à chaque frame (≤ 64 CP au total). Pour un modèle **low-poly** (moins de 8 sommets par unité de longueur, par exemple une lame faite de quelques quads plats),
chaque bord est calculé comme l'enveloppe convexe des sommets de la région. Elle suit exactement les bords droits entre
les coins et ignore les sommets intérieurs. Elle s'appuie aussi sur la colonne de sommets la plus proche juste
à l'extérieur de chaque bout de la région. Les modèles denses gardent la méthode par tranches, qui préserve les creux
(comme l'encoche d'Hiramekarei). Aux bouts de la
région, les tranches ne lisent que l'intérieur : une garde voisine n'élargit pas la silhouette.
Avec `style.type: demonic` (Berserk), le composeur ajoute une chaîne sur **chaque face** de la lame, décalée juste
devant le métal. Elle porte les fissures rouges, qui pulsent en vague lente.
`shape.silhouette: false`
revient à la version simple (segment CP0 → CP1).

## 10. Regions
```yaml
regions:
  blade: {hitbox_bone: RightHand, start: 0.2, end: 0.98}
```
`start` et `end` sont des fractions de l'axe principal (0 = base, 1 = pointe). L'effet s'adapte à la longueur réelle.
Exemple réel : `examples/hiramekarei_aura.yaml`. Le modèle n'a pas d'os « blade » ; `start: 0.15` exclut la
poignée et garde les nageoires (valeur à ajuster en jeu).

## 11. Runtime GMod
L'addon généré contient `lua/pcfforge/runtime.lua` (client) et `lua/autorun/pcfforge_<id>.lua`.
```lua
local h = PCFForge.AttachEffect(ent, "chakra_aura")        -- attache décrite dans la spec
PCFForge.UpdateEffect(h, { [1] = Vector(0, 0, 100) })      -- points de contrôle à la main
PCFForge.DetachEffect(h)                                   -- arrêt de l'émission (true = immédiat)
```
Console (client) : `pcfforge_attach <id> [entity|bone|region|bounds|attachment]`, `pcfforge_list`, `pcfforge_clear`.
`pcfforge_debug 1` dessine les points de contrôle à travers les modèles : CP0 en vert, CP1 en bleu, chaînes en rouge.
À utiliser pour vérifier en jeu qu'une silhouette tombe bien sur la lame.
API utilisées : CreateParticleSystem, SetControlPoint(Orientation), StopEmission, LookupBone, GetBoneMatrix,
LookupAttachment. **Ce runtime n'a pas été exécuté dans GMod par l'outil** : il faut le tester en jeu.

### Références
`python -m pcfforge analyze <fichier.pcf>` décrit chaque système : matériau, débit, vie, taille, couleurs, position,
mouvement, verrouillage, rendu. On l'utilise pour calibrer un effet sur un PCF que l'utilisateur aime
(voir `references/README.md`).
Couches : `release: 0.7` libère le verrou à 70 % de la vie : les particules collent à l'arme, puis s'en détachent
et traînent. `twist_axis: [force, axe]` fait tourbillonner autour d'un axe exprimé dans le repère de CP0 (la lame).

### Tester avec un outil de particules (sans Lua)
`python -m pcfforge drop <spec...>` construit les effets, puis copie seulement `particles/*.pcf` et `materials/<effet>/`
dans `out/drop/`, avec la même structure que `garrysmod/`. On y ajoute un petit fichier `lua/autorun` qui fait seulement `game.AddParticles`, car les outils de particules n'affichent que les PCF chargés par le jeu. Il suffit de fusionner ces dossiers dans `garrysmod/`.
Les effets model-driven y sont signalés : ils ont besoin du runtime pour placer leurs points de contrôle.

### Donner un effet à quelqu'un
`python -m pcfforge pack <spec...>` produit `out/share/<id>.zip` : un dossier d'addon à extraire dans
`garrysmod/addons/`. Il contient le PCF, ses matériaux, un chargeur (`game.AddParticles` + précache), `addon.json`
et un LISEZMOI. Les effets model-driven y ajoutent le runtime, dont ils ont besoin.
Un `.pcf` seul ne suffit que si l'effet n'utilise que des matériaux déjà présents dans le jeu, ce qui n'est pas le
cas de nos textures générées.

## 12. Validation
- `generate` : spec → textures → PCF → relecture du PCF → lint (préfixes, Lifespan Decay, rendu, enfants, budget).
- `lint <spec>` : même contrôle sans rien écrire.
- `validate <fichier.pcf>` : format DMX, opérateurs connus du schéma et bien placés, enfants existants.
- `python -m pytest -q tests` : tests positifs et négatifs, dont la lecture du vrai modèle Hiramekarei.
- Le rendu final se juge dans Garry's Mod (`python -m pcfforge capture <spec>` sous Windows).

## 13. Performance
```yaml
performance: {max_particles: 250, quality: high, draw_distance: 3000}
```
- `quality` : low (×0,45, retire la couche secondary et la turbulence), medium, high, ultra.
- Au-delà de `max_particles` (pic estimé), les rôles les moins importants sont réduits en premier
  (secondary → sparks → accents…), puis une note est émise.
- Chaque système a sa bounding box et sa distance d'affichage (culling).
- Un effet permanent doit rester sous environ 150 à 250 particules.
