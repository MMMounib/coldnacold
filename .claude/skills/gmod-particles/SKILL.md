---
name: gmod-particles
description: Conception, génération, analyse et optimisation de systèmes de particules PCF pour Garry's Mod / Source Engine. Utiliser pour tout travail visuel de particules destiné aux spells, auras, projectiles, impacts, explosions, trails et effets magiques.
---

# GMOD PARTICLES SKILL

Ce skill complète les règles de `CLAUDE.md`.

## Mission

Transformer une description visuelle utilisateur en un système de particules GMod cohérent, performant et esthétique.

Le travail porte sur :
- PCF ;
- DMX Particle Systems ;
- emitters ;
- initializers ;
- operators ;
- renderers ;
- matériaux ;
- textures ;
- timing ;
- mouvement ;
- layering ;
- optimisation ;
- validation visuelle.

## Avant toute génération

1. Lire les références pertinentes.
2. Chercher les exemples similaires dans `examples/`.
3. Vérifier les informations fournies par l'utilisateur.
4. Identifier les ambiguïtés.
5. Poser les questions nécessaires.
6. Ne commencer la production qu'après clarification des points critiques.

## Méthode de conception

Toujours réfléchir dans cet ordre :

DESCRIPTION
→ INTENTION VISUELLE
→ FORME
→ LAYERS
→ TIMING
→ MOTION
→ INITIALIZERS
→ OPERATORS
→ RENDERERS
→ MATERIALS
→ OPTIMISATION
→ VALIDATION

## Layering

Un système peut être composé de :
- core ;
- glow ;
- secondary particles ;
- sparks ;
- trail ;
- smoke ;
- ambient particles.

Ne pas utiliser toutes les couches par défaut.

## Référence aux fichiers existants

Lorsqu'un exemple du dépôt ressemble à la demande :
- l'étudier ;
- réutiliser les techniques pertinentes ;
- conserver les bonnes pratiques ;
- adapter plutôt que copier mécaniquement.

## Aperçu

Si l'environnement permet de produire une image ou une vidéo :
- utiliser l'aperçu pour valider la direction artistique ;
- ne pas présenter un concept comme preuve que le PCF fonctionne ;
- privilégier le rendu GMod réel pour la validation finale.

## Sortie

Le résultat doit rester dans le périmètre des particules.

Ne pas ajouter de gameplay ou de logique de spell.

## Supplied PCF corpus

`examples/` contains the supplied PCF corpus. `references/pcf_corpus_inventory.md` summarizes components observed directly in those binary PCFs. Inspect similar examples before designing a new effect. Do not blindly copy an existing system and do not infer undocumented behavior.
