# Plan d'exécution — fabrication de modèles IA dans le catalogue commun

## Phase 0 — contrat et garde-fous

- [x] Corriger l'objectif du dépôt : construire les modèles IA eux-mêmes avec les langages du catalogue commun.
- [x] Distinguer la fabrication de modèles des outils d'agent et des adaptateurs.
- [ ] Geler la version du contrat mathématique et du format checkpoint.
- [ ] Ajouter un manifeste de preuve par langage sans attribuer de faux statuts PASS.

## Phase 1 — référence CPU

- [x] Ajouter des kernels Python FP64 de référence : matvec, matmul, softmax stable et cross-entropy, avec tests de validation des entrées.
- [x] Ajouter un noyau Python d'attention causale avec tests de non-fuite vers le passé.
- [ ] Définir des vecteurs numériques communs versionnés, partagés entre langages, et leur tolérance.
- [ ] Implémenter en C les tenseurs FP32, opérations de base, softmax stable et tests.
- [ ] Implémenter un modèle causal compact complet, avec projections, embeddings, couches, perte, gradients et boucle d'entraînement.
- [ ] Entraîner sur un corpus synthétique déterministe et vérifier que la perte évolue.
- [ ] Sauvegarder/recharger un checkpoint et exécuter une inférence séparée.
- [x] Ajouter un runner de preuve synthétique reproductible pour le modèle neuronal de référence : séparation entraînement/test, hashes SHA-256, round-trip checkpoint, métriques hors entraînement, génération, temps et rapport JSON archivable par CI. Cette preuve valide le pipeline minimal, pas la qualité générale du modèle.
- [ ] Enregistrer les mesures mémoire et les journaux complets d'entraînement pour le modèle causal complet.
- [ ] Porter le même contrat en Rust et comparer les résultats au modèle de référence, sans créer un objectif de modèle indépendant par langage.

## Phase 2 — matrice des langages

Pour chaque ID du `LANGUAGE-CATALOG.md`, évaluer séparément la contribution au même modèle universel :
1. confirmer compilateur/runtime et dépendances disponibles;
2. implémenter les opérations primitives dans ce langage;
3. passer les vecteurs de référence;
4. implémenter/porter les composants du modèle commun et l'entraînement si le runtime le permet;
5. produire un checkpoint de test ou charger le checkpoint universel partagé, puis vérifier l'interopérabilité;
6. mesurer l'inférence et la qualité sur le test retenu;
7. enregistrer les limites et le statut réel.

Les langages sans runtime, compilateur ou bibliothèques adaptés ne sont pas supprimés silencieusement : ils reçoivent un blocage précis et une preuve minimale de faisabilité. Les pistes assembleur portent sur les kernels numériques et leurs benchmarks.

## Phase 3 — chaîne d'outils locale et spécialisation code

- [ ] CLI native de bout en bout pour préparer les données, entraîner, évaluer, exporter, recharger et générer sans Ollama ni fournisseur externe.
- [ ] Manifeste de données et licences, déduplication, filtrage et séparation train/validation/test.
- [ ] Reprise après interruption, checkpoints atomiques, journaux et budgets de ressources.
- [ ] Tests de compilation et d'exécution du code généré en sandbox.
- [ ] Mesurer sur des fichiers/problèmes tenus à l'écart.
- [ ] Ne revendiquer une spécialisation que si elle améliore une baseline mesurée.

## Phase 4 — runtime, performance et extensions

- [ ] Runtime d'inférence local autonome, avec limites mémoire/temps et erreurs explicites.
- [ ] Profilage CPU avant optimisation.
- [ ] SIMD/GPU uniquement avec tests de correction et benchmarks reproductibles.
- [ ] Quantification uniquement avec mesures de qualité, mémoire et vitesse.
- [ ] Augmenter les tailles après preuve de stabilité et ressources disponibles.

## Conditions de publication

Aucun résultat n'est déclaré terminé sans artefacts inspectables. Pas de poids inventés, pas de chiffres supposés, pas de données sans licence vérifiée, pas de commit de grands checkpoints au dépôt Git. Les publications, fusions et opérations destructives nécessitent une approbation distincte.
