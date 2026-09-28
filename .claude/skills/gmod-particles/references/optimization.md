# OPTIMIZATION

## Objectif

Obtenir le meilleur rapport :

QUALITÉ VISUELLE / COÛT CPU / COÛT GPU / NOMBRE DE PARTICULES

## Principes

- Éviter les émissions permanentes élevées.
- Éviter les lifetimes inutilement longs.
- Limiter les particules secondaires.
- Utiliser le culling lorsque pertinent.
- Utiliser une draw distance cohérente.
- Éviter les systèmes qui continuent à simuler lorsqu'ils ne sont pas visibles.
- Garder les bounding boxes cohérentes.
- Éviter les operators coûteux lorsqu'une solution plus simple donne le même résultat.

## Priorité

Si un effet est trop lourd :

1. retirer les éléments décoratifs faibles ;
2. réduire les émissions secondaires ;
3. réduire les lifetimes ;
4. simplifier le mouvement ;
5. réduire la densité ;
6. seulement ensuite réduire le core principal.

La qualité du sujet principal doit être conservée autant que possible.
