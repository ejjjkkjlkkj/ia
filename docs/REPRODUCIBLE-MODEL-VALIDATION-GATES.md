# IA — portes de validation reproductible du modèle

Statut : **CONTRAT DE VALIDATION — NON EXÉCUTÉ PAR CE DOCUMENT**. La présence de cette procédure ne prouve ni l'entraînement d'un modèle ni la qualité d'une inférence.

## Séparer les affirmations

Chaque composant doit porter un statut distinct :

1. **SPECIFIED** — spécification mathématique et dimensions documentées.
2. **IMPLEMENTED** — code de référence présent, avec tests unitaires.
3. **TRAINING_STARTED** — commande lancée et journal de démarrage conservé.
4. **TRAINING_COMPLETED** — exécution terminée sans erreur et checkpoints produits.
5. **EVALUATED** — métriques calculées sur des ensembles de validation/test documentés.
6. **INFERENCE_VALIDATED** — chargement du checkpoint et sorties de référence vérifiés dans un environnement déclaré.

Ne pas déduire un statut du précédent. Un README, un squelette de code ou un job simulé ne prouve pas un entraînement.

## Portes de qualité

### A. Contrat et données
- Versionner tokenizer, vocabulaire, dimensions des tenseurs, ordre des opérations, précision numérique et format des checkpoints.
- Documenter source, licence, empreinte et transformations des données.
- Séparer entraînement, validation et test ; prévenir les doublons et fuites entre ensembles.
- Pour les essais de base, privilégier des données synthétiques déterministes dont la génération est versionnée.

### B. Tests numériques
- Tester formes et dimensions, valeurs limites, valeurs non finies, batch de taille 1 et séquences vides si elles sont autorisées.
- Vérifier la reproductibilité des initialisations et du pipeline avec une graine fixée.
- Tester les gradients par différences finies sur de petits tenseurs lorsque l'autodiff est implémentée.
- Comparer les résultats inter-langages avec une tolérance numérique explicite ; ne pas exiger l'égalité bit à bit sans contrat de déterminisme.

### C. Checkpoints et provenance
- Enregistrer commit, configuration complète, versions des outils, graine, métriques, durée, code retour et empreinte SHA-256 du checkpoint.
- Tester aller-retour export/import et rejeter les dimensions, versions ou empreintes incompatibles.
- Ne pas renommer un checkpoint externe pour le présenter comme entraîné par ce dépôt.
- Ne pas committer poids volumineux, secrets ou corpus non licenciés.

### D. Évaluation
- Définir les métriques et seuils avant l'exécution.
- Conserver les résultats bruts et le script de calcul.
- Comparer à une baseline explicitement identifiée.
- Déclarer les ressources utilisées et les limites ; une exécution interrompue ou sans checkpoint valide n'est pas un entraînement terminé.

### E. Portabilité multi-langage
- Maintenir un jeu de vecteurs d'entrée/sortie versionné.
- Vérifier les mêmes identifiants de tokenizer, noms d'opérations, formes de tenseurs et règles de sérialisation.
- Marquer chaque langage séparément : SPECIFIED, IMPLEMENTED, TESTED, BLOCKED ou NOT_VALIDATED.
- L'existence d'un répertoire ne prouve pas l'existence d'un backend fonctionnel.

## Preuve minimale par exécution

Fournir commit, commande exacte, environnement, code retour, configuration, graine, métriques, artefacts et empreintes. Toute preuve doit pouvoir être reproduite sans accès cloud obligatoire. Les contraintes matérielles et les échecs doivent être rapportés, jamais remplacés par des résultats inventés.

## Porte de publication

Une publication ne peut annoncer un modèle entraîné que si les checkpoints produits, la configuration, les données autorisées, les journaux, les empreintes et l'évaluation sur test tenu à l'écart sont disponibles. Aucun merge ni publication de poids n'est autorisé implicitement par ce document.
