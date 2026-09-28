# PCF STRUCTURE

## Architecture logique

Un système de particules Source/GMod peut être organisé autour de :

Particle System
- configuration générale
- emitters
- initializers
- operators
- renderers
- matériaux

## Configuration

Selon le système, contrôler notamment :
- maximum draw distance ;
- time to sleep when not drawn ;
- maximum simulation tick rate ;
- maximum time step ;
- bounding box ;
- culling.

## Emitters

Exemples de familles rencontrées dans les PCF :
- émission continue ;
- émission instantanée.

## Initializers

Ils définissent principalement l'état initial :
- lifetime ;
- radius ;
- color ;
- alpha ;
- rotation ;
- velocity ;
- position ;
- dispersion.

## Operators

Ils modifient le comportement pendant la vie :
- mouvement ;
- fade ;
- scale ;
- couleur ;
- rotation ;
- bruit ;
- oscillation ;
- attraction ;
- rotation autour d'un axe.

## Renderers

Ils déterminent le rendu :
- animated sprites ;
- sprite trails ;
- rope ;
- modèles selon le besoin.

IMPORTANT :
Ce document décrit l'architecture de travail. Les paramètres exacts doivent être confirmés à partir des fichiers PCF et des références du projet avant d'inventer une valeur ou un champ.
