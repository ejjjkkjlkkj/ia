# Feuille de route multimodale : images, vidéo, jeux, cinéma et médias

## Objectif produit

NEXORA IA doit évoluer vers une plateforme multimodale capable de comprendre, créer, transformer et analyser, lorsque les composants nécessaires sont réellement disponibles, des images, vidéos, animations, jeux vidéo, scènes 3D, audio, scénarios, montages et œuvres cinématographiques. Cela inclut la préproduction (synopsis, scénarios, storyboard), la production (images, animation, audio, vidéo), la postproduction (montage, sous-titres, doublage autorisé, effets) et les prototypes de jeux (code, logique, niveaux, tests).

Cette feuille de route définit la cible ; elle ne prétend pas que ces capacités sont déjà implémentées.

## Principes

- Distinguer compréhension, génération, édition, rendu et production complète.
- Ne jamais déclarer une tâche réussie si la chaîne n'a pas réellement été exécutée.
- Local d'abord ; tout traitement distant doit être explicite, désactivable et soumis au consentement.
- Utiliser uniquement des données, modèles, voix, musiques, images, vidéos et actifs dont la provenance et la licence sont vérifiées. Ne pas contourner les DRM ou les contrôles d'accès.
- Respecter les droits d'auteur, les droits à l'image, le consentement vocal et la transparence ; ne pas présenter un deepfake comme authentique.
- Isoler les fichiers, codecs, plugins et projets de jeux non fiables ; limiter les ressources.
- Accessibilité universelle : clavier, lecteur d'écran, sous-titres, transcription, descriptions, remappage, commandes alternatives, options sensorielles et difficulté configurable.
- Documenter les formats, codecs, métadonnées, dépendances, limites et empreintes des artefacts.
- Évaluer qualité, conformité au prompt, cohérence temporelle, artefacts, latence, mémoire/VRAM, robustesse, accessibilité et droits.

## Domaines à construire et à valider

### Images
Import, décodage, description, OCR accessible, compréhension visuelle, génération et édition. Évaluer la conformité, les artefacts, la fidélité des modifications, la provenance et l'accessibilité. La vision et la génération sont deux capacités différentes.

### Vidéo et animation
Import/export, timeline, découpage, transitions, stabilisation, sous-titres, transcription et génération de clips à partir de texte ou d'images. Évaluer la continuité des objets/personnages, le mouvement, la synchronisation audio/vidéo, la fréquence d'images et les ressources. Une vidéo assemblée à partir d'images fixes n'est pas la preuve d'un modèle de génération vidéo.

### Cinéma et production audiovisuelle
Synopsis, scénarios, dialogues, découpage, storyboard, plans de tournage, continuité, montage et sous-titres. Un scénario n'est pas un film terminé : il faut des médias rendus, montage, son, droits et contrôles de qualité. Les voix, musiques et images doivent avoir les autorisations requises.

### Jeux vidéo
Aide à produire le code, scènes, niveaux, dialogues, quêtes, textures, sons, animations et prototypes. Les adaptateurs de moteurs doivent être testés explicitement. Vérifier compilation, démarrage, commandes, sauvegardes, collisions, performances, accessibilité, sécurité et jouabilité. Générer du code ne prouve pas qu'un jeu complet est jouable.

### Audio, voix et 3D
Transcription, synthèse, mixage, synchronisation, génération/édition de maillages, matériaux, éclairage, rigging, animation et export. Séparer les preuves pour la parole, la musique, les effets, les scènes 3D interactives et les rendus.

### Orchestration multimodale
Chaque pipeline doit enregistrer entrée, prétraitement, modèle/version, paramètres, sortie, provenance, métriques et erreurs. Prendre en charge annulation, reprise, limites de ressources et statut de chaque étape : local, distant, simulé ou indisponible.

## Architecture proposée

1. Contrats de tâches versionnés et interfaces de plugins.
2. Couche de formats/codecs avec validation des fichiers et limites de ressources.
3. Runtime local, gestionnaire de modèles, licences et empreintes.
4. Pipelines distincts image, vidéo, audio, 3D et jeux ; ne pas confondre ces moteurs avec le modèle de langage.
5. Orchestrateur et registre de provenance.
6. Benchmarks reproductibles, tests de droits, sécurité, accessibilité et évaluations humaines.
7. Interface clavier/lecteur d'écran et commandes batch/API documentées.

Les modèles externes éventuels peuvent servir à des comparaisons ou à des adaptateurs facultatifs ; ils ne doivent pas être présentés comme entraînés par ce dépôt.

## Statuts de preuve

- NOT_IMPLEMENTED : aucun moteur opérationnel.
- PARTIAL : certains composants existent, la chaîne complète ne fonctionne pas.
- BLOCKED : blocage identifié (modèle, licence, dépendance ou matériel).
- NOT_VALIDATED : code présent, preuves d'exécution/qualité insuffisantes.
- PASS : exécution reproductible, artefact réel, hash, configuration, logs, tests et critères de qualité vérifiés.

## Priorités

1. Inventorier code, modèles, codecs, dépendances, licences et capacités réelles.
2. Définir les schémas de tâches, artefacts et preuves.
3. Réaliser une première chaîne d'image locale de bout en bout si modèle et matériel sont disponibles.
4. Ajouter les pipelines audio/vidéo avec tests de synchronisation et de cohérence.
5. Ajouter les prototypes de jeux et un adaptateur de moteur, sandbox et tests de jouabilité.
6. Construire les workflows de préproduction et postproduction cinéma.
7. Ajouter 3D et orchestration selon les résultats mesurés.
8. Ne déclarer une capacité prête qu'après validation fonctionnelle, accessibilité, sécurité et droits.

## État initial

PARTIAL / NOT_VALIDATED. Ce document formalise la cible mais ne prouve pas l'existence d'un générateur d'images, d'un modèle vidéo, d'un moteur 3D ou d'un générateur de jeux complet. Un inventaire technique et des exécutions réelles sont nécessaires.
