# Limites réelles (V3)

| Élément | Statut |
|---|---|
| Écriture PCF (DMX binaire v2, pcf 1) au format de l'éditeur Valve (`dmx2.py`) + relecture | IMPLEMENTED, TESTED hors moteur |
| Opérateurs : schéma extrait de 148 PCF réels + 3mel.pcf (99 opérateurs) | IMPLEMENTED, TESTED |
| Composition, phases, motions, variation, textures | IMPLEMENTED, TESTED (hors moteur) |
| Lecture MDL v44-49 (os, hiérarchie, attachments, hitboxes) + VVD | IMPLEMENTED, TESTED sur Hiramekarei (v48) |
| Lecture MDL v49 | TESTED sur sword_persee (Berserk, 1 os, lame low-poly) |
| Formats MDL v44-47 | IMPLEMENTED, NOT TESTED (aucun fichier de test) |
| Runtime Lua (AttachEffect / DetachEffect / UpdateEffect) | IMPLEMENTED, NOT TESTED dans GMod |
| Rendu visuel | NOT TESTED : seul GMod fait foi |
| Captures automatiques | OPTIONAL DEPENDENCY (Windows + GMod) |
| Déformation animée des vertices, os procéduraux, flex | UNSUPPORTED : le segment suit la matrice de l'os |
| Silhouette (contour + remplissage en chaîne de CP, 41 CP pour Hiramekarei) | IMPLEMENTED, TESTED hors moteur ; limite de 64 CP et rendu NOT TESTED en jeu |
| Modèles sans VVD | le segment vient de la hitbox (moins précis) |
| Parseur de texte | règles simples FR/EN ; ce qui n'est pas reconnu est listé, jamais deviné |

## Leçons des tests en jeu
- **30/09 — planches animées affichées en entier** (motifs « 日 » sur chaque particule) : le VTF écrit par srctools
  (sheet v0) n'est pas lu par GMod. Les planches passent par `pcfforge/textures/vtf.py` : VTF 7.4, miniature DXT1
  → sheet v1 → image. C'est le format validé en jeu le 28/09. Elles ne sont pas compressées, ce qui les rend plus lourdes.
- **Animation des planches** : `animation rate` = nombre de cycles par seconde ; `animation_fit_lifetime` ne fait rien.
  Par défaut, la séquence fait un cycle sur la durée de vie moyenne ; `anim_rate` impose un autre rythme.
- **30/09 — Hiramekarei trop grande, trop dense, flammes qui partent partout** : sur une arme, tout ce qui dessine la
  forme est verrouillé sur la lame (CP0, avec la rotation). Seules quelques particules traînent derrière.
  L'enveloppe reste proche (×1,15), et le corps utilise une texture sans bord net (sinon on voit des boules).
- **30/09 — version sobre jugée simpliste** : sur une arme opaque, tout ce qui est dessiné à l'intérieur de sa silhouette
  est caché. La masse de chakra est donc placée sur la bande du contour. Deux traits de lumière (`chain_seq`, rope)
  font le tour de la lame en 1,8 s, décalés d'un demi-tour. Ces couches sont `fixed` : ni le style ni la variation
  ne modifient leur rythme. `chain_seq` (paires de CP successives, en ordre) n'est **pas encore vu en jeu**.
- **30/09 — Berserk jugée « mignonne » et identique aux autres** : c'était la recette chakra recolorée.
  L'énergie `demonic` a maintenant sa propre recette et ses propres textures :
  - colonne de miasme noir qui monte (libre, elle traîne derrière l'arme quand elle bouge) ;
  - pointes d'encre au cœur rouge ;
  - lueur rouge sang ;
  - arcs rouges brefs ;
  - fissures ;
  - braises et cendres.
  Particules visibles d'un seul côté de la lame : cause non établie à distance, d'où l'ajout de `pcfforge_debug`.
- **30/09 — référence « nébuleuse violette »** : nouvelle énergie `abyss` avec ses propres textures (`sparkle`,
  `nebula`, `curl`) :
  - lame éclairée de l'intérieur (lueur devant chaque face) ;
  - paillettes denses qui scintillent ;
  - nébuleuse filamenteuse ;
  - boucles fines ;
  - vide violet sombre derrière.
- **30/09 — abyss v1 trop légère, lumière de lame en « boules »** : recette recalibrée sur `fsc_aura2` (voir
  `references/README.md`) : pic ~380, fumée violette dense qui grandit, relâchement à 70 %, éclats qui tourbillonnent
  autour de la lame. La lumière de la lame devient une corde douce le long de chaque face (boucle fermée, sans raccord).
  Nouveau : `python -m pcfforge analyze`.
- **30/09 — Darui (sword_darui, 518 sommets)** : sur une lame low-poly, la méthode par tranches faisait zigzaguer
  le contour, car certaines tranches ne voyaient que les sommets du centre. Pour ces modèles, on utilise maintenant
  l'enveloppe convexe de la région (`method: hull`), ancrée sur la colonne voisine à chaque bout.
  Recette `black_lightning` (foudre noire) :
  - arcs d'encre qui crépitent ;
  - ligne brisée redessinée sur chaque face ;
  - lueur bleu pâle ;
  - étincelles ; pic ~90.
- **30/09 — Darui v1 jugée « horrible »** : crépitement en sprites d'éclair, pas d'aura, boules de lueur. Refaite sur
  la structure validée d'abyss :
  - lumière dans la lame ;
  - fumée d'orage qui colle puis se détache ;
  - brume électrique ;
  - deux cordes d'éclair le long du contour, redessinées avec du jitter à deux rythmes différents ;
  - électricité statique.
  Règle ajoutée : « sobre » garde un corps d'aura, et les éclairs suivent la géométrie.
- **30/09 — Darui v3** : aura resserrée sur les bords pour dessiner de vrais contours (fumée ×0,7, dispersion ÷2).
  Les éclairs deviennent des particules animées (`lightning_anim`, 2 séquences de 8 images) : ils frappent d'un bout
  à l'autre, crépitent avec des fourches qui changent, puis s'éteignent. Le choix de la séquence est aléatoire
  quand une texture en a plusieurs.
- **30/09 — Darui v4** : les éclairs en sprites (orientation au hasard) ressemblaient à des gribouillis qui
  tournoient, pas à de la foudre, et ne suivaient pas l'arme ; le bleu manquait d'éclat. Règle : **une décharge
  suit l'arme**. Trois décharges font le tour du contour exact : cordes en ordre (`chain_seq`), brisées par le jitter,
  avec une texture `bolt_strand` à segments droits qui se raccorde sans couture, et un trait d'encre noire dessous.
  Elles tournent à trois vitesses. Bleu électrique saturé.
- **01/10 — bouclier Black Clover (`bc_shield`)** : effet standalone en 4 systèmes (apparition, maintien, impact,
  rupture). Pas d'orientation « normale à la sphère » dans le corpus : les alvéoles sont donc debout sur la paroi et
  à plat sur la calotte. Les rangées sont régulières et décalées. Le maintien est statique : environ 165 particules
  sans simulation de mouvement, sauf quelques paillettes. Non vu en jeu.
  `texture_size` (par effet) réduit les textures peu visibles à l'écran : addon du bouclier 2,7 → 1,2 Mo.
- **01/10 — PCF déposé seul : liste vide dans l'outil de particules.** Les fichiers chargés par un addon s'affichent
  avec une étoile orange, ceux qui sont seulement posés dans le dossier avec une flamme. `drop` ajoute donc un
  chargeur `lua/autorun` (`game.AddParticles` + précache, rien d'autre). Cause probable, à confirmer en jeu.
- **01/10 — l'outil de particules de l'utilisateur lit `1gonzo.pcf` et `bigfumee.pcf`, mais pas nos PCF.** Le moteur,
  lui, les chargeait. Nos fichiers sont maintenant écrits comme ceux de l'éditeur Valve (`pcfforge/dmx2.py`, comparé à
  `references/1gonzo.pcf`) :
  - ordre des éléments en profondeur ;
  - pas d'attribut `name` ;
  - attributs des systèmes dans l'ordre de l'éditeur, avec l'orthographe exacte (`Sort particles`) ;
  - **tous** les attributs des opérateurs écrits, avec les valeurs par défaut de l'éditeur GMod
    (`pcfforge/defaults.json`, repris de Particle Effects+, licence MIT).

  Nouveau : `pack`, un zip par effet à donner.
- **01/10 — bouclier v2 d'après le croquis de l'utilisateur** : losange (deux cônes joints à la taille). **Une seule
  particule** `bc_shield`, qui se forme et tient d'elle-même. Les 8 cercles se tracent un par un du bas vers le haut :
  corde en ordre, émission continue courte, vie persistante, et un anneau qui pulse à la naissance de chaque cercle.
  Ensuite viennent les alvéoles, rangée par rangée. `hit` et `rupture` restent des options.
  Règle : un sort = un système appelable complet, sauf si l'utilisateur demande des moments séparés. Un système
  nommé comme le préfixe garde ce nom exact. Non vu en jeu : on suppose que l'ordre de distribution de
  `Position Along Ring` suit l'ordre d'émission.
- **01/10 — « une particule qui reste, une qui part »** : `bc_shield` se forme puis reste ; `bc_shield_fin` arrive complet
  puis se défait cercle par cercle, du haut vers le bas, en éclats et paillettes. L'option `hide_children` marque les
  sous-parties `preventNameBasedLookup` : les outils de particules ne listent que les 2 effets. À vérifier en jeu :
  les enfants doivent toujours s'afficher, car ils sont liés par élément et non par nom.
- **01/10 — bouclier en 3 particules** (demande) : `bc_shield_start` (formation, environ 1,6 s, qui s'efface),
  `bc_shield_loop` (bouclier déjà formé, persistant) et `bc_shield_end` (il se défait). Le sort lance `loop` à 1,34 s :
  `start` s'efface pendant que `loop` apparaît, en fondu croisé.
- **01/10 — la technique renforce une personne** : `loop` doit rester vivant, avec le cristal formé, et suivre le
  joueur. Toutes les couches de start, loop et end sont maintenant verrouillées sur CP0 : sans ça, les particules
  persistantes restaient sur place quand le joueur marchait.
  Animation de loop :
  - cercles en traits de rune (`rune_line`) qui défilent dans des sens alternés ;
  - rangées d'alvéoles qui tournent lentement ;
  - vague de lumière qui monte en suivant le losange (deux `Radius Scale` successifs) ;
  - éclats qui convergent de la paroi vers le joueur (le renforcement).
- **01/10 — « loop doit se jouer en boucle »** : `bc_shield_loop` ne contient plus de particules persistantes.
  Tout est ré-émis en continu, avec des vies courtes : un cercle se renouvelle en 2 s, une rangée d'alvéoles en 2,6 s.
  L'effet tourne donc indéfiniment et s'éteint seul quand on l'arrête. Pour qu'il soit complet dès la première image,
  chaque forme a une **amorce** : la même forme émise d'un coup, dont la i-ème particule vit i/n d'un cycle
  (`Remap Particle Count to Scalar`, ajouté au schéma depuis les défauts de l'éditeur GMod, absent du corpus).
  Chaque morceau de l'amorce s'éteint quand le cycle vient le remplacer.
  Règle : une particule `loop` est un vrai cycle, sans vie persistante. À vérifier en jeu : la répartition régulière
  de `Position Along Ring` doit avancer dans l'ordre d'émission.
- **01/10 — bouclier v3 : bulle ovale anime** (retour : « les alvéoles c'est très moche », losange refusé ; référence :
  bulle bleu-violet translucide au bord lumineux, nuages d'énergie à bord brillant dans le bas, barrière de Symmetra).
  Choix de l'utilisateur : ovale, couleur de la référence, apparition « bulle qui gonfle ». Alvéoles et runes retirées.
  Langage visuel :
  - **contour** : un seul sprite face caméra `shield_rim` (planche animée en boucle : contour net, intérieur en
    2 aplats plus denses vers le bord, reflets qui montent). L'ovale est un corps de révolution : vu de côté, son
    contour est le même partout. Vu de très haut, le vrai contour s'arrondit alors que le sprite reste un ovale
    vertical : **NOT TESTED**. En loop, deux contours se relaient en fondu (intensité constante) ;
  - **peau** : ~240 sprites `shield_film` sur la surface, qui tournent lentement à des vitesses différentes selon
    l'étage (reflets qui coulent). Un aperçu approximatif hors moteur montrait que la peau seule donne un brouillard
    sans bord : d'où le sprite de contour ;
  - **cœur** : nuages `shield_wisp` à bord lumineux qui montent dans la moitié basse.
  Gonflement : chaque sprite part du sol sous le joueur et file vers sa place, freiné par `Movement Basic` drag
  (vitesse × (1 − drag) toutes les 1/30 s d'après le code Source, v0 = distance × K) : ralenti en fin de course.
  **NOT TESTED** : la formule de la traînée et le sens de la vitesse de `Position Along Ring`. Rayon 1 pour que la
  vitesse soit juste qu'elle soit normalisée ou non.
  Nouvelle clé de couche `hide_in_first_person` : remplit « control point to disable rendering if it is the camera ».
  Elle sert au contour, qui couvrirait l'écran du joueur protégé. Effet en jeu **NOT TESTED**.
  `build.textures` retire désormais du dossier `materials` les textures qu'une ancienne version utilisait : le zip ne
  les embarque plus. Après une modification d'une fonction de texture, il faut `generate --retex`, car le cache ne le
  détecte pas.
- **01/10 — bouclier v4, retour en jeu sur la v3** (captures : start 1, loop 2, end 3) : « pas animé, moche, manque de
  peps », et dans start le contour finissait au-dessus de la bulle. **Cause du bug de start** : le sprite de contour
  partait déjà du centre (offset z = 50) au lieu du sol, puis montait encore de toute sa vitesse. Le nouvel aperçu
  `preview` reproduit ce défaut à l'identique, ce qui conforte le modèle de traînée utilisé (cohérent avec la
  capture, toujours non mesuré).
  Corrections : départ du contour au sol (z = 1) ; tout ce qui porte le rendu est une planche animée qui coule en
  boucle, avec des ondes progressives et une déformation du domaine, une phase entière par boucle, donc sans
  raccord visible :
  - `energy_cloud` : nuage qui bouillonne, à bords en volutes ;
  - `shield_veins` : veines liquides sur la peau ;
  - `shield_rim` : contour qui ondule.
  Mouvements plus francs : peau à environ 20 °/s, nuages à 36 °/s, veines à contre-sens. Plus d'éclat : alphas
  relevés, poussière qui monte, gerbe au départ, éclats à la fin du gonflement, onde de choc et 48 éclats à la fin.
  Le contour du loop a maintenant une amorce pleine pendant un cycle : il n'y a plus de trou avant le premier contour
  émis.
- **Nouvel outil `python -m pcfforge preview <spec> --chain start:0,loop:0.85:5,end:5`** : GIF approximatif hors
  moteur, sans cordes et sans éclairage HDR. Il rend plus blanc que GMod. Il sert à vérifier l'enchaînement, les
  positions et le rythme. **Ce n'est pas le rendu Source.**
- **01/10 — bouclier v5, BUG TROUVÉ en jeu** (capture du loop : contours empilés qui montent au-dessus de la bulle).
  Les couches `shape: point` (contour, vagues, halo) n'avaient **aucun initialiseur de position**. Source garde alors la
  position de la particule morte dans l'emplacement, et `Position Modify Offset Random` y ajoute à nouveau l'offset :
  chaque contour apparaissait 50 u plus haut que le précédent. C'était aussi la cause du contour trop haut dans start v3.
  Corrections :
  - les couches point ont toujours `Position Within Sphere Random` (distance 0) ;
  - le lint refuse tout système sans initialiseur `Position*`, et tous les exemples ont été régénérés.
  Les références Valve donnent toujours une position.
  Start refait à la demande de l'utilisateur : un petit cercle s'allume au sol et s'élargit jusqu'à la largeur de la
  bulle, puis le bouclier en sort. Les étages de peau naissent au sol à leur rayon final et montent, avec une vitesse
  verticale seule, plus sûre que la vitesse radiale de l'anneau.
  Fin propre : les vies du loop sont raccourcies (cycle de 1,4 s) et, pour une fin nette, il faut **détruire le loop
  d'un coup** en lançant end :
  - en Lua : `ent:StopParticles()` ou `CNewParticleEffect:StopEmissionAndDestroyImmediately()` ;
  - sinon, le loop s'éteint en environ 1,5 s.
  `preview` simule ce cas : `--chain 'start:0,loop:1.1:4.5!,end:4.5'`.
- **01/10 — zone magique de protection au sol `bc_zone`** (Black Clover, rayon 150 u, sans runes : cercle géométrique).
  Construction : 5 grands sprites à plat au sol (orientation 2, comme `fsc_aura2` et `3mel`), un par pièce :
  - contour d'énergie (planche animée) ;
  - double anneau gradué ;
  - 12 satellites ;
  - étoile à 12 branches ;
  - anneaux centraux.
  **Boucle sans raccord pour des pièces qui tournent** : une copie neuve, à rotation 0, naît toutes les
  T = symétrie / vitesse et vit 2T (fondu entrant et sortant de moitié chacun, somme constante). Elle recouvre
  exactement l'ancienne, qui a tourné d'une symétrie entière.
  Nouvelles clés de couche : `turn` (°/s fixe, sans inversion aléatoire) et `turn_from` (angle de départ).
  L'aperçu `preview` mesure une intensité constante en loop et une baisse de ~20 % pendant 0,1 s au passage de start
  à loop (corrigée en partie). **NOT TESTED** :
  - unité de `Rotation Speed Random` (degrés/s supposés) ;
  - rotation d'un sprite d'orientation 2 dans le plan du sol ;
  - à la fin, petit saut d'angle possible (≤ moitié d'une symétrie) car end repart à rotation 0, masqué par
    l'extinction.
- **02/10 — première version Ohirume (rejetée, retirée du dépôt)** : rose fluo, néon, surcharge, aura qui couvrait
  le personnage. **Leçon : l'additif seul devient du néon sans contraste sur un fond clair** (il ne peut
  qu'éclaircir : le rouge vire au rose puis au blanc, le noir n'existe pas). Règles retenues pour la suite :
  - toute la matière (noir, carmin) en mélange alpha, couleurs intégrées aux textures ;
  - l'additif réservé à quelques lueurs très faibles et à des accents minuscules ;
  - rien de dessiné à l'intérieur d'une sphère noire ; matière aspirée en traînées étirées, pas en sprites ronds ;
  - toujours vérifier un aperçu sur fond clair ET sur fond sombre.
  Points de Source encore non vérifiés en jeu : sens de défilement des cordes, sémantique de « travel time » du
  chemin contraint, ordre de dessin entre systèmes additifs et translucides.
- **02/10 — pack autonome « Sarada — Mangekyō Sharingan / Ōhirume »** (`sarada_ohirume.pcf`), entièrement nouveau
  (l'utilisateur rejette les versions Ohirume précédentes) :
  - générateur : `examples/gen_sarada_ohirume.py` ;
  - archive : `examples/package_sarada_ohirume.py` -> `out/share/pcfforge_sarada_ohirume.zip`, utilisable sans
    pcfforge ni Python.
  16 particules appelables, aux noms exacts sur deux familles. Nouvelles clés de spec : `exact_names: true` et
  `prefixes: [...]`.
  Langage visuel :
  - 17 textures cel-shading de `pcfforge/textures/sarada.py`, couleurs intégrées (particules blanches) ;
  - la matière est en alpha ; l'additif est réservé à `sarada_glow` et `sarada_spark` (rouge vif, rare) ;
  - motif Mangekyō (pupille + rayons triangulaires) repris dans les éclats et dans l'iris du target.
  Les pièces qui tournent se relaient en phase (T = un tour). L'orbite des 4 sphères tourne à 90 °/s avec T = 4 s :
  chaque copie neuve naît exactement à la place de l'ancienne.
  Vérifié hors moteur (PASS) : syntaxe PCF, définitions, références matériaux / VMT / VTF, ressources, structure de
  l'archive.
  **NOT EXECUTED** : GMod, Hammer++, aperçu Source. Les GIF sont une simulation : `preview` dessine maintenant les
  cordes dans la couleur moyenne de leur texture.
  Points non vérifiés en jeu : sémantique de « travel time » du chemin contraint (projectile et attraction) ; rendu des
  cordes SpriteCard ; motif du Mangekyō (interprétation des descriptions publiées, pas d'image officielle).
