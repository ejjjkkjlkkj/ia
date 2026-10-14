# Modèle IA — Python

**Statut : PARTIAL.** Une baseline statistique bigramme exécutable existe dans `src/ia_reference/ngram.py`. Elle est entraînable depuis un corpus UTF-8, génère du texte de façon déterministe, évalue un fichier distinct et écrit/recharge un checkpoint JSON avec vérification SHA-256.

Cette baseline n'est **ni un réseau neuronal ni un Transformer**. Elle valide une première chaîne d'exécution reproductible, mais ne satisfait pas les critères de `MODEL-SPEC.md`. La matrice CI Linux/Windows/macOS doit confirmer les tests avant que l'entraînement et l'inférence soient déclarés validés.

## Exécuter

Voir [la documentation de la baseline](../../docs/REFERENCE_MODEL_BASELINE.md).

Depuis la racine du dépôt :

```bash
PYTHONPATH=src python -m ia_reference.ngram train corpus.txt model.json
PYTHONPATH=src python -m ia_reference.ngram evaluate model.json heldout.txt
PYTHONPATH=src python -m ia_reference.ngram generate model.json --prompt "the screen reader" --max-tokens 20
PYTHONPATH=src python -m unittest discover -s tests -v
```

Le modèle est construit à partir du texte fourni. Aucun modèle préentraîné, service cloud, clé API ou dépendance tierce n'est requis.

## Statut par capacité

- Baseline statistique implémentée : PARTIAL
- Réseau neuronal / Transformer : NOT_IMPLEMENTED
- Entraînement de la baseline exécuté et validé par CI : NOT_VALIDATED
- Checkpoint avec vérification d'intégrité : IMPLEMENTED, tests CI en attente
- Inférence de la baseline : IMPLEMENTED, tests CI en attente
- Modèle de production / spécialisation code : NOT_IMPLEMENTED
