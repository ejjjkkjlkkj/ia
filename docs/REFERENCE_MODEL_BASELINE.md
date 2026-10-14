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

## Limite obligatoire

Cette implémentation est une baseline statistique réellement entraînable. **Ce n'est pas un réseau neuronal, pas un Transformer, et pas un modèle IA de production.** Elle valide le premier cycle exécutable données → apprentissage → checkpoint → rechargement → génération/évaluation. Elle ne satisfait pas à elle seule les critères de `MODEL-SPEC.md`.

## Lancer localement

```bash
PYTHONPATH=src python -m ia_reference.ngram train corpus.txt model.json
PYTHONPATH=src python -m ia_reference.ngram evaluate model.json heldout.txt
PYTHONPATH=src python -m ia_reference.ngram generate model.json --prompt "the screen reader" --max-tokens 20
PYTHONPATH=src python -m unittest discover -s tests -v
```

Les corpus et checkpoints sont générés localement ; aucun secret, service cloud ou modèle préentraîné n'est requis. Les évaluations doivent utiliser des exemples distincts de ceux d'entraînement pour mesurer une généralisation réelle.
