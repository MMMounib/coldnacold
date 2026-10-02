"""Documentation du pack « Sarada — Mangekyō Sharingan / Ōhirume » (écrite dans l'archive par package_sarada_ohirume.py).
README.md, techniques.md, particle_list.md. Contenu en français, statuts honnêtes."""
import os

PARTICLES = [
    # (nom, rôle court, CP, durée / boucle)
    ('sarada_aura', 'Aura générale de Sarada : cœur sombre discret, halo carmin qui respire, filaments fins.',
     'CP0 = pieds de Sarada', 'boucle'),
    ('sarada_activate', 'Activation du Mangekyō : énergie de l\'œil, pulsation rouge, l\'aura s\'étend.',
     'CP0 = pieds de Sarada', '0,7 s (lancer sarada_aura à 0,45 s)'),
    ('sarada_eye', 'Mangekyō sur l\'œil : rouge qui respire, bord sombre, sans halo.', 'CP0 = l\'œil', 'boucle'),
    ('sarada_target', 'Verrouillage d\'une cible : acquire → lock → maintain (iris en rotation).',
     'CP0 = pieds de la cible', 'boucle (maintain dès 0,35 s)'),
    ('sarada_target_release', 'Relâchement du verrouillage : les éléments se dispersent.', 'CP0 = pieds de la cible',
     '0,4 s'),
    ('sarada_attract_trail', 'Traînée gravitationnelle du personnage attiré.', 'CP0 = buste du personnage, en mouvement',
     'continu'),
    ('ohirume_sphere', 'Sphère de gravité (noyau 16 u) : se forme en 0,35 s puis tourne en boucle.',
     'CP0 = centre', 'boucle'),
    ('ohirume_sphere_s', 'Petite sphère (noyau 6 u).', 'CP0 = centre', 'boucle'),
    ('ohirume_sphere_l', 'Grande sphère (noyau 36 u).', 'CP0 = centre', 'boucle'),
    ('ohirume_sphere_end', 'La sphère (taille normale) se résorbe.', 'CP0 = centre', '0,35 s'),
    ('ohirume_projectile', 'Sphère lancée : charge, vol CP0 → CP1, impact.', 'CP0 = départ, CP1 = cible', '≈ 1,5 s'),
    ('ohirume_pull', 'Attraction de la cible vers la sphère (entonnoir de matière).', 'CP0 = sphère, CP1 = cible',
     'boucle'),
    ('ohirume_impact', 'Compression gravitationnelle (pas d\'explosion classique).', 'CP0 = point d\'impact', '≈ 0,5 s'),
    ('ohirume_implosion', 'La sphère s\'effondre sur elle-même.', 'CP0 = centre', '≈ 1,15 s'),
    ('ohirume_orbit', 'Quatre sphères en orbite autour de Sarada.', 'CP0 = pieds de Sarada', 'boucle'),
    ('ohirume_float', 'Lévitation discrète sous les pieds.', 'CP0 = pieds de Sarada', 'boucle'),
]

TEXTURES = [
    ('ohirume_void', 'noyau noir profond, propre et dense, qui absorbe la lumière'),
    ('ohirume_core', 'coque d\'énergie sombre en cel-shading autour du noyau (reflet carmin en croissant)'),
    ('ohirume_ring', 'anneau de gravité rouge très fin, en arcs, épaisseur irrégulière (2 variantes)'),
    ('ohirume_distort', 'lignes de distorsion aspirées en spirale vers le noyau (planche animée en boucle)'),
    ('ohirume_gravity', 'matière attirée, étirée en aiguille par le rendu en traînée'),
    ('ohirume_streak', 'ruban tuilable (sillage du projectile)'),
    ('ohirume_fragment', 'éclats de vide anguleux (4 variantes)'),
    ('sarada_core', 'cœur sombre très discret de l\'aura'),
    ('sarada_glow', 'halo rouge sombre très faible (seule lueur additive, avec sarada_spark)'),
    ('sarada_filament', 'filament d\'énergie vertical, onde qui monte (planche animée en boucle)'),
    ('sarada_spark', 'micro-étincelle rouge vif : le seul rouge lumineux du pack, rare'),
    ('sarada_ring', 'pièces d\'iris du verrouillage : arcs incomplets, iris à 3 rayons, orbite pointée'),
    ('sarada_void', 'petite pupille sombre cerclée de carmin'),
    ('sarada_distort', 'onde qui plie l\'espace (double anneau ondulé, 4 variantes)'),
    ('sarada_fragment', 'éclats triangulaires du Mangekyō (4 variantes)'),
    ('sarada_streak', 'ruban tuilable de la traînée d\'attraction'),
    ('sarada_eye', 'motif du Mangekyō pour l\'œil, rouge qui respire (planche animée)'),
]

TECHNIQUES = [
    dict(name='Mangekyō Sharingan — Activation',
         rp='Sarada active son Mangekyō Sharingan : son regard s\'embrase d\'un rouge sombre et une énergie noire et '
            'carmin se déploie autour d\'elle.',
         role='Ouvre toutes les techniques d\'Ōhirume.',
         visual='Un point rouge vif s\'allume à hauteur des yeux, une pulsation d\'arcs carmin s\'ouvre sur le buste, '
                'une onde ondulée plie l\'air, quelques éclats triangulaires partent, puis des filaments fins montent '
                'autour du corps et l\'énergie se stabilise.',
         use='`sarada_activate` sur les pieds de Sarada ; `sarada_aura` à 0,45 s ; `sarada_eye` sur chaque œil '
             '(attachement « eyes » du modèle, ou deux positions).',
         parts='sarada_activate, sarada_aura, sarada_eye',
         effect='Rapide (0,7 s), élégant, aucune explosion : l\'aura prend le relais sans coupure.'),
    dict(name='Mangekyō Sharingan — Aura',
         rp='Une énergie sombre et carmin enveloppe Sarada tant que son Mangekyō reste actif.',
         role='Présence permanente pendant l\'usage du Mangekyō.',
         visual='Cœur sombre très discret au buste, halo rouge sombre qui respire, filaments carmin très fins qui '
                'montent en tournant lentement, rares éclats noirs et micro-étincelles. Le personnage reste lisible.',
         use='`sarada_aura` sur les pieds de Sarada, en boucle. Pour l\'arrêter net : détruire l\'effet.',
         parts='sarada_aura (≈ 25 particules)', effect='Léger, vivant, sans brouillard ni disque lumineux.'),
    dict(name='Ōhirume — Cible',
         rp='Sarada verrouille une cible de son Mangekyō : seule la cible de son regard subira la force '
            'gravitationnelle d\'Ōhirume.',
         role='Marquer la cible choisie (seules les cibles du regard sont affectées).',
         visual='Acquire : des éclats triangulaires convergent vers la cible. Lock : des arcs incomplets se '
                'resserrent et un point rouge claque au centre. Maintain : un iris (arcs, iris à trois rayons, orbite '
                'pointée, pupille sombre) tourne lentement en sens opposés et attire un peu de matière. Release : les '
                'arcs s\'ouvrent, l\'iris file, les éclats se dispersent.',
         use='`sarada_target` sur les pieds de la cible (le symbole est à hauteur de buste) ; pour relâcher : '
             'détruire `sarada_target` et lancer `sarada_target_release` au même endroit.',
         parts='sarada_target, sarada_target_release', effect='« Cible verrouillée », lisible sans HUD militaire.'),
    dict(name='Ōhirume — Sphère',
         rp='Une sphère noire d\'une densité extrême se forme et exerce une puissante attraction sur tout ce qui '
            'l\'entoure.',
         role='Le cœur du pouvoir : jusqu\'à quatre sphères, de quelques centimètres à 2,5 m.',
         visual='De l\'extérieur vers le centre : lignes de distorsion aspirées en spirale, double anneau rouge très '
                'fin et irrégulier qui tourne, coque d\'énergie sombre, noyau presque noir. De la matière (aiguilles, '
                'éclats) est aspirée même quand la sphère est immobile.',
         use='`ohirume_sphere` (noyau 16 u), `ohirume_sphere_s` (6 u), `ohirume_sphere_l` (36 u) sur le centre ; '
             'jusqu\'à 4 instances, chacune avec sa position. Fin : détruire l\'effet et lancer `ohirume_sphere_end` '
             '(taille normale) ou `ohirume_implosion`.',
         parts='ohirume_sphere(_s/_l), ohirume_sphere_end', effect='Une sphère qui « avale » la lumière, en boucle.'),
    dict(name='Ōhirume — Lancer',
         rp='Sarada projette une sphère qui fond sur sa cible en happant tout sur son passage.',
         role='Projectile d\'Ōhirume.',
         visual='La sphère naît et se charge (matière aspirée), une onde fine marque le départ, elle file vers la '
                'cible en gardant toutes ses pièces, laisse un sillage sombre qui s\'affine et des débris happés, '
                'puis comprime l\'espace à l\'arrivée (impact).',
         use='`ohirume_projectile` : CP0 = point de départ, CP1 = cible. Vol de 0,55 s après 0,45 s de charge, '
             'quelle que soit la distance ; l\'impact est inclus.',
         parts='ohirume_projectile (contient l\'impact)', effect='Une sphère qui garde son identité pendant le vol.'),
    dict(name='Ōhirume — Attraction',
         rp='La force gravitationnelle d\'Ōhirume attire violemment la cible vers la sphère.',
         role='Tirer une cible vers une sphère.',
         visual='Entre la cible et la sphère, un entonnoir de matière converge : longues aiguilles-filaments, '
                'traînées carmin, éclats de vide qui tournoient, rares étincelles, tous avalés au contact de la '
                'sphère. Sur la cible en mouvement, une traînée sombre s\'étire et se comprime derrière elle.',
         use='`ohirume_pull` : CP0 = sphère, CP1 = cible (mettre à jour CP1 chaque image si la cible bouge). '
             '`sarada_attract_trail` sur le buste du personnage déplacé.',
         parts='ohirume_pull, sarada_attract_trail', effect='L\'espace semble tiré vers la sphère.'),
    dict(name='Ōhirume — Impact',
         rp='Au contact, la sphère comprime brutalement l\'espace autour de sa cible.',
         role='Impact d\'une sphère ou d\'une attraction.',
         visual='Tout est aspiré (anneau qui se referme, aiguilles qui rentrent), flash rouge très bref, onde de '
                'gravité fine qui s\'ouvre, petit vide noir qui s\'effondre sur lui-même.',
         use='`ohirume_impact` au point de contact.', parts='ohirume_impact',
         effect='Très court (0,5 s), très propre : une compression, pas une explosion.'),
    dict(name='Ōhirume — Implosion',
         rp='La sphère concentre brutalement sa force gravitationnelle avant de s\'effondrer en un point d\'une '
            'densité extrême.',
         role='Faire détoner une sphère.',
         visual='La sphère s\'élargit, se stabilise en vibrant, se comprime pendant que la matière s\'y précipite, '
                'implose en un point, un bref flash rouge et un anneau claquent, quelques éclats restent puis '
                'disparaissent.',
         use='Détruire `ohirume_sphere` et lancer `ohirume_implosion` au même centre (taille normale).',
         parts='ohirume_implosion', effect='Tout va vers l\'intérieur ; pas d\'explosion rouge classique.'),
    dict(name='Ōhirume — Quatre sphères',
         rp='Sarada fait graviter jusqu\'à quatre sphères autour d\'elle, prêtes à frapper ou à la porter.',
         role='Sphères en attente autour de Sarada.',
         visual='Quatre sphères complètes de tailles différentes tournent autour de Sarada à des hauteurs '
                'différentes, avec un fin sillage d\'orbite.',
         use='`ohirume_orbit` sur les pieds de Sarada. Pour des positions libres : quatre `ohirume_sphere(_s/_l)`, '
             'chacune sur sa position.', parts='ohirume_orbit',
         effect='Composition lisible, ≈ 50 particules pour les quatre.'),
    dict(name='Ōhirume — Lévitation',
         rp='En équilibrant la gravité de ses sphères, Sarada s\'élève et se déplace dans les airs.',
         role='Lévitation et déplacement avec les sphères.',
         visual='Deux anneaux fins qui tournent sous les pieds, micro-éclats et petits filaments qui montent.',
         use='`ohirume_float` sur les pieds de Sarada (avec `ohirume_orbit` si voulu).', parts='ohirume_float',
         effect='Très léger, aucun grand effet au sol.'),
]


def readme(rep):
    L = ['# SARADA — MANGEKYŌ SHARINGAN / ŌHIRUME', '',
         'Pack de particules dédié aux capacités de Sarada.', '',
         'Direction artistique : **Dark Crimson / Void / Gravity / Mangekyō** — anime cel-shading, noir profond, '
         'carmin ; le rouge lumineux reste un accent rare.', '',
         '## Contenu', '',
         '```text', 'pcfforge_sarada_ohirume/',
         '├── particles/sarada_ohirume.pcf                 le PCF final (16 particules appelables)',
         '├── particles/sarada_ohirume_manifest_example.txt  ligne à ajouter au manifeste (Hammer)',
         '├── materials/sarada_ohirume/*.vmt *.vtf         tous les matériaux du PCF (+ mangekyo_sarada)',
         '├── textures/sarada_ohirume/*.png                textures sources (planches)',
         '├── textures/sarada/mangekyo_sarada*.png         motif du Mangekyō (couleur, masque, émissif)',
         '├── lua/autorun/sarada_ohirume_particles.lua     chargeur GMod (AddParticles + précache + commande test)',
         '├── addon.json', '├── documentation/                               README, techniques, liste, tests',
         '└── preview/*.gif                                aperçus (simulation hors moteur)', '```', '',
         '## Installation (Garry\'s Mod)', '',
         '1. Extraire le dossier `pcfforge_sarada_ohirume` dans `garrysmod/addons/`.',
         '2. Relancer la partie. Le chargeur Lua appelle `game.AddParticles("particles/sarada_ohirume.pcf")` et '
         'précache toutes les particules.', '',
         'Sans addon : copier `particles/` et `materials/` dans `garrysmod/`, puis appeler '
         '`game.AddParticles("particles/sarada_ohirume.pcf")` (et `PrecacheParticleSystem("<nom>")`) depuis votre '
         'propre Lua, partagé (client + serveur).', '',
         '- PCF : `particles/sarada_ohirume.pcf`',
         '- Matériaux : `materials/sarada_ohirume/` (SpriteCard ; le PCF les référence comme '
         '`sarada_ohirume\\<nom>.vmt`)',
         '- Aucune dépendance : pas de modèle, pas de contenu d\'un autre jeu, pas de pcfforge ni de Python.', '',
         '## Particules', '', '| Particule | Rôle | Points de contrôle | Durée |', '|---|---|---|---|']
    for n, role, cp, d in PARTICLES:
        L.append(f'| `{n}` | {role} | {cp} | {d} |')
    L += ['', 'Les sous-parties (`<particule>_<couche>`) sont cachées des listes des outils de particules '
          '(`preventNameBasedLookup`) : seules les 16 particules ci-dessus s\'appellent par leur nom.', '',
          '## Visualiser dans Garry\'s Mod', '',
          '- **Commande de test** (console) : `sarada_ohirume_test <particule> [secondes]` — l\'effet apparaît là où '
          'vous visez (CP1 placé 160 u plus loin pour `ohirume_pull` et `ohirume_projectile`), puis est détruit au '
          'bout du délai (4 s par défaut). L\'autocomplétion liste les noms.',
          '- **Outil de particules** (Particle Effects+, Advanced Particle Controller…) : les 16 particules '
          'apparaissent dans la liste du PCF.', '- **Lua** :', '```lua',
          '-- sur une entité (CP0 = son origine, suit l\'entité)',
          'local fx = CreateParticleSystem(ent, "ohirume_sphere", PATTACH_ABSORIGIN_FOLLOW)',
          '-- sur un attachement (ex. un œil)',
          'ParticleEffectAttach("sarada_eye", PATTACH_POINT_FOLLOW, ply, ply:LookupAttachment("eyes"))',
          '-- dans le monde, avec une cible (pull / projectile)',
          'local p = CreateParticleSystemNoEntity("ohirume_projectile", depart)', 'p:SetControlPoint(1, cible)',
          '-- arrêt net d\'une boucle', 'fx:StopEmissionAndDestroyImmediately()', '```', '',
          '## Visualiser dans Hammer++', '',
          '1. Ajouter `"file" "particles/sarada_ohirume.pcf"` dans `garrysmod/particles/particles_manifest.txt` '
          '(exemple : `particles/sarada_ohirume_manifest_example.txt`) et installer le pack (étape 1 ci-dessus).',
          '2. Placer une entité `info_particle_system`, « Particle System Name » = le nom de la particule, '
          '« Start Active » = oui. Pour `ohirume_pull` / `ohirume_projectile`, renseigner « Control Point 1 » avec '
          'une `info_target`.',
          '3. Statut : **NOT EXECUTED** (non vérifié dans Hammer++).', '',
          '## Mangekyō Sharingan de Sarada (textures du personnage)', '',
          '- `textures/sarada/mangekyo_sarada.png` (1024 px, transparent, centré), `mangekyo_sarada_mask.png` '
          '(motif noir en blanc), `mangekyo_sarada_emissive.png` (iris rouge à faire briller).',
          '- `materials/sarada_ohirume/mangekyo_sarada.vmt/.vtf` : version Source (UnlitGeneric translucide) prête '
          'pour un overlay ou un test.',
          '- **Interprétation artistique** : aucune image officielle exploitable n\'a pu être utilisée ici. Le motif '
          'suit les descriptions publiées (motif en soleil : pupille ronde sombre d\'où partent des rayons '
          'triangulaires, 8 rayons selon plusieurs sources). À comparer avec la planche du manga (Boruto: Two Blue '
          'Vortex) et à corriger au besoin.',
          '- Application sur les yeux du modèle : **DEPENDENCY REQUIRED** (matériau d\'œil de votre modèle, '
          'shader Eyes / EyeRefract ou VertexLitGeneric selon le modèle).', '',
          '## Statut', '', 'Voir `documentation/tests.md`. Le PCF, les matériaux et l\'archive ont été vérifiés '
          'hors moteur. **GMod runtime : NOT EXECUTED** — les aperçus GIF sont une simulation, seul le jeu fait foi.',
          '']
    return '\n'.join(L)


def techniques():
    L = ['# Techniques — Mangekyō Sharingan de Sarada / Ōhirume', '',
         'Chaque technique : nom, rôle, description visuelle, utilisation, particules, effet attendu, et une '
         'description prête pour un serveur Naruto RP.', '']
    for t in TECHNIQUES:
        L += [f'## {t["name"]}', '', f'> {t["rp"]}', '', f'- **Rôle** : {t["role"]}',
              f'- **Description visuelle** : {t["visual"]}', f'- **Utilisation** : {t["use"]}',
              f'- **Particules utilisées** : {t["parts"]}', f'- **Effet attendu** : {t["effect"]}', '']
    L += ['## Textures du pack', '', '| Texture | Rôle |', '|---|---|']
    L += [f'| `{n}` | {d} |' for n, d in TEXTURES]
    L += ['', 'Toutes les textures sont dessinées en cel-shading avec leurs couleurs intégrées (particules blanches). '
          'La matière noire et carmin est en mélange alpha (lisible sur fond clair comme sombre) ; seuls '
          '`sarada_glow` et `sarada_spark` sont additifs.', '',
          '## Performance', '',
          'Pics estimés (particules vivantes) : aura ≈ 25, sphère ≈ 30 à 50 selon la taille, orbite à 4 sphères ≈ 50, '
          'projectile ≈ 60, attraction ≈ 40. Les boucles sont de vraies boucles (copies relayées, flux continus) : '
          'aucune particule persistante. Textures : 64 à 256 px par image.', '']
    return '\n'.join(L)


def particle_list():
    L = ['# Liste des particules', '']
    for n, role, cp, d in PARTICLES:
        L += [f'{n}', f'→ {role}', '']
    return '\n'.join(L)


def write(d, spec, rep):
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'README.md'), 'w', encoding='utf-8').write(readme(rep))
    open(os.path.join(d, 'techniques.md'), 'w', encoding='utf-8').write(techniques())
    open(os.path.join(d, 'particle_list.md'), 'w', encoding='utf-8').write(particle_list())
