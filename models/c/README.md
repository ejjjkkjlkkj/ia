# Modèle IA — C

**Statut initial : NOT_IMPLEMENTED.** Ce dossier est la piste indépendante pour construire un modèle dans C. Il ne contient pas encore un modèle entraîné.

## Objectif de cette piste

Modèle numérique natif : tenseurs FP32, entraînement causal CPU, checkpoints et inférence.

Construire les composants du modèle dans ce langage, et non appeler simplement un modèle préentraîné distant :
1. opérations numériques et tests comparés aux vecteurs communs;
2. modèle causal minimal entraînable sur CPU ou cible déclarée;
3. calcul de perte et gradients, ou justification documentée des limites du prototype;
4. boucle d'entraînement reproductible sur données synthétiques/licenciées;
5. sauvegarde et rechargement de checkpoints;
6. inférence et évaluation sur des exemples tenus à l'écart;
7. mesures, commandes, versions d'outils et hashes consignés dans `STATUS.md`.

## Preuves exigées

Le dossier ne passe à `PASS` que lorsque le code compile/s'exécute, qu'un entraînement réel produit un checkpoint, que le checkpoint est rechargé et que l'évaluation est reproductible. Une documentation, un squelette ou un appel à un modèle externe ne satisfait pas ces critères.

## Spécification partagée

Voir [../../MODEL-SPEC.md](../../MODEL-SPEC.md) et [../../LANGUAGE-CATALOG.md](../../LANGUAGE-CATALOG.md). Les limites propres à ce langage doivent rester explicites. Les assembleurs sont des pistes de noyaux bas niveau, pas des modèles applicatifs complets autonomes. Scratch vise un modèle pédagogique à petite échelle.

## Statut

- Modèle implémenté : NOT_IMPLEMENTED
- Entraînement exécuté : NOT_VALIDATED
- Checkpoint : NOT_IMPLEMENTED
- Inférence : NOT_VALIDATED
- Validation externe : NOT_VALIDATED
