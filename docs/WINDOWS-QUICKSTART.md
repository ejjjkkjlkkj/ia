# NEXORA IA — démarrage sous Windows

## Périmètre de cette version

Cette version fournit un paquet source portable et les outils Python de référence. Elle n'est pas un exécutable autonome (.exe) et n'embarque pas de modèle de langage de production. Le modèle neuronal inclus est une baseline expérimentale de prédiction du prochain octet. Les capacités multimodales complètes, le lecteur d'écran complet et le runtime UEFI ne sont pas annoncés comme opérationnels.

## Prérequis

- Windows 10 ou Windows 11 x64.
- Python 3.12 ou version ultérieure, disponible avec la commande `py` ou `python`.
- PowerShell 7 recommandé, Windows PowerShell compatible pour les commandes ci-dessous.
- Aucun compte cloud, clé API ou service distant n'est requis pour exécuter les outils Python de référence.

## Démarrage rapide guidé

Depuis PowerShell, dans le dossier extrait, lancez la démonstration locale :

```powershell
.\windows\Start-IA.ps1 -Mode Demo
```

Pour lancer les tests complets, installez pytest une seule fois, puis exécutez :

```powershell
py -3 -m pip install pytest
.\windows\Start-IA.ps1 -Mode Verify
```

Le lanceur utilise Python localement, sans clé API ni envoi du corpus vers un service distant. Le mode Demo crée ses fichiers temporaires dans le répertoire temporaire Windows puis les supprime.

## Vérifier Python

Dans PowerShell, depuis le dossier extrait :

```powershell
py -3 --version
```

Si `py` n'est pas disponible :

```powershell
python --version
```

## Lancer les tests

Installez le seul outil de test, si nécessaire :

```powershell
py -3 -m pip install pytest
$env:PYTHONPATH = "src"
py -3 -m pytest -q
```

Le résultat est valide uniquement pour les tests effectivement exécutés sur cette machine. Un succès GitHub Actions ne prouve pas la compatibilité avec chaque PC Windows.

## Entraîner une baseline minuscule

Préparez deux fichiers UTF-8 distincts : `train.txt` pour l'entraînement et `heldout.txt` pour l'évaluation. Utilisez uniquement des données dont l'utilisation est autorisée. L'évaluateur refuse que les deux fichiers aient exactement le même contenu, mais ne détecte pas les recouvrements partiels.

```powershell
$env:PYTHONPATH = "src"
py -3 -m ia_reference.tiny_neural train .\train.txt .\model.json --epochs 3 --seed 7 --learning-rate 0.05 --embedding-dim 8
py -3 tools\evaluate_tiny_neural.py .\model.json .\train.txt .\heldout.txt --report .\reports\evaluation.json
py -3 -m ia_reference.tiny_neural generate .\model.json --prompt "Bonjour" --max-bytes 64
```

Le checkpoint est un modèle expérimental de prédiction d'octets, pas un Transformer/LLM de production. La génération peut être incohérente et ne doit pas être utilisée comme source fiable sans validation humaine.

## Paquet Windows CI

Le workflow GitHub Actions **Windows validation and portable package** exécute les tests et la démonstration sur un runner Windows, puis construit un ZIP source nommé `nexora-ia-windows-source` avec un fichier de somme SHA-256. Sur les exécutions de branche, récupérez l'artefact dans la section **Artifacts** (rétention de 30 jours). La poussée d'un tag versionné `v*` publie également une GitHub Release avec le ZIP et sa somme SHA-256.

## Limites connues

- Aucun binaire autonome signé ni programme d'installation Windows n'est produit par ce workflow.
- Pas de Transformer universel de production validé.
- Pas de génération image/vidéo/audio ou de jeu complet revendiquée comme prête à l'emploi.
- Pas de lecteur d'écran complet ni de validation UEFI sur matériel physique.
- Ne jamais interpréter une réussite de tests unitaires ou d'émulation comme une validation matérielle ou comme une preuve de qualité sémantique.
