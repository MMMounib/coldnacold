# Références

| Fichier | Rôle |
|---|---|
| `3mel.pcf` | PCF de référence utilisé pour le schéma des opérateurs |
| `1gonzo.pcf` | PCF écrit par l'éditeur (fourni par l'utilisateur, lu par son outil) : modèle de format pour `dmx2.py` |
| `fsc_aura2.pcf` + `fsc_aura2.md` | auras du serveur que l'utilisateur apprécie (akuma, amaterasu_armor, blackfire_armor) ; `fsc_aura2.md` est l'analyse générée par `python -m pcfforge analyze` |

## Leçons de fsc_aura2 (30/09/2026)
- **Densité** : 60 à 160 particules/s par couche, environ 1 s de vie. Une aura compte **plusieurs centaines** de
  particules à la fois. Autour de 100 au total, le rendu paraît « léger ».
- **Couleurs** : violets saturés et **sombres** (`[88,0,186]` → `[30,0,107]`, `[180,0,255]` pour les éclats),
  noir pur pour blackfire. Pas de blanc, sauf sur de rares éclats.
- **Volume** : de grands sprites texturés (fumée, poussière, flammes) qui **grandissent** beaucoup pendant leur vie
  (`Oscillate Scalar` sur le rayon, taux 10 à 40 ; `Noise Scalar` jusqu'à 30).
- **Accroche** : `Movement Lock to Control Point` ou `Movement Lock to Bone` (hitbox set `effects`), avec un
  **relâchement à 70 %** de la vie : les particules collent, puis traînent derrière le mouvement → `release: 0.7`.
- **Mouvement doux** : force aléatoire ±15, tourbillon 64 autour d'un axe, montée lente (gravité +1 à +40).
- **Position** : sphère creuse (rayon 25) étirée par `Position Modify Warp Random` et décalée de 0 à 55 en Z local
  (colonne autour du corps) ; `Position on Model Random` (hitbox set `effects`) pour couvrir tout le modèle.
- **Blackfire** : `Set Control Point Positions` crée des points au-dessus, puis `Pull towards control point` (350)
  aspire la matière vers le haut. C'est ce qui donne les formes noires en flammes.
- **Double rendu** : deux `render_animated_sprites` sur le même système (face caméra + à plat, orientation 2).
  Chaque particule est dessinée deux fois, ce qui donne plus d'épaisseur.
