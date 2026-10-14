# Modèle IA en U

**Statut initial : `NOT_IMPLEMENTED`**

## Langage visé

Cette piste cible explicitement le langage **U documenté sur [ulanguage.org](https://ulanguage.org/u_language)**, et non les autres langages/projets homonymes. Le compilateur présenté par ce projet transforme U en C; la disponibilité exacte du compilateur et les fonctionnalités requises doivent être vérifiées avant de marquer une étape comme réussie.

## Objectif

Construire le modèle lui-même dans cette piste, et non un simple adaptateur vers un modèle externe.

1. Valider une version reproductible du compilateur U et compiler un programme minimal.
2. Implémenter des opérations numériques et des tests de précision.
3. Implémenter un petit modèle entraînable avec paramètres propres et données synthétiques.
4. Ajouter une boucle d'entraînement reproductible et une séparation entraînement/validation/test.
5. Enregistrer les poids dans un format documenté, calculer leur empreinte, puis les recharger.
6. Exécuter l'inférence depuis les poids rechargés et comparer les résultats aux tests de référence.
7. Mesurer les performances et documenter les limites.

## Règles de preuve

- La documentation ou la présence de ce dossier ne prouve pas qu'un modèle existe.
- La génération de C ne suffit pas : les sources du modèle doivent être écrites et conservées dans U.
- Ne pas déclarer `PASS` sans compilation réelle, entraînement terminé, checkpoint rechargé, inférence et tests consignés.
- Si une fonctionnalité U nécessaire n'est pas supportée par le compilateur testé, marquer l'étape `BLOCKED` et fournir le journal exact.

## État

- Code du modèle : **NOT_IMPLEMENTED**
- Compilateur U vérifié dans cette piste : **NOT_VALIDATED**
- Entraînement et poids : **NOT_IMPLEMENTED**
- Inférence et benchmarks : **NOT_VALIDATED**
