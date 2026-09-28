# GMod Particle Claude Kit

Kit de travail pour utiliser Claude Code comme assistant spécialisé dans la création de particules **Garry's Mod / Source Engine**.

## Objectif

Tu décris l'effet que tu veux en texte.

Claude doit :
1. comprendre la demande ;
2. détecter les informations manquantes ;
3. poser les questions nécessaires ;
4. concevoir la particule ;
5. produire les fichiers nécessaires ;
6. vérifier la structure et l'optimisation ;
7. produire/chercher un aperçu lorsque l'environnement le permet ;
8. te laisser valider le rendu.

## Règle fondamentale

Claude ne doit pas inventer silencieusement une couleur, une taille, une forme, un mouvement ou une autre caractéristique importante.

Si une information critique est ambiguë, il doit poser la question avant de générer.

## Installation

Copier le contenu du dépôt dans le dossier racine du projet Claude Code.

La structure attendue est :

```text
CLAUDE.md
.claude/
└── skills/
    └── gmod-particles/
        ├── SKILL.md
        ├── references/
        ├── examples/
        └── assets/
```

## Utilisation

Exemple de demande :

> Je veux une aura de feu autour du joueur, assez compacte, avec un noyau orange et des petites flammes rouges qui tournent lentement.

Claude doit demander les précisions nécessaires avant de générer si quelque chose d'important manque.

## Exemples de bonnes demandes

```text
Je veux une explosion magique violette.
```

Cette demande est volontairement incomplète : Claude doit demander les informations nécessaires.

```text
Je veux une aura bleue autour du joueur.
Elle doit rester assez proche du corps.
Elle dure tant que le spell est actif.
Je veux un core lumineux, un glow léger et quelques petites particules qui montent.
Pas de trail.
Style propre et premium.
Priorité aux performances.
```

Cette demande contient déjà beaucoup plus d'informations et peut permettre à Claude de commencer après avoir vérifié les éventuelles ambiguïtés.

## GitHub

Le dépôt est conçu pour être versionné.

Structure recommandée :

```text
gmod-particle-claude-kit/
├── CLAUDE.md
├── README.md
├── .claude/
│   └── skills/
│       └── gmod-particles/
│           ├── SKILL.md
│           ├── references/
│           ├── examples/
│           └── assets/
└── particles/
    ├── generated/
    ├── approved/
    └── previews/
```

Ajoute progressivement tes vrais PCF validés dans `examples/` et tes connaissances techniques vérifiées dans `references/`.

## Important

Ce kit ne contient volontairement pas de logique Lua de spell.

Le projet est centré sur la conception visuelle des particules.
