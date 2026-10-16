# IA — construire des modèles IA avec le catalogue commun de langages

## Objectif exact

Ce dépôt vise à construire **un modèle IA universel partagé** pour les langues naturelles et les langages de programmation, avec un contrat mathématique et un format de poids communs, puis à l'implémenter/porter dans les langages du catalogue synchronisé avec `ejjjkkjlkkj/accessibility`. Il ne doit pas être réduit à un agent qui appelle un modèle existant ni à des profils par langage au-dessus d'un modèle tiers.

Pour chaque langage du catalogue, le travail vise à contribuer au **même modèle universel** via un port de référence, des kernels, des outils d'entraînement/inférence ou un runtime explicitement documenté :
1. les composants du modèle (tenseurs, opérations, couches, attention, embeddings, perte, rétropropagation et optimiseur) ;
2. le pipeline d'entraînement et de validation ;
3. l'import/export des poids et le format de checkpoint ;
4. l'inférence locale et les tests reproductibles ;
5. une spécialisation pour les tâches de code, dont le langage ciblé, si les données, les ressources et les benchmarks le justifient.

Les langages partagent une **spécification mathématique, un tokenizer versionné et un format de poids interopérable**. Chaque piste doit préciser ce qu'elle implémente réellement; les dossiers ne signifient pas qu'un modèle indépendant doit être entraîné pour chaque langage. Le partage d'un checkpoint prouve l'interopérabilité seulement si le chargement et les résultats sont testés.

## Contrat avec ACCESSIBILITY

Le contrat commun versionné est maintenu dans [ACCESSIBILITY — AI integration contract](https://github.com/ejjjkkjlkkj/accessibility/blob/feature/dark-redteam-from-scratch-20261015/docs/AI-ACCESSIBILITY-INTEGRATION-CONTRACT-V1.md). Il fixe la séparation des preuves, le mode sans IA, la confidentialité et les critères d'interopérabilité. La présence du contrat ne signifie pas que le modèle est entraîné ni que l'intégration est exécutée.

## Langage universel NEXORA

Le dépôt contient aussi le prototype initial du langage **NEXORA**, distinct du langage existant U : [spécification NEXORA](NEXORA-LANGUAGE-SPEC.md), lexer/parseur/interpréteur de référence dans `src/nexora_language.py`, et tests dans `tests/test_nexora_language.py`. Le prototype gère un sous-ensemble syntaxique avec identifiants Unicode et arithmétique; il n'est pas encore un compilateur ni un langage prêt pour l'OS/UEFI. Les backends et la représentation intermédiaire seront ajoutés après stabilisation de la grammaire et des tests de conformité.

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


## Modèle universel partagé

L'objectif est **un modèle commun**, pas une collection obligatoire de modèles séparés. `models/<id>/` décrit les ports, kernels, runtimes, benchmarks et limites par langage. Une spécialisation ou un expert ne sera ajouté que si des mesures montrent un gain réel. La première implémentation exécutable byte-level est documentée dans [UNIVERSAL-MODEL-ARCHITECTURE.md](UNIVERSAL-MODEL-ARCHITECTURE.md); elle accepte l'UTF-8 de langues et de code, mais reste une baseline statistique et ne prouve pas encore une compréhension universelle.

Un prototype neuronal minuscule entraînable depuis zéro est disponible dans `src/ia_reference/tiny_neural.py` (stdlib Python uniquement). Il utilise des embeddings d'octets, une couche linéaire de prédiction du prochain octet, une perte cross-entropy et une descente de gradient SGD; il fournit entraînement déterministe, checkpoint JSON haché, évaluation et génération gloutonne. Commandes depuis la racine : `PYTHONPATH=src python -m ia_reference.tiny_neural train train.txt model.json --epochs 3`, puis `evaluate model.json heldout.txt` et `generate model.json --prompt "hello"`. Ce prototype est une preuve de pipeline neuronal minimal, **pas** un Transformer, pas un LLM de production et pas une preuve d'universalité; les données et les résultats de qualité doivent encore être évalués.

Voir [MODELS-INDEX.md](MODELS-INDEX.md) pour la cartographie des pistes d'implémentation.


NEXORA IR v1 contract: [NEXORA-IR-V1.md](NEXORA-IR-V1.md). The IR is a bounded JSON serialization of the prototype AST, not a native compiler backend.

## Séparation obligatoire des pistes

- [Implémentations indépendantes par langage et rôle distinct de NEXORA](docs/INDEPENDENT-LANGUAGE-IMPLEMENTATIONS-AND-NEXORA.md)
