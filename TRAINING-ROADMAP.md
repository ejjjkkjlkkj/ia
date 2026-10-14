# Plan d'exécution — fabrication de modèles IA dans le catalogue commun

## Phase 0 — contrat et garde-fous

- [x] Corriger l'objectif du dépôt : construire les modèles IA eux-mêmes avec les langages du catalogue commun.
- [x] Distinguer la fabrication de modèles des outils d'agent et des adaptateurs.
- [ ] Geler la version du contrat mathématique et du format checkpoint.
- [ ] Ajouter un manifeste de preuve par langage sans attribuer de faux statuts PASS.

## Phase 1 — référence CPU

- [ ] Définir les vecteurs numériques communs et la tolérance.
- [ ] Implémenter en C les tenseurs FP32, opérations de base, softmax stable et tests.
- [ ] Implémenter un modèle causal compact, perte, gradients et boucle d'entraînement.
- [ ] Entraîner sur un corpus synthétique déterministe et vérifier que la perte évolue.
- [ ] Sauvegarder/recharger un checkpoint et exécuter une inférence séparée.
- [ ] Enregistrer commandes, journaux, hash, temps et mémoire.
- [ ] Répéter indépendamment en Rust et comparer les résultats.

## Phase 2 — matrice des langages

Pour chaque ID du `LANGUAGE-CATALOG.md`, exécuter les étapes séparément :
1. confirmer compilateur/runtime et dépendances disponibles;
2. implémenter les opérations primitives dans ce langage;
3. passer les vecteurs de référence;
4. implémenter le modèle et l'entraînement;
5. produire puis recharger un checkpoint;
6. mesurer l'inférence et la qualité sur le test retenu;
7. enregistrer les limites et le statut réel.

Les langages sans runtime, compilateur ou bibliothèques adaptés ne sont pas supprimés silencieusement : ils reçoivent un blocage précis et une preuve minimale de faisabilité. Les pistes assembleur portent sur les kernels numériques et leurs benchmarks.

## Phase 3 — spécialisation code

- [ ] Créer des tâches de génération et correction de code avec licences et provenance.
- [ ] Ajouter des tests de compilation et d'exécution en sandbox.
- [ ] Mesurer sur des fichiers/problèmes tenus à l'écart.
- [ ] Ne revendiquer une spécialisation que si elle améliore une baseline mesurée.

## Phase 4 — performance et extensions

- [ ] Profilage CPU avant optimisation.
- [ ] SIMD/GPU uniquement avec tests de correction et benchmarks reproductibles.
- [ ] Quantification uniquement avec mesures de qualité, mémoire et vitesse.
- [ ] Augmenter les tailles après preuve de stabilité et ressources disponibles.

## Conditions de publication

Aucun résultat n'est déclaré terminé sans artefacts inspectables. Pas de poids inventés, pas de chiffres supposés, pas de données sans licence vérifiée, pas de commit de grands checkpoints au dépôt Git. Les publications, fusions et opérations destructives nécessitent une approbation distincte.
