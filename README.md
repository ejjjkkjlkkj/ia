# IA — construire des modèles IA avec le catalogue commun de langages

## Objectif exact

Ce dépôt sert à **fabriquer les modèles IA eux-mêmes** en utilisant les mêmes langages et identifiants que `ejjjkkjlkkj/accessibility`. Il ne doit pas être réduit à un agent qui appelle un modèle existant, à des adaptateurs de compilateurs, ni à des profils par langage au-dessus d'un unique modèle tiers.

Pour chaque langage du catalogue, le travail vise à implémenter, selon les capacités réelles du langage :
1. les composants du modèle (tenseurs, opérations, couches, attention, embeddings, perte, rétropropagation et optimiseur) ;
2. le pipeline d'entraînement et de validation ;
3. l'import/export des poids et le format de checkpoint ;
4. l'inférence locale et les tests reproductibles ;
5. une spécialisation pour les tâches de code, dont le langage ciblé, si les données, les ressources et les benchmarks le justifient.

Les langages peuvent partager une **spécification mathématique et un format de poids interopérable**, mais chaque piste doit contenir du code qui construit, entraîne ou exécute réellement le modèle dans ce langage. Le partage d'un fichier de poids ne prouve pas qu'un modèle a été entraîné dans ce langage.

## Règles de vérité

- Aucun modèle n'est déclaré entraîné tant que les poids produits, la configuration, les données, la commande, les journaux, le hash et les résultats sur un jeu de test tenu à l'écart ne sont pas disponibles.
- Distinguer strictement : modèle implémenté, entraînement exécuté, entraînement terminé, qualité évaluée et inférence validée.
- Ne pas renommer les poids d'un modèle externe pour prétendre avoir fabriqué un nouveau modèle.
- Les modèles préentraînés externes sont facultatifs pour comparaison ou amorçage clairement documenté, jamais présentés comme un modèle créé par ce dépôt.
- Les données doivent être synthétiques ou avoir une provenance et une licence vérifiées; séparer entraînement, validation et test.
- Ne pas committer de poids volumineux, secrets, données privées ou corpus non licenciés. Utiliser les artefacts CI ou le stockage prévu.
- Le développement local est prioritaire; aucun fournisseur cloud ou clé API n'est obligatoire.

## Catalogue commun

Voir [LANGUAGE-CATALOG.md](LANGUAGE-CATALOG.md). Les IDs doivent correspondre à ceux du dépôt accessibilité. Le catalogue comprend les langages systèmes, les candidats de faisabilité, les langages hébergés et les assembleurs d'architecture. Chaque piste conserve ses propres preuves et bloqueurs.

## Architecture du modèle à construire

1. **Spécification de référence** : vocabulaire, tokenisation, tenseurs, dimensions, précision numérique, initialisation, couches, attention, fonction de perte et optimiseur.
2. **Cœur numérique** : opérations scalaires/vectorielles, tenseurs, gradients, rétropropagation, stabilité numérique et tests différentiels.
3. **Modèle minimal entraînable** : d'abord un petit modèle de langage causal, assez réduit pour être entraîné sur CPU; pas de promesse de qualité de production.
4. **Pipeline de données** : corpus synthétiques/licenciés, déduplication, filtrage, tokenisation, séparation train/validation/test et manifeste de provenance.
5. **Entraînement** : initialisation déterministe, batches, perte, gradients, clipping, optimiseur, checkpoints, reprise après interruption et journalisation.
6. **Évaluation** : perte/perplexité, tests de mémorisation/fuite, tâches de génération de code, compilation/tests sur données retenues, comparaison avec une baseline.
7. **Inférence** : chargement des checkpoints produits, génération déterministe et contrôlée, limites mémoire/temps et tests de non-régression.
8. **Optimisations par cible** : CPU d'abord; SIMD/GPU uniquement avec une implémentation et des résultats mesurés. Ne pas simuler une accélération.
9. **Interopérabilité** : format de poids et vecteurs de test partagés afin de comparer les implémentations entre langages.
10. **Applications** : après validation du modèle, intégrations facultatives avec l'agent de code et le projet d'accessibilité.

## Stratégie par langage

Chaque langage doit avoir une implémentation du cœur du modèle ou une couche d'entraînement/inférence qui appelle explicitement des primitives documentées de ce langage. Quand un runtime, des bibliothèques numériques ou une cible freestanding manquent, noter le blocage et construire les composants réalisables au lieu de prétendre que le modèle complet fonctionne.

Les assembleurs x86-64, AArch64 et RISC-V sont des pistes de noyaux numériques bas niveau et d'optimisations; ils ne sont pas artificiellement présentés comme des langages d'application complets à eux seuls. Les langages hébergés peuvent construire des modèles via leur runtime et leurs bibliothèques, mais ne sont pas considérés freestanding sans preuve.

## Statuts

- `NOT_IMPLEMENTED` : aucun composant implémenté.
- `PARTIAL` : code présent, mais critères du composant incomplets.
- `BLOCKED` : limitation précise de compilateur, runtime, bibliothèques, données ou matériel.
- `NOT_VALIDATED` : code présent, preuve insuffisante.
- `PASS` : commandes reproductibles, configuration, logs, poids/checkpoint avec hash et résultats d'évaluation disponibles.

## Première séquence d'exécution

1. Écrire la spécification mathématique commune et des vecteurs de test.
2. Implémenter un petit cœur de tenseurs et un modèle causal minimal en C puis Rust, avec tests CPU reproductibles.
3. Enregistrer un véritable entraînement minuscule de bout en bout et recharger le checkpoint pour l'inférence.
4. Vérifier l'interopérabilité des poids et les résultats numériques.
5. Porter le cœur aux autres langages du catalogue; maintenir un statut indépendant par piste.
6. Augmenter la taille et la spécialisation uniquement après mesures de qualité, mémoire, vitesse et reproductibilité.

## Sécurité et reproductibilité

Exécuter les tests et le code généré dans un environnement isolé avec limites de ressources. Exiger une approbation avant toute opération destructive, publication, fusion ou modification de firmware/NVRAM. Un test d'émulateur ne prouve pas le fonctionnement sur matériel physique.
