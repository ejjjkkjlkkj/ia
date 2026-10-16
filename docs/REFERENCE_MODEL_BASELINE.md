# Modèle de référence exécutable — baseline bigramme

## Ce qui fonctionne dans cette première tranche

Le module `src/ia_reference/ngram.py` implémente, sans dépendance externe ni accès réseau :

- entraînement déterministe d'un modèle statistique bigramme à partir d'un texte UTF-8 ;
- lissage add-alpha ;
- génération déterministe ;
- évaluation sur un fichier de texte distinct ;
- sauvegarde et rechargement d'un checkpoint JSON avec vérification SHA-256 ;
- commandes CLI `train`, `evaluate` et `generate` ;
- tests unitaires et smoke tests sur Linux, Windows et macOS, Python 3.11–3.13.

Le dépôt contient également `src/ia_reference/tiny_neural.py`, un petit prédicteur neuronal du prochain octet entraînable depuis zéro, avec évaluation et checkpoints hachés. Ce prototype n'est pas un Transformer et sa qualité n'est pas réputée validée.

## Kernels numériques de référence

`src/ia_reference/numeric.py` fournit maintenant des opérations FP64 de référence, uniquement avec la bibliothèque standard Python :

- multiplication matrice-vecteur et matrice-matrice ;
- softmax stable ;
- perte cross-entropy pour une cible ;
- contrôles de dimensions, de valeurs non finies, de booléens et de magnitude ;
- tests de référence dans `tests/test_numeric.py`.

`src/ia_reference/causal_attention.py` ajoute l'attention causale scaled dot-product. Il s'agit d'un noyau isolé, pas d'une couche Transformer complète. Ces kernels Python ne prouvent ni une implémentation C/Rust, ni la rétropropagation complète, ni un entraînement Transformer.

## Limite obligatoire

La baseline bigramme et le prédicteur neuronal sont réellement entraînables à petite échelle, mais **ils ne sont pas des modèles IA de production**. Le dépôt ne revendique pas encore un modèle universel complet. Le cycle de production restant doit couvrir le contrat de tenseurs, le modèle causal entraînable avec gradients, l'optimiseur, le pipeline de données traçable, l'évaluation retenue, l'interopérabilité des checkpoints et le runtime d'inférence.

## Lancer localement

Depuis la racine du dépôt :

```bash
PYTHONPATH=src python -m ia_reference.ngram train corpus.txt model.json
PYTHONPATH=src python -m ia_reference.ngram evaluate model.json heldout.txt
PYTHONPATH=src python -m ia_reference.ngram generate model.json --prompt "the screen reader" --max-tokens 20
PYTHONPATH=src python -m unittest discover -s tests -v
```

Les corpus et checkpoints sont générés localement ; aucun secret, service cloud ou modèle préentraîné n'est requis. Les évaluations doivent utiliser des exemples distincts de ceux d'entraînement pour mesurer une généralisation réelle.
