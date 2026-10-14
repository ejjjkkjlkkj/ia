# Spécification de référence — modèle IA entraînable

Statut initial : SPECIFIED / IMPLEMENTATION NOT VALIDATED. Ce document définit le contrat d'un modèle universel partagé compact et les exigences pour ses ports. Il ne prétend pas qu'un Transformer universel a déjà été entraîné. Voir UNIVERSAL-MODEL-ARCHITECTURE.md pour l'architecture globale et la baseline réellement disponible.

## Première cible

Un petit modèle de langage causal de type Transformer, entraînable sur CPU avec un corpus synthétique ou licencié. Le premier prototype doit rester assez petit pour tester les mathématiques et les checkpoints sans GPU. La qualité attendue est une preuve d'apprentissage et de génération cohérente sur le corpus de test, pas une prétention à rivaliser avec les grands modèles.

## Contrat mathématique partagé

1. Vocabulaire déterministe et versionné; tokenizer simple pour la première preuve, puis tokenizer sous licence vérifiée.
2. Tenseurs contigus avec formes explicites et contrôles de dépassement.
3. Opérations minimales : addition, multiplication élément par élément, multiplication matrice-vecteur/matrice-matrice, réduction, softmax stable, normalisation, masque causal.
4. Couches minimales : embeddings, projection, attention causale, MLP, résiduel, normalisation et tête de prédiction.
5. Fonction de perte : entropie croisée sur le prochain token, avec masquage explicite des tokens ignorés.
6. Entraînement : gradients, rétropropagation, clipping configurable, optimiseur SGD de référence puis Adam, graines déterministes.
7. Inférence : chargement de checkpoint, génération greedy de référence puis stratégies facultatives.
8. Numérique : d'abord FP32; toute quantification ou précision réduite est une variante explicitement mesurée.

## Formats et interopérabilité

Chaque checkpoint contient : version de schéma, configuration du modèle, vocabulaire/tokenizer versionné, noms et formes des tenseurs, type numérique, poids, étape d'entraînement et hash. Le chargement rejette les formes incorrectes, versions inconnues et fichiers tronqués. Les implémentations doivent passer les mêmes vecteurs de test avec des tolérances documentées et charger le même format de checkpoint universel. Des checkpoints propres à un port sont des artefacts de test, pas des modèles séparés par défaut.

## Jeux de données et séparation

Commencer avec un jeu synthétique versionné, généré de façon déterministe, afin de tester l'apprentissage sans redistribuer du code tiers. Pour tout corpus réel, conserver la source, la licence, la date, les transformations et les exclusions. Séparer entraînement, validation et test avant l'entraînement. Ne pas entraîner ni évaluer sur les mêmes exemples pour déclarer la généralisation.

## Critères d'acceptation

- Les opérations primitives passent des tests unitaires et des vecteurs numériques de référence.
- La perte est finie, les gradients ne sont pas NaN/Inf et une petite tâche synthétique montre une amélioration reproductible.
- Le checkpoint est écrit, son hash est enregistré, puis relu dans un nouveau processus.
- L'inférence du checkpoint rechargé est reproductible dans les tolérances fixées.
- La perte et les résultats sont rapportés sur des exemples tenus à l'écart.
- Les mesures comprennent version d'outil, commande exacte, durée, mémoire, configuration, graines et hash d'artefact.
- Toute implémentation incomplète reste `PARTIAL`, `BLOCKED` ou `NOT_VALIDATED`.

## Implémentations par langage

Le contrat mathématique et le modèle visé sont communs; chaque piste implémente ou optimise des composants dans le langage déclaré et doit prouver l'interopérabilité avec le checkpoint partagé. Des bibliothèques peuvent servir d'accélérateurs ou de dépendances explicites; une simple invocation d'un modèle préentraîné externe ne satisfait pas le test. Les noyaux assembleur doivent être comparés à une référence sûre et ne peuvent remplacer à eux seuls le pipeline complet.

## Non-objectifs de la première preuve

Pas d'affirmation de modèle généraliste de production, de qualité humaine, de capacité multimodale, de vitesse GPU, de validation matérielle ou de modèle autonome par langage tant que les preuves correspondantes ne sont pas publiées.
