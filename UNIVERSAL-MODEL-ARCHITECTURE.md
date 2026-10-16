# Architecture du modèle universel — contrat commun

**Statut : baselines statistiques et prototype neuronal minuscule implémentés ; modèle neuronal universel de type Transformer NOT_IMPLEMENTED. Le prototype neuronal n'a pas encore de preuve CI réussie ni de benchmark de qualité publié.**

## Objectif produit

Construire un modèle commun capable de traiter les langues naturelles et les langages de programmation dans un même espace de représentation, avec un checkpoint partagé. Le modèle ne doit pas être remplacé par un ensemble obligatoire de modèles indépendants par langage. Les dossiers `models/<id>/` sont des ports d'implémentation, kernels, benchmarks ou adaptateurs runtime du même contrat mathématique, pas une affirmation qu'il faut entraîner un modèle distinct par langage.

« Universel » est un objectif à démontrer par des benchmarks, pas une propriété acquise parce que l'entrée accepte du texte.

## Prototype neuronal minimal présent

`src/ia_reference/tiny_neural.py` entraîne un prédicteur neuronal du prochain octet avec embeddings, couche linéaire, softmax/cross-entropy et SGD, en Python standard library. Il possède des limites de taille/époques, un checkpoint JSON canonique avec SHA-256, une évaluation perplexité et une génération gloutonne. Les tests dédiés sont dans `tests/test_tiny_neural.py`. Ce prototype valide un chemin d'entraînement/inférence réduit seulement; il ne contient ni attention causale, ni blocs Transformer, ni corpus de qualité, ni benchmark multilingue/code, et ne satisfait pas le critère de release du modèle universel.

## Architecture cible

1. **Couche d'entrée universelle** : couverture UTF-8, sans tokenizer propre à une langue comme condition préalable. La première baseline utilise les octets UTF-8 (256 valeurs possibles) plus BOS/EOS réservés. Cette méthode accepte les écritures Unicode et la syntaxe des langages, mais ne garantit ni compréhension ni qualité.
2. **Tokenisation améliorée** : comparer byte-level, tokenizer Unicode et tokenizer hybride sous un format/versionnage commun. Ne changer que sur résultats mesurés sur langues naturelles et code.
3. **Modèle neuronal commun** : modèle causal compact avec embeddings, attention causale, MLP, normalisation, perte du prochain token, gradients et optimiseur. Un seul contrat de poids/version pour toutes les entrées.
4. **Entraînement mixte** : corpus multilingues et multi-langages de programmation, provenance/licence vérifiées, déduplication et séparation train/validation/test. Publier les proportions, les langues couvertes et les limites.
5. **Spécialisation sans fragmentation obligatoire** : capacités de code, accessibilité, UEFI et OS évaluées comme tâches du même modèle. Des adaptateurs ou experts ne sont retenus que si les benchmarks prouvent leur valeur; ils ne remplacent pas le modèle commun.
6. **Interopérabilité** : même configuration, noms/formes des tenseurs, dtype, ordre des poids, tokenisation versionnée et vecteurs de référence pour toutes les implémentations.
7. **Exécution portable** : cœur CPU de référence d'abord; SIMD/GPU et runtimes spécifiques ensuite. Les pistes freestanding/UEFI sont limitées par la mémoire, le compilateur, le runtime et les pilotes disponibles; ne pas prétendre qu'un modèle de grande taille fonctionne directement dans UEFI.

## Baseline réellement disponible

`src/ia_reference/universal.py` est un modèle statistique bigramme sur octets UTF-8, entraînable localement sans dépendance tierce. Il peut accepter des corpus mixtes, écrire/recharger un checkpoint avec SHA-256, générer et mesurer la perplexité sur un corpus séparé. Il **n'est pas un Transformer**, ne comprend pas les langages et ne valide pas encore un modèle universel de qualité.

La baseline `src/ia_reference/ngram.py` reste une référence mot/bigramme versionnée en schéma 2. Elle inclut un token `UNK` explicite pour les tokens hors vocabulaire, des probabilités lissées normalisées, une validation structurelle stricte du checkpoint et une écriture atomique avec SHA-256. Elle ne représente pas le modèle cible et les anciens checkpoints de schéma 1 sont rejetés explicitement.

## Portes de validation

- **G0 — Couverture** : corpus multilingue et code, UTF-8 valide, tests d'entrée.
- **G1 — Mathématiques** : vecteurs numériques communs et tests différentiels.
- **G2 — Apprentissage** : entraînement déterministe terminé, perte finie et amélioration sur une tâche tenue à l'écart.
- **G3 — Checkpoint** : version de schéma, formes contrôlées, hash, sauvegarde/rechargement dans un nouveau processus.
- **G4 — Qualité universelle** : résultats séparés par langue naturelle, famille de scripts, langage de programmation et tâche; comparaison à des baselines; aucun agrégat ne doit cacher une régression.
- **G5 — Portabilité** : même checkpoint exécuté par plusieurs ports, avec tolérances documentées.
- **G6 — Sécurité et déploiement** : sandbox, limites mémoire/temps, dépendances recensées et preuve séparée pour chaque OS ou cible UEFI.

Un PASS à une porte ne donne pas automatiquement PASS aux suivantes. Compilation, couverture UTF-8, CI multi-OS et exécution QEMU ne prouvent pas la qualité du modèle ni le fonctionnement matériel.

## Commandes de la baseline

```bash
PYTHONPATH=src python -m ia_reference.universal train corpus-mixte.txt checkpoint.json
PYTHONPATH=src python -m ia_reference.universal evaluate checkpoint.json test-tenu-a-part.txt
PYTHONPATH=src python -m ia_reference.universal generate checkpoint.json --prompt "fn main()" --max-bytes 64
PYTHONPATH=src python -m unittest discover -s tests -v
```

Les données d'évaluation doivent être séparées de l'entraînement. Le checkpoint de test n'est pas un modèle de production.
