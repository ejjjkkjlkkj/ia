# Agent autonome local — mode borné

`tools/local_autonomous_agent.py` est un premier agent de programmation utilisant un serveur Ollama local. Il ne constitue pas encore un système autonome permanent ni un agent multi-dépôts.

## Prérequis

- Python 3.10 ou plus récent.
- Git.
- Ollama démarré sur `127.0.0.1:11434` et un modèle local disponible. Le modèle par défaut est `qwen3-coder:30b`; surcharge possible via `OLLAMA_MODEL`.
- Un dépôt Git propre et une tâche écrite dans un fichier UTF-8 situé hors du dépôt ou déjà versionné.

Aucune clé API ni connexion à un fournisseur cloud n'est requise par le script. Les dépendances Python sont limitées à la bibliothèque standard.

## Exécution

Depuis la racine du dépôt, commencer en aperçu :

```bash
python tools/local_autonomous_agent.py --repo . --task-file C:/chemin/vers/tache.txt
```

L'aperçu imprime le résumé et le diff proposé sans modifier les fichiers. Après inspection humaine, autoriser explicitement l'application :

```bash
python tools/local_autonomous_agent.py --repo . --task-file C:/chemin/vers/tache.txt --apply
```

Chaque exécution écrit par défaut un rapport JSON avec identifiant unique, empreintes SHA-256 de la tâche et du patch, fichiers concernés, commandes exactes, codes de sortie et extraits de logs dans `~/.ia-agent/last-run.json` (remplaçable avec `--report-file`). Le contenu intégral de la tâche n'est pas enregistré.

Pour appliquer puis lancer les contrôles fixes (syntaxe Python, JSON et suite pytest), avec retour arrière automatique du patch si un contrôle échoue :

```bash
python tools/local_autonomous_agent.py --repo . --task-file C:/chemin/vers/tache.txt --apply --verify
```

Le script refuse un worktree sale, limite la taille de la tâche, de la réponse et du patch, vérifie les chemins, rejette les modifications de workflows GitHub et d'artefacts binaires, puis lance `git apply --check` avant application.

## Limites de sécurité et de capacité

- L'agent n'exécute aucune commande proposée par le modèle.
- Sans `--verify`, il ne lance pas automatiquement les tests. Avec `--verify`, il n'exécute que des contrôles prédéfinis, annule le patch si l'un échoue, et ne crée jamais de commit, ne pousse pas et ne fusionne pas.
- Le patch doit être revu, puis les tests du projet exécutés séparément.
- Le modèle peut produire du code incorrect ou malveillant; les garde-fous de chemins ne remplacent pas une revue.
- Le script ne constitue pas une boucle 24/7 et ne prouve pas que l'agent est installé ou opérationnel sur une machine particulière.
- Les capacités de raisonnement, la qualité du code et les performances du modèle ne sont pas certifiées par la seule présence du script.

## Tests

```bash
python -m pytest -q tests/test_local_autonomous_agent.py
```

Les tests couvrent les contrôles de diff; ils ne prouvent ni l'accessibilité du serveur Ollama, ni la qualité des patches générés, ni le fonctionnement d'une boucle autonome permanente.
