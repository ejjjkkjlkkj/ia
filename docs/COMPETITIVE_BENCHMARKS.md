# Protocole de comparaison concurrentielle — IA

Statut au 2026-10-16 : **SPECIFIED / NOT RUN**. Ce protocole ne prétend pas que notre modèle dépasse déjà Claude, Qwen ou Llama. Aucun score ne doit être publié sans artefact, commande, configuration et résultats reproductibles.

## Objectif

Construire un modèle et une chaîne d'outils que l'on peut comparer honnêtement aux familles Claude, Qwen et Llama sur les mêmes tâches. L'objectif de dépassement est une cible de recherche, pas un résultat acquis.

## Références concurrentes

- **Qwen** : vérifier la version ouverte la plus récente et son identifiant exact au moment de chaque campagne. Le billet officiel Qwen3.8-Max du 3 août 2026 annonce une famille 2,4T paramètres / 95B actifs et indique que les poids ouverts sont publiés ou prévus; ne pas supposer que chaque variante est librement redistribuable. Enregistrer le dépôt, le hash des poids et la licence réellement attachée à la variante testée.
- **Llama** : sélectionner une version et une taille précises; enregistrer le modèle, la licence et les conditions d'utilisation. « Llama » seul n'est pas une référence reproductible.
- **Claude** : modèle propriétaire distant. Sans accès autorisé à ce modèle, utiliser uniquement des résultats publics vérifiables et marquer la comparaison directe **BLOCKED**. Ne pas présenter une comparaison indirecte comme un benchmark face-à-face.
- **Notre modèle** : checkpoint exact, hash SHA-256, configuration, tokenizer, corpus/licences, étape d'entraînement, runtime et précision numérique.

Les noms de famille ne sont jamais des versions de benchmark suffisantes. Chaque ligne doit fixer modèle, date, quantification, contexte et matériel.

## Périmètre de tests

Chaque campagne doit couvrir séparément :

1. **Langue et instruction** : respect des contraintes, résumé, extraction structurée, français et anglais.
2. **Raisonnement** : problèmes déterministes, logique multi-étapes, calcul avec réponse vérifiable.
3. **Code** : génération, correction, tests unitaires cachés, exécution en bac à sable sans accès réseau.
4. **Utilisation d'outils** : choix d'outil, schéma d'arguments, gestion d'erreurs, arrêt correct et absence d'actions non autorisées.
5. **Contexte long** : récupération d'informations positionnées, citations des passages fournis et détection d'informations absentes.
6. **Fiabilité** : taux d'hallucination sur questions sans réponse, cohérence, sorties malformées, robustesse aux prompts adversariaux.
7. **Efficacité locale** : latence médiane et p95, tokens/s, RAM/VRAM, taille du checkpoint, énergie si instrumentée, démarrage à froid.
8. **Sécurité et confidentialité** : refus appropriés, injection de prompt, fuite de données de test, absence d'appels réseau non déclarés.

Publier les scores par catégorie. Un score composite seul est insuffisant et ne doit pas masquer une régression.

## Règles pour des preuves comparables

- Jeux de données versionnés avec licence vérifiée; séparer entraînement, validation et test avant l'entraînement.
- Pas de données de test dans l'entraînement, le prompt système ou les exemples de démonstration.
- Même jeu de tâches, même limite de tokens, même budget d'outils et règles de notation; documenter les différences inévitables.
- Répéter les évaluations stochastiques avec graines multiples; publier moyenne, dispersion et nombre d'exemples.
- Pour le code, exécuter les tests cachés dans un bac à sable avec délais et ressources limités.
- Mesurer les modèles dans des conditions locales reproductibles lorsque les poids et licences le permettent. Les résultats publiés par un fournisseur sont notés **VENDOR-REPORTED**, pas **INDEPENDENT**.
- Stocker les prompts, sorties, verdicts, durées, versions, commandes, journaux expurgés et hashes des données/poids dans un artefact de campagne.
- Toute comparaison non exécutable ou sans données brutes est **UNVERIFIED**; toute référence inaccessible est **BLOCKED**.
- Vérifier la licence avant de copier des poids, du code ou des données dans ce dépôt. Ne pas committer des poids tiers volumineux ou des secrets; préférer un manifeste d'acquisition avec source, licence et hash.

## Critère de « dépassement »

Nous ne déclarerons « dépasse Qwen/Llama/Claude » que si notre modèle obtient une amélioration statistiquement crédible sur un ensemble de test indépendant préenregistré, sans régression critique dans les catégories sécurité, fiabilité et code, et si le protocole et les artefacts sont publics. Les comparaisons directes ne sont valables qu'entre modèles effectivement exécutés dans des conditions comparables. Une victoire sur une seule tâche ne prouve pas une supériorité générale.

## État actuel de la chaîne

À ce stade, le dépôt contient une référence numérique Python et des prototypes isolés, pas encore un modèle Transformer complet entraîné et validé de bout en bout. Les éléments suivants restent des portes de sortie obligatoires :

- modèle causal complet (embeddings, attention masquée, MLP, résidus, normalisation, tête de sortie);
- rétropropagation et optimiseur vérifiés par différences finies;
- entraînement reproductible sur données synthétiques, puis corpus licenciés;
- sauvegarde/reprise et chargement vérifiés par hash;
- runtime d'inférence local sans Ollama, API ni service cloud obligatoire;
- harness de benchmark, évaluations indépendantes et résultats bruts;
- packaging de version et tests d'installation depuis une machine propre.

La priorité est de faire fonctionner cette chaîne complète avant de revendiquer une comparaison gagnée.
