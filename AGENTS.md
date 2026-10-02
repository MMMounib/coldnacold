# pcfforge V3 — instructions pour l'agent

Mission : à partir d'une demande, produire une particule Garry's Mod (.pcf + textures + runtime) propre, lisible,
optimisée. Répondre dans la langue de l'utilisateur (français par défaut). Mode d'emploi : `docs/GUIDE.md`.

## Règles
1. **Ne pas deviner.** Couleur, forme, échelle, durée, mouvement, style : si un point qui change le résultat manque,
   poser une question courte à choix (A/B/C) avant de générer. `parse` liste ces points (`# à préciser`).
2. **Ne rien faire semblant.** Distinguer IMPLEMENTED / TESTED / NOT TESTED / OPTIONAL DEPENDENCY / UNSUPPORTED
   (`docs/LIMITES.md`). Ne jamais écrire « compatible GMod » ni décrire un rendu non vu. N'utiliser que des API GMod réelles.
3. **Seul Garry's Mod fait foi** pour le rendu (`capture` sous Windows) ; sinon le dire.
4. **Standalone d'abord.** Model-driven seulement si un modèle est fourni ou demandé.
5. **Qualité > quantité** : une couche core porte la silhouette, pas de disque de glow comme sujet, mouvement
   organique (flux, pas bruit), budget respecté (`performance.max_particles`).
6. **Chaque effet a son propre langage visuel.** Changer la couleur d'une recette existante ne suffit pas.
   Avant de produire, se demander : quelles formes (textures) ? quelle matière ? quel mouvement ? qu'est-ce qui
   le rend impressionnant ? Si une texture de la bibliothèque ne correspond pas, en créer une (voir `ink_spike`, `miasma`).
7. **Calibrer sur une référence.** Si l'utilisateur fournit un PCF qui lui plaît, lancer d'abord
   `python -m pcfforge analyze <pcf>`, puis reprendre ses ordres de grandeur : débit, durée de vie, taille, couleurs,
   verrouillage. Les références validées et leurs leçons sont dans `references/README.md`.
8. **Rendu propre.** Pas de sprites ronds isolés qui se lisent comme des « boules » : une lumière le long d'une lame
   passe par une corde (`softline`), et un volume par beaucoup de grands sprites texturés qui se chevauchent.
   Ne rien laisser flotter sans raison.
   « Sobre » ne veut pas dire « sans aura » : une aura garde toujours un corps (volume calibré sur la base validée,
   seulement plus léger). Les éclairs, lignes et traits suivent la géométrie (cordes le long du contour), jamais de
   gros sprites d'éclair collés au hasard ni orientés au hasard (ils « tournoient »). Une décharge suit l'arme,
   par exemple en faisant le tour de son contour.
   Base validée par l'utilisateur : `abyss_aura` (structure et densité à reprendre pour les autres armes).
9. **Moments d'un sort.** Demander à l'utilisateur le découpage voulu. Par défaut : `<id>_start`, `<id>_loop`
   (déjà formé, VRAIE boucle : ré-émission continue, vies courtes, amorce pour être complet dès la 1re image ;
   jamais de particules persistantes) et `<id>_end`, avec un fondu croisé entre start et loop. Indiquer à quel moment lancer loop.
   Cacher les sous-parties (`hide_children: true`). Livrer avec `pack` (zip à donner).
10. **Pas de débordement** : pas de logique de sort, pas de Lua hors runtime généré, sauf demande.

## Boucle
`parse` (optionnel) → questions → spec `specs/<id>.yaml` → `generate` → corriger les erreurs de lint →
`pytest` si le code change → livrer l'addon `out/<id>_fx/` avec son LISEZMOI et le statut honnête.
